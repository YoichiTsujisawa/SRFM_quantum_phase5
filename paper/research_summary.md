# SRFM Quantum Protocol Phase 5  
## Predictive Structural Response and Noise-Dependent Chain–Ring Divergence

## Abstract

We present Phase 5 of the SRFM (Self-Regulating Field Model) Quantum Protocol, demonstrating predictive structural response behavior in quantum circuits and revealing topology-dependent divergence under noise.

Multi-edge ablation experiments confirm that SRFM can predict stability changes derived from prior structural observations (Phase 4). Hardware validation on IBM Quantum systems verifies that these predictions persist beyond simulation.

A noise sweep extension (Phase 5.5) reveals a key phenomenon: structural response diverges depending on topology, producing consistent parity amplification in chain structures and suppression in ring structures.

These results suggest that stability under noise is not uniform, but governed by topology-dependent pathways of perturbation redistribution.

---

## Introduction

Understanding how structured systems respond to perturbations is a fundamental problem across physics and complex systems.

We define the **Self-Regulating Field Model (SRFM)** as a framework describing how structured systems redistribute perturbations through their internal connectivity, resulting in emergent stabilization or destabilization patterns.

In this context, stability is not treated as static robustness, but as a **dynamic response governed by topology-dependent pathways of information flow**.

Previous phases established:
- Phase 4: topology-dependent structural behavior
- Phase 5: predictive structural response

This work extends these results by:
1. validating predictive behavior experimentally
2. introducing controlled noise to probe structural mechanisms

---

## Methods

### Circuit Design

- 6-qubit systems
- Topologies:
  - chain6
  - ring6
- Two-layer SRFM-inspired circuit construction
- Symmetric profile weights
- X-basis measurement

### Perturbation

- Single-edge removal (k = 1)
- Baseline vs perturbed comparison

### Noise Model

- Depolarizing noise (1-qubit and 2-qubit)
- Readout error
- Noise scaling:
  0.0 → 2.0

### Metrics

We define:

- Δtarget probability  
- Δabsolute parity  
- Δentropy  

Parity is defined as:

The global coherence metric derived from measurement outcomes, representing the balance between even and odd excitation configurations.

Positive parity shift indicates concentration of probability mass into coherent subspaces, while negative parity shift indicates dispersion or fragmentation of state distribution.

---

## Results

### Phase 5 — Predictive Structural Response

Observed behavior:

- chain6:
  maintains or improves structural coherence under perturbation
- ring6:
  degrades under equivalent perturbation

This matches predictions derived from Phase 4.

The observed responses match predictions derived from Phase 4, confirming that SRFM possesses predictive capability rather than merely descriptive power.

---

### Hardware Validation

Experiments on IBM Quantum hardware confirm:

- qualitative agreement with simulation
- preservation of structural response patterns

This validates that SRFM predictions extend beyond idealized simulation environments.

---

### Phase 5.5 — Noise Sweep

Noise scaling reveals:

- chain6:
  Δparity > 0 for all noise levels
- ring6:
  Δparity < 0 for all noise levels

This produces persistent divergence:

Δparity(chain) > Δparity(ring) for all tested noise scales

---

## Interpretation

We hypothesize that SRFM captures topology-dependent pathways of error redistribution.

Specifically:

- In chain-like structures, perturbations propagate along open pathways, enabling redistribution and reorganization of the system state.
- In ring-like structures, closed-loop connectivity traps perturbations, leading to accumulation and suppression of coherent restructuring.

This results in:

- chain topologies exhibiting positive parity shifts (adaptive stabilization)
- ring topologies exhibiting negative parity shifts (suppressed restructuring)

---

## Noise Interaction

Noise does not uniformly degrade system stability. Instead, it interacts with topology to selectively amplify or suppress structural responses.

This indicates that noise acts as a **discriminator of structural regimes rather than a purely destructive factor**.

---

## Phase Space Structure

In the response space (Δtarget, Δparity):

- chain6 occupies:
  (+parity, -target)
- ring6 occupies:
  (-parity, -target)

This defines distinct dynamical regimes:

- adaptive restructuring regime (chain)
- redundancy-buffered regime (ring)

---

## Conclusion

SRFM extends beyond robustness modeling.

It describes topology-dependent structural adaptation processes under perturbation and noise.

Key findings:

1. Structural response is predictable
2. Structural response persists under hardware execution
3. Structural response diverges under noise based on topology
4. Noise acts as a topology-dependent selector of system behavior

---

## Limitations

- fixed system size (n = 6)
- specific noise model
- specific circuit construction

---

## Future Work

- scaling behavior (n → larger systems)
- noise model generalization
- topology interpolation

---

## Author

Yoichi Tsujisawa