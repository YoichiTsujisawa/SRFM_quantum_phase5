from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


# ============================================================
# Phase5 Predictive Structural Response Multi-Ablation Analysis
# ------------------------------------------------------------
# Purpose:
#   - Read Phase5 parent baseline raw results
#   - Read Phase5 multi-ablation raw results
#   - Build edge-level summary table
#   - Build perturbation-order summary table
#   - Build topology-level response summary table
#   - Build prediction-vs-observation summary table
#   - Write markdown analysis summary
#
# Output files:
#   data/tables/phase5_multi_ablation_edge_level_summary.csv
#   data/tables/phase5_multi_ablation_order_summary.csv
#   data/tables/phase5_multi_ablation_topology_summary.csv
#   data/tables/phase5_prediction_vs_observation_summary.csv
#   results/summary/phase5_multi_ablation_analysis_summary.md
# ============================================================

REPO_ROOT = Path(r"E:\SRFM_QUANTUM_PHASE5")

BASELINE_RAW_DIR = REPO_ROOT / "results" / "raw"
MULTI_RAW_DIR = REPO_ROOT / "results" / "raw"

TABLES_DIR = REPO_ROOT / "data" / "tables"
SUMMARY_DIR = REPO_ROOT / "results" / "summary"

EDGE_LEVEL_CSV = TABLES_DIR / "phase5_multi_ablation_edge_level_summary.csv"
ORDER_SUMMARY_CSV = TABLES_DIR / "phase5_multi_ablation_order_summary.csv"
TOPOLOGY_SUMMARY_CSV = TABLES_DIR / "phase5_multi_ablation_topology_summary.csv"
PREDICTION_SUMMARY_CSV = TABLES_DIR / "phase5_prediction_vs_observation_summary.csv"
ANALYSIS_SUMMARY_MD = SUMMARY_DIR / "phase5_multi_ablation_analysis_summary.md"

EXPECTED_TOPOLOGIES = ["chain6", "random6", "ring6"]
EXPECTED_BASELINE_COUNT = 3
EXPECTED_MULTI_COUNT = 107


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def safe_get_summary_metric(payload: Dict[str, Any], key: str) -> float:
    return float(payload.get("summary", {}).get(key, 0.0))


def load_phase5_baseline_payloads() -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []

    for topology in EXPECTED_TOPOLOGIES:
        baseline_dir = BASELINE_RAW_DIR / topology / "baseline"
        if not baseline_dir.exists():
            raise FileNotFoundError(f"Missing baseline directory: {baseline_dir}")

        files = sorted(baseline_dir.glob("phase5_*__*.json"))
        for path in files:
            payload = read_json(path)
            if payload.get("phase") != "Phase5":
                continue
            if payload.get("run_type") != "baseline":
                continue
            payload["_source_path"] = str(path)
            payloads.append(payload)

    if len(payloads) != EXPECTED_BASELINE_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_BASELINE_COUNT} Phase5 baseline payloads, found {len(payloads)}"
        )

    return payloads


def load_phase5_multi_ablation_payloads() -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []

    for topology in EXPECTED_TOPOLOGIES:
        multi_dir = MULTI_RAW_DIR / topology / "multi_ablation"
        if not multi_dir.exists():
            raise FileNotFoundError(f"Missing multi_ablation directory: {multi_dir}")

        files = sorted(multi_dir.glob("phase5_*__*.json"))
        for path in files:
            payload = read_json(path)
            if payload.get("phase") != "Phase5":
                continue
            if payload.get("run_type") != "multi_ablation":
                continue
            payload["_source_path"] = str(path)
            payloads.append(payload)

    if len(payloads) != EXPECTED_MULTI_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_MULTI_COUNT} Phase5 multi-ablation payloads, found {len(payloads)}"
        )

    return payloads


def build_baseline_lookup(baseline_payloads: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    for payload in baseline_payloads:
        circuit_id = payload["circuit_id"]
        topology = payload["topology"]

        if circuit_id in lookup:
            raise ValueError(f"Duplicate baseline circuit_id found: {circuit_id}")

        lookup[circuit_id] = {
            "topology": topology,
            "abs_parity": safe_get_summary_metric(payload, "abs_parity"),
            "target_probability": safe_get_summary_metric(payload, "target_probability"),
            "entropy_bits": safe_get_summary_metric(payload, "entropy_bits"),
            "top_probability": safe_get_summary_metric(payload, "top_probability"),
            "top_state": payload.get("summary", {}).get("top_state"),
            "n_observed_states": int(payload.get("summary", {}).get("n_observed_states", 0)),
            "source_path": payload.get("_source_path"),
        }

    return lookup


def build_edge_level_rows(
    multi_payloads: List[Dict[str, Any]],
    baseline_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for payload in multi_payloads:
        parent_circuit_id = payload["parent_circuit_id"]

        if parent_circuit_id not in baseline_lookup:
            raise KeyError(
                f"Missing baseline reference for parent_circuit_id={parent_circuit_id}"
            )

        baseline = baseline_lookup[parent_circuit_id]
        summary = payload["summary"]
        ablation = payload["ablation"]
        derived = payload.get("derived_topology_state", {})

        abs_parity = float(summary.get("abs_parity", 0.0))
        target_probability = float(summary.get("target_probability", 0.0))
        entropy_bits = float(summary.get("entropy_bits", 0.0))
        top_probability = float(summary.get("top_probability", 0.0))

        baseline_abs_parity = float(baseline["abs_parity"])
        baseline_target_probability = float(baseline["target_probability"])
        baseline_entropy_bits = float(baseline["entropy_bits"])
        baseline_top_probability = float(baseline["top_probability"])

        row = {
            "phase": payload["phase"],
            "study_title": payload.get("study_title"),
            "topology": payload["topology"],
            "topology_class": payload.get("topology_class"),
            "phase_role": payload.get("phase_role"),
            "phase5_role": payload.get("phase5_role"),
            "predicted_response_class": payload.get("predicted_response_class"),
            "circuit_id": payload["circuit_id"],
            "parent_circuit_id": parent_circuit_id,
            "perturbation_order": int(ablation["perturbation_order"]),
            "dropped_edges": ",".join(ablation["dropped_edges"]),
            "dropped_edge_count": len(ablation["dropped_edges"]),
            "dropped_edge_qubits": json.dumps(ablation["dropped_edge_qubits"], ensure_ascii=False),
            "abs_parity": abs_parity,
            "target_probability": target_probability,
            "entropy_bits": entropy_bits,
            "top_probability": top_probability,
            "top_state": summary.get("top_state"),
            "n_observed_states": int(summary.get("n_observed_states", 0)),
            "baseline_abs_parity": baseline_abs_parity,
            "baseline_target_probability": baseline_target_probability,
            "baseline_entropy_bits": baseline_entropy_bits,
            "baseline_top_probability": baseline_top_probability,
            "delta_abs_parity": abs_parity - baseline_abs_parity,
            "delta_target_probability": target_probability - baseline_target_probability,
            "delta_entropy": entropy_bits - baseline_entropy_bits,
            "delta_top_probability": top_probability - baseline_top_probability,
            "is_connected_after_ablation": bool(derived.get("is_connected_after_ablation", False)),
            "n_components_after_ablation": int(derived.get("n_components_after_ablation", 0)),
            "has_loop_after_ablation": bool(derived.get("has_loop_after_ablation", False)),
            "remaining_edge_count": int(derived.get("remaining_edge_count", 0)),
            "dropped_edge_count_check": int(derived.get("dropped_edge_count", 0)),
            "source_path": payload.get("_source_path"),
        }
        rows.append(row)

    return rows


def classify_observed_response(topology_df: pd.DataFrame) -> str:
    """
    Heuristic Phase5 response-class classifier based on order summary trends.
    Uses mean_delta_target_probability / mean_delta_abs_parity / mean_delta_entropy.
    """

    ordered = topology_df.sort_values("perturbation_order").reset_index(drop=True)

    if ordered.empty:
        return "insufficient_data"

    dt = ordered["mean_delta_target_probability"].tolist()
    dp = ordered["mean_delta_abs_parity"].tolist()
    de = ordered["mean_delta_entropy"].tolist()

    # Improvement then collapse:
    # some early positive improvement in target or parity, then later deterioration
    if len(dt) >= 3:
        early_improvement = (dt[0] > 0.0) or (dp[0] > 0.0)
        mid_or_early_peak = max(dt[:2]) > 0.0 or max(dp[:2]) > 0.0
        late_degradation = (dt[-1] < min(dt[:2])) or (dp[-1] < min(dp[:2]))
        if early_improvement and mid_or_early_peak and late_degradation:
            return "adaptive_improvement_then_collapse"

    # Gradual degradation:
    # target/parity stay non-positive and tend to worsen with order
    if len(dt) >= 3:
        monotoneish_target = dt[0] >= dt[1] >= dt[2] or (dt[2] < 0.0 and dt[1] < 0.0)
        monotoneish_parity = dp[0] >= dp[1] >= dp[2] or (dp[2] < 0.0 and dp[1] < 0.0)
        if max(dt) <= 0.0 and max(dp) <= 0.0 and (monotoneish_target or monotoneish_parity):
            return "formation_dominated_gradual_degradation"

    # Intermediate mixed:
    return "intermediate_mixed_response"


def compute_prediction_match(predicted: str, observed: str) -> str:
    if predicted == observed:
        return "match"

    if predicted == "intermediate_mixed_response" and observed == "intermediate_mixed_response":
        return "match"

    if predicted == "formation_dominated_gradual_degradation" and observed in {
        "formation_dominated_gradual_degradation",
        "intermediate_mixed_response",
    }:
        return "partial_match"

    if predicted == "adaptive_improvement_then_collapse" and observed in {
        "adaptive_improvement_then_collapse",
        "intermediate_mixed_response",
    }:
        return "partial_match"

    if predicted == "intermediate_mixed_response" and observed in {
        "formation_dominated_gradual_degradation",
        "adaptive_improvement_then_collapse",
    }:
        return "partial_match"

    return "mismatch"


def make_markdown_summary(
    baseline_payloads: List[Dict[str, Any]],
    edge_df: pd.DataFrame,
    order_df: pd.DataFrame,
    topology_df: pd.DataFrame,
    prediction_df: pd.DataFrame,
) -> str:
    lines: List[str] = []

    lines.append("# Phase5 Multi-Ablation Analysis Summary")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Parent baseline records: {len(baseline_payloads)}")
    lines.append(f"- Multi-ablation records: {len(edge_df)}")
    lines.append(f"- Topologies: {', '.join(sorted(edge_df['topology'].unique()))}")
    lines.append(f"- Perturbation orders: {', '.join(str(x) for x in sorted(edge_df['perturbation_order'].unique()))}")
    lines.append("")

    lines.append("## Parent Baseline Reference")
    lines.append("")
    for payload in sorted(baseline_payloads, key=lambda x: x["topology"]):
        s = payload["summary"]
        lines.append(
            f"- {payload['topology']} | parent={payload['circuit_id']} | "
            f"abs_parity={float(s.get('abs_parity', 0.0)):.6f} | "
            f"target_probability={float(s.get('target_probability', 0.0)):.6f} | "
            f"entropy_bits={float(s.get('entropy_bits', 0.0)):.6f}"
        )
    lines.append("")

    lines.append("## Perturbation-Order Response Summary")
    lines.append("")
    for topology in EXPECTED_TOPOLOGIES:
        sub = order_df[order_df["topology"] == topology].sort_values("perturbation_order")
        if sub.empty:
            continue
        lines.append(f"### {topology}")
        lines.append("")
        for _, row in sub.iterrows():
            lines.append(
                f"- k={int(row['perturbation_order'])} | "
                f"mean_delta_abs_parity={row['mean_delta_abs_parity']:.6f} | "
                f"mean_delta_target_probability={row['mean_delta_target_probability']:.6f} | "
                f"mean_delta_entropy={row['mean_delta_entropy']:.6f} | "
                f"connected_fraction={row['connected_fraction']:.3f}"
            )
        lines.append("")

    lines.append("## Topology-Level Interpretation")
    lines.append("")
    for _, row in topology_df.sort_values("topology").iterrows():
        lines.append(
            f"- {row['topology']} | "
            f"observed_response_class={row['observed_response_class']} | "
            f"best_order_by_target={int(row['best_order_by_target'])} | "
            f"best_mean_delta_target_probability={row['best_mean_delta_target_probability']:.6f} | "
            f"worst_order_by_target={int(row['worst_order_by_target'])} | "
            f"worst_mean_delta_target_probability={row['worst_mean_delta_target_probability']:.6f}"
        )
    lines.append("")

    lines.append("## Prediction vs Observation")
    lines.append("")
    for _, row in prediction_df.sort_values("topology").iterrows():
        lines.append(
            f"- {row['topology']} | "
            f"predicted={row['predicted_response_class']} | "
            f"observed={row['observed_response_class']} | "
            f"evaluation={row['prediction_match']}"
        )
    lines.append("")

    lines.append("## Output Files")
    lines.append("")
    lines.append(f"- {EDGE_LEVEL_CSV}")
    lines.append(f"- {ORDER_SUMMARY_CSV}")
    lines.append(f"- {TOPOLOGY_SUMMARY_CSV}")
    lines.append(f"- {PREDICTION_SUMMARY_CSV}")
    lines.append(f"- {ANALYSIS_SUMMARY_MD}")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    ensure_dir(TABLES_DIR)
    ensure_dir(SUMMARY_DIR)

    baseline_payloads = load_phase5_baseline_payloads()
    multi_payloads = load_phase5_multi_ablation_payloads()

    baseline_lookup = build_baseline_lookup(baseline_payloads)
    edge_rows = build_edge_level_rows(multi_payloads, baseline_lookup)

    edge_df = pd.DataFrame(edge_rows)
    if edge_df.empty:
        raise ValueError("Edge-level dataframe is empty.")

    edge_df = edge_df.sort_values(
        by=["topology", "perturbation_order", "dropped_edges"]
    ).reset_index(drop=True)

    # 1) Edge-level summary
    edge_df.to_csv(EDGE_LEVEL_CSV, index=False, encoding="utf-8-sig")

    # 2) Perturbation-order summary
    order_df = (
        edge_df.groupby(["topology", "predicted_response_class", "perturbation_order"], as_index=False)
        .agg(
            n_records=("circuit_id", "count"),
            mean_abs_parity=("abs_parity", "mean"),
            mean_target_probability=("target_probability", "mean"),
            mean_entropy=("entropy_bits", "mean"),
            mean_delta_abs_parity=("delta_abs_parity", "mean"),
            mean_delta_target_probability=("delta_target_probability", "mean"),
            mean_delta_entropy=("delta_entropy", "mean"),
            mean_top_probability=("top_probability", "mean"),
            mean_delta_top_probability=("delta_top_probability", "mean"),
            connected_fraction=("is_connected_after_ablation", "mean"),
            loop_fraction=("has_loop_after_ablation", "mean"),
            mean_n_components=("n_components_after_ablation", "mean"),
            mean_remaining_edge_count=("remaining_edge_count", "mean"),
        )
    )

    order_df = order_df.sort_values(
        by=["topology", "perturbation_order"]
    ).reset_index(drop=True)
    order_df.to_csv(ORDER_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    # 3) Topology-level summary
    topology_rows: List[Dict[str, Any]] = []
    for topology in EXPECTED_TOPOLOGIES:
        sub = order_df[order_df["topology"] == topology].sort_values("perturbation_order")
        if sub.empty:
            continue

        observed_class = classify_observed_response(sub)

        best_target_row = sub.loc[sub["mean_delta_target_probability"].idxmax()]
        worst_target_row = sub.loc[sub["mean_delta_target_probability"].idxmin()]
        best_parity_row = sub.loc[sub["mean_delta_abs_parity"].idxmax()]
        worst_parity_row = sub.loc[sub["mean_delta_abs_parity"].idxmin()]

        topology_rows.append(
            {
                "topology": topology,
                "predicted_response_class": sub["predicted_response_class"].iloc[0],
                "observed_response_class": observed_class,
                "best_order_by_target": int(best_target_row["perturbation_order"]),
                "best_mean_delta_target_probability": float(best_target_row["mean_delta_target_probability"]),
                "worst_order_by_target": int(worst_target_row["perturbation_order"]),
                "worst_mean_delta_target_probability": float(worst_target_row["mean_delta_target_probability"]),
                "best_order_by_parity": int(best_parity_row["perturbation_order"]),
                "best_mean_delta_abs_parity": float(best_parity_row["mean_delta_abs_parity"]),
                "worst_order_by_parity": int(worst_parity_row["perturbation_order"]),
                "worst_mean_delta_abs_parity": float(worst_parity_row["mean_delta_abs_parity"]),
                "k1_mean_delta_target_probability": float(sub[sub["perturbation_order"] == 1]["mean_delta_target_probability"].iloc[0]) if (sub["perturbation_order"] == 1).any() else None,
                "k2_mean_delta_target_probability": float(sub[sub["perturbation_order"] == 2]["mean_delta_target_probability"].iloc[0]) if (sub["perturbation_order"] == 2).any() else None,
                "k3_mean_delta_target_probability": float(sub[sub["perturbation_order"] == 3]["mean_delta_target_probability"].iloc[0]) if (sub["perturbation_order"] == 3).any() else None,
                "k1_mean_delta_abs_parity": float(sub[sub["perturbation_order"] == 1]["mean_delta_abs_parity"].iloc[0]) if (sub["perturbation_order"] == 1).any() else None,
                "k2_mean_delta_abs_parity": float(sub[sub["perturbation_order"] == 2]["mean_delta_abs_parity"].iloc[0]) if (sub["perturbation_order"] == 2).any() else None,
                "k3_mean_delta_abs_parity": float(sub[sub["perturbation_order"] == 3]["mean_delta_abs_parity"].iloc[0]) if (sub["perturbation_order"] == 3).any() else None,
                "k1_connected_fraction": float(sub[sub["perturbation_order"] == 1]["connected_fraction"].iloc[0]) if (sub["perturbation_order"] == 1).any() else None,
                "k2_connected_fraction": float(sub[sub["perturbation_order"] == 2]["connected_fraction"].iloc[0]) if (sub["perturbation_order"] == 2).any() else None,
                "k3_connected_fraction": float(sub[sub["perturbation_order"] == 3]["connected_fraction"].iloc[0]) if (sub["perturbation_order"] == 3).any() else None,
            }
        )

    topology_df = pd.DataFrame(topology_rows).sort_values("topology").reset_index(drop=True)
    topology_df.to_csv(TOPOLOGY_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    # 4) Prediction-vs-observation summary
    prediction_df = topology_df.copy()
    prediction_df["prediction_match"] = prediction_df.apply(
        lambda row: compute_prediction_match(
            str(row["predicted_response_class"]),
            str(row["observed_response_class"]),
        ),
        axis=1,
    )
    prediction_df = prediction_df[
        [
            "topology",
            "predicted_response_class",
            "observed_response_class",
            "prediction_match",
            "best_order_by_target",
            "best_mean_delta_target_probability",
            "worst_order_by_target",
            "worst_mean_delta_target_probability",
            "best_order_by_parity",
            "best_mean_delta_abs_parity",
            "worst_order_by_parity",
            "worst_mean_delta_abs_parity",
        ]
    ]
    prediction_df.to_csv(PREDICTION_SUMMARY_CSV, index=False, encoding="utf-8-sig")

    # 5) Markdown summary
    summary_text = make_markdown_summary(
        baseline_payloads=baseline_payloads,
        edge_df=edge_df,
        order_df=order_df,
        topology_df=topology_df,
        prediction_df=prediction_df,
    )
    write_text(ANALYSIS_SUMMARY_MD, summary_text)

    print("Phase5 multi-ablation analysis completed.")
    print(f"Baseline payloads : {len(baseline_payloads)}")
    print(f"Multi payloads    : {len(multi_payloads)}")
    print("Generated files:")
    print(f"  - {EDGE_LEVEL_CSV}")
    print(f"  - {ORDER_SUMMARY_CSV}")
    print(f"  - {TOPOLOGY_SUMMARY_CSV}")
    print(f"  - {PREDICTION_SUMMARY_CSV}")
    print(f"  - {ANALYSIS_SUMMARY_MD}")


if __name__ == "__main__":
    main()