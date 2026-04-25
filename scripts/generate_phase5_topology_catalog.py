from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PHASE5_SETTINGS = {
    "phase": "Phase5",
    "study_title": "SRFM Quantum Phase5 Predictive Structural Response Study",
    "catalog_version": "v1.0",
    "builder_script": "generate_phase5_topology_catalog.py",
    "source_reference": "Phase4 topology layer carried forward into Phase5.",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def build_topology_records() -> list[dict[str, Any]]:
    """
    Phase5 fixed topology definitions.

    Design policy:
    - Preserve exact Phase4 topology layer for continuity
    - ring6   : reference formation-favoring topology
    - chain6  : loop-free adaptive comparison topology
    - random6 : fixed irregular connected topology for reproducibility
    """
    records: list[dict[str, Any]] = [
        {
            "topology_name": "ring6",
            "topology_class": "cycle",
            "n_qubits": 6,
            "edge_count": 6,
            "edges": [
                [0, 1],
                [1, 2],
                [2, 3],
                [3, 4],
                [4, 5],
                [5, 0],
            ],
            "is_connected": True,
            "has_loop": True,
            "phase_role": "formation_reference",
            "phase5_response_hypothesis": (
                "Strong baseline formation, weak adaptive gain, gradual degradation "
                "under increasing perturbation."
            ),
            "notes": (
                "Reference ring topology carried forward from Phase4. "
                "Expected to favor formation strength over adaptive improvement."
            ),
        },
        {
            "topology_name": "chain6",
            "topology_class": "path",
            "n_qubits": 6,
            "edge_count": 5,
            "edges": [
                [0, 1],
                [1, 2],
                [2, 3],
                [3, 4],
                [4, 5],
            ],
            "is_connected": True,
            "has_loop": False,
            "phase_role": "adaptive_comparison",
            "phase5_response_hypothesis": (
                "Weaker baseline formation, adaptive improvement under small perturbation, "
                "eventual collapse under larger perturbation."
            ),
            "notes": (
                "Loop-free comparison topology carried forward from Phase4. "
                "Expected to reveal constraint-release behavior more clearly."
            ),
        },
        {
            "topology_name": "random6",
            "topology_class": "irregular6_fixed",
            "n_qubits": 6,
            "edge_count": 6,
            "edges": [
                [0, 1],
                [1, 2],
                [2, 3],
                [3, 4],
                [4, 1],
                [4, 5],
            ],
            "is_connected": True,
            "has_loop": True,
            "phase_role": "intermediate_comparison",
            "phase5_response_hypothesis": (
                "Intermediate regime between ring-like persistence and chain-like adaptation."
            ),
            "notes": (
                "Fixed irregular connected topology carried forward from Phase4. "
                "Must remain fixed across runs and releases for reproducibility."
            ),
        },
    ]
    return records


def main() -> None:
    repo_root = Path(r"E:\SRFM_QUANTUM_PHASE5")
    circuits_dir = repo_root / "circuits"
    topologies_dir = circuits_dir / "topologies"

    ensure_dir(circuits_dir)
    ensure_dir(topologies_dir)

    topology_records = build_topology_records()

    # Write individual topology JSON files
    for record in topology_records:
        topology_name = record["topology_name"]
        out_path = topologies_dir / f"{topology_name}_topology.json"
        write_json(out_path, record)

    # Write master catalog
    catalog = {
        "catalog_name": "phase5_topology_catalog",
        "phase": PHASE5_SETTINGS["phase"],
        "study_title": PHASE5_SETTINGS["study_title"],
        "catalog_version": PHASE5_SETTINGS["catalog_version"],
        "builder_script": PHASE5_SETTINGS["builder_script"],
        "n_topologies": len(topology_records),
        "topologies": topology_records,
        "global_notes": [
            "This catalog defines the fixed topology layer for Phase5.",
            "Phase5 preserves the exact 6-qubit topology layer from Phase4 for continuity.",
            "Phase5 reinterprets these topologies in a predictive structural-response framework.",
            "random6 is intentionally fixed for reproducibility and should never be regenerated randomly.",
        ],
        "source_reference": PHASE5_SETTINGS["source_reference"],
    }

    catalog_path = circuits_dir / "phase5_topology_catalog.json"
    write_json(catalog_path, catalog)

    print("Phase5 topology catalog generation completed.")
    print(f"Repository root : {repo_root}")
    print(f"Topologies dir  : {topologies_dir}")
    print(f"Catalog path    : {catalog_path}")
    print("Generated files:")
    for record in topology_records:
        print(f"  - {topologies_dir / (record['topology_name'] + '_topology.json')}")
    print(f"  - {catalog_path}")


if __name__ == "__main__":
    main()