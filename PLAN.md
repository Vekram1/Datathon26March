# UK MVP Plan

This plan is deliberately narrow. The goal is not to build the full cross-country research project. The goal is to produce a fast, working UK-only prototype with real data and one usable model.

## 0. Goal

Build the fastest possible UK-only sector-year prototype that tests whether more energy-exposed sectors had worse insolvency outcomes when energy prices rose, using real data and one interpretable baseline model.

Done means one of two things:

* a clean merged UK sector-year panel plus one baseline regression
* a short blocker note showing exactly which dataset or mapping failed

## 1. Success Criteria

We are trying to finish one of these two outcomes:

* **success case:** a UK sector-year panel plus one baseline regression
* **fallback case:** a short data-readiness note explaining exactly which UK dataset failed to match

The point of this plan is speed and execution, not completeness.

## 2. Locked Scope

Use only this scope:

* **geography:** United Kingdom only
* **unit of analysis:** `sector x year`
* **outcome:** sector insolvency count first; sector insolvency rate only if the denominator is easy to obtain
* **treatment:** UK energy price shock by year
* **exposure:** lagged sector energy intensity, or a simpler sector energy-exposure proxy if the output merge is the blocker
* **model:** one baseline fixed-effects style panel regression

Do not expand to multiple countries, event studies, or robustness checks in the first pass.

## 3. Data Sources

These are the sources we should actually use.

### A. Distress outcome

Use official UK company insolvency data by industry from the Insolvency Service.

Need:

* year
* sector or SIC-based industry label
* insolvency count

Preferred output:

* `sector_insolvencies`
* `sector_insolvency_rate` if we also have an active-firms denominator

### B. Sector energy exposure

Use a UK sector energy dataset with annual sector energy use.

Preferred source path:

* UK government energy statistics first
* fallback to a sector energy table already bundled in an official UK release

Need:

* year
* sector
* energy use

### C. Sector output denominator

Use UK sector gross value added or output.

Preferred source path:

* UK ONS
* fallback to OECD STAN if UK sector mappings are easier there

Need:

* year
* sector
* gross output or GVA

Preferred MVP use:

* `energy_intensity = energy_use / output`

This is helpful, but it is not a hard blocker for the first pass if a simpler exposure proxy gets us to a working model faster.

### D. Energy shock

Use one UK-relevant annual energy price series.

Good enough for MVP:

* annual change in a UK energy price index
* or annual change in an international fossil-energy benchmark used as a UK shock proxy

Need:

* year
* `energy_price_shock`

## 4. Main Question

Do more energy-exposed UK sectors show worse insolvency outcomes when energy prices rise?

## 5. Baseline Model

Use one simple specification:

\[
Y_{s,t} = \beta_1 EI_{s,t-1} + \beta_2(Shock_t \times EI_{s,t-1}) + \alpha_s + \tau_t + \varepsilon_{s,t}
\]

Where:

* `Y_{s,t}` = insolvency outcome for sector `s` in year `t`
* `Shock_t` = UK energy price shock in year `t`
* `EI_{s,t-1}` = lagged sector energy intensity
* `alpha_s` = sector fixed effects
* `tau_t` = year fixed effects

Notes:

* with year fixed effects, the standalone `Shock_t` term is absorbed
* the only coefficient we really care about in the MVP is the interaction term
* if `energy_intensity` is not feasible in time, replace it with the simplest defensible sector energy-exposure proxy and keep moving

## 6. Required Inputs

### Tier 1 required

We proceed with the MVP if these exist:

* UK sector insolvency data
* UK sector energy-use data
* one annual energy shock series

### Tier 2 preferred

These improve the MVP but should not block it:

* UK sector output or GVA data
* active-firms denominator for an insolvency rate

If Tier 1 fails, we stop and document the blocker instead of forcing the model.

## 7. Two-Hour Build Plan

### Phase 1. Audit + Mapping

Time budget: `45 to 60 minutes`

Tasks:

* download or confirm the UK insolvency dataset
* download or confirm the UK sector energy dataset
* download or confirm one annual energy-price series
* download or confirm the UK output or GVA dataset only if it looks easy
* inspect each file for sector labels and year coverage
* collapse everything to one coarse common sector taxonomy immediately
* drop sectors that do not map cleanly
* identify the common overlap window

Outputs:

* `docs/mvp_log.md`
* `outputs/tables/source_coverage.csv`
* `data/processed/sector_crosswalk.csv`

Decision rule:

* small clean sample is better than a wide messy sample
* if the sector mapping is impossible or Tier 1 data is missing, stop and write the blocker

### Phase 2. Build Panel

Time budget: `30 to 40 minutes`

Tasks:

* merge insolvencies, energy use, and shock data
* merge output or GVA only if it is clean and fast
* define the main insolvency outcome
* compute `energy_intensity` if output exists
* otherwise compute the simplest defensible sector energy-exposure proxy
* compute `lagged_energy_intensity` or the lagged proxy
* save the merged panel

Required columns:

* `sector`
* `year`
* `sector_insolvencies`
* `energy_use`
* `energy_price_shock`
* `lagged_energy_intensity` or another lagged exposure measure

Preferred columns:

* `output`
* `energy_intensity`

Output:

* `data/processed/uk_sector_year_panel.parquet`

### Phase 3. Run One Model

Time budget: `20 to 30 minutes`

Tasks:

* run one baseline regression
* export one regression table
* export one simple descriptive figure only if it is quick

Outputs:

* `outputs/tables/baseline_fe.csv`
* `outputs/figures/interaction_coef.png` if time permits

## 8. What Is Out of Scope

Not for the first version:

* multiple countries
* multiple shock definitions
* event study
* local projections
* placebo tests
* robustness section
* large package architecture
* full report generation

## 9. Minimum File Structure

Keep the repo simple:

```text
project/
├── PLAN.md
├── data/
│   ├── raw/
│   └── processed/
├── docs/
├── outputs/
│   ├── tables/
│   └── figures/
└── scripts/
    ├── 01_audit_and_map.py
    └── 02_build_panel_and_run_baseline.py
```

## 10. Practical Rule

The order is:

1. get UK data
2. force a coarse sector mapping that actually works
3. build the smallest clean panel possible
4. run one model
5. stop

That is the correct MVP. A small clean answer beats a broad messy one.
