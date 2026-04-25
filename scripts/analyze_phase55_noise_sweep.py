from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

RAW_ROOT = REPO_ROOT / "results" / "raw_phase55_noise_sweep"
TABLES_DIR = REPO_ROOT / "data" / "tables"
SUMMARY_DIR = REPO_ROOT / "results" / "summary"

RAW_SUMMARY_CSV = TABLES_DIR / "phase55_noise_sweep_raw_summary.csv"
DELTA_SUMMARY_CSV = TABLES_DIR / "phase55_noise_sweep_delta_summary.csv"
PARITY_DIVERGENCE_CSV = TABLES_DIR / "phase55_parity_divergence_summary.csv"
CLASSIFICATION_CSV = TABLES_DIR / "phase55_noise_response_classification.csv"
SUMMARY_MD = SUMMARY_DIR / "phase55_noise_sweep_summary.md"

EXPECTED_TOPOLOGIES = ["chain6", "ring6"]
EXPECTED_NOISE_SCALES = [0.0, 0.5, 1.0, 1.5, 2.0]


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


def load_raw_rows() -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for topology in EXPECTED_TOPOLOGIES:
        topo_dir = RAW_ROOT / topology
        if not topo_dir.exists():
            raise FileNotFoundError(f"Missing directory: {topo_dir}")

        for path in sorted(topo_dir.glob("*.json")):
            payload = read_json(path)
            summary = payload.get("summary", {})
            noise = payload.get("noise_model", {})

            rows.append(
                {
                    "phase": payload.get("phase"),
                    "topology": payload.get("topology"),
                    "kind": payload.get("kind"),
                    "circuit_id": payload.get("circuit_id"),
                    "parent_circuit_id": payload.get("parent_circuit_id"),
                    "noise_scale": float(payload.get("noise_scale")),
                    "shots": int(payload.get("shots", 0)),
                    "target_probability": float(summary.get("target_probability", 0.0)),
                    "abs_parity": float(summary.get("abs_parity", 0.0)),
                    "entropy_bits": float(summary.get("entropy_bits", 0.0)),
                    "top_probability": float(summary.get("top_probability", 0.0)),
                    "top_state": summary.get("top_state"),
                    "n_observed_states": int(summary.get("n_observed_states", 0)),
                    "scaled_p1": float(noise.get("scaled_single_qubit_depolarizing_p", 0.0)),
                    "scaled_p2": float(noise.get("scaled_two_qubit_depolarizing_p", 0.0)),
                    "scaled_readout_e01": float(noise.get("scaled_readout_e01", 0.0)),
                    "scaled_readout_e10": float(noise.get("scaled_readout_e10", 0.0)),
                    "source_path": str(path),
                }
            )

    df = pd.DataFrame(rows)

    expected_count = len(EXPECTED_TOPOLOGIES) * len(EXPECTED_NOISE_SCALES) * 2
    if len(df) != expected_count:
        raise ValueError(f"Expected {expected_count} rows, found {len(df)}")

    return df.sort_values(["topology", "noise_scale", "kind"]).reset_index(drop=True)


def build_delta_summary(raw_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for topology in EXPECTED_TOPOLOGIES:
        for noise_scale in EXPECTED_NOISE_SCALES:
            sub = raw_df[
                (raw_df["topology"] == topology)
                & (raw_df["noise_scale"] == noise_scale)
            ]

            baseline = sub[sub["kind"] == "baseline"]
            k1 = sub[sub["kind"] == "multi_ablation"]

            if len(baseline) != 1 or len(k1) != 1:
                raise ValueError(
                    f"Expected one baseline and one k1 for {topology}, noise={noise_scale}"
                )

            b = baseline.iloc[0]
            a = k1.iloc[0]

            delta_target = a["target_probability"] - b["target_probability"]
            delta_parity = a["abs_parity"] - b["abs_parity"]
            delta_entropy = a["entropy_bits"] - b["entropy_bits"]
            delta_top_probability = a["top_probability"] - b["top_probability"]

            rows.append(
                {
                    "topology": topology,
                    "noise_scale": noise_scale,
                    "baseline_circuit_id": b["circuit_id"],
                    "k1_circuit_id": a["circuit_id"],
                    "baseline_target_probability": b["target_probability"],
                    "k1_target_probability": a["target_probability"],
                    "delta_target_probability": delta_target,
                    "delta_target_sign": sign_label(delta_target),
                    "baseline_abs_parity": b["abs_parity"],
                    "k1_abs_parity": a["abs_parity"],
                    "delta_abs_parity": delta_parity,
                    "delta_parity_sign": sign_label(delta_parity),
                    "baseline_entropy_bits": b["entropy_bits"],
                    "k1_entropy_bits": a["entropy_bits"],
                    "delta_entropy": delta_entropy,
                    "delta_entropy_sign": sign_label(delta_entropy),
                    "baseline_top_probability": b["top_probability"],
                    "k1_top_probability": a["top_probability"],
                    "delta_top_probability": delta_top_probability,
                    "delta_top_probability_sign": sign_label(delta_top_probability),
                    "scaled_p1": b["scaled_p1"],
                    "scaled_p2": b["scaled_p2"],
                    "scaled_readout_e01": b["scaled_readout_e01"],
                    "scaled_readout_e10": b["scaled_readout_e10"],
                }
            )

    return pd.DataFrame(rows).sort_values(["topology", "noise_scale"]).reset_index(drop=True)


def build_parity_divergence_summary(delta_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for noise_scale in EXPECTED_NOISE_SCALES:
        chain = delta_df[
            (delta_df["topology"] == "chain6")
            & (delta_df["noise_scale"] == noise_scale)
        ].iloc[0]

        ring = delta_df[
            (delta_df["topology"] == "ring6")
            & (delta_df["noise_scale"] == noise_scale)
        ].iloc[0]

        parity_divergence = chain["delta_abs_parity"] - ring["delta_abs_parity"]
        target_divergence = chain["delta_target_probability"] - ring["delta_target_probability"]
        entropy_divergence = chain["delta_entropy"] - ring["delta_entropy"]

        rows.append(
            {
                "noise_scale": noise_scale,
                "chain_delta_abs_parity": chain["delta_abs_parity"],
                "ring_delta_abs_parity": ring["delta_abs_parity"],
                "chain_minus_ring_delta_abs_parity": parity_divergence,
                "parity_divergence_sign": sign_label(parity_divergence),
                "chain_delta_target_probability": chain["delta_target_probability"],
                "ring_delta_target_probability": ring["delta_target_probability"],
                "chain_minus_ring_delta_target_probability": target_divergence,
                "target_divergence_sign": sign_label(target_divergence),
                "chain_delta_entropy": chain["delta_entropy"],
                "ring_delta_entropy": ring["delta_entropy"],
                "chain_minus_ring_delta_entropy": entropy_divergence,
                "entropy_divergence_sign": sign_label(entropy_divergence),
                "chain_parity_gt_ring": bool(chain["delta_abs_parity"] > ring["delta_abs_parity"]),
                "chain_target_gt_ring": bool(chain["delta_target_probability"] > ring["delta_target_probability"]),
            }
        )

    return pd.DataFrame(rows).sort_values("noise_scale").reset_index(drop=True)


def classify_noise_response(delta_df: pd.DataFrame, divergence_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for topology in EXPECTED_TOPOLOGIES:
        sub = delta_df[delta_df["topology"] == topology].sort_values("noise_scale")

        corr_noise_parity = sub["noise_scale"].corr(sub["delta_abs_parity"])
        corr_noise_target = sub["noise_scale"].corr(sub["delta_target_probability"])
        corr_noise_entropy = sub["noise_scale"].corr(sub["delta_entropy"])

        parity_values = sub["delta_abs_parity"].tolist()
        target_values = sub["delta_target_probability"].tolist()

        if all(v > 0 for v in parity_values):
            parity_regime = "persistent_parity_amplification"
        elif all(v < 0 for v in parity_values):
            parity_regime = "persistent_parity_suppression"
        else:
            parity_regime = "mixed_parity_response"

        if all(v > 0 for v in target_values):
            target_regime = "persistent_target_amplification"
        elif all(v < 0 for v in target_values):
            target_regime = "persistent_target_suppression"
        else:
            target_regime = "mixed_target_response"

        rows.append(
            {
                "scope": topology,
                "n_noise_levels": len(sub),
                "corr_noise_vs_delta_abs_parity": corr_noise_parity,
                "corr_noise_vs_delta_target_probability": corr_noise_target,
                "corr_noise_vs_delta_entropy": corr_noise_entropy,
                "parity_response_regime": parity_regime,
                "target_response_regime": target_regime,
                "min_delta_abs_parity": min(parity_values),
                "max_delta_abs_parity": max(parity_values),
                "min_delta_target_probability": min(target_values),
                "max_delta_target_probability": max(target_values),
            }
        )

    div = divergence_df.sort_values("noise_scale")
    div_values = div["chain_minus_ring_delta_abs_parity"].tolist()

    if all(v > 0 for v in div_values):
        divergence_regime = "chain_parity_advantage_persistent"
    elif all(v < 0 for v in div_values):
        divergence_regime = "ring_parity_advantage_persistent"
    else:
        divergence_regime = "mixed_or_crossing_parity_divergence"

    rows.append(
        {
            "scope": "chain_minus_ring",
            "n_noise_levels": len(div),
            "corr_noise_vs_delta_abs_parity": div["noise_scale"].corr(
                div["chain_minus_ring_delta_abs_parity"]
            ),
            "corr_noise_vs_delta_target_probability": div["noise_scale"].corr(
                div["chain_minus_ring_delta_target_probability"]
            ),
            "corr_noise_vs_delta_entropy": div["noise_scale"].corr(
                div["chain_minus_ring_delta_entropy"]
            ),
            "parity_response_regime": divergence_regime,
            "target_response_regime": "chain_minus_ring_target_divergence",
            "min_delta_abs_parity": min(div_values),
            "max_delta_abs_parity": max(div_values),
            "min_delta_target_probability": div["chain_minus_ring_delta_target_probability"].min(),
            "max_delta_target_probability": div["chain_minus_ring_delta_target_probability"].max(),
        }
    )

    return pd.DataFrame(rows)


def make_markdown(
    raw_df: pd.DataFrame,
    delta_df: pd.DataFrame,
    divergence_df: pd.DataFrame,
    class_df: pd.DataFrame,
) -> str:
    lines: List[str] = []

    lines.append("# Phase5.5 Noise Sweep Summary")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Raw records: {len(raw_df)}")
    lines.append(f"- Topologies: {', '.join(EXPECTED_TOPOLOGIES)}")
    lines.append(f"- Noise scales: {', '.join(str(x) for x in EXPECTED_NOISE_SCALES)}")
    lines.append("- Target circuits: chain6 baseline/k1_e2 and ring6 baseline/k1_e0")
    lines.append("")

    lines.append("## Delta Summary")
    lines.append("")
    for topology in EXPECTED_TOPOLOGIES:
        lines.append(f"### {topology}")
        lines.append("")
        sub = delta_df[delta_df["topology"] == topology].sort_values("noise_scale")
        for _, row in sub.iterrows():
            lines.append(
                f"- noise={row['noise_scale']:.1f} | "
                f"Δtarget={row['delta_target_probability']:.6f} "
                f"({row['delta_target_sign']}) | "
                f"Δparity={row['delta_abs_parity']:.6f} "
                f"({row['delta_parity_sign']}) | "
                f"Δentropy={row['delta_entropy']:.6f} "
                f"({row['delta_entropy_sign']})"
            )
        lines.append("")

    lines.append("## Chain vs Ring Divergence")
    lines.append("")
    for _, row in divergence_df.iterrows():
        lines.append(
            f"- noise={row['noise_scale']:.1f} | "
            f"chain-ring Δparity={row['chain_minus_ring_delta_abs_parity']:.6f} | "
            f"chain-ring Δtarget={row['chain_minus_ring_delta_target_probability']:.6f} | "
            f"chain_parity_gt_ring={row['chain_parity_gt_ring']} | "
            f"chain_target_gt_ring={row['chain_target_gt_ring']}"
        )
    lines.append("")

    lines.append("## Response Classification")
    lines.append("")
    for _, row in class_df.iterrows():
        lines.append(
            f"- {row['scope']} | "
            f"parity_regime={row['parity_response_regime']} | "
            f"target_regime={row['target_response_regime']} | "
            f"corr_noise_parity={row['corr_noise_vs_delta_abs_parity']:.6f} | "
            f"corr_noise_target={row['corr_noise_vs_delta_target_probability']:.6f}"
        )
    lines.append("")

    lines.append("## Output Files")
    lines.append("")
    lines.append(f"- {RAW_SUMMARY_CSV}")
    lines.append(f"- {DELTA_SUMMARY_CSV}")
    lines.append(f"- {PARITY_DIVERGENCE_CSV}")
    lines.append(f"- {CLASSIFICATION_CSV}")
    lines.append(f"- {SUMMARY_MD}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    ensure_dir(TABLES_DIR)
    ensure_dir(SUMMARY_DIR)

    raw_df = load_raw_rows()
    delta_df = build_delta_summary(raw_df)
    divergence_df = build_parity_divergence_summary(delta_df)
    class_df = classify_noise_response(delta_df, divergence_df)

    raw_df.to_csv(RAW_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    delta_df.to_csv(DELTA_SUMMARY_CSV, index=False, encoding="utf-8-sig")
    divergence_df.to_csv(PARITY_DIVERGENCE_CSV, index=False, encoding="utf-8-sig")
    class_df.to_csv(CLASSIFICATION_CSV, index=False, encoding="utf-8-sig")

    md = make_markdown(raw_df, delta_df, divergence_df, class_df)
    SUMMARY_MD.write_text(md, encoding="utf-8")

    print("Phase5.5 noise sweep analysis completed.")
    print(f"Raw rows: {len(raw_df)}")
    print("Generated files:")
    print(f"  - {RAW_SUMMARY_CSV}")
    print(f"  - {DELTA_SUMMARY_CSV}")
    print(f"  - {PARITY_DIVERGENCE_CSV}")
    print(f"  - {CLASSIFICATION_CSV}")
    print(f"  - {SUMMARY_MD}")


if __name__ == "__main__":
    main()