from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ============================================================
# Phase5 Multi-Edge Ablation Circuit Generator
# ------------------------------------------------------------
# Purpose:
#   - Read Phase5 parent circuit catalog
#   - Generate Phase5 multi-edge ablation circuit specifications
#   - Support perturbation orders k = 1, 2, 3
#   - Write per-circuit JSON files under:
#       circuits/{topology}/multi_ablation/
#   - Write/update:
#       circuits/phase5_multi_ablation_catalog.json
#
# Design policy:
#   - Preserve Phase4-style spec/catalog workflow
#   - Parent truth source: phase5_parent_catalog.json
#   - One ablation spec per (parent circuit, edge subset)
#   - Same dropped edges are intended to be removed from both CZ support layers
#   - Structural post-ablation metadata is computed at generation time
# ============================================================


PHASE_NAME = "Phase5"
STUDY_TITLE = "SRFM Quantum Phase5 Predictive Structural Response Study"

ROOT_DIR = Path(r"E:\SRFM_QUANTUM_PHASE5")
CIRCUITS_DIR = ROOT_DIR / "circuits"
PARENT_CATALOG_PATH = CIRCUITS_DIR / "phase5_parent_catalog.json"
ABLATION_CATALOG_PATH = CIRCUITS_DIR / "phase5_multi_ablation_catalog.json"

SUPPORTED_PERTURBATION_ORDERS = [1, 2, 3]
EXPECTED_TOPOLOGIES = {"ring6", "chain6", "random6"}


@dataclass
class MultiAblationCircuitSpec:
    circuit_id: str
    parent_circuit_id: str
    topology: str
    topology_class: str
    phase_role: str
    phase5_role: str
    n_qubits: int
    rx_ratio: float
    ry_ratio: float
    predicted_response_class: str
    ablation: Dict[str, Any]
    derived_topology_state: Dict[str, Any]
    edge_definition_ref: str
    gate_pattern: str
    notes: str


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def normalize_edge(edge: List[int] | Tuple[int, int]) -> Tuple[int, int]:
    a, b = edge
    return (a, b) if a <= b else (b, a)


def edge_name_map_from_parent(parent_record: Dict[str, Any]) -> Dict[str, List[int]]:
    """
    Convert parent edge list into named edge definition:
      [[0,1],[1,2],...] -> {"e0":[0,1], "e1":[1,2], ...}
    """
    return {f"e{i}": edge for i, edge in enumerate(parent_record["edges"])}


def infer_gate_pattern_for_topology(topology: str) -> str:
    if topology == "ring6":
        return "phase5_ring6_two_layer_profile_multi_edge_ablation"
    if topology == "chain6":
        return "phase5_chain6_two_layer_profile_multi_edge_ablation"
    if topology == "random6":
        return "phase5_random6_two_layer_profile_multi_edge_ablation"
    return "phase5_two_layer_profile_multi_edge_ablation"


def build_qiskit_metadata_stub(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase5 runtime metadata stub.
    This stays generator-side and does not require Qiskit.
    """
    return {
        "qiskit_ready": False,
        "qasm2_path": None,
        "qasm3_path": None,
        "n_layers": 4,  # Local A -> CZ A -> Local B -> CZ B
        "measurement_supported": ["X"],
        "noise_modes_supported": ["noisy_sim"],
        "default_shots": 4096,
        "topology": spec["topology"],
        "n_qubits": spec["n_qubits"],
        "ablation_supported": ["multi_edge_drop"],
        "supported_perturbation_orders": SUPPORTED_PERTURBATION_ORDERS,
    }


def validate_parent_catalog(catalog: Dict[str, Any]) -> None:
    if catalog.get("catalog_name") != "phase5_parent_catalog":
        raise ValueError("Unexpected catalog_name in Phase5 parent catalog.")

    records = catalog.get("records", [])
    if len(records) != 3:
        raise ValueError(f"Expected 3 parent records, found {len(records)}.")

    topology_set = {record["topology_name"] for record in records}
    if topology_set != EXPECTED_TOPOLOGIES:
        raise ValueError(
            f"Topology set mismatch. Found {topology_set}, expected {EXPECTED_TOPOLOGIES}"
        )

    fixed_settings = catalog.get("fixed_settings", {})
    if fixed_settings.get("measurement_basis") != "xbasis":
        raise ValueError("Expected measurement_basis=xbasis in parent catalog.")
    if fixed_settings.get("noise_model_tag") != "noisy_sim":
        raise ValueError("Expected noise_model_tag=noisy_sim in parent catalog.")
    if fixed_settings.get("shots") != 4096:
        raise ValueError("Expected shots=4096 in parent catalog.")


def build_adjacency(n_qubits: int, edges: List[List[int]]) -> Dict[int, set[int]]:
    adj: Dict[int, set[int]] = {i: set() for i in range(n_qubits)}
    for edge in edges:
        a, b = edge
        adj[a].add(b)
        adj[b].add(a)
    return adj


def count_components(n_qubits: int, edges: List[List[int]]) -> int:
    adj = build_adjacency(n_qubits, edges)
    visited: set[int] = set()
    components = 0

    for node in range(n_qubits):
        if node in visited:
            continue
        components += 1
        stack = [node]
        visited.add(node)
        while stack:
            cur = stack.pop()
            for nxt in adj[cur]:
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append(nxt)
    return components


def has_cycle_undirected(n_qubits: int, edges: List[List[int]]) -> bool:
    adj = build_adjacency(n_qubits, edges)
    visited: set[int] = set()

    def dfs(node: int, parent: int) -> bool:
        visited.add(node)
        for nxt in adj[node]:
            if nxt not in visited:
                if dfs(nxt, node):
                    return True
            elif nxt != parent:
                return True
        return False

    for node in range(n_qubits):
        if node not in visited:
            if dfs(node, -1):
                return True
    return False


def edge_subset_label(edge_names: List[str]) -> str:
    """
    e.g.
      ["e0"] -> "k1_e0"
      ["e0","e3"] -> "k2_e0_e3"
      ["e0","e2","e4"] -> "k3_e0_e2_e4"
    """
    return f"k{len(edge_names)}_" + "_".join(edge_names)


def derive_remaining_edges(
    edge_definitions: Dict[str, List[int]],
    dropped_edge_names: List[str],
) -> List[List[int]]:
    dropped_set = set(dropped_edge_names)
    return [
        edge_definitions[edge_name]
        for edge_name in edge_definitions.keys()
        if edge_name not in dropped_set
    ]


def build_derived_topology_state(
    parent_record: Dict[str, Any],
    edge_definitions: Dict[str, List[int]],
    dropped_edge_names: List[str],
) -> Dict[str, Any]:
    remaining_edges = derive_remaining_edges(edge_definitions, dropped_edge_names)
    n_qubits = int(parent_record["n_qubits"])
    remaining_edge_count = len(remaining_edges)
    n_components = count_components(n_qubits, remaining_edges)
    is_connected = n_components == 1
    has_loop = has_cycle_undirected(n_qubits, remaining_edges)

    return {
        "remaining_edges": remaining_edges,
        "remaining_edge_count": remaining_edge_count,
        "dropped_edge_count": len(dropped_edge_names),
        "is_connected_after_ablation": is_connected,
        "n_components_after_ablation": n_components,
        "has_loop_after_ablation": has_loop,
    }


def make_multi_ablation_spec(
    parent_record: Dict[str, Any],
    edge_definitions: Dict[str, List[int]],
    dropped_edge_names: List[str],
) -> MultiAblationCircuitSpec:
    topology = parent_record["topology_name"]
    perturbation_order = len(dropped_edge_names)
    dropped_edge_qubits = [edge_definitions[name] for name in dropped_edge_names]

    derived_state = build_derived_topology_state(
        parent_record=parent_record,
        edge_definitions=edge_definitions,
        dropped_edge_names=dropped_edge_names,
    )

    subset_label = edge_subset_label(dropped_edge_names)
    circuit_id = f"{parent_record['circuit_id']}_drop_{subset_label}"

    return MultiAblationCircuitSpec(
        circuit_id=circuit_id,
        parent_circuit_id=parent_record["circuit_id"],
        topology=topology,
        topology_class=parent_record["topology_class"],
        phase_role=parent_record["phase_role"],
        phase5_role=parent_record["phase5_role"],
        n_qubits=int(parent_record["n_qubits"]),
        rx_ratio=float(parent_record["rx_ratio"]),
        ry_ratio=float(parent_record["ry_ratio"]),
        predicted_response_class=parent_record["predicted_response_class"],
        ablation={
            "type": "multi_edge_drop",
            "perturbation_order": perturbation_order,
            "dropped_edges": dropped_edge_names,
            "dropped_edge_qubits": dropped_edge_qubits,
        },
        derived_topology_state=derived_state,
        edge_definition_ref=f"phase5_{topology}.edge_definition",
        gate_pattern=infer_gate_pattern_for_topology(topology),
        notes=(
            "Phase5 predictive multi-edge ablation candidate. "
            "Uses the same selected parent circuit structure as the predictive baseline, "
            "with the specified support edges removed from both CZ support layers."
        ),
    )


def save_spec_files(ablation_specs: List[MultiAblationCircuitSpec]) -> None:
    """
    Save one JSON file per multi-ablation circuit spec under:
      circuits/{topology}/multi_ablation/
    """
    for spec in ablation_specs:
        payload = asdict(spec)
        payload["runtime_metadata"] = build_qiskit_metadata_stub(payload)

        out_dir = CIRCUITS_DIR / spec.topology / "multi_ablation"
        ensure_dir(out_dir)

        out_path = out_dir / f"{spec.circuit_id}.json"
        write_json(out_path, payload)


def build_catalog(
    parent_catalog: Dict[str, Any],
    ablation_specs: List[MultiAblationCircuitSpec],
) -> Dict[str, Any]:
    parent_records = parent_catalog["records"]

    topology_edge_definitions: Dict[str, Dict[str, List[int]]] = {}
    for record in parent_records:
        topology = record["topology_name"]
        if topology not in topology_edge_definitions:
            topology_edge_definitions[topology] = edge_name_map_from_parent(record)

    by_topology_counts: Dict[str, Dict[str, int]] = {}
    for topology in topology_edge_definitions.keys():
        by_topology_counts[topology] = {"k1": 0, "k2": 0, "k3": 0}

    for spec in ablation_specs:
        k = spec.ablation["perturbation_order"]
        by_topology_counts[spec.topology][f"k{k}"] += 1

    catalog = {
        "catalog_name": "phase5_multi_ablation_catalog",
        "phase": PHASE_NAME,
        "study_title": STUDY_TITLE,
        "catalog_version": "v1.0",
        "builder_script": "generate_phase5_multi_ablation_circuits.py",
        "source_parent_catalog_ref": str(PARENT_CATALOG_PATH).replace("\\", "/"),
        "topologies": sorted(list(topology_edge_definitions.keys())),
        "edge_definitions": topology_edge_definitions,
        "noise_modes_supported": ["noisy_sim"],
        "measurement_bases_supported": ["X"],
        "default_shots": 4096,
        "perturbation_orders_supported": SUPPORTED_PERTURBATION_ORDERS,
        "ablation_type": "multi_edge_drop",
        "n_ablation_specs": len(ablation_specs),
        "counts_by_topology_and_order": by_topology_counts,
        "ablation_circuits": [asdict(spec) for spec in ablation_specs],
        "global_notes": [
            "This catalog defines the Phase5 multi-edge perturbation layer.",
            "Each record is generated from a selected Phase5 predictive parent circuit.",
            "Dropped edges are removed from both CZ support layers.",
            "Structural post-ablation metadata is computed at generation time.",
            "Disconnected states are retained as valid perturbation outcomes because Phase5 explicitly studies collapse onset.",
        ],
    }
    return catalog


def main() -> None:
    if not PARENT_CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Missing parent catalog: {PARENT_CATALOG_PATH}\n"
            f"Run generate_phase5_parent_catalog.py first."
        )

    parent_catalog = read_json(PARENT_CATALOG_PATH)
    validate_parent_catalog(parent_catalog)

    parent_records = parent_catalog["records"]
    all_specs: List[MultiAblationCircuitSpec] = []

    for parent_record in parent_records:
        topology = parent_record["topology_name"]
        edge_definitions = edge_name_map_from_parent(parent_record)
        edge_names = list(edge_definitions.keys())

        for k in SUPPORTED_PERTURBATION_ORDERS:
            if k > len(edge_names):
                continue

            for dropped_edge_names_tuple in itertools.combinations(edge_names, k):
                dropped_edge_names = list(dropped_edge_names_tuple)

                spec = make_multi_ablation_spec(
                    parent_record=parent_record,
                    edge_definitions=edge_definitions,
                    dropped_edge_names=dropped_edge_names,
                )
                all_specs.append(spec)

    # Stable deterministic ordering
    all_specs = sorted(
        all_specs,
        key=lambda s: (
            s.topology,
            s.ablation["perturbation_order"],
            tuple(s.ablation["dropped_edges"]),
        ),
    )

    save_spec_files(all_specs)

    catalog = build_catalog(parent_catalog, all_specs)
    write_json(ABLATION_CATALOG_PATH, catalog)

    print("Phase5 multi-edge ablation circuit generation completed.")
    print(f"Parent catalog   : {PARENT_CATALOG_PATH}")
    print(f"Ablation catalog : {ABLATION_CATALOG_PATH}")
    print(f"Total specs      : {len(all_specs)}")

    # Expected counts:
    # ring6   -> 6C1 + 6C2 + 6C3 = 6 + 15 + 20 = 41
    # chain6  -> 5C1 + 5C2 + 5C3 = 5 + 10 + 10 = 25
    # random6 -> 6C1 + 6C2 + 6C3 = 6 + 15 + 20 = 41
    # total = 107
    print("Expected topology counts:")
    print("  - ring6   : 41")
    print("  - chain6  : 25")
    print("  - random6 : 41")
    print("  - total   : 107")


if __name__ == "__main__":
    main()