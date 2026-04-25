# Phase5 Hardware Validation Summary

## Overview

- Hardware records: 4
- Compared topologies: chain6, ring6
- Backend: ibm_fez
- Validation result: **strong_success**

## Hardware Raw Metrics

- chain6 | baseline | target=0.033691 | parity=0.025391 | entropy=5.586058 | job_id=d7lp7atqrg3c738kd76g
- chain6 | k1 | target=0.025391 | parity=0.165039 | entropy=5.349046 | job_id=d7lp7cit99kc73d1m840
- ring6 | baseline | target=0.034424 | parity=0.024414 | entropy=5.868486 | job_id=d7lp7ebaq2pc73a0r870
- ring6 | k1 | target=0.019531 | parity=0.031738 | entropy=5.691192 | job_id=d7lp7fs3g2mc7391ki60

## Hardware Baseline-to-k1 Deltas

- chain6 | Δtarget=-0.008301 | Δparity=0.139648 | Δentropy=-0.237012
- ring6 | Δtarget=-0.014893 | Δparity=0.007324 | Δentropy=-0.177293

## Hardware vs Simulation Sign Comparison

- chain6 | edge=e2 | hardware Δtarget=-0.008301 (negative) | sim Δtarget=-0.006592 (negative) | target_sign_match=True | hardware Δparity=0.139648 (positive) | sim Δparity=0.255371 (positive) | parity_sign_match=True
- ring6 | edge=e0 | hardware Δtarget=-0.014893 (negative) | sim Δtarget=-0.022461 (negative) | target_sign_match=True | hardware Δparity=0.007324 (positive) | sim Δparity=-0.082520 (negative) | parity_sign_match=False

## Ranking Comparison

- Hardware chain-minus-ring Δtarget: 0.006592
- Simulation chain-minus-ring Δtarget: 0.015869
- Ranking match chain > ring: True

## Output Files

- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_hardware_validation_summary.csv
- E:\SRFM_QUANTUM_PHASE5\data\tables\phase5_hardware_vs_sim_comparison.csv
- E:\SRFM_QUANTUM_PHASE5\results\summary\phase5_hardware_validation_summary.md
