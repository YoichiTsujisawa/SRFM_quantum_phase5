from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


# ============================================================
# Phase5.5 Noise Sweep
# ------------------------------------------------------------
# Purpose:
#   - Re-run the Phase5 hardware-validation target set in simulator
#   - Sweep noise scale:
#       0.0, 0.5, 1.0, 1.5, 2.0
#   - Analyze chain6 vs ring6 response under controlled noise
#
# Target circuits:
#   - chain6 baseline
#   - chain6 k1_e2
#   - ring6 baseline
#   - ring6 k1_e0
#
# Output:
#   results/raw_phase55_noise_sweep/{topology}/...
# ============================================================

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

PARENT_CATALOG_PATH = REPO_ROOT / "circuits" / "phase5_parent_catalog.json"
MULTI_CATALOG_PATH = REPO_ROOT / "circuits" / "phase5_multi_ablation_catalog.json"

OUT_ROOT = REPO_ROOT / "results" / "raw_phase55_noise_sweep"

DEFAULT_SEED = 42
SHOTS = 4096

NOISE_SCALES = [0.0, 0.5, 1.0, 1.5, 2.0]

# Standard Phase4/5 noise
BASE_P1 = 0.0015
BASE_P2 = 0.015
BASE_READOUT_E01 = 0.015
BASE_READOUT_E10 = 0.020

PHASE55_PROFILE_WEIGHTS = [1.00, 0.80, 0.60, 0.60, 0.80, 1.00]
LAYER_A_RX_SCALE = 1.00
LAYER_A_RY_SCALE = 1.00
LAYER_B_RX_SCALE = 0.85
LAYER_B_RY_SCALE = 0.85


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


def build_baseline_circuit(
    n_qubits: int,
    rx_ratio: float,
    ry_ratio: float,
    edge_definition: Dict[str, List[int]],
) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits, n_qubits)

    base_rx = math.pi * rx_ratio
    base_ry = math.pi * ry_ratio

    for q in range(n_qubits):
        w = PHASE55_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_A_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_A_RY_SCALE, q)

    for _edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        qc.cz(a, b)

    for q in range(n_qubits):
        w = PHASE55_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_B_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_B_RY_SCALE, q)

    for _edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        qc.cz(a, b)

    apply_x_basis_measurement(qc, n_qubits)
    return qc


def build_multi_ablation_circuit(
    n_qubits: int,
    rx_ratio: float,
    ry_ratio: float,
    edge_definition: Dict[str, List[int]],
    dropped_edge_names: List[str],
) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits, n_qubits)

    base_rx = math.pi * rx_ratio
    base_ry = math.pi * ry_ratio
    dropped = set(dropped_edge_names)

    for q in range(n_qubits):
        w = PHASE55_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_A_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_A_RY_SCALE, q)

    for edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        if edge_name in dropped:
            continue
        qc.cz(a, b)

    for q in range(n_qubits):
        w = PHASE55_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_B_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_B_RY_SCALE, q)

    for edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        if edge_name in dropped:
            continue
        qc.cz(a, b)

    apply_x_basis_measurement(qc, n_qubits)
    return qc


def build_noise_model(noise_scale: float) -> NoiseModel | None:
    if noise_scale == 0.0:
        return None

    p1 = BASE_P1 * noise_scale
    p2 = BASE_P2 * noise_scale
    e01 = BASE_READOUT_E01 * noise_scale
    e10 = BASE_READOUT_E10 * noise_scale

    if not (0.0 <= e01 <= 1.0 and 0.0 <= e10 <= 1.0):
        raise ValueError(f"Invalid readout errors for noise_scale={noise_scale}")

    noise_model = NoiseModel()

    one_qubit_error = depolarizing_error(p1, 1)
    two_qubit_error = depolarizing_error(p2, 2)

    for gate in ["rx", "ry", "rz", "h", "x", "sx"]:
        noise_model.add_all_qubit_quantum_error(one_qubit_error, gate)

    for gate in ["cx", "cz"]:
        noise_model.add_all_qubit_quantum_error(two_qubit_error, gate)

    readout = ReadoutError([[1.0 - e01, e01], [e10, 1.0 - e10]])
    for q in range(6):
        noise_model.add_readout_error(readout, [q])

    return noise_model


def make_backend(noise_scale: float) -> AerSimulator:
    noise_model = build_noise_model(noise_scale)

    if noise_model is None:
        return AerSimulator(seed_simulator=DEFAULT_SEED)

    return AerSimulator(
        noise_model=noise_model,
        seed_simulator=DEFAULT_SEED,
    )


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
            spec["_edge_definition"] = {
                f"e{i}": edge for i, edge in enumerate(spec["edges"])
            }
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


def run_one(spec: Dict[str, Any], noise_scale: float) -> Dict[str, Any]:
    topology = spec["_topology"]
    edge_definition = spec["_edge_definition"]

    if spec["_kind"] == "baseline":
        qc = build_baseline_circuit(
            n_qubits=int(spec["n_qubits"]),
            rx_ratio=float(spec["rx_ratio"]),
            ry_ratio=float(spec["ry_ratio"]),
            edge_definition=edge_definition,
        )
    else:
        qc = build_multi_ablation_circuit(
            n_qubits=int(spec["n_qubits"]),
            rx_ratio=float(spec["rx_ratio"]),
            ry_ratio=float(spec["ry_ratio"]),
            edge_definition=edge_definition,
            dropped_edge_names=list(spec["ablation"]["dropped_edges"]),
        )

    backend = make_backend(noise_scale)

    tqc = transpile(
        qc,
        backend=backend,
        seed_transpiler=DEFAULT_SEED,
        optimization_level=0,
    )

    result = backend.run(tqc, shots=SHOTS).result()
    counts = result.get_counts()
    summary = summarize_counts(counts)
    op_counts = tqc.count_ops()

    return {
        "phase": "Phase5.5",
        "study_title": "SRFM Quantum Phase5.5 Noise Sweep",
        "run_type": "noise_sweep",
        "topology": topology,
        "kind": spec["_kind"],
        "circuit_id": spec["circuit_id"],
        "parent_circuit_id": spec.get("parent_circuit_id", spec["circuit_id"]),
        "predicted_response_class": spec.get("predicted_response_class"),
        "noise_scale": noise_scale,
        "shots": SHOTS,
        "seed_simulator": DEFAULT_SEED,
        "seed_transpiler": DEFAULT_SEED,
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
            "transpiled_depth": int(tqc.depth()),
            "transpiled_size": int(tqc.size()),
            "transpiled_count_ops": {str(k): int(v) for k, v in op_counts.items()},
        },
        "noise_model": {
            "base_single_qubit_depolarizing_p": BASE_P1,
            "base_two_qubit_depolarizing_p": BASE_P2,
            "base_readout_e01": BASE_READOUT_E01,
            "base_readout_e10": BASE_READOUT_E10,
            "scaled_single_qubit_depolarizing_p": BASE_P1 * noise_scale,
            "scaled_two_qubit_depolarizing_p": BASE_P2 * noise_scale,
            "scaled_readout_e01": BASE_READOUT_E01 * noise_scale,
            "scaled_readout_e10": BASE_READOUT_E10 * noise_scale,
        },
        "metadata": {
            "generator": "run_phase55_noise_sweep.py",
            "builder_version": "phase55_noise_sweep_v1",
            "profile_weights": PHASE55_PROFILE_WEIGHTS,
            "layerA_rx_scale": LAYER_A_RX_SCALE,
            "layerA_ry_scale": LAYER_A_RY_SCALE,
            "layerB_rx_scale": LAYER_B_RX_SCALE,
            "layerB_ry_scale": LAYER_B_RY_SCALE,
        },
    }


def save_payload(payload: Dict[str, Any], target_tag: str) -> Path:
    topology = payload["topology"]
    noise_scale = payload["noise_scale"]
    noise_label = f"noise{noise_scale:.1f}".replace(".", "p")

    out_dir = OUT_ROOT / topology
    ensure_dir(out_dir)

    filename = f"{target_tag}__{noise_label}__shots{payload['shots']}.json"
    out_path = out_dir / filename
    write_json(out_path, payload)
    return out_path


def main() -> None:
    ensure_dir(OUT_ROOT)

    specs = load_target_specs()

    print("Starting Phase5.5 noise sweep...")
    print(f"Shots: {SHOTS}")
    print(f"Noise scales: {NOISE_SCALES}")
    print(f"Targets: {len(TARGETS)}")
    print(f"Total jobs: {len(TARGETS) * len(NOISE_SCALES)}")
    print()

    completed = 0

    for noise_scale in NOISE_SCALES:
        print(f"=== noise_scale={noise_scale} ===")

        for target in TARGETS:
            target_tag = target["target_tag"]
            circuit_id = target["circuit_id"]
            spec = specs[circuit_id]

            print(
                f"Running {target_tag} | topology={spec['_topology']} | "
                f"kind={spec['_kind']} | noise_scale={noise_scale}"
            )

            payload = run_one(spec, noise_scale)
            out_path = save_payload(payload, target_tag)

            print(f"  saved -> {out_path}")
            completed += 1

        print()

    print("Phase5.5 noise sweep complete.")
    print(f"Completed jobs: {completed}")
    print(f"Expected jobs: {len(TARGETS) * len(NOISE_SCALES)}")


if __name__ == "__main__":
    main()