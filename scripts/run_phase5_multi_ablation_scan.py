from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


# ============================================================
# Phase5 Predictive Structural Response Multi-Edge Ablation Scan
# ------------------------------------------------------------
# Purpose:
#   - Read Phase5 multi-edge ablation circuit catalog
#   - Build Phase5 ablation circuits using a Phase4-compatible
#     two-layer SRFM builder
#   - Run noisy_sim only
#   - Run X basis only
#   - Use fixed shots = 4096
#   - Save raw JSON results under:
#       results/raw/{topology}/multi_ablation/
#
# Builder policy:
#   - Preserve Phase4 two-layer SRFM builder
#   - Keep the same 6-qubit symmetric profile across topologies
#   - Remove the same dropped edge subset from both CZ support layers
#
# Fixed Phase5 condition:
#   - noise_mode = noisy_sim
#   - measurement_basis = X
#   - shots = 4096
# ============================================================

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")
CATALOG_PATH = REPO_ROOT / "circuits" / "phase5_multi_ablation_catalog.json"

DEFAULT_SEED = 42

EXPECTED_NOISE_MODE = "noisy_sim"
EXPECTED_MEASUREMENT_BASIS = "X"
EXPECTED_SHOTS = 4096

# Phase2 / Phase3 / Phase4 continuity noise model
P1 = 0.0015
P2 = 0.015
READOUT_CONFUSION = [[0.985, 0.015], [0.020, 0.980]]

# Phase4-compatible shared profile
PHASE5_PROFILE_WEIGHTS = [1.00, 0.80, 0.60, 0.60, 0.80, 1.00]
LAYER_A_RX_SCALE = 1.00
LAYER_A_RY_SCALE = 1.00
LAYER_B_RX_SCALE = 0.85
LAYER_B_RY_SCALE = 0.85


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_noise_model() -> NoiseModel:
    noise_model = NoiseModel()

    one_qubit_error = depolarizing_error(P1, 1)
    two_qubit_error = depolarizing_error(P2, 2)

    one_qubit_gates = ["rx", "ry", "rz", "h", "x", "sx"]
    two_qubit_gates = ["cx", "cz"]

    for gate in one_qubit_gates:
        noise_model.add_all_qubit_quantum_error(one_qubit_error, gate)

    for gate in two_qubit_gates:
        noise_model.add_all_qubit_quantum_error(two_qubit_error, gate)

    readout = ReadoutError(READOUT_CONFUSION)
    for q in range(6):
        noise_model.add_readout_error(readout, [q])

    return noise_model


def ordered_edges_from_definition(edge_definition: Dict[str, List[int]]) -> List[Tuple[str, List[int]]]:
    """
    Return ordered edges preserving edge names.
    Assumes edge names like e0, e1, e2, ...
    """
    ordered_names = sorted(edge_definition.keys(), key=lambda s: int(s[1:]))
    return [(name, edge_definition[name]) for name in ordered_names]


def apply_x_basis_measurement(qc: QuantumCircuit, n_qubits: int) -> None:
    for q in range(n_qubits):
        qc.h(q)
    qc.measure(range(n_qubits), range(n_qubits))


def build_phase5_multi_ablation_circuit(
    n_qubits: int,
    rx_ratio: float,
    ry_ratio: float,
    edge_definition: Dict[str, List[int]],
    dropped_edge_names: List[str],
) -> QuantumCircuit:
    """
    Phase5 multi-edge ablation circuit:
      Local Layer A
      -> CZ support layer A (with dropped edges removed)
      -> Local Layer B
      -> CZ support layer B (with same dropped edges removed)
      -> X-basis transform
      -> measurement
    """
    qc = QuantumCircuit(n_qubits, n_qubits)

    if len(PHASE5_PROFILE_WEIGHTS) != n_qubits:
        raise ValueError("PHASE5_PROFILE_WEIGHTS length must match n_qubits")

    unknown_edges = [name for name in dropped_edge_names if name not in edge_definition]
    if unknown_edges:
        raise ValueError(f"Unknown dropped edge names: {unknown_edges}")

    dropped_edge_set = set(dropped_edge_names)

    base_rx = math.pi * rx_ratio
    base_ry = math.pi * ry_ratio

    # ---- Local Layer A ----
    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_A_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_A_RY_SCALE, q)

    # ---- CZ support layer A with dropped subset removed ----
    for edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        if edge_name in dropped_edge_set:
            continue
        qc.cz(a, b)

    # ---- Local Layer B ----
    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_B_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_B_RY_SCALE, q)

    # ---- CZ support layer B with same dropped subset removed ----
    for edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        if edge_name in dropped_edge_set:
            continue
        qc.cz(a, b)

    apply_x_basis_measurement(qc, n_qubits)
    return qc


def simulator_backend(noise_mode: str) -> AerSimulator:
    if noise_mode != EXPECTED_NOISE_MODE:
        raise ValueError(
            f"Unsupported noise mode for Phase5 multi-ablation: {noise_mode} "
            f"(expected {EXPECTED_NOISE_MODE})"
        )

    return AerSimulator(
        noise_model=build_noise_model(),
        seed_simulator=DEFAULT_SEED,
    )


def summarize_counts(counts: Dict[str, int]) -> Dict[str, Any]:
    total_counts = int(sum(counts.values()))
    if total_counts <= 0:
        raise ValueError("Counts are empty.")

    probs = {k.replace(" ", ""): v / total_counts for k, v in counts.items()}

    abs_parity_signed = 0.0
    for bitstring, prob in probs.items():
        ones = bitstring.count("1")
        parity = 1.0 if (ones % 2 == 0) else -1.0
        abs_parity_signed += parity * prob

    abs_parity = abs(abs_parity_signed)
    entropy_bits = -sum(p * math.log2(p) for p in probs.values() if p > 0.0)

    top_state, top_count = max(counts.items(), key=lambda kv: kv[1])
    top_state = top_state.replace(" ", "")
    top_probability = top_count / total_counts

    target_bitstring = "1" * len(top_state)
    target_probability = probs.get(target_bitstring, 0.0)

    return {
        "total_counts": total_counts,
        "n_observed_states": len(counts),
        "top_state": top_state,
        "top_count": int(top_count),
        "top_probability": top_probability,
        "target_probability": target_probability,
        "abs_parity": abs_parity,
        "entropy_bits": entropy_bits,
    }


def build_edge_definition_for_spec(circuit_spec: Dict[str, Any], catalog_root: Dict[str, Any]) -> Dict[str, List[int]]:
    """
    Fetch topology-specific edge_definition from catalog.
    """
    edge_definitions = catalog_root.get("edge_definitions", {})
    topology = circuit_spec["topology"]
    if topology not in edge_definitions:
        raise KeyError(f"Topology '{topology}' not found in catalog edge_definitions")
    return edge_definitions[topology]


def run_single_job(circuit_spec: Dict[str, Any], catalog_root: Dict[str, Any]) -> Dict[str, Any]:
    n_qubits = int(circuit_spec["n_qubits"])
    rx_ratio = float(circuit_spec["rx_ratio"])
    ry_ratio = float(circuit_spec["ry_ratio"])

    ablation = circuit_spec["ablation"]
    dropped_edge_names = list(ablation["dropped_edges"])

    edge_definition = build_edge_definition_for_spec(circuit_spec, catalog_root)

    qc = build_phase5_multi_ablation_circuit(
        n_qubits=n_qubits,
        rx_ratio=rx_ratio,
        ry_ratio=ry_ratio,
        edge_definition=edge_definition,
        dropped_edge_names=dropped_edge_names,
    )

    backend = simulator_backend(EXPECTED_NOISE_MODE)
    tqc = transpile(
        qc,
        backend=backend,
        seed_transpiler=DEFAULT_SEED,
        optimization_level=0,
    )

    result = backend.run(tqc, shots=EXPECTED_SHOTS).result()
    counts = result.get_counts()
    summary = summarize_counts(counts)

    return {
        "phase": PHASE_NAME,
        "study_title": STUDY_TITLE,
        "topology": circuit_spec["topology"],
        "topology_class": circuit_spec["topology_class"],
        "phase_role": circuit_spec.get("phase_role"),
        "phase5_role": circuit_spec.get("phase5_role"),
        "predicted_response_class": circuit_spec.get("predicted_response_class"),
        "circuit_id": circuit_spec["circuit_id"],
        "parent_circuit_id": circuit_spec["parent_circuit_id"],
        "run_type": "multi_ablation",
        "noise_mode": EXPECTED_NOISE_MODE,
        "measurement_basis": EXPECTED_MEASUREMENT_BASIS,
        "shots": EXPECTED_SHOTS,
        "seed_simulator": DEFAULT_SEED,
        "seed_transpiler": DEFAULT_SEED,
        "n_qubits": n_qubits,
        "rx_ratio": rx_ratio,
        "ry_ratio": ry_ratio,
        "ablation": ablation,
        "edge_definition": edge_definition,
        "derived_topology_state": circuit_spec.get("derived_topology_state"),
        "counts": counts,
        "summary": summary,
        "target_bitstring": "1" * n_qubits,
        "metadata": {
            "generator": "run_phase5_multi_ablation_scan.py",
            "builder_version": "phase5_v1_phase4_generalized_multi_ablation",
            "profile_weights": PHASE5_PROFILE_WEIGHTS,
            "layerA_rx_scale": LAYER_A_RX_SCALE,
            "layerA_ry_scale": LAYER_A_RY_SCALE,
            "layerB_rx_scale": LAYER_B_RX_SCALE,
            "layerB_ry_scale": LAYER_B_RY_SCALE,
            "dropped_edge_names": dropped_edge_names,
            "dropped_edge_qubits": ablation["dropped_edge_qubits"],
            "gate_pattern": circuit_spec.get("gate_pattern"),
            "notes": circuit_spec.get("notes"),
            "noise_model": {
                "single_qubit_depolarizing_p": P1,
                "two_qubit_depolarizing_p": P2,
                "readout_confusion": READOUT_CONFUSION,
            },
        },
    }


def save_raw_result(payload: Dict[str, Any]) -> Path:
    topology = payload["topology"]
    circuit_id = payload["circuit_id"]
    basis = payload["measurement_basis"].lower() + "basis"
    noise_mode = payload["noise_mode"]
    shots = payload["shots"]

    out_dir = REPO_ROOT / "results" / "raw" / topology / "multi_ablation"
    ensure_dir(out_dir)

    filename = f"{circuit_id}__{noise_mode}__{basis}__shots{shots}.json"
    out_path = out_dir / filename

    write_json(out_path, payload)
    return out_path


def validate_catalog(catalog_root: Dict[str, Any]) -> None:
    if catalog_root.get("catalog_name") != "phase5_multi_ablation_catalog":
        raise KeyError("Catalog root must be phase5_multi_ablation_catalog")

    ablation_circuits = catalog_root.get("ablation_circuits", [])
    if len(ablation_circuits) != 107:
        raise ValueError(
            f"Expected 107 ablation circuits, found {len(ablation_circuits)}"
        )

    edge_definitions = catalog_root.get("edge_definitions", {})
    expected_topologies = {"ring6", "chain6", "random6"}
    if set(edge_definitions.keys()) != expected_topologies:
        raise ValueError(
            f"Edge definition topologies mismatch. "
            f"Found {set(edge_definitions.keys())}, expected {expected_topologies}"
        )

    supported_orders = catalog_root.get("perturbation_orders_supported", [])
    if supported_orders != [1, 2, 3]:
        raise ValueError(
            f"Expected perturbation_orders_supported=[1, 2, 3], found {supported_orders}"
        )

    for spec in ablation_circuits:
        if int(spec.get("n_qubits", -1)) != 6:
            raise ValueError(f"Expected n_qubits=6, found {spec.get('n_qubits')} in {spec.get('circuit_id')}")

        ablation = spec.get("ablation")
        if not isinstance(ablation, dict):
            raise ValueError(f"Missing ablation dict in {spec.get('circuit_id')}")

        if ablation.get("type") != "multi_edge_drop":
            raise ValueError(
                f"Unsupported ablation type in {spec.get('circuit_id')}: {ablation.get('type')}"
            )

        perturbation_order = int(ablation.get("perturbation_order", -1))
        dropped_edges = ablation.get("dropped_edges", [])
        dropped_edge_qubits = ablation.get("dropped_edge_qubits", [])

        if perturbation_order not in [1, 2, 3]:
            raise ValueError(
                f"Unsupported perturbation_order in {spec.get('circuit_id')}: {perturbation_order}"
            )

        if len(dropped_edges) != perturbation_order:
            raise ValueError(
                f"dropped_edges length mismatch in {spec.get('circuit_id')}: "
                f"len={len(dropped_edges)} vs perturbation_order={perturbation_order}"
            )

        if len(dropped_edge_qubits) != perturbation_order:
            raise ValueError(
                f"dropped_edge_qubits length mismatch in {spec.get('circuit_id')}: "
                f"len={len(dropped_edge_qubits)} vs perturbation_order={perturbation_order}"
            )


def main() -> None:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Missing multi-ablation catalog: {CATALOG_PATH}\n"
            "Run generate_phase5_multi_ablation_circuits.py first."
        )

    catalog_root = read_json(CATALOG_PATH)
    validate_catalog(catalog_root)

    ablation_circuits = catalog_root["ablation_circuits"]

    print("Starting Phase5 predictive structural response multi-edge ablation scan...")
    print(f"Catalog: {CATALOG_PATH}")
    print(f"Ablation circuits: {len(ablation_circuits)}")
    print(f"Noise mode: {EXPECTED_NOISE_MODE}")
    print(f"Measurement basis: {EXPECTED_MEASUREMENT_BASIS}")
    print(f"Shots: {EXPECTED_SHOTS}")
    print("Builder version: phase5_v1_phase4_generalized_multi_ablation")
    print()

    completed = 0

    for circuit_spec in ablation_circuits:
        circuit_id = circuit_spec["circuit_id"]
        topology = circuit_spec["topology"]
        perturbation_order = circuit_spec["ablation"]["perturbation_order"]
        dropped_edges = circuit_spec["ablation"]["dropped_edges"]

        print(
            f"Running {circuit_id} | topology={topology} | "
            f"k={perturbation_order} | drop={dropped_edges} | "
            f"noise={EXPECTED_NOISE_MODE} | basis={EXPECTED_MEASUREMENT_BASIS} | shots={EXPECTED_SHOTS}"
        )

        payload = run_single_job(circuit_spec, catalog_root)
        out_path = save_raw_result(payload)

        print(f"  saved -> {out_path}")
        completed += 1

    print()
    print("Phase5 predictive structural response multi-edge ablation scan complete.")
    print(f"Completed jobs: {completed}")
    print(f"Expected jobs: {len(ablation_circuits)}")


if __name__ == "__main__":
    PHASE_NAME = "Phase5"
    STUDY_TITLE = "SRFM Quantum Phase5 Predictive Structural Response Study"
    main()