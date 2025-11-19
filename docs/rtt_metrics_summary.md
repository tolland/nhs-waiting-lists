# NHS RTT Metrics Summary

## 1. System Context

**Dataset:** NHS England *Consultant-led Referral to Treatment (RTT)* provider-level statistics

**Core tables:**
- `Incomplete` – patients still waiting for first treatment
- `Admitted` – completed via inpatient or day case
- `NonAdmitted` – completed via outpatient or administrative stop
- `Incomplete_with_decision_to_admit` (DTA) – subset of incomplete, awaiting admission
- `NewPeriods` – new referral clock starts

Each specialty within each provider behaves as a **population system**:

$[\text{Incomplete}_{t+1} = \text{Incomplete}_t + \text{NewPeriods}_{t+1} - (\text{Admitted}_{t+1} + \text{NonAdmitted}_{t+1})]$

If the data were fully consistent, this would balance exactly.

---

## 2. Key Empirical Findings

1. **Accounting imbalance (residual)**  
   $[\text{residual}_t = (\text{Incomplete}_{t-1} + \text{NewPeriods}_t - \text{Admitted}_t - \text{NonAdmitted}_t) - \text{Incomplete}_t]$
   → Large unexplained residuals (thousands of patients) indicate patients disappearing or appearing without matching inflows/outflows.

2. **Direction of imbalance**
   - Negative residuals → unrecorded removals (e.g. DNAs, nullifications)
   - Positive residuals → retroactive additions or delayed entry

3. **RAJ Cardiology (C_320) anomaly**  
   Inflows exceed outflows, yet total incomplete *falls*. Indicates **administrative removals** or nullified pathways.

4. **No consistent revisions**  
   Comparison between original and revised RTT files shows no numeric back-correction, implying deletions are not historically restated.

---

## 3. Derived Metrics

### a. Residual Balance
$[\text{residual}_t = (INC_{t-1} + NPP_t - AP_t - NAP_t) - INC_t]$
Main forensic signal. Nonzero values = untracked removals or additions.

### b. Residual Ratio
\[R_t = \frac{residual_t}{INC_{t-1} + NPP_t}\]
Normalised version for cross-specialty comparison.

### c. Flow Consistency Index (FCI)
\[FCI = 1 - \frac{std(residual)}{mean(NPP)}\]
Measures internal coherence: 1 = stable, 0 = chaotic flows.

### d. Completion-to-Inflow Ratio (CIR)
\[CIR_t = \frac{AP_t + NAP_t}{NPP_t}\]
Indicates whether backlogs should rise or fall.

### e. Backlog Elasticity
\[E_t = \frac{\Delta INC_t / INC_{t-1}}{CIR_t - 1}\]
Measures sensitivity of backlog to flow imbalance.

### f. Nullification Signature
\[Null_t = \sum_{\tau=1}^{t} \min(0, residual_\tau)\]
Cumulative estimate of total untracked removals.

---

## 4. Comparative Analyses

| Comparison | Metric(s) | Insight |
|-------------|------------|---------|
| **Between providers (same specialty)** | Mean residual ratio, std(residual), FCI | Detect trusts with inconsistent population accounting |
| **Within provider (across specialties)** | CIR vs \u0394Incomplete | Identify departments diverging from internal trends |
| **Temporal (national)** | Rolling residuals vs revision months | Reveal rebaselining or data cleansing cycles |
| **Population integrity** | \u2211 residual | Estimate total untracked patients ("dark backlog") |

---

## 5. Interpretation Framework

| Pattern | Probable cause | Behaviour |
|----------|----------------|------------|
| Sustained **negative residuals** | Nullified DNAs, unrecorded discharges | Artificial backlog shrinkage |
| **Spiky residuals** | Periodic data cleansing | Poor system hygiene |
| **Smooth near-zero residuals** | Consistent process | Reliable data |
| **Positive residuals** | Delayed inflow reporting | Administrative lag |

---

## 6. Advanced Extensions

- **Provider Integrity Index:** combine FCI + |mean residual ratio| to rank reliability.
- **Residual heatmap:** visualise residual ratio by month/specialty to detect manipulation clusters.
- **Markov transition model:** infer implied state transitions and test for conservation.
- **Balance sheet view:** treat incomplete as asset, admissions as expense, new periods as income – visualise per-provider 'liquidity' of patient flow.

---

**Summary:**  
NHS RTT data is not a closed accounting system. Missing mass in the flow equations reflects *administrative deletions, nullifications, and rebaselining*, not patient outcomes. Measuring and comparing the *residual dynamics* across providers is the most effective way to quantify these hidden practices.

