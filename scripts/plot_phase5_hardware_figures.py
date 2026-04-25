from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

INPUT_COMPARISON = REPO_ROOT / "data" / "tables" / "phase5_hardware_vs_sim_comparison.csv"
INPUT_SUMMARY = REPO_ROOT / "data" / "tables" / "phase5_hardware_validation_summary.csv"

FIG_DIR = REPO_ROOT / "figures" / "paper"
FIG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Figure 1: Hardware vs Simulation Δ comparison
# ============================================================

def plot_delta_comparison():
    df = pd.read_csv(INPUT_COMPARISON)

    topologies = df["topology"].values

    x = np.arange(len(topologies))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(x - width/2, df["hardware_delta_target_probability"], width, label="Hardware Δtarget")
    ax.bar(x + width/2, df["sim_delta_target_probability"], width, label="Simulation Δtarget")

    ax.set_xticks(x)
    ax.set_xticklabels(topologies)
    ax.set_ylabel("Δ Target Probability")
    ax.set_title("Phase5: Hardware vs Simulation Δtarget")
    ax.legend()

    plt.tight_layout()
    plt.savefig(FIG_DIR / "figure1_phase5_delta_target_comparison.png", dpi=300)
    plt.close()


# ============================================================
# Figure 2: Baseline vs k=1
# ============================================================

def plot_baseline_vs_k1():
    df = pd.read_csv(INPUT_SUMMARY)

    fig, ax = plt.subplots(figsize=(8, 5))

    for topology in ["chain6", "ring6"]:
        sub = df[df["topology"] == topology]

        baseline = sub[sub["kind"] == "baseline"]["target_probability"].values[0]
        k1 = sub[sub["kind"] == "k1"]["target_probability"].values[0]

        ax.plot(["baseline", "k1"], [baseline, k1], marker="o", label=topology)

    ax.set_ylabel("Target Probability")
    ax.set_title("Phase5: Baseline vs k=1 (Hardware)")
    ax.legend()

    plt.tight_layout()
    plt.savefig(FIG_DIR / "figure2_phase5_baseline_vs_k1.png", dpi=300)
    plt.close()


# ============================================================
# Figure 3: Topology Δ comparison
# ============================================================

def plot_topology_delta():
    df = pd.read_csv(INPUT_COMPARISON)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(df["topology"], df["hardware_delta_target_probability"])

    ax.set_ylabel("Δ Target Probability")
    ax.set_title("Phase5: Topology Difference (Hardware)")

    plt.tight_layout()
    plt.savefig(FIG_DIR / "figure3_phase5_topology_delta.png", dpi=300)
    plt.close()


# ============================================================
# MAIN
# ============================================================

def main():
    plot_delta_comparison()
    plot_baseline_vs_k1()
    plot_topology_delta()

    print("Phase5 figure generation completed.")
    print(f"Saved to: {FIG_DIR}")


if __name__ == "__main__":
    main()