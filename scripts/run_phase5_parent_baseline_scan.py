from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error


# ============================================================
# Phase5 Predictive Parent Baseline Scan
# ------------------------------------------------------------
# Purpose:
#   - Read Phase5 parent circuit catalog
#   - Build Phase5 predictive parent baseline circuits using a
#     Phase4-compatible two-layer SRFM builder
#   - Run noisy_sim only
#   - Run X basis only
#   - Use fixed shots = 4096
#   - Save raw JSON results under:
#       results/raw/{topology}/baseline/
#
# Builder policy:
#   - Preserve Phase4 baseline builder structure exactly
#   - Keep the same 6-qubit symmetric profile across topologies
#   - Vary only topology edge structure and selected parent ratios
#
# Fixed Phase5 condition:
#   - noise_mode = noisy_sim
#   - measurement_basis = X
#   - shots = 4096
# ============================================================

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")
CATALOG_PATH = REPO_ROOT / "circuits" / "phase5_parent_catalog.json"

DEFAULT_SEED = 42

EXPECTED_NOISE_MODE = "noisy_sim"
EXPECTED_MEASUREMENT_BASIS = "xbasis"
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
    """
    Phase5 parent baseline circuit:
      Local Layer A
      -> CZ support layer A
      -> Local Layer B
      -> CZ support layer B
      -> X-basis transform
      -> measurement
    """
    qc = QuantumCircuit(n_qubits, n_qubits)

    if len(PHASE5_PROFILE_WEIGHTS) != n_qubits:
        raise ValueError("PHASE5_PROFILE_WEIGHTS length must match n_qubits")

    base_rx = math.pi * rx_ratio
    base_ry = math.pi * ry_ratio

    # ---- Local Layer A ----
    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_A_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_A_RY_SCALE, q)

    # ---- CZ support layer A ----
    for _edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        qc.cz(a, b)

    # ---- Local Layer B ----
    for q in range(n_qubits):
        w = PHASE5_PROFILE_WEIGHTS[q]
        qc.rx(base_rx * w * LAYER_B_RX_SCALE, q)
        qc.ry(base_ry * w * LAYER_B_RY_SCALE, q)

    # ---- CZ support layer B ----
    for _edge_name, (a, b) in ordered_edges_from_definition(edge_definition):
        qc.cz(a, b)

    apply_x_basis_measurement(qc, n_qubits)
    return qc


def simulator_backend(noise_mode: str) -> AerSimulator:
    if noise_mode != EXPECTED_NOISE_MODE:
        raise ValueError(
            f"Unsupported noise mode for Phase5 parent baseline: {noise_mode} "
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
        "abs_parity": abs(abs_parity),
        "entropy_bits": entropy_bits,
    }


def build_edge_definition_from_spec(spec: Dict[str, Any]) -> Dict[str, List[int]]:
    edges = spec["edges"]
    return {f"e{i}": edge for i, edge in enumerate(edges)}


def run_single_job(circuit_spec: Dict[str, Any]) -> Dict[str, Any]:
    n_qubits = int(circuit_spec["n_qubits"])
    rx_ratio = float(circuit_spec["rx_ratio"])
    ry_ratio = float(circuit_spec["ry_ratio"])
    noise_mode = str(circuit_spec["noise_model_tag"])
    measurement_basis = str(circuit_spec["measurement_basis"])
    shots = int(circuit_spec["shots"])

    if measurement_basis != EXPECTED_MEASUREMENT_BASIS:
        raise ValueError(
            f"Unsupported measurement basis for Phase5 parent baseline: {measurement_basis} "
            f"(expected {EXPECTED_MEASUREMENT_BASIS})"
        )
    if shots != EXPECTED_SHOTS:
        raise ValueError(
            f"Unexpected shots for Phase5 parent baseline: {shots} "
            f"(expected {EXPECTED_SHOTS})"
        )

    edge_definition = build_edge_definition_from_spec(circuit_spec)

    qc = build_phase5_parent_baseline_circuit(
        n_qubits=n_qubits,
        rx_ratio=rx_ratio,
        ry_ratio=ry_ratio,
        edge_definition=edge_definition,
    )

    backend = simulator_backend(noise_mode)
    tqc = transpile(
        qc,
        backend=backend,
        seed_transpiler=DEFAULT_SEED,
        optimization_level=0,
    )

    result = backend.run(tqc, shots=shots).result()
    counts = result.get_counts()
    summary = summarize_counts(counts)

    return {
        "phase": circuit_spec["phase"],
        "study_title": circuit_spec["study_title"],
        "topology": circuit_spec["topology_name"],
        "topology_class": circuit_spec["topology_class"],
        "phase_role": circuit_spec.get("phase_role"),
        "phase5_role": circuit_spec.get("phase5_role"),
        "predicted_response_class": circuit_spec.get("predicted_response_class"),
        "circuit_id": circuit_spec["circuit_id"],
        "parent_circuit_id": circuit_spec["circuit_id"],
        "source_phase4_circuit_id": circuit_spec.get("source_phase4_circuit_id"),
        "run_type": "baseline",
        "noise_mode": noise_mode,
        "measurement_basis": "X",
        "shots": shots,
        "seed_simulator": DEFAULT_SEED,
        "seed_transpiler": DEFAULT_SEED,
        "n_qubits": n_qubits,
        "rx_ratio": rx_ratio,
        "ry_ratio": ry_ratio,
        "rx_percent": circuit_spec["rx_percent"],
        "ry_percent": circuit_spec["ry_percent"],
        "ablation": None,
        "edge_definition": edge_definition,
        "counts": counts,
        "summary": summary,
        "target_bitstring": "1" * n_qubits,
        "metadata": {
            "generator": "run_phase5_parent_baseline_scan.py",
            "builder_version": "phase5_v1_phase4_generalized_parent_baseline",
            "profile_weights": PHASE5_PROFILE_WEIGHTS,
            "layerA_rx_scale": LAYER_A_RX_SCALE,
            "layerA_ry_scale": LAYER_A_RY_SCALE,
            "layerB_rx_scale": LAYER_B_RX_SCALE,
            "layerB_ry_scale": LAYER_B_RY_SCALE,
            "selection_reason": circuit_spec.get("selection_reason"),
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

    out_dir = REPO_ROOT / "results" / "raw" / topology / "baseline"
    ensure_dir(out_dir)

    filename = f"{circuit_id}__{noise_mode}__{basis}__shots{shots}.json"
    out_path = out_dir / filename

    write_json(out_path, payload)
    return out_path


def validate_catalog(catalog: Dict[str, Any]) -> None:
    if catalog.get("catalog_name") != "phase5_parent_catalog":
        raise ValueError("Unexpected catalog_name for Phase5 parent catalog.")

    records = catalog.get("records", [])
    if len(records) != 3:
        raise ValueError(f"Expected 3 parent records, found {len(records)}")

    for spec in records:
        if int(spec.get("n_qubits", -1)) != 6:
            raise ValueError(
                f"Expected n_qubits=6, found {spec.get('n_qubits')} in {spec.get('circuit_id')}"
            )
        if spec.get("noise_model_tag") != EXPECTED_NOISE_MODE:
            raise ValueError(
                f"Expected noise_model_tag={EXPECTED_NOISE_MODE}, "
                f"found {spec.get('noise_model_tag')} in {spec.get('circuit_id')}"
            )
        if spec.get("measurement_basis") != EXPECTED_MEASUREMENT_BASIS:
            raise ValueError(
                f"Expected measurement_basis={EXPECTED_MEASUREMENT_BASIS}, "
                f"found {spec.get('measurement_basis')} in {spec.get('circuit_id')}"
            )
        if int(spec.get("shots", -1)) != EXPECTED_SHOTS:
            raise ValueError(
                f"Expected shots={EXPECTED_SHOTS}, "
                f"found {spec.get('shots')} in {spec.get('circuit_id')}"
            )
        if len(spec.get("edges", [])) <= 0:
            raise ValueError(f"Missing edges in {spec.get('circuit_id')}")


def main() -> None:
    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Parent catalog not found: {CATALOG_PATH}\n"
            "Run generate_phase5_parent_catalog.py first."
        )

    catalog = read_json(CATALOG_PATH)
    validate_catalog(catalog)

    records = catalog["records"]

    print("Starting Phase5 predictive parent baseline scan...")
    print(f"Catalog: {CATALOG_PATH}")
    print(f"Parent baseline records: {len(records)}")
    print(f"Noise mode: {EXPECTED_NOISE_MODE}")
    print("Measurement basis: X")
    print(f"Shots: {EXPECTED_SHOTS}")
    print("Builder version: phase5_v1_phase4_generalized_parent_baseline")
    print()

    completed = 0

    for spec in records:
        circuit_id = spec["circuit_id"]
        topology = spec["topology_name"]

        print(
            f"Running {circuit_id} | topology={topology} | "
            f"noise={spec['noise_model_tag']} | basis={spec['measurement_basis']} | shots={spec['shots']}"
        )

        payload = run_single_job(spec)
        out_path = save_raw_result(payload)

        print(f"  saved -> {out_path}")
        completed += 1

    print()
    print("Phase5 predictive parent baseline scan complete.")
    print(f"Completed jobs: {completed}")
    print(f"Expected jobs: {len(records)}")


if __name__ == "__main__":
    main()