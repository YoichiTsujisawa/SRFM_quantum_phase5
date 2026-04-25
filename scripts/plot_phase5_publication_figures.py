from __future__ import annotations

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# Phase5 Publication Figures
# ------------------------------------------------------------
# Purpose:
#   - Read Phase5 structural analysis tables
#   - Produce publication-style figures for Phase5
#
# Input:
#   data/tables/phase5_structural_fragility_curve.csv
#   data/tables/phase5_connectivity_impact_summary.csv
#   data/tables/phase5_entropy_order_correlation.csv
#   data/tables/phase5_edge_redundancy_summary.csv
#
# Output:
#   figures/paper/figure1_phase5_fragility_curve.png
#   figures/paper/figure2_phase5_connectivity_impact.png
#   figures/paper/figure3_phase5_entropy_order_coupling.png
#   figures/paper/figure4_phase5_edge_redundancy_response.png
#   figures/paper/phase5_publication_figures_manifest.md
# ============================================================

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

TABLES_DIR = REPO_ROOT / "data" / "tables"
FIGURES_DIR = REPO_ROOT / "figures" / "paper"

FRAGILITY_CSV = TABLES_DIR / "phase5_structural_fragility_curve.csv"
CONNECTIVITY_CSV = TABLES_DIR / "phase5_connectivity_impact_summary.csv"
ENTROPY_CSV = TABLES_DIR / "phase5_entropy_order_correlation.csv"
REDUNDANCY_CSV = TABLES_DIR / "phase5_edge_redundancy_summary.csv"

FIG1 = FIGURES_DIR / "figure1_phase5_fragility_curve.png"
FIG2 = FIGURES_DIR / "figure2_phase5_connectivity_impact.png"
FIG3 = FIGURES_DIR / "figure3_phase5_entropy_order_coupling.png"
FIG4 = FIGURES_DIR / "figure4_phase5_edge_redundancy_response.png"
MANIFEST_MD = FIGURES_DIR / "phase5_publication_figures_manifest.md"

EXPECTED_TOPOLOGIES = ["chain6", "random6", "ring6"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def save_manifest(text: str) -> None:
    MANIFEST_MD.write_text(text, encoding="utf-8")


def plot_fragility_curve(df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))

    for topology in EXPECTED_TOPOLOGIES:
        sub = df[df["topology"] == topology].sort_values("perturbation_order")
        if sub.empty:
            continue
        plt.plot(
            sub["perturbation_order"],
            sub["mean_delta_target_probability"],
            marker="o",
            label=topology,
        )

    plt.axhline(0.0, linewidth=1)
    plt.xlabel("Perturbation order")
    plt.ylabel("Mean Δ target probability")
    plt.title("Phase5 structural fragility curves")
    plt.xticks([1, 2, 3])
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG1, dpi=300, bbox_inches="tight")
    plt.close()


def plot_connectivity_impact(df: pd.DataFrame) -> None:
    plt.figure(figsize=(9, 5))

    x_positions = []
    y_values = []
    tick_labels = []

    xpos = 0
    for topology in EXPECTED_TOPOLOGIES:
        for k in [1, 2, 3]:
            sub = df[
                (df["topology"] == topology) &
                (df["perturbation_order"] == k)
            ].sort_values("connectivity_state")

            for _, row in sub.iterrows():
                x_positions.append(xpos)
                y_values.append(row["mean_delta_target_probability"])
                tick_labels.append(f"{topology}\nk={k}\n{row['connectivity_state']}")
                xpos += 1
        xpos += 1

    plt.bar(x_positions, y_values)
    plt.axhline(0.0, linewidth=1)
    plt.ylabel("Mean Δ target probability")
    plt.title("Phase5 connectivity impact comparison")
    plt.xticks(x_positions, tick_labels, rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(FIG2, dpi=300, bbox_inches="tight")
    plt.close()


def plot_entropy_order_coupling(df: pd.DataFrame) -> None:
    plt.figure(figsize=(7, 5))

    for topology in EXPECTED_TOPOLOGIES:
        sub = df[df["topology"] == topology]
        if sub.empty:
            continue
        plt.scatter(
            sub["mean_delta_entropy"],
            sub["mean_delta_target_probability"],
            label=topology,
            s=70,
        )

        for _, row in sub.iterrows():
            plt.annotate(
                f"k={int(row['perturbation_order'])}",
                (row["mean_delta_entropy"], row["mean_delta_target_probability"]),
                textcoords="offset points",
                xytext=(4, 4),
            )

    plt.axhline(0.0, linewidth=1)
    plt.axvline(0.0, linewidth=1)
    plt.xlabel("Mean Δ entropy")
    plt.ylabel("Mean Δ target probability")
    plt.title("Phase5 entropy-order coupling")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG3, dpi=300, bbox_inches="tight")
    plt.close()


def plot_edge_redundancy_response(df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))

    for topology in EXPECTED_TOPOLOGIES:
        sub = df[df["topology"] == topology].sort_values("remaining_edge_ratio")
        if sub.empty:
            continue

        plt.plot(
            sub["remaining_edge_ratio"],
            sub["mean_delta_target_probability"],
            marker="o",
            label=topology,
        )

    plt.axhline(0.0, linewidth=1)
    plt.xlabel("Remaining edge ratio")
    plt.ylabel("Mean Δ target probability")
    plt.title("Phase5 edge redundancy response")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG4, dpi=300, bbox_inches="tight")
    plt.close()


def build_manifest() -> str:
    lines = []
    lines.append("# Phase5 Publication Figures Manifest")
    lines.append("")
    lines.append("## Generated figures")
    lines.append("")
    lines.append(f"- {FIG1.name}: Structural fragility curves (perturbation order vs mean Δ target probability)")
    lines.append(f"- {FIG2.name}: Connectivity impact comparison (connected/disconnected response summary)")
    lines.append(f"- {FIG3.name}: Entropy-order coupling (mean Δ entropy vs mean Δ target probability)")
    lines.append(f"- {FIG4.name}: Edge redundancy response (remaining edge ratio vs mean Δ target probability)")
    lines.append("")
    lines.append("## Suggested interpretation")
    lines.append("")
    lines.append("- Figure 1 shows topology-specific structural response curves.")
    lines.append("- Figure 2 isolates connected vs disconnected response behavior.")
    lines.append("- Figure 3 shows entropy reduction coupled to target amplification.")
    lines.append("- Figure 4 shows response as a function of remaining structural redundancy.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ensure_dir(FIGURES_DIR)

    fragility_df = load_csv(FRAGILITY_CSV)
    connectivity_df = load_csv(CONNECTIVITY_CSV)
    redundancy_df = load_csv(REDUNDANCY_CSV)

    # Figure 3 uses fragility table because it has per-topology/per-order mean deltas
    plot_fragility_curve(fragility_df)
    plot_connectivity_impact(connectivity_df)
    plot_entropy_order_coupling(fragility_df)
    plot_edge_redundancy_response(redundancy_df)

    manifest_text = build_manifest()
    save_manifest(manifest_text)

    print("Phase5 publication figures generated successfully.")
    print("Generated files:")
    print(f"  - {FIG1}")
    print(f"  - {FIG2}")
    print(f"  - {FIG3}")
    print(f"  - {FIG4}")
    print(f"  - {MANIFEST_MD}")


if __name__ == "__main__":
    main()