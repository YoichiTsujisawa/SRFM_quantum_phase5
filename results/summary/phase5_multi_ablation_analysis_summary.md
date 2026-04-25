# Phase5 Multi-Ablation Analysis Summary

## Overview

- Parent baseline records: 3
- Multi-ablation records: 107
- Topologies: chain6, random6, ring6
- Perturbation orders: 1, 2, 3

## Parent Baseline Reference

- chain6 | parent=phase5_chain6_predictive_parent | abs_parity=0.011230 | target_probability=0.030029 | entropy_bits=5.576555
- random6 | parent=phase5_random6_predictive_parent | abs_parity=0.022949 | target_probability=0.031738 | entropy_bits=5.703712
- ring6 | parent=phase5_ring6_predictive_parent | abs_parity=0.083984 | target_probability=0.044678 | entropy_bits=5.724978

## Perturbation-Order Response Summary

### chain6

- k=1 | mean_delta_abs_parity=0.099219 | mean_delta_target_probability=0.079102 | mean_delta_entropy=-0.671155 | connected_fraction=0.000
- k=2 | mean_delta_abs_parity=0.163770 | mean_delta_target_probability=0.125977 | mean_delta_entropy=-1.261653 | connected_fraction=0.000
- k=3 | mean_delta_abs_parity=0.119775 | mean_delta_target_probability=0.214673 | mean_delta_entropy=-1.780669 | connected_fraction=0.000

### random6

- k=1 | mean_delta_abs_parity=0.040771 | mean_delta_target_probability=0.021322 | mean_delta_entropy=-0.419394 | connected_fraction=0.667
- k=2 | mean_delta_abs_parity=0.075911 | mean_delta_target_probability=0.059066 | mean_delta_entropy=-0.820552 | connected_fraction=0.000
- k=3 | mean_delta_abs_parity=0.120239 | mean_delta_target_probability=0.086487 | mean_delta_entropy=-1.265469 | connected_fraction=0.000

### ring6

- k=1 | mean_delta_abs_parity=-0.023193 | mean_delta_target_probability=-0.026001 | mean_delta_entropy=-0.066196 | connected_fraction=1.000
- k=2 | mean_delta_abs_parity=-0.000456 | mean_delta_target_probability=0.006999 | mean_delta_entropy=-0.532441 | connected_fraction=0.000
- k=3 | mean_delta_abs_parity=0.049512 | mean_delta_target_probability=0.036719 | mean_delta_entropy=-1.055595 | connected_fraction=0.000

## Topology-Level Interpretation

- chain6 | observed_response_class=intermediate_mixed_response | best_order_by_target=3 | best_mean_delta_target_probability=0.214673 | worst_order_by_target=1 | worst_mean_delta_target_probability=0.079102
- random6 | observed_response_class=intermediate_mixed_response | best_order_by_target=3 | best_mean_delta_target_probability=0.086487 | worst_order_by_target=1 | worst_mean_delta_target_probability=0.021322
- ring6 | observed_response_class=intermediate_mixed_response | best_order_by_target=3 | best_mean_delta_target_probability=0.036719 | worst_order_by_target=1 | worst_mean_delta_target_probability=-0.026001

## Prediction vs Observation

- chain6 | predicted=adaptive_improvement_then_collapse | observed=intermediate_mixed_response | evaluation=partial_match
- random6 | predicted=intermediate_mixed_response | observed=intermediate_mixed_response | evaluation=match
- ring6 | predicted=formation_dominated_gradual_degradation | observed=intermediate_mixed_response | evaluation=partial_match

## Output Files

- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_multi_ablation_edge_level_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_multi_ablation_order_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_multi_ablation_topology_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_prediction_vs_observation_summary.csv
- E:\SRFM_QUANTUM_PHASE5\results\summary\phase5_multi_ablation_analysis_summary.md
