# Phase5 Structural Metrics Summary

## Overview

- Derived from phase5_multi_ablation_edge_level_summary.csv
- Focus: connectivity impact, redundancy response, fragility curves, entropy-order coupling

## Connectivity Impact

### chain6

- k=1 | disconnected | n=5 | mean_delta_target=0.079102 | mean_delta_parity=0.099219 | mean_delta_entropy=-0.671155
- k=2 | disconnected | n=10 | mean_delta_target=0.125977 | mean_delta_parity=0.163770 | mean_delta_entropy=-1.261653
- k=3 | disconnected | n=10 | mean_delta_target=0.214673 | mean_delta_parity=0.119775 | mean_delta_entropy=-1.780669

### random6

- k=1 | connected | n=4 | mean_delta_target=0.039246 | mean_delta_parity=0.047729 | mean_delta_entropy=-0.277419
- k=1 | disconnected | n=2 | mean_delta_target=-0.014526 | mean_delta_parity=0.026855 | mean_delta_entropy=-0.703345
- k=2 | disconnected | n=15 | mean_delta_target=0.059066 | mean_delta_parity=0.075911 | mean_delta_entropy=-0.820552
- k=3 | disconnected | n=20 | mean_delta_target=0.086487 | mean_delta_parity=0.120239 | mean_delta_entropy=-1.265469

### ring6

- k=1 | connected | n=6 | mean_delta_target=-0.026001 | mean_delta_parity=-0.023193 | mean_delta_entropy=-0.066196
- k=2 | disconnected | n=15 | mean_delta_target=0.006999 | mean_delta_parity=-0.000456 | mean_delta_entropy=-0.532441
- k=3 | disconnected | n=20 | mean_delta_target=0.036719 | mean_delta_parity=0.049512 | mean_delta_entropy=-1.055595

## Structural Fragility Curves

### chain6

- k=1 | mean_delta_target=0.079102 | mean_delta_parity=0.099219 | mean_delta_entropy=-0.671155 | connected_fraction=0.000 | remaining_edge_ratio=0.800
- k=2 | mean_delta_target=0.125977 | mean_delta_parity=0.163770 | mean_delta_entropy=-1.261653 | connected_fraction=0.000 | remaining_edge_ratio=0.600
- k=3 | mean_delta_target=0.214673 | mean_delta_parity=0.119775 | mean_delta_entropy=-1.780669 | connected_fraction=0.000 | remaining_edge_ratio=0.400

### random6

- k=1 | mean_delta_target=0.021322 | mean_delta_parity=0.040771 | mean_delta_entropy=-0.419394 | connected_fraction=0.667 | remaining_edge_ratio=0.833
- k=2 | mean_delta_target=0.059066 | mean_delta_parity=0.075911 | mean_delta_entropy=-0.820552 | connected_fraction=0.000 | remaining_edge_ratio=0.667
- k=3 | mean_delta_target=0.086487 | mean_delta_parity=0.120239 | mean_delta_entropy=-1.265469 | connected_fraction=0.000 | remaining_edge_ratio=0.500

### ring6

- k=1 | mean_delta_target=-0.026001 | mean_delta_parity=-0.023193 | mean_delta_entropy=-0.066196 | connected_fraction=1.000 | remaining_edge_ratio=0.833
- k=2 | mean_delta_target=0.006999 | mean_delta_parity=-0.000456 | mean_delta_entropy=-0.532441 | connected_fraction=0.000 | remaining_edge_ratio=0.667
- k=3 | mean_delta_target=0.036719 | mean_delta_parity=0.049512 | mean_delta_entropy=-1.055595 | connected_fraction=0.000 | remaining_edge_ratio=0.500

## Entropy / Order Coupling

- chain6 | corr(target, entropy)=-0.873764 | corr(parity, entropy)=-0.615139 | corr(target, remaining_ratio)=-0.369537
- random6 | corr(target, entropy)=-0.670878 | corr(parity, entropy)=-0.739755 | corr(target, remaining_ratio)=-0.298925
- ring6 | corr(target, entropy)=-0.467513 | corr(parity, entropy)=-0.628274 | corr(target, remaining_ratio)=-0.350594

## Output Files

- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_connectivity_impact_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_edge_redundancy_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_structural_fragility_curve.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_entropy_order_correlation.csv
- E:\SRFM_QUANTUM_PHASE5\results\summary\phase5_structural_metrics_summary.md
