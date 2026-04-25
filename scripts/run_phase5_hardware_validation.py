from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from qiskit import QuantumCircuit, transpile, qasm2
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler


REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

PARENT_CATALOG_PATH = REPO_ROOT / "circuits" / "phase5_parent_catalog.json"
MULTI_CATALOG_PATH = REPO_ROOT / "circuits" / "phase5_multi_ablation_catalog.json"

RAW_HARDWARE_DIR = REPO_ROOT / "results" / "raw_hardware"
QASM2_DIR = REPO_ROOT / "circuits" / "qasm2_hardware_validation"

DEFAULT_SEED = 42
SHOTS = 4096

PHASE5_PROFILE_WEIGHTS = [1.00, 0.80, 0.60, 0.60, 0.80, 1.00]
LAYER_A_RX_SCALE = 1.00
LAYER_A_RY_SCALE = 1.00
LAYER_B_RX_SCALE = 0.85
LAYER_B_RY_SCALE = 0.85

# Noneならleast_busyで選ぶ。固定したいなら "ibm_fez" などを入れる。
BACKEND_NAME: str | None = None

INITIAL_LAYOUTS: Dict[str, List[int] | None] = {
    "chain6": None,
    "ring6": None,
}

TARGETS = [
    {
        "target_tag": "chain6_baseline",
        "kind": "baseline",
        "topology": "chain6",
        "circuit_id": "phase5_chain6_predictive_parent",
    },
    {
        "target_tag": "chain6_k1_e2",
        "kind": "multi_ablation",
        "topology": "chain6",
        "circuit_id": "phase5_chain6_predictive_parent_drop_k1_e2",
    },
    {
        "target_tag": "ring6_baseline",
        "kind": "baseline",
        "topology": "ring6",
        "circuit_id": "phase5_ring6_predictive_parent",
    },
    {
        "target_tag": "ring6_k1_e0",
        "kind": "multi_ablation",
        "topology": "ring6",
        "circuit_id": "phase5_ring6_predictive_parent_drop_k1_e0",
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def ordered_edges_from_definition(edge_definition: Dict[str, List[int]]) -> List[Tuple[str, List[int]]]:
    ordered_names = sorted(edge_definition.keys(), key=lambda s: int(s[1:]))
    return [(name, edge_definition[name]) for name in ordered_names]


def apply_x_basis_measurement(qc: QuantumCircuit, n_qubits: int) -> None:
    for q in range(n_qubits):
        qc.h(q)
    qc.measure(range(n_qubits), range(n_qubits))


def build_phase5_parent_baseline_circuit(
    n_qubits: int,
    rx_ratio: float,
    ry_ratio: float,
    edge_definition: Dict[str, List[int]],
) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits, n_qubits)

    base_rx = math.pi * rx_ratio
    base_ry = math.pi * ry_ratio

    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_A_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_A_RY_SCALE, q)

    for _edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        qc.cz(a, b)

    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_B_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_B_RY_SCALE, q)

    for _edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        qc.cz(a, b)

    apply_x_basis_measurement(qc, n_qubits)
    return qc


def build_phase5_multi_ablation_circuit(
    n_qubits: int,
    rx_ratio: float,
    ry_ratio: float,
    edge_definition: Dict[str, List[int]],
    dropped_edge_names: List[str],
) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits, n_qubits)

    base_rx = math.pi * rx_ratio
    base_ry = math.pi * ry_ratio
    dropped_edge_set = set(dropped_edge_names)

    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_A_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_A_RY_SCALE, q)

    for edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        if edge_name in dropped_edge_set:
            continue
        qc.cz(a, b)

    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_B_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_B_RY_SCALE, q)

    for edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        if edge_name in dropped_edge_set:
            continue
        qc.cz(a, b)

    apply_x_basis_measurement(qc, n_qubits)
    return qc


def summarize_counts(counts: Dict[str, int]) -> Dict[str, Any]:
    total_counts = int(sum(counts.values()))
    if total_counts <= 0:
        raise ValueError("Counts are empty.")

    probs = {str(k).replace(" ", ""): int(v) / total_counts for k, v in counts.items()}

    abs_parity_signed = 0.0
    for bitstring, prob in probs.items():
        ones = bitstring.count("1")
        parity = 1.0 if (ones % 2 == 0) else -1.0
        abs_parity_signed += parity * prob

    abs_parity = abs(abs_parity_signed)
    entropy_bits = -sum(p * math.log2(p) for p in probs.values() if p > 0.0)

    top_state, top_count = max(counts.items(), key=lambda kv: kv[1])
    top_state = str(top_state).replace(" ", "")
    top_probability = int(top_count) / total_counts

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


def load_target_specs() -> Dict[str, Dict[str, Any]]:
    parent_catalog = read_json(PARENT_CATALOG_PATH)
    multi_catalog = read_json(MULTI_CATALOG_PATH)

    parent_records = {r["circuit_id"]: r for r in parent_catalog["records"]}
    multi_records = {r["circuit_id"]: r for r in multi_catalog["ablation_circuits"]}
    edge_definitions = multi_catalog["edge_definitions"]

    loaded: Dict[str, Dict[str, Any]] = {}

    for target in TARGETS:
        circuit_id = target["circuit_id"]
        kind = target["kind"]

        if kind == "baseline":
            spec = parent_records[circuit_id].copy()
            topology = spec["topology_name"]
            spec["_kind"] = "baseline"
            spec["_topology"] = topology
            spec["_edge_definition"] = {f"e{i}": edge for i, edge in enumerate(spec["edges"])}
            loaded[circuit_id] = spec

        elif kind == "multi_ablation":
            spec = multi_records[circuit_id].copy()
            topology = spec["topology"]
            spec["_kind"] = "multi_ablation"
            spec["_topology"] = topology
            spec["_edge_definition"] = edge_definitions[topology]
            loaded[circuit_id] = spec

        else:
            raise ValueError(f"Unknown target kind: {kind}")

    return loaded


def choose_backend(service: QiskitRuntimeService):
    if BACKEND_NAME:
        return service.backend(BACKEND_NAME)

    return service.least_busy(
        min_num_qubits=6,
        simulator=False,
        operational=True,
    )


def export_qasm2(
    logical_qc: QuantumCircuit,
    transpiled_qc: QuantumCircuit,
    target_tag: str,
    topology: str,
) -> Dict[str, str | None]:
    qasm_dir = QASM2_DIR / topology
    ensure_dir(qasm_dir)

    logical_path = qasm_dir / f"{target_tag}__logical.qasm"
    transpiled_path = qasm_dir / f"{target_tag}__transpiled.qasm"

    qasm2.dump(logical_qc, logical_path)

    transpiled_error = None
    try:
        qasm2.dump(transpiled_qc, transpiled_path)
    except Exception as exc:
        transpiled_error = str(exc)
        transpiled_path = None

    return {
        "logical_qasm2_path": str(logical_path),
        "transpiled_qasm2_path": str(transpiled_path) if transpiled_path else None,
        "transpiled_qasm2_export_error": transpiled_error,
    }


def count_two_qubit_ops(counts: Dict[str, int]) -> int:
    return sum(int(n) for gate, n in counts.items() if gate in {"cx", "cz", "ecr"})


def count_one_qubit_ops(counts: Dict[str, int]) -> int:
    return sum(
        int(n)
        for gate, n in counts.items()
        if gate not in {"cx", "cz", "ecr", "measure", "barrier", "delay"}
    )


def extract_counts_from_sampler_result(result: Any) -> Dict[str, int]:
    """
    SamplerV2 result extractor.
    QuantumCircuit(n, n) usually creates classical register name 'c'.
    measure_all() often creates 'meas'.
    This handles both.
    """
    pub_result = result[0]
    data = pub_result.data

    if hasattr(data, "meas"):
        return dict(data.meas.get_counts())

    if hasattr(data, "c"):
        return dict(data.c.get_counts())

    # fallback: try first data field with get_counts()
    try:
        for key in data.keys():
            candidate = getattr(data, key)
            if hasattr(candidate, "get_counts"):
                return dict(candidate.get_counts())
    except Exception:
        pass

    raise RuntimeError(
        f"Could not extract counts from SamplerV2 result. Data object: {data!r}"
    )


def run_one_target(
    backend,
    target_tag: str,
    spec: Dict[str, Any],
) -> Dict[str, Any]:
    topology = spec["_topology"]
    edge_definition = spec["_edge_definition"]

    if spec["_kind"] == "baseline":
        logical_qc = build_phase5_parent_baseline_circuit(
            n_qubits=int(spec["n_qubits"]),
            rx_ratio=float(spec["rx_ratio"]),
            ry_ratio=float(spec["ry_ratio"]),
            edge_definition=edge_definition,
        )
    else:
        logical_qc = build_phase5_multi_ablation_circuit(
            n_qubits=int(spec["n_qubits"]),
            rx_ratio=float(spec["rx_ratio"]),
            ry_ratio=float(spec["ry_ratio"]),
            edge_definition=edge_definition,
            dropped_edge_names=list(spec["ablation"]["dropped_edges"]),
        )

    initial_layout = INITIAL_LAYOUTS.get(topology, None)

    transpiled_qc = transpile(
        logical_qc,
        backend=backend,
        optimization_level=0,
        seed_transpiler=DEFAULT_SEED,
        initial_layout=initial_layout,
    )

    qasm_meta = export_qasm2(
        logical_qc=logical_qc,
        transpiled_qc=transpiled_qc,
        target_tag=target_tag,
        topology=topology,
    )

    sampler = Sampler(mode=backend)
    job = sampler.run([transpiled_qc], shots=SHOTS)
    result = job.result()
    counts = extract_counts_from_sampler_result(result)

    summary = summarize_counts(counts)
    op_counts = transpiled_qc.count_ops()
    backend_name = backend.name if isinstance(backend.name, str) else backend.name()

    payload = {
        "phase": "Phase5",
        "study_title": "SRFM Quantum Phase5 Hardware Validation",
        "hardware_validation_tag": target_tag,
        "source_phase5_circuit_id": spec["circuit_id"],
        "run_type": "hardware_validation",
        "backend_name": backend_name,
        "backend_repr": str(backend),
        "job_id": job.job_id(),
        "run_datetime_utc": datetime.now(timezone.utc).isoformat(),
        "shots": SHOTS,
        "seed_transpiler": DEFAULT_SEED,
        "topology": topology,
        "topology_class": spec.get("topology_class"),
        "kind": spec["_kind"],
        "predicted_response_class": spec.get("predicted_response_class"),
        "parent_circuit_id": spec.get("parent_circuit_id", spec["circuit_id"]),
        "circuit_id": spec["circuit_id"],
        "n_qubits": int(spec["n_qubits"]),
        "rx_ratio": float(spec["rx_ratio"]),
        "ry_ratio": float(spec["ry_ratio"]),
        "edge_definition": edge_definition,
        "ablation": spec.get("ablation"),
        "counts": counts,
        "summary": summary,
        "target_bitstring": "1" * int(spec["n_qubits"]),
        "transpile_metadata": {
            "optimization_level": 0,
            "initial_layout": initial_layout,
            "transpiled_depth": int(transpiled_qc.depth()),
            "transpiled_size": int(transpiled_qc.size()),
            "transpiled_count_ops": {str(k): int(v) for k, v in op_counts.items()},
            "transpiled_two_qubit_gate_count": count_two_qubit_ops(op_counts),
            "transpiled_one_qubit_gate_count": count_one_qubit_ops(op_counts),
            "layout_repr": str(getattr(transpiled_qc, "layout", None)),
        },
        "qasm2_export": qasm_meta,
        "metadata": {
            "generator": "run_phase5_hardware_validation.py",
            "builder_version": "phase5_hardware_v2_sampler_qasm2_minimal_validation",
            "profile_weights": PHASE5_PROFILE_WEIGHTS,
            "layerA_rx_scale": LAYER_A_RX_SCALE,
            "layerA_ry_scale": LAYER_A_RY_SCALE,
            "layerB_rx_scale": LAYER_B_RX_SCALE,
            "layerB_ry_scale": LAYER_B_RY_SCALE,
            "validation_policy": "minimal_chain_ring_sign_validation",
            "execution_interface": "SamplerV2",
        },
    }

    return payload


def save_payload(payload: Dict[str, Any]) -> Path:
    topology = payload["topology"]
    target_tag = payload["hardware_validation_tag"]

    out_dir = RAW_HARDWARE_DIR / topology
    ensure_dir(out_dir)

    filename = f"{target_tag}__hardware__shots{payload['shots']}.json"
    out_path = out_dir / filename
    write_json(out_path, payload)
    return out_path


def main() -> None:
    ensure_dir(RAW_HARDWARE_DIR)
    ensure_dir(QASM2_DIR)

    if not PARENT_CATALOG_PATH.exists():
        raise FileNotFoundError(f"Missing parent catalog: {PARENT_CATALOG_PATH}")
    if not MULTI_CATALOG_PATH.exists():
        raise FileNotFoundError(f"Missing multi catalog: {MULTI_CATALOG_PATH}")

    specs = load_target_specs()

    service = QiskitRuntimeService()
    backend = choose_backend(service)
    backend_name = backend.name if isinstance(backend.name, str) else backend.name()

    print("Starting Phase5 IBM hardware validation...")
    print(f"Backend: {backend_name}")
    print(f"Shots: {SHOTS}")
    print("Targets:")
    for t in TARGETS:
        print(f"  - {t['target_tag']} -> {t['circuit_id']}")
    print()

    completed = 0

    for target in TARGETS:
        target_tag = target["target_tag"]
        spec = specs[target["circuit_id"]]

        print(f"Running {target_tag} | topology={spec['_topology']} | kind={spec['_kind']}")

        payload = run_one_target(
            backend=backend,
            target_tag=target_tag,
            spec=spec,
        )
        out_path = save_payload(payload)

        print(f"  job_id -> {payload['job_id']}")
        print(f"  saved -> {out_path}")
        print(f"  logical qasm2 -> {payload['qasm2_export']['logical_qasm2_path']}")
        if payload["qasm2_export"]["transpiled_qasm2_path"]:
            print(f"  transpiled qasm2 -> {payload['qasm2_export']['transpiled_qasm2_path']}")
        else:
            print(
                "  transpiled qasm2 export skipped: "
                f"{payload['qasm2_export']['transpiled_qasm2_export_error']}"
            )

        completed += 1

    print()
    print("Phase5 IBM hardware validation complete.")
    print(f"Completed jobs: {completed}")
    print(f"Expected jobs: {len(TARGETS)}")


if __name__ == "__main__":
    main()