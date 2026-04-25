from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


# ============================================================
# Phase5 Hardware Validation Analysis
# ------------------------------------------------------------
# Purpose:
#   - Read Phase5 hardware validation raw JSON results
#   - Compare chain6 baseline vs chain6 k=1
#   - Compare ring6 baseline vs ring6 k=1
#   - Compare hardware deltas with simulation deltas
#   - Produce CSV + Markdown summary
#
# Outputs:
#   data/tables/phase5_hardware_validation_summary.csv
#   data/tables/phase5_hardware_vs_sim_comparison.csv
#   results/summary/phase5_hardware_validation_summary.md
# ============================================================

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

RAW_HARDWARE_DIR = REPO_ROOT / "results" / "raw_hardware"
SIM_EDGE_SUMMARY_CSV = REPO_ROOT / "data" / "tables" / "phase5_multi_ablation_edge_level_summary.csv"

TABLES_DIR = REPO_ROOT / "data" / "tables"
SUMMARY_DIR = REPO_ROOT / "results" / "summary"

HARDWARE_SUMMARY_CSV = TABLES_DIR / "phase5_hardware_validation_summary.csv"
HARDWARE_VS_SIM_CSV = TABLES_DIR / "phase5_hardware_vs_sim_comparison.csv"
SUMMARY_MD = SUMMARY_DIR / "phase5_hardware_validation_summary.md"


TARGETS = [
    {
        "topology": "chain6",
        "kind": "baseline",
        "tag": "chain6_baseline",
        "path": RAW_HARDWARE_DIR / "chain6" / "chain6_baseline__hardware__shots4096.json",
    },
    {
        "topology": "chain6",
        "kind": "k1",
        "tag": "chain6_k1_e2",
        "path": RAW_HARDWARE_DIR / "chain6" / "chain6_k1_e2__hardware__shots4096.json",
    },
    {
        "topology": "ring6",
        "kind": "baseline",
        "tag": "ring6_baseline",
        "path": RAW_HARDWARE_DIR / "ring6" / "ring6_baseline__hardware__shots4096.json",
    },
    {
        "topology": "ring6",
        "kind": "k1",
        "tag": "ring6_k1_e0",
        "path": RAW_HARDWARE_DIR / "ring6" / "ring6_k1_e0__hardware__shots4096.json",
    },
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sign_label(x: float, eps: float = 1e-12) -> str:
    if x > eps:
        return "positive"
    if x < -eps:
        return "negative"
    return "zero"


def sign_match(a: float, b: float) -> bool:
    return sign_label(a) == sign_label(b)


def load_hardware_rows() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for target in TARGETS:
        path = target["path"]
        if not path.exists():
            raise FileNotFoundError(f"Missing hardware raw result: {path}")

        payload = read_json(path)
        summary = payload.get("summary", {})
        transpile = payload.get("transpile_metadata", {})

        rows.append(
            {
                "topology": target["topology"],
                "kind": target["kind"],
                "hardware_validation_tag": payload.get("hardware_validation_tag", target["tag"]),
                "circuit_id": payload.get("circuit_id"),
                "source_phase5_circuit_id": payload.get("source_phase5_circuit_id"),
                "parent_circuit_id": payload.get("parent_circuit_id"),
                "backend_name": payload.get("backend_name"),
                "job_id": payload.get("job_id"),
                "shots": int(payload.get("shots", 0)),
                "target_probability": float(summary.get("target_probability", 0.0)),
                "abs_parity": float(summary.get("abs_parity", 0.0)),
                "entropy_bits": float(summary.get("entropy_bits", 0.0)),
                "top_probability": float(summary.get("top_probability", 0.0)),
                "top_state": summary.get("top_state"),
                "n_observed_states": int(summary.get("n_observed_states", 0)),
                "transpiled_depth": int(transpile.get("transpiled_depth", 0)),
                "transpiled_size": int(transpile.get("transpiled_size", 0)),
                "transpiled_two_qubit_gate_count": int(transpile.get("transpiled_two_qubit_gate_count", 0)),
                "transpiled_one_qubit_gate_count": int(transpile.get("transpiled_one_qubit_gate_count", 0)),
                "logical_qasm2_path": payload.get("qasm2_export", {}).get("logical_qasm2_path"),
                "transpiled_qasm2_path": payload.get("qasm2_export", {}).get("transpiled_qasm2_path"),
                "source_path": str(path),
            }
        )

    return pd.DataFrame(rows)


def build_hardware_delta_summary(hw_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for topology in ["chain6", "ring6"]:
        baseline = hw_df[(hw_df["topology"] == topology) & (hw_df["kind"] == "baseline")]
        k1 = hw_df[(hw_df["topology"] == topology) & (hw_df["kind"] == "k1")]

        if len(baseline) != 1 or len(k1) != 1:
            raise ValueError(f"Expected exactly one baseline and one k1 row for {topology}")

        b = baseline.iloc[0]
        a = k1.iloc[0]

        rows.append(
            {
                "topology": topology,
                "backend_name": a["backend_name"],
                "baseline_tag": b["hardware_validation_tag"],
                "k1_tag": a["hardware_validation_tag"],
                "baseline_job_id": b["job_id"],
                "k1_job_id": a["job_id"],
                "baseline_target_probability": b["target_probability"],
                "k1_target_probability": a["target_probability"],
                "hardware_delta_target_probability": a["target_probability"] - b["target_probability"],
                "baseline_abs_parity": b["abs_parity"],
                "k1_abs_parity": a["abs_parity"],
                "hardware_delta_abs_parity": a["abs_parity"] - b["abs_parity"],
                "baseline_entropy_bits": b["entropy_bits"],
                "k1_entropy_bits": a["entropy_bits"],
                "hardware_delta_entropy": a["entropy_bits"] - b["entropy_bits"],
                "baseline_top_probability": b["top_probability"],
                "k1_top_probability": a["top_probability"],
                "hardware_delta_top_probability": a["top_probability"] - b["top_probability"],
                "baseline_two_qubit_gates": b["transpiled_two_qubit_gate_count"],
                "k1_two_qubit_gates": a["transpiled_two_qubit_gate_count"],
                "baseline_depth": b["transpiled_depth"],
                "k1_depth": a["transpiled_depth"],
            }
        )

    return pd.DataFrame(rows)


def get_sim_delta_for_target(topology: str, dropped_edges: str) -> Dict[str, float]:
    if not SIM_EDGE_SUMMARY_CSV.exists():
        raise FileNotFoundError(
            f"Missing simulation edge-level summary: {SIM_EDGE_SUMMARY_CSV}"
        )

    sim_df = pd.read_csv(SIM_EDGE_SUMMARY_CSV)

    sub = sim_df[
        (sim_df["topology"] == topology)
        & (sim_df["perturbation_order"] == 1)
        & (sim_df["dropped_edges"] == dropped_edges)
    ]

    if len(sub) != 1:
        raise ValueError(
            f"Expected exactly one sim row for topology={topology}, dropped_edges={dropped_edges}, found {len(sub)}"
        )

    row = sub.iloc[0]

    return {
        "sim_delta_target_probability": float(row["delta_target_probability"]),
        "sim_delta_abs_parity": float(row["delta_abs_parity"]),
        "sim_delta_entropy": float(row["delta_entropy"]),
        "sim_target_probability": float(row["target_probability"]),
        "sim_abs_parity": float(row["abs_parity"]),
        "sim_entropy_bits": float(row["entropy_bits"]),
        "sim_baseline_target_probability": float(row["baseline_target_probability"]),
        "sim_baseline_abs_parity": float(row["baseline_abs_parity"]),
        "sim_baseline_entropy_bits": float(row["baseline_entropy_bits"]),
    }


def build_hardware_vs_sim_summary(delta_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    target_edges = {
        "chain6": "e2",
        "ring6": "e0",
    }

    for _, row in delta_df.iterrows():
        topology = row["topology"]
        sim = get_sim_delta_for_target(topology, target_edges[topology])

        hw_dt = float(row["hardware_delta_target_probability"])
        hw_dp = float(row["hardware_delta_abs_parity"])
        hw_de = float(row["hardware_delta_entropy"])

        sim_dt = sim["sim_delta_target_probability"]
        sim_dp = sim["sim_delta_abs_parity"]
        sim_de = sim["sim_delta_entropy"]

        rows.append(
            {
                "topology": topology,
                "dropped_edges": target_edges[topology],
                "hardware_delta_target_probability": hw_dt,
                "sim_delta_target_probability": sim_dt,
                "target_sign_match": sign_match(hw_dt, sim_dt),
                "hardware_target_sign": sign_label(hw_dt),
                "sim_target_sign": sign_label(sim_dt),
                "hardware_delta_abs_parity": hw_dp,
                "sim_delta_abs_parity": sim_dp,
                "parity_sign_match": sign_match(hw_dp, sim_dp),
                "hardware_parity_sign": sign_label(hw_dp),
                "sim_parity_sign": sign_label(sim_dp),
                "hardware_delta_entropy": hw_de,
                "sim_delta_entropy": sim_de,
                "entropy_sign_match": sign_match(hw_de, sim_de),
                "hardware_entropy_sign": sign_label(hw_de),
                "sim_entropy_sign": sign_label(sim_de),
                "hardware_baseline_target_probability": float(row["baseline_target_probability"]),
                "hardware_k1_target_probability": float(row["k1_target_probability"]),
                "sim_baseline_target_probability": sim["sim_baseline_target_probability"],
                "sim_k1_target_probability": sim["sim_target_probability"],
                "hardware_baseline_abs_parity": float(row["baseline_abs_parity"]),
                "hardware_k1_abs_parity": float(row["k1_abs_parity"]),
                "sim_baseline_abs_parity": sim["sim_baseline_abs_parity"],
                "sim_k1_abs_parity": sim["sim_abs_parity"],
                "backend_name": row["backend_name"],
                "baseline_job_id": row["baseline_job_id"],
                "k1_job_id": row["k1_job_id"],
            }
        )

    out = pd.DataFrame(rows)

    # topology-level ranking comparison
    if set(out["topology"]) == {"chain6", "ring6"}:
        chain_hw = float(out[out["topology"] == "chain6"]["hardware_delta_target_probability"].iloc[0])
        ring_hw = float(out[out["topology"] == "ring6"]["hardware_delta_target_probability"].iloc[0])
        chain_sim = float(out[out["topology"] == "chain6"]["sim_delta_target_probability"].iloc[0])
        ring_sim = float(out[out["topology"] == "ring6"]["sim_delta_target_probability"].iloc[0])

        out["hardware_chain_minus_ring_delta_target"] = chain_hw - ring_hw
        out["sim_chain_minus_ring_delta_target"] = chain_sim - ring_sim
        out["ranking_match_chain_gt_ring"] = (chain_hw > ring_hw) == (chain_sim > ring_sim)

    return out


def evaluate_validation(comparison_df: pd.DataFrame) -> str:
    target_matches = comparison_df["target_sign_match"].sum()
    parity_matches = comparison_df["parity_sign_match"].sum()

    ranking_match = bool(comparison_df["ranking_match_chain_gt_ring"].iloc[0])

    if target_matches == 2 and ranking_match:
        return "strong_success"

    if target_matches >= 1 and ranking_match:
        return "moderate_success"

    if ranking_match or target_matches >= 1 or parity_matches >= 1:
        return "weak_success"

    return "inconclusive_or_mismatch"


def make_markdown(
    hw_df: pd.DataFrame,
    delta_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
) -> str:
    validation_result = evaluate_validation(comparison_df)

    lines: List[str] = []
    lines.append("# Phase5 Hardware Validation Summary")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Hardware records: {len(hw_df)}")
    lines.append(f"- Compared topologies: {', '.join(delta_df['topology'].tolist())}")
    lines.append(f"- Backend: {hw_df['backend_name'].iloc[0]}")
    lines.append(f"- Validation result: **{validation_result}**")
    lines.append("")

    lines.append("## Hardware Raw Metrics")
    lines.append("")
    for _, row in hw_df.sort_values(["topology", "kind"]).iterrows():
        lines.append(
            f"- {row['topology']} | {row['kind']} | "
            f"target={row['target_probability']:.6f} | "
            f"parity={row['abs_parity']:.6f} | "
            f"entropy={row['entropy_bits']:.6f} | "
            f"job_id={row['job_id']}"
        )
    lines.append("")

    lines.append("## Hardware Baseline-to-k1 Deltas")
    lines.append("")
    for _, row in delta_df.sort_values("topology").iterrows():
        lines.append(
            f"- {row['topology']} | "
            f"Δtarget={row['hardware_delta_target_probability']:.6f} | "
            f"Δparity={row['hardware_delta_abs_parity']:.6f} | "
            f"Δentropy={row['hardware_delta_entropy']:.6f}"
        )
    lines.append("")

    lines.append("## Hardware vs Simulation Sign Comparison")
    lines.append("")
    for _, row in comparison_df.sort_values("topology").iterrows():
        lines.append(
            f"- {row['topology']} | edge={row['dropped_edges']} | "
            f"hardware Δtarget={row['hardware_delta_target_probability']:.6f} "
            f"({row['hardware_target_sign']}) | "
            f"sim Δtarget={row['sim_delta_target_probability']:.6f} "
            f"({row['sim_target_sign']}) | "
            f"target_sign_match={row['target_sign_match']} | "
            f"hardware Δparity={row['hardware_delta_abs_parity']:.6f} "
            f"({row['hardware_parity_sign']}) | "
            f"sim Δparity={row['sim_delta_abs_parity']:.6f} "
            f"({row['sim_parity_sign']}) | "
            f"parity_sign_match={row['parity_sign_match']}"
        )
    lines.append("")

    if "ranking_match_chain_gt_ring" in comparison_df.columns:
        r = comparison_df.iloc[0]
        lines.append("## Ranking Comparison")
        lines.append("")
        lines.append(
            f"- Hardware chain-minus-ring Δtarget: "
            f"{r['hardware_chain_minus_ring_delta_target']:.6f}"
        )
        lines.append(
            f"- Simulation chain-minus-ring Δtarget: "
            f"{r['sim_chain_minus_ring_delta_target']:.6f}"
        )
        lines.append(
            f"- Ranking match chain > ring: {bool(r['ranking_match_chain_gt_ring'])}"
        )
        lines.append("")

    lines.append("## Output Files")
    lines.append("")
    lines.append(f"- {HARDWARE_SUMMARY_CSV}")
    lines.append(f"- {HARDWARE_VS_SIM_CSV}")
    lines.append(f"- {SUMMARY_MD}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    ensure_dir(TABLES_DIR)
    ensure_dir(SUMMARY_DIR)

    hw_df = load_hardware_rows()
    delta_df = build_hardware_delta_summary(hw_df)
    comparison_df = build_hardware_vs_sim_summary(delta_df)

    hw_df.to_csv(HARDWARE_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    comparison_df.to_csv(HARDWARE_VS_SIM_CSV, index=False, encoding="utf-8-sig")

    md = make_markdown(hw_df, delta_df, comparison_df)
    SUMMARY_MD.write_text(md, encoding="utf-8")

    print("Phase5 hardware validation analysis completed.")
    print(f"Hardware rows: {len(hw_df)}")
    print("Generated files:")
    print(f"  - {HARDWARE_SUMMARY_CSV}")
    print(f"  - {HARDWARE_VS_SIM_CSV}")
    print(f"  - {SUMMARY_MD}")

    print()
    print("Validation result:")
    print(f"  - {evaluate_validation(comparison_df)}")


if __name__ == "__main__":
    main()