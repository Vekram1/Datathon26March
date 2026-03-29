# UK MVP Plan

This plan is deliberately narrow. The goal is not to build the full cross-country research project. The goal is to produce a fast, working UK-only prototype with real data and one usable model.

## 1. Session Goal

We are trying to finish one of these two outcomes:

* **success case:** a UK sector-year panel plus one baseline regression
* **fallback case:** a short data-readiness note explaining exactly which UK dataset failed to match

The point of this plan is speed and execution, not completeness.

## 2. Locked Scope

Use only this scope:

* **geography:** United Kingdom only
* **unit of analysis:** `sector x year`
* **outcome:** sector insolvency rate or sector insolvency count
* **treatment:** UK energy price shock by year
* **exposure:** lagged sector energy intensity
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

This is required to build:

* `energy_intensity = energy_use / output`

### D. Energy shock

Use one UK-relevant annual energy price series.

Good enough for MVP:

* annual change in a UK energy price index
* or annual change in an international fossil-energy benchmark used as a UK shock proxy

Need:

* year
* `energy_price_shock`

## 4. Main Question

Do more energy-intensive UK sectors show worse insolvency outcomes when energy prices rise?

## 5. Baseline Model

Use one simple specification:

\[
Y_{s,t} = \beta_1 Shock_t + \beta_2 EI_{s,t-1} + \beta_3(Shock_t \times EI_{s,t-1}) + \alpha_s + \tau_t + \varepsilon_{s,t}
\]

Where:

* `Y_{s,t}` = insolvency outcome for sector `s` in year `t`
* `Shock_t` = UK energy price shock in year `t`
* `EI_{s,t-1}` = lagged sector energy intensity
* `alpha_s` = sector fixed effects
* `tau_t` = year fixed effects

The only coefficient we really care about in the MVP is the interaction term.

## 6. Required Inputs

We only proceed if all of these exist:

* UK sector insolvency data
* UK sector energy-use data
* UK sector output or GVA data
* one annual energy shock series

If one of these is missing, we stop and document the blocker instead of forcing the model.

## 7. Two-Hour Build Plan

### Phase 1. Data Gate

Time budget: `30 to 45 minutes`

Tasks:

* download or confirm the UK insolvency dataset
* download or confirm the UK sector energy dataset
* download or confirm the UK output or GVA dataset
* download or confirm one annual energy-price series
* inspect each file for sector labels and year coverage
* identify the common overlap window

Outputs:

* `docs/data_readiness.md`
* `outputs/tables/source_coverage.csv`

Decision rule:

* if sector mappings are impossible or a required dataset is missing, stop and write the blocker

### Phase 2. Sector Mapping

Time budget: `25 to 35 minutes`

Tasks:

* standardize years
* standardize sector names
* collapse all sources to one common sector taxonomy
* drop sectors that do not map cleanly

Rule:

* small clean sample is better than a wide messy sample

Outputs:

* `data/processed/sector_crosswalk.csv`
* `docs/sector_mapping.md`

### Phase 3. Build Panel

Time budget: `20 to 30 minutes`

Tasks:

* merge insolvencies, energy use, output, and shock data
* compute `energy_intensity`
* compute `lagged_energy_intensity`
* define the main insolvency outcome
* save the merged panel

Required columns:

* `sector`
* `year`
* `sector_insolvencies`
* `energy_use`
* `output`
* `energy_intensity`
* `lagged_energy_intensity`
* `energy_price_shock`

Output:

* `data/processed/uk_sector_year_panel.parquet`

### Phase 4. Run One Model

Time budget: `15 to 20 minutes`

Tasks:

* run one baseline regression
* export one regression table
* export one simple plot of the interaction estimate

Outputs:

* `outputs/tables/baseline_fe.csv`
* `outputs/figures/interaction_coef.png`

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
    ├── 01_audit_data.py
    ├── 02_build_panel.py
    └── 03_run_baseline.py
```

## 10. Practical Rule

The order is:

1. get UK data
2. verify sectors and years line up
3. build the smallest clean panel possible
4. run one model
5. stop

That is the correct MVP.
