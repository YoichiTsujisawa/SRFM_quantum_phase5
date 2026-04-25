# Phase5.5 Noise Sweep Summary

## Overview

- Raw records: 20
- Topologies: chain6, ring6
- Noise scales: 0.0, 0.5, 1.0, 1.5, 2.0
- Target circuits: chain6 baseline/k1_e2 and ring6 baseline/k1_e0

## Delta Summary

### chain6

- noise=0.0 | Δtarget=-0.006348 (negative) | Δparity=0.366699 (positive) | Δentropy=-0.339885 (negative)
- noise=0.5 | Δtarget=-0.007080 (negative) | Δparity=0.314453 (positive) | Δentropy=-0.291177 (negative)
- noise=1.0 | Δtarget=-0.006592 (negative) | Δparity=0.255371 (positive) | Δentropy=-0.244803 (negative)
- noise=1.5 | Δtarget=-0.008057 (negative) | Δparity=0.191895 (positive) | Δentropy=-0.199681 (negative)
- noise=2.0 | Δtarget=-0.007812 (negative) | Δparity=0.139648 (positive) | Δentropy=-0.162779 (negative)

### ring6

- noise=0.0 | Δtarget=-0.033447 (negative) | Δparity=-0.113770 (negative) | Δentropy=-0.223195 (negative)
- noise=0.5 | Δtarget=-0.027832 (negative) | Δparity=-0.104980 (negative) | Δentropy=-0.218864 (negative)
- noise=1.0 | Δtarget=-0.022461 (negative) | Δparity=-0.082520 (negative) | Δentropy=-0.196421 (negative)
- noise=1.5 | Δtarget=-0.020264 (negative) | Δparity=-0.071777 (negative) | Δentropy=-0.156414 (negative)
- noise=2.0 | Δtarget=-0.016113 (negative) | Δparity=-0.031738 (negative) | Δentropy=-0.155446 (negative)

## Chain vs Ring Divergence

- noise=0.0 | chain-ring Δparity=0.480469 | chain-ring Δtarget=0.027100 | chain_parity_gt_ring=True | chain_target_gt_ring=True
- noise=0.5 | chain-ring Δparity=0.419434 | chain-ring Δtarget=0.020752 | chain_parity_gt_ring=True | chain_target_gt_ring=True
- noise=1.0 | chain-ring Δparity=0.337891 | chain-ring Δtarget=0.015869 | chain_parity_gt_ring=True | chain_target_gt_ring=True
- noise=1.5 | chain-ring Δparity=0.263672 | chain-ring Δtarget=0.012207 | chain_parity_gt_ring=True | chain_target_gt_ring=True
- noise=2.0 | chain-ring Δparity=0.171387 | chain-ring Δtarget=0.008301 | chain_parity_gt_ring=True | chain_target_gt_ring=True

## Response Classification

- chain6 | parity_regime=persistent_parity_amplification | target_regime=persistent_target_suppression | corr_noise_parity=-0.999452 | corr_noise_target=-0.829561
- ring6 | parity_regime=persistent_parity_suppression | target_regime=persistent_target_suppression | corr_noise_parity=0.966828 | corr_noise_target=0.988781
- chain_minus_ring | parity_regime=chain_parity_advantage_persistent | target_regime=chain_minus_ring_target_divergence | corr_noise_parity=-0.997849 | corr_noise_target=-0.993088

## Output Files

- E:\SRFM_QUANTUM_PHASE5\data\tables\phase55_noise_sweep_raw_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase55_noise_sweep_delta_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase55_parity_divergence_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase55_noise_response_classification.csv
- E:\SRFM_QUANTUM_PHASE5\results\summary\phase55_noise_sweep_summary.md
