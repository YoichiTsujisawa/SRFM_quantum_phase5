from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd


# ============================================================
# Phase5 Structural Metrics Analysis
# ------------------------------------------------------------
# Purpose:
#   - Read Phase5 edge-level summary
#   - Derive structural metrics for deeper interpretation
#   - Quantify:
#       1) connectivity impact
#       2) edge redundancy / remaining-edge ratio
#       3) structural fragility curves
#       4) entropy-order coupling
#
# Output files:
#   data/tables/phase5_connectivity_impact_summary.csv
#   data/tables/phase5_edge_redundancy_summary.csv
#   data/tables/phase5_structural_fragility_curve.csv
#   data/tables/phase5_entropy_order_correlation.csv
#   results/summary/phase5_structural_metrics_summary.md
# ============================================================

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

TABLES_DIR = REPO_ROOT / "data" / "tables"
SUMMARY_DIR = REPO_ROOT / "results" / "summary"

EDGE_LEVEL_CSV = TABLES_DIR / "phase5_multi_ablation_edge_level_summary.csv"

CONNECTIVITY_CSV = TABLES_DIR / "phase5_connectivity_impact_summary.csv"
REDUNDANCY_CSV = TABLES_DIR / "phase5_edge_redundancy_summary.csv"
FRAGILITY_CSV = TABLES_DIR / "phase5_structural_fragility_curve.csv"
ENTROPY_CORR_CSV = TABLES_DIR / "phase5_entropy_order_correlation.csv"
SUMMARY_MD = SUMMARY_DIR / "phase5_structural_metrics_summary.md"

EXPECTED_TOPOLOGIES = ["chain6", "random6", "ring6"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def load_edge_level() -> pd.DataFrame:
    if not EDGE_LEVEL_CSV.exists():
        raise FileNotFoundError(
            f"Missing edge-level summary: {EDGE_LEVEL_CSV}\n"
            "Run analyze_phase5_multi_ablation.py first."
        )

    df = pd.read_csv(EDGE_LEVEL_CSV)

    required_cols = [
        "topology",
        "perturbation_order",
        "remaining_edge_count",
        "is_connected_after_ablation",
        "n_components_after_ablation",
        "has_loop_after_ablation",
        "abs_parity",
        "target_probability",
        "entropy_bits",
        "delta_abs_parity",
        "delta_target_probability",
        "delta_entropy",
        "baseline_abs_parity",
        "baseline_target_probability",
        "baseline_entropy_bits",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in edge-level CSV: {missing}")

    return df


def add_structural_fields(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # parent edge count inferred from baseline + dropped edges
    # equivalent to remaining + dropped, but use explicit columns if present
    if "dropped_edge_count" in out.columns:
        out["parent_edge_count"] = out["remaining_edge_count"] + out["dropped_edge_count"]
    elif "perturbation_order" in out.columns:
        out["parent_edge_count"] = out["remaining_edge_count"] + out["perturbation_order"]
    else:
        raise ValueError("Cannot infer parent_edge_count")

    out["remaining_edge_ratio"] = out["remaining_edge_count"] / out["parent_edge_count"]

    out["connectivity_state"] = out["is_connected_after_ablation"].map(
        lambda x: "connected" if bool(x) else "disconnected"
    )

    out["loop_state"] = out["has_loop_after_ablation"].map(
        lambda x: "loop_present" if bool(x) else "loop_absent"
    )

    out["order_entropy_coupling"] = out["delta_target_probability"] * (-out["delta_entropy"])

    return out


def build_connectivity_impact_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["topology", "perturbation_order", "connectivity_state"], as_index=False)
        .agg(
            n_records=("circuit_id", "count"),
            mean_delta_abs_parity=("delta_abs_parity", "mean"),
            mean_delta_target_probability=("delta_target_probability", "mean"),
            mean_delta_entropy=("delta_entropy", "mean"),
            mean_abs_parity=("abs_parity", "mean"),
            mean_target_probability=("target_probability", "mean"),
            mean_entropy_bits=("entropy_bits", "mean"),
            mean_remaining_edge_ratio=("remaining_edge_ratio", "mean"),
            mean_n_components=("n_components_after_ablation", "mean"),
        )
        .sort_values(["topology", "perturbation_order", "connectivity_state"])
        .reset_index(drop=True)
    )
    return summary


def build_edge_redundancy_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["topology", "parent_edge_count", "remaining_edge_count", "remaining_edge_ratio"], as_index=False)
        .agg(
            n_records=("circuit_id", "count"),
            mean_delta_abs_parity=("delta_abs_parity", "mean"),
            mean_delta_target_probability=("delta_target_probability", "mean"),
            mean_delta_entropy=("delta_entropy", "mean"),
            mean_abs_parity=("abs_parity", "mean"),
            mean_target_probability=("target_probability", "mean"),
            mean_entropy_bits=("entropy_bits", "mean"),
            connected_fraction=("is_connected_after_ablation", "mean"),
            loop_fraction=("has_loop_after_ablation", "mean"),
        )
        .sort_values(["topology", "remaining_edge_ratio", "remaining_edge_count"])
        .reset_index(drop=True)
    )
    return summary


def build_fragility_curve(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["topology", "perturbation_order"], as_index=False)
        .agg(
            n_records=("circuit_id", "count"),
            mean_delta_abs_parity=("delta_abs_parity", "mean"),
            mean_delta_target_probability=("delta_target_probability", "mean"),
            mean_delta_entropy=("delta_entropy", "mean"),
            mean_abs_parity=("abs_parity", "mean"),
            mean_target_probability=("target_probability", "mean"),
            mean_entropy_bits=("entropy_bits", "mean"),
            connected_fraction=("is_connected_after_ablation", "mean"),
            loop_fraction=("has_loop_after_ablation", "mean"),
            mean_remaining_edge_ratio=("remaining_edge_ratio", "mean"),
        )
        .sort_values(["topology", "perturbation_order"])
        .reset_index(drop=True)
    )

    summary["fragility_score"] = -summary["mean_delta_target_probability"]
    summary["stabilization_score"] = summary["mean_delta_target_probability"] + summary["mean_delta_abs_parity"] - summary["mean_delta_entropy"]

    return summary


def build_entropy_order_correlation(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[dict] = []

    for topology in EXPECTED_TOPOLOGIES:
        sub = df[df["topology"] == topology].copy()
        if sub.empty:
            continue

        corr_target_entropy = sub["delta_target_probability"].corr(sub["delta_entropy"])
        corr_parity_entropy = sub["delta_abs_parity"].corr(sub["delta_entropy"])
        corr_target_remaining = sub["delta_target_probability"].corr(sub["remaining_edge_ratio"])
        corr_entropy_remaining = sub["delta_entropy"].corr(sub["remaining_edge_ratio"])

        rows.append(
            {
                "topology": topology,
                "n_records": int(len(sub)),
                "corr_delta_target_vs_delta_entropy": corr_target_entropy,
                "corr_delta_abs_parity_vs_delta_entropy": corr_parity_entropy,
                "corr_delta_target_vs_remaining_edge_ratio": corr_target_remaining,
                "corr_delta_entropy_vs_remaining_edge_ratio": corr_entropy_remaining,
                "mean_order_entropy_coupling": float(sub["order_entropy_coupling"].mean()),
                "mean_delta_target_probability": float(sub["delta_target_probability"].mean()),
                "mean_delta_entropy": float(sub["delta_entropy"].mean()),
            }
        )

    summary = pd.DataFrame(rows).sort_values("topology").reset_index(drop=True)
    return summary


def make_markdown_summary(
    connectivity_df: pd.DataFrame,
    redundancy_df: pd.DataFrame,
    fragility_df: pd.DataFrame,
    entropy_df: pd.DataFrame,
) -> str:
    lines: List[str] = []

    lines.append("# Phase5 Structural Metrics Summary")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("- Derived from phase5_multi_ablation_edge_level_summary.csv")
    lines.append("- Focus: connectivity impact, redundancy response, fragility curves, entropy-order coupling")
    lines.append("")

    lines.append("## Connectivity Impact")
    lines.append("")
    for topology in EXPECTED_TOPOLOGIES:
        sub = connectivity_df[connectivity_df["topology"] == topology]
        if sub.empty:
            continue
        lines.append(f"### {topology}")
        lines.append("")
        for _, row in sub.iterrows():
            lines.append(
                f"- k={int(row['perturbation_order'])} | {row['connectivity_state']} | "
                f"n={int(row['n_records'])} | "
                f"mean_delta_target={row['mean_delta_target_probability']:.6f} | "
                f"mean_delta_parity={row['mean_delta_abs_parity']:.6f} | "
                f"mean_delta_entropy={row['mean_delta_entropy']:.6f}"
            )
        lines.append("")

    lines.append("## Structural Fragility Curves")
    lines.append("")
    for topology in EXPECTED_TOPOLOGIES:
        sub = fragility_df[fragility_df["topology"] == topology]
        if sub.empty:
            continue
        lines.append(f"### {topology}")
        lines.append("")
        for _, row in sub.iterrows():
            lines.append(
                f"- k={int(row['perturbation_order'])} | "
                f"mean_delta_target={row['mean_delta_target_probability']:.6f} | "
                f"mean_delta_parity={row['mean_delta_abs_parity']:.6f} | "
                f"mean_delta_entropy={row['mean_delta_entropy']:.6f} | "
                f"connected_fraction={row['connected_fraction']:.3f} | "
                f"remaining_edge_ratio={row['mean_remaining_edge_ratio']:.3f}"
            )
        lines.append("")

    lines.append("## Entropy / Order Coupling")
    lines.append("")
    for _, row in entropy_df.iterrows():
        lines.append(
            f"- {row['topology']} | "
            f"corr(target, entropy)={row['corr_delta_target_vs_delta_entropy']:.6f} | "
            f"corr(parity, entropy)={row['corr_delta_abs_parity_vs_delta_entropy']:.6f} | "
            f"corr(target, remaining_ratio)={row['corr_delta_target_vs_remaining_edge_ratio']:.6f}"
        )
    lines.append("")

    lines.append("## Output Files")
    lines.append("")
    lines.append(f"- {CONNECTIVITY_CSV}")
    lines.append(f"- {REDUNDANCY_CSV}")
    lines.append(f"- {FRAGILITY_CSV}")
    lines.append(f"- {ENTROPY_CORR_CSV}")
    lines.append(f"- {SUMMARY_MD}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    ensure_dir(TABLES_DIR)
    ensure_dir(SUMMARY_DIR)

    edge_df = load_edge_level()
    edge_df = add_structural_fields(edge_df)

    connectivity_df = build_connectivity_impact_summary(edge_df)
    redundancy_df = build_edge_redundancy_summary(edge_df)
    fragility_df = build_fragility_curve(edge_df)
    entropy_df = build_entropy_order_correlation(edge_df)

    connectivity_df.to_csv(CONNECTIVITY_CSV, index=False, encoding="utf-8-sig")
    redundancy_df.to_csv(REDUNDANCY_CSV, index=False, encoding="utf-8-sig")
    fragility_df.to_csv(FRAGILITY_CSV, index=False, encoding="utf-8-sig")
    entropy_df.to_csv(ENTROPY_CORR_CSV, index=False, encoding="utf-8-sig")

    summary_text = make_markdown_summary(
        connectivity_df=connectivity_df,
        redundancy_df=redundancy_df,
        fragility_df=fragility_df,
        entropy_df=entropy_df,
    )
    write_text(SUMMARY_MD, summary_text)

    print("Phase5 structural metrics analysis completed.")
    print("Generated files:")
    print(f"  - {CONNECTIVITY_CSV}")
    print(f"  - {REDUNDANCY_CSV}")
    print(f"  - {FRAGILITY_CSV}")
    print(f"  - {ENTROPY_CORR_CSV}")
    print(f"  - {SUMMARY_MD}")


if __name__ == "__main__":
    main()