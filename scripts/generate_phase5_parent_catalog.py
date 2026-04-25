from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PHASE5_SETTINGS = {
    "phase": "Phase5",
    "study_title": "SRFM Quantum Phase5 Predictive Structural Response Study",
    "catalog_version": "v1.0",
    "builder_script": "generate_phase5_parent_catalog.py",
    "builder_version": "phase5_parent_selector_v1",
    "noise_model_tag": "noisy_sim",
    "measurement_basis": "xbasis",
    "shots": 4096,
    "n_qubits": 6,
    "selection_policy": "one_representative_parent_per_topology",
}


# Locked Phase5 parent choices
PHASE5_PARENT_SELECTION = {
    "ring6": {
        "source_circuit_id": "phase4_ring6_rx62_ry38",
        "selection_reason": (
            "Selected as the Phase5 ring6 parent because Phase4 identified this design "
            "as the strongest ring-side representative under difference-centered interpretation."
        ),
        "predicted_response_class": "formation_dominated_gradual_degradation",
    },
    "chain6": {
        "source_circuit_id": "phase4_chain6_rx50_ry50",
        "selection_reason": (
            "Selected as the Phase5 chain6 parent because Phase4 identified this design "
            "as the strongest adaptive-improvement representative."
        ),
        "predicted_response_class": "adaptive_improvement_then_collapse",
    },
    "random6": {
        "source_circuit_id": "phase4_random6_rx48_ry52",
        "selection_reason": (
            "Selected as the Phase5 random6 parent because Phase4 identified this design "
            "as the strongest intermediate irregular representative."
        ),
        "predicted_response_class": "intermediate_mixed_response",
    },
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def validate_phase4_baseline_catalog(catalog: dict[str, Any]) -> None:
    if catalog.get("catalog_name") != "phase4_baseline_catalog":
        raise ValueError("Unexpected catalog_name in Phase4 baseline catalog.")

    records = catalog.get("records", [])
    if len(records) != 15:
        raise ValueError(f"Expected 15 Phase4 baseline records, found {len(records)}.")

    fixed_settings = catalog.get("fixed_settings", {})
    if fixed_settings.get("measurement_basis") != PHASE5_SETTINGS["measurement_basis"]:
        raise ValueError(
            f"Expected measurement_basis={PHASE5_SETTINGS['measurement_basis']}, "
            f"found {fixed_settings.get('measurement_basis')}."
        )
    if fixed_settings.get("noise_model_tag") != PHASE5_SETTINGS["noise_model_tag"]:
        raise ValueError(
            f"Expected noise_model_tag={PHASE5_SETTINGS['noise_model_tag']}, "
            f"found {fixed_settings.get('noise_model_tag')}."
        )
    if fixed_settings.get("shots") != PHASE5_SETTINGS["shots"]:
        raise ValueError(
            f"Expected shots={PHASE5_SETTINGS['shots']}, "
            f"found {fixed_settings.get('shots')}."
        )


def build_phase5_parent_record(
    phase4_record: dict[str, Any],
    selection_metadata: dict[str, str],
) -> dict[str, Any]:
    topology_name = phase4_record["topology_name"]
    source_spec_name = phase4_record["spec_name"]

    phase5_spec_name = f"{topology_name}_predictive_parent"
    phase5_circuit_id = f"phase5_{phase5_spec_name}"

    circuit_json_relpath = Path("circuits") / topology_name / "baseline" / f"{phase5_spec_name}.json"
    output_json_relpath = (
        Path("results")
        / "raw"
        / topology_name
        / "baseline"
        / f"{phase5_spec_name}__{PHASE5_SETTINGS['noise_model_tag']}__"
          f"{PHASE5_SETTINGS['measurement_basis']}__"
          f"shots{PHASE5_SETTINGS['shots']}.json"
    )

    record = {
        "circuit_id": phase5_circuit_id,
        "spec_name": phase5_spec_name,
        "scan_type": "predictive_parent_baseline",
        "phase": PHASE5_SETTINGS["phase"],
        "study_title": PHASE5_SETTINGS["study_title"],
        "builder_version": PHASE5_SETTINGS["builder_version"],
        "source_phase4_circuit_id": phase4_record["circuit_id"],
        "source_phase4_spec_name": source_spec_name,
        "source_phase4_builder_version": phase4_record["builder_version"],
        "parent_selection_policy": PHASE5_SETTINGS["selection_policy"],
        "topology_name": topology_name,
        "topology_class": phase4_record["topology_class"],
        "phase_role": phase4_record["phase_role"],
        "phase5_role": "predictive_parent",
        "n_qubits": phase4_record["n_qubits"],
        "edge_count": phase4_record["edge_count"],
        "edges": phase4_record["edges"],
        "is_connected": phase4_record["is_connected"],
        "has_loop": phase4_record["has_loop"],
        "rx_ratio": phase4_record["rx_ratio"],
        "ry_ratio": phase4_record["ry_ratio"],
        "rx_percent": phase4_record["rx_percent"],
        "ry_percent": phase4_record["ry_percent"],
        "noise_model_tag": PHASE5_SETTINGS["noise_model_tag"],
        "measurement_basis": PHASE5_SETTINGS["measurement_basis"],
        "shots": PHASE5_SETTINGS["shots"],
        "predicted_response_class": selection_metadata["predicted_response_class"],
        "selection_reason": selection_metadata["selection_reason"],
        "circuit_json_relpath": str(circuit_json_relpath).replace("\\", "/"),
        "output_json_relpath": str(output_json_relpath).replace("\\", "/"),
        "notes": (
            "Phase5 predictive parent circuit specification. "
            "This record is a selected representative parent derived from the Phase4 baseline layer "
            "and serves as the source circuit for multi-edge perturbation experiments."
        ),
    }
    return record


def main() -> None:
    repo_root = Path(r"E:\SRFM_QUANTUM_PHASE5")
    circuits_dir = repo_root / "circuits"
    baseline_dir_ring = circuits_dir / "ring6" / "baseline"
    baseline_dir_chain = circuits_dir / "chain6" / "baseline"
    baseline_dir_random = circuits_dir / "random6" / "baseline"

    ensure_dir(circuits_dir)
    ensure_dir(baseline_dir_ring)
    ensure_dir(baseline_dir_chain)
    ensure_dir(baseline_dir_random)

    phase4_root = Path(r"E:\SRFM_QUANTUM_PHASE4")
    phase4_baseline_catalog_path = phase4_root / "circuits" / "phase4_baseline_catalog.json"

    if not phase4_baseline_catalog_path.exists():
        raise FileNotFoundError(
            f"Missing Phase4 baseline catalog: {phase4_baseline_catalog_path}"
        )

    phase4_baseline_catalog = read_json(phase4_baseline_catalog_path)
    validate_phase4_baseline_catalog(phase4_baseline_catalog)

    phase4_records = phase4_baseline_catalog["records"]
    phase4_by_circuit_id = {record["circuit_id"]: record for record in phase4_records}

    selected_records: list[dict[str, Any]] = []

    for topology_name, selection_metadata in PHASE5_PARENT_SELECTION.items():
        source_circuit_id = selection_metadata["source_circuit_id"]

        if source_circuit_id not in phase4_by_circuit_id:
            raise KeyError(
                f"Selected Phase4 parent not found in catalog: {source_circuit_id}"
            )

        phase4_record = phase4_by_circuit_id[source_circuit_id]

        if phase4_record["topology_name"] != topology_name:
            raise ValueError(
                f"Topology mismatch for {source_circuit_id}: "
                f"expected {topology_name}, found {phase4_record['topology_name']}"
            )

        phase5_record = build_phase5_parent_record(phase4_record, selection_metadata)

        out_path = repo_root / phase5_record["circuit_json_relpath"]
        write_json(out_path, phase5_record)

        selected_records.append(phase5_record)

    selected_records = sorted(selected_records, key=lambda x: x["topology_name"])

    catalog = {
        "catalog_name": "phase5_parent_catalog",
        "phase": PHASE5_SETTINGS["phase"],
        "study_title": PHASE5_SETTINGS["study_title"],
        "catalog_version": PHASE5_SETTINGS["catalog_version"],
        "builder_script": PHASE5_SETTINGS["builder_script"],
        "builder_version": PHASE5_SETTINGS["builder_version"],
        "source_catalog_ref": str(phase4_baseline_catalog_path).replace("\\", "/"),
        "parent_selection_policy": PHASE5_SETTINGS["selection_policy"],
        "fixed_settings": {
            "noise_model_tag": PHASE5_SETTINGS["noise_model_tag"],
            "measurement_basis": PHASE5_SETTINGS["measurement_basis"],
            "shots": PHASE5_SETTINGS["shots"],
            "n_qubits": PHASE5_SETTINGS["n_qubits"],
        },
        "n_records": len(selected_records),
        "records": selected_records,
        "global_notes": [
            "This catalog defines the selected parent layer for Phase5 predictive experiments.",
            "Each topology contributes exactly one representative parent circuit.",
            "Phase5 intentionally reduces parameter diversity in order to foreground predictive structural-response testing.",
            "These parent circuits are the truth source for Phase5 multi-edge perturbation generation.",
        ],
    }

    catalog_path = circuits_dir / "phase5_parent_catalog.json"
    write_json(catalog_path, catalog)

    print("Phase5 parent catalog generation completed.")
    print(f"Phase4 source catalog : {phase4_baseline_catalog_path}")
    print(f"Phase5 catalog path   : {catalog_path}")
    print(f"Selected records      : {len(selected_records)}")
    print("Selected parents:")
    for record in selected_records:
        print(
            f"  - {record['topology_name']}: "
            f"{record['source_phase4_circuit_id']} -> {record['circuit_id']}"
        )


if __name__ == "__main__":
    main()