# SRFM Quantum Protocol Phase 5  
## Predictive Structural Response and Noise-Dependent Chain–Ring Divergence

---

## Overview

This repository contains Phase 5 of the SRFM (Self-Regulating Field Model) Quantum Protocol.

This release includes:

- Phase 5: Predictive structural response validation
- Phase 5.5: Noise-dependent structural response extension

The central research question is:

Can SRFM predict how structural perturbations affect stability?

---

## What is SRFM?

The Self-Regulating Field Model (SRFM) describes how structured systems redistribute perturbations through their internal connectivity.

In SRFM:

- Stability is not static robustness
- It is a dynamic response governed by topology-dependent pathways of information flow

---

## Phase Structure

### Phase 5 — Predictive Structural Response

- Multi-edge ablation experiments (k = 1)
- Predictions derived from Phase 4
- Validated using:
  - noisy simulation
  - IBM Quantum hardware (QASM 2.0)

Result:

- chain6 improves or maintains coherence
- ring6 degrades

---

### Phase 5.5 — Noise Sweep Extension

- Noise scaling: 0.0 → 2.0
- Same circuits evaluated under increasing noise

Result:

Topology-dependent divergence emerges

---

## Key Findings

### Persistent Parity Divergence

- chain6: Δparity > 0
- ring6: Δparity < 0

→ Structural response sign is topology-determined

---

### Predictive Capability

Predictions match observations.

→ SRFM is predictive, not only descriptive

---

### Noise-Dependent Behavior

- chain6:
  noise-assisted stabilization
- ring6:
  redundancy-buffered degradation

---

### Structural Role Separation

chain6 → adaptive restructuring  
ring6  → passive stabilization  

---

### Noise as Structural Selector

Noise interacts with topology to select response regimes.

---

## Physical Interpretation

We hypothesize that SRFM captures topology-dependent pathways of error redistribution.

- chain:
  open structure → propagation → restructuring

- ring:
  closed loop → trapping → suppression

---

## Metrics

- Δtarget probability
- Δabsolute parity
- Δentropy

### Parity Definition

Parity is a global coherence metric:

- positive Δparity → concentration into coherent states
- negative Δparity → dispersion

---

## Phase Space

- chain6 → (+parity, -target)
- ring6  → (-parity, -target)

→ distinct dynamical regimes

---

## Repository Structure

circuits/  
data/  
figures/  
results/  
scripts/  
paper/  

---

## Reproducibility

Environment:

Python 3.10+  
qiskit  
qiskit-aer  
qiskit-ibm-runtime  
numpy  
pandas  
matplotlib  

Execution:

generate → run → analyze → plot

---

## Significance

SRFM is:

- a predictive structural response model
- topology-sensitive
- noise-interactive

---

## Limitations

- fixed system size (n = 6)
- specific noise model
- fixed circuit structure

---

## Future Work (Phase 6)

- scaling (n > 6)
- noise generalization
- topology interpolation

---

## Author

Yoichi Tsujisawa

---

## License

MIT License

DOI: https://zenodo.org/records/19742766
