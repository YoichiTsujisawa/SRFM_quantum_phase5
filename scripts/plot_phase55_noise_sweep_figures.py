from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

TABLES_DIR = REPO_ROOT / "data" / "tables"
FIG_DIR = REPO_ROOT / "figures" / "paper"
FIG_DIR.mkdir(parents=True, exist_ok=True)

DELTA_CSV = TABLES_DIR / "phase55_noise_sweep_delta_summary.csv"
DIVERGENCE_CSV = TABLES_DIR / "phase55_parity_divergence_summary.csv"
CLASS_CSV = TABLES_DIR / "phase55_noise_response_classification.csv"

FIG1 = FIG_DIR / "figure1_phase55_noise_vs_delta_parity.png"
FIG2 = FIG_DIR / "figure2_phase55_noise_vs_delta_target.png"
FIG3 = FIG_DIR / "figure3_phase55_chain_ring_parity_divergence.png"
FIG4 = FIG_DIR / "figure4_phase55_noise_response_phase_map.png"
MANIFEST = FIG_DIR / "phase55_publication_figures_manifest.md"

TOPOLOGIES = ["chain6", "ring6"]


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    return pd.read_csv(path)


def plot_noise_vs_delta_parity(delta_df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))

    for topology in TOPOLOGIES:
        sub = delta_df[delta_df["topology"] == topology].sort_values("noise_scale")
        plt.plot(
            sub["noise_scale"],
            sub["delta_abs_parity"],
            marker="o",
            label=topology,
        )

    plt.axhline(0.0, linewidth=1, linestyle="--")
    plt.xlabel("Noise scale")
    plt.ylabel("Δ abs parity")
    plt.title("Phase5.5: Noise-dependent parity response")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG1, dpi=300, bbox_inches="tight")
    plt.close()


def plot_noise_vs_delta_target(delta_df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))

    for topology in TOPOLOGIES:
        sub = delta_df[delta_df["topology"] == topology].sort_values("noise_scale")
        plt.plot(
            sub["noise_scale"],
            sub["delta_target_probability"],
            marker="o",
            label=topology,
        )

    plt.axhline(0.0, linewidth=1, linestyle="--")
    plt.xlabel("Noise scale")
    plt.ylabel("Δ target probability")
    plt.title("Phase5.5: Noise-dependent target response")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG2, dpi=300, bbox_inches="tight")
    plt.close()


def plot_chain_ring_parity_divergence(div_df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))

    plt.plot(
        div_df["noise_scale"],
        div_df["chain_minus_ring_delta_abs_parity"],
        marker="o",
        label="chain6 - ring6 Δparity",
    )

    plt.axhline(0.0, linewidth=1, linestyle="--")
    plt.xlabel("Noise scale")
    plt.ylabel("Chain - Ring Δ abs parity")
    plt.title("Phase5.5: Persistent chain-ring parity divergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG3, dpi=300, bbox_inches="tight")
    plt.close()


def plot_noise_response_phase_map(delta_df: pd.DataFrame) -> None:
    plt.figure(figsize=(7, 5))

    for topology in TOPOLOGIES:
        sub = delta_df[delta_df["topology"] == topology].sort_values("noise_scale")
        plt.plot(
            sub["delta_target_probability"],
            sub["delta_abs_parity"],
            marker="o",
            label=topology,
        )

        for _, row in sub.iterrows():
            plt.annotate(
                f"{row['noise_scale']:.1f}",
                (row["delta_target_probability"], row["delta_abs_parity"]),
                textcoords="offset points",
                xytext=(4, 4),
            )

    plt.axhline(0.0, linewidth=1, linestyle="--")
    plt.axvline(0.0, linewidth=1, linestyle="--")
    plt.xlabel("Δ target probability")
    plt.ylabel("Δ abs parity")
    plt.title("Phase5.5: Noise response phase map")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG4, dpi=300, bbox_inches="tight")
    plt.close()


def write_manifest() -> None:
    lines = [
        "# Phase5.5 Publication Figures Manifest",
        "",
        "## Generated figures",
        "",
        f"- {FIG1.name}: Noise scale vs Δ abs parity for chain6 and ring6.",
        f"- {FIG2.name}: Noise scale vs Δ target probability for chain6 and ring6.",
        f"- {FIG3.name}: Chain-minus-ring parity divergence across noise scales.",
        f"- {FIG4.name}: Response phase map using Δtarget and Δparity.",
        "",
        "## Suggested interpretation",
        "",
        "- Figure 1 shows that chain6 maintains positive parity amplification, while ring6 remains parity-suppressive across the tested noise scales.",
        "- Figure 2 shows persistent target suppression in both topologies, with chain6 consistently less target-fragile than ring6.",
        "- Figure 3 shows that chain6 keeps a positive parity advantage over ring6 across all noise scales.",
        "- Figure 4 separates active chain-like order amplification from ring-like suppression in response space.",
        "",
    ]
    MANIFEST.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    delta_df = load_csv(DELTA_CSV)
    div_df = load_csv(DIVERGENCE_CSV)

    plot_noise_vs_delta_parity(delta_df)
    plot_noise_vs_delta_target(delta_df)
    plot_chain_ring_parity_divergence(div_df)
    plot_noise_response_phase_map(delta_df)
    write_manifest()

    print("Phase5.5 publication figures generated.")
    print(f"  - {FIG1}")
    print(f"  - {FIG2}")
    print(f"  - {FIG3}")
    print(f"  - {FIG4}")
    print(f"  - {MANIFEST}")


if __name__ == "__main__":
    main()