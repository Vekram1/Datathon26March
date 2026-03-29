Yes — here is the rewritten version for a **sector-year panel** in Python.

The main design change is this: instead of asking whether a firm’s bankruptcy risk changes with energy exposure, you ask whether **more energy-intensive sectors experience worse distress outcomes when an energy-transition or energy-cost shock hits**. That is a better fit for official energy datasets, because EIA now publishes international end-use consumption by country, fuel, sector, and up to 34 subsectors with annual data through 2023, while the World Bank provides country-year renewable share and energy-intensity indicators you can use for transition context. FRED is useful for macro controls because it aggregates hundreds of thousands of national and international series from many sources. ([U.S. Energy Information Administration][1])

## 1. Project framing

**Working title**
**Energy Transition Shocks and Sector-Level Financial Distress**

**Core question**
Do energy-transition shocks increase financial distress more in energy-intensive sectors, and which sectors appear most exposed?

**Unit of analysis**
`country × sector × year`

**Why this version works**

* energy exposure is naturally measured at the sector level
* transition variables are naturally measured at the country-year level
* distress can be aggregated to sector-year
* panel fixed effects are much more defensible here than trying to force a firm-level causal forest onto mismatched data sources

## 2. Research question and hypotheses

### Main question

**Does a transition-related shock have a larger effect on sector-level distress in more energy-intensive sectors?**

### Hypotheses

* **H1:** sectors with higher lagged energy intensity experience larger increases in distress after an energy-cost or transition shock
* **H2:** this effect is strongest in heavy industry, transport, mining, refining, and other sectors with large direct energy use
* **H3:** sectors in countries with higher renewable adoption may be less exposed over time, conditional on macro controls

## 3. Outcome, treatment, and exposure

This is the most important conceptual cleanup.

### Outcome

You need a **sector-year distress outcome**. Use one primary outcome and maybe one secondary one.

Good options:

* `sector_bankruptcy_rate_cts` = bankruptcies in sector `s` / active firms in sector `s`
* `sector_distress_share_cts` = share of firms in a sector-year classified as distressed
* `median_interest_coverage_cts`
* `median_altman_z_cts`
* `distress_index_cts` built from standardized distress measures

If you do not have a true bankruptcy-count dataset with sector labels, build a **sector distress proxy** by aggregating firm-level financial distress signals to the sector-year level.

### Treatment

Use a **shock**, not “energy intensity” itself.

Examples:

* `energy_price_shock_ct` = large annual rise in fossil-energy prices or electricity prices
* `transition_shock_ct` = sharp increase in renewable penetration, carbon price, or regulatory transition pressure
* `post_shock_ct` = indicator for years after a major transition or price shock event

### Exposure

Use:

* `energy_intensity_cst_minus1`

That should be lagged sector energy intensity, ideally:

* sector energy use / sector gross output
* or sector fuel expenditure share
* or sector final energy consumption per real output unit

The World Bank’s economy-wide energy intensity indicator is defined as energy supply divided by PPP GDP and is best used as a **country-level control**, not as your main sector exposure. ([DataBank][2])

### Main estimand

The object you really care about is the interaction:

[
\text{Shock}*{c,t} \times \text{EnergyIntensity}*{c,s,t-1}
]

Interpretation: when a shock hits, do sectors with higher pre-existing energy intensity deteriorate more?

## 4. Data sources

### A. Sector energy exposure

Use the EIA international end-use dataset as your main sector-energy source. It provides annual data through 2023 and breaks consumption out by country, fuel, sector, and up to 34 subsectors. ([U.S. Energy Information Administration][1])

Store fields like:

* country
* year
* sector / subsector
* fuel type
* total final energy consumption
* sector energy use

### B. Transition variables

Use World Bank indicators:

* **renewable energy consumption (% of total final energy consumption)**, indicator `EG.FEC.RNEW.ZS` ([DataBank][3])
* **energy intensity level of primary energy**, indicator `EG.EGY.PRIM.PP.KD` ([DataBank][2])

These are country-year variables.

### C. Macro controls

Use FRED or direct-source macro series for:

* GDP growth
* inflation
* unemployment
* interest rates
* industrial production if available
* commodity and energy price controls

FRED is a convenient wrapper because it carries large numbers of national and international series from many public and private sources. ([FRED Help][4])

### D. Sector output denominator

To compute energy intensity properly, you need a sector output denominator:

* country-sector gross output
* or country-sector value added

This may come from OECD, World Bank-related sources, national statistics offices, or another sector accounts dataset you already have. The exact choice depends on coverage.

### E. Sector distress outcome

This is the one place where your actual available data matters most.

You need one of:

* a sector-year bankruptcy count dataset
* a firm-level distress dataset with sector codes that you can aggregate
* a sector financial fragility proxy constructed from listed firms

If you already have a “bankruptcy prediction” dataset without sector labels, it is **not sufficient by itself** for this design.

## 5. Final analytic dataset

Your canonical modeling table should look like this:

`country_sector_year_panel.parquet`

Columns:

* `country`
* `sector_code`
* `sector_name`
* `year`
* `distress_outcome`
* `bankruptcy_rate`
* `energy_use`
* `gross_output`
* `energy_intensity`
* `renewable_share_country`
* `country_energy_intensity`
* `energy_price_shock`
* `gdp_growth`
* `inflation`
* `unemployment`
* `sector_output_growth`
* `sample_flag`
* `matched_source_flag`

## 6. Recommended identification strategy

Do **not** lead with Granger or machine learning here. Lead with a panel model.

### Baseline panel fixed-effects model

[
Y_{c,s,t} = \beta_1 Shock_{c,t} + \beta_2 EI_{c,s,t-1} + \beta_3(Shock_{c,t}\times EI_{c,s,t-1}) + \Gamma X_{c,s,t} + \alpha_{c,s} + \tau_t + \varepsilon_{c,s,t}
]

Where:

* `Y_{c,s,t}` = sector distress outcome
* `Shock_{c,t}` = energy-cost or transition shock
* `EI_{c,s,t-1}` = lagged sector energy intensity
* `X_{c,s,t}` = controls
* `α_{c,s}` = country-sector fixed effects
* `τ_t` = year fixed effects

**Key coefficient:** `β3`

If `β3 > 0`, more energy-intensive sectors are more adversely affected by the shock.

### Stronger variants

After the baseline:

* add `country × year` fixed effects if identification allows
* add `sector × year` fixed effects if you want to absorb global sector shocks
* run event-study style specifications if you define a discrete policy shock

### What not to claim

Call this a **causal panel design with identifying assumptions**, not automatic proof of causality. The credibility comes from the shock design, lag structure, fixed effects, and robustness checks.

## 7. Project directory structure

```text
energy-transition-sector-panel/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── Makefile
├── configs/
│   ├── paths.yaml
│   ├── data_sources.yaml
│   ├── variables.yaml
│   ├── model_baseline.yaml
│   └── model_event_study.yaml
├── data/
│   ├── raw/
│   │   ├── eia_international/
│   │   ├── world_bank/
│   │   ├── fred/
│   │   ├── sector_output/
│   │   ├── distress/
│   │   └── crosswalks/
│   ├── interim/
│   ├── processed/
│   └── features/
├── docs/
│   ├── research_question.md
│   ├── identification.md
│   ├── data_dictionary.md
│   ├── sector_mapping.md
│   └── presentation_outline.md
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_build_energy_panel.ipynb
│   ├── 03_build_distress_panel.ipynb
│   ├── 04_merge_panel.ipynb
│   ├── 05_eda.ipynb
│   ├── 06_baseline_fe.ipynb
│   ├── 07_event_study.ipynb
│   └── 08_figures.ipynb
├── outputs/
│   ├── tables/
│   ├── figures/
│   ├── models/
│   └── logs/
├── src/
│   └── etsp/
│       ├── __init__.py
│       ├── settings.py
│       ├── io/
│       │   ├── load_eia.py
│       │   ├── load_world_bank.py
│       │   ├── load_fred.py
│       │   ├── load_sector_output.py
│       │   └── load_distress.py
│       ├── clean/
│       │   ├── normalize_country_names.py
│       │   ├── normalize_sector_codes.py
│       │   ├── clean_energy_data.py
│       │   ├── clean_distress_data.py
│       │   └── crosswalks.py
│       ├── features/
│       │   ├── build_energy_intensity.py
│       │   ├── build_transition_shocks.py
│       │   ├── build_macro_controls.py
│       │   ├── build_distress_outcomes.py
│       │   └── assemble_panel.py
│       ├── models/
│       │   ├── baseline_fe.py
│       │   ├── event_study.py
│       │   ├── local_projections.py
│       │   └── diagnostics.py
│       ├── eval/
│       │   ├── placebo.py
│       │   ├── pretrends.py
│       │   ├── robustness.py
│       │   └── sensitivity.py
│       └── viz/
│           ├── trend_plots.py
│           ├── coefficient_plots.py
│           ├── sector_rankings.py
│           └── heatmaps.py
├── scripts/
│   ├── 00_pull_data.py
│   ├── 01_build_crosswalks.py
│   ├── 02_build_energy_panel.py
│   ├── 03_build_distress_panel.py
│   ├── 04_build_macro_controls.py
│   ├── 05_merge_panel.py
│   ├── 06_run_baseline.py
│   ├── 07_run_event_study.py
│   ├── 08_run_robustness.py
│   └── 09_make_report.py
└── tests/
    ├── test_crosswalks.py
    ├── test_merge_keys.py
    ├── test_lagging.py
    ├── test_shock_construction.py
    └── test_no_future_leakage.py
```

## 8. Python stack

Use:

* `pandas`
* `polars` or `duckdb` for larger joins
* `pyarrow`
* `requests`
* `statsmodels`
* `linearmodels`
* `scikit-learn` for preprocessing and diagnostics
* `matplotlib`

I would store all final intermediate tables as **Parquet** and do heavy merges in **DuckDB**.

## 9. Data engineering plan

### Phase 1: data audit

Goal: verify the project is buildable before modeling.

Tasks:

* inspect coverage by country, sector, year
* inspect sector naming and coding systems
* identify the overlap window across all sources
* confirm the distress outcome exists at sector-year or can be aggregated there
* produce a coverage matrix

Outputs:

* `docs/data_dictionary.md`
* `outputs/tables/source_coverage.csv`

### Phase 2: sector crosswalks

This is usually the most annoying part.

Tasks:

* harmonize sector names across energy data, distress data, and output data
* create a master sector crosswalk
* define the final sector taxonomy you will use
* drop sectors that cannot be mapped cleanly

Outputs:

* `data/processed/sector_crosswalk.parquet`
* `docs/sector_mapping.md`

### Phase 3: energy exposure build

Tasks:

* ingest EIA country-sector-year energy data
* aggregate subsectors if needed
* merge sector output
* compute
  `energy_intensity = energy_use / gross_output`
* lag exposure by one year
* compute rolling averages if needed

Outputs:

* `data/features/energy_exposure.parquet`

### Phase 4: transition-shock build

Tasks:

* ingest World Bank renewable share and country energy intensity
* ingest energy-price or macro shock series
* define one primary treatment
* define alternate treatments for robustness

Good first treatment choices:

* top-quartile annual increase in energy prices
* top-quartile annual change in renewable share
* post-policy-shift indicator for a set of countries

Outputs:

* `data/features/transition_shocks.parquet`

### Phase 5: distress outcome build

Tasks:

* ingest sector distress data
* build yearly sector distress outcome
* winsorize or smooth where needed
* define the main and backup outcome

Outputs:

* `data/features/distress_outcomes.parquet`

### Phase 6: final panel assembly

Tasks:

* merge energy, distress, and macro tables
* construct lags
* generate sample flags
* freeze the modeling window

Outputs:

* `data/processed/country_sector_year_panel.parquet`

## 10. Modeling plan

### Model 1: descriptive trends

Show:

* average energy intensity by sector
* distress rate by sector
* renewable adoption by country
* a heatmap of sector exposure across countries

### Model 2: baseline two-way fixed effects

Run:

* sector-year distress on shock, lagged exposure, interaction, controls
* cluster standard errors by country or country-sector depending on sample structure

### Model 3: richer FE specification

Try:

* `country-sector FE + year FE`
* then `country-year FE + sector FE` if your treatment variation still survives
* compare coefficient stability

### Model 4: event study

If you define a discrete transition shock or policy event:

* estimate leads and lags
* test pre-trends
* show whether distress rises after the shock more in high-energy-intensity sectors

### Model 5: local projections

Optional but good for presentations:

* estimate dynamic response of sector distress for 1–3 years after a shock

## 11. Main figures and tables

You should plan the final deck around these.

### Figures

* sector energy intensity ranking
* country renewable adoption trends
* coefficient plot for `shock × energy_intensity`
* event-study plot
* heatmap of estimated sector vulnerability

### Tables

* source coverage and sample construction
* baseline FE results
* robustness specifications
* top 10 most exposed sectors
* top 10 least exposed sectors

## 12. Robustness checks

Run at least these:

* alternate shock definitions
* alternate distress outcome
* alternate lag length
* exclude one country at a time
* exclude one broad sector at a time
* pre-trend test for event-study design
* placebo shocks in non-event years

## 13. Suggested scripts

A clean command-line workflow:

```bash
python scripts/00_pull_data.py
python scripts/01_build_crosswalks.py
python scripts/02_build_energy_panel.py
python scripts/03_build_distress_panel.py
python scripts/04_build_macro_controls.py
python scripts/05_merge_panel.py
python scripts/06_run_baseline.py
python scripts/07_run_event_study.py
python scripts/08_run_robustness.py
python scripts/09_make_report.py
```

## 14. Recommended README structure

Your README should have:

* project question
* unit of analysis
* source list
* sample window
* variable definitions
* exact empirical specification
* how to reproduce the main tables and figures

## 15. Suggested six-week schedule

### Week 1

Set up repo, audit sources, define sector taxonomy.

### Week 2

Build energy panel and sector crosswalks.

### Week 3

Build distress outcome and macro controls.

### Week 4

Assemble final panel and run EDA.

### Week 5

Run baseline FE and event-study results.

### Week 6

Run robustness, finalize figures, write presentation.

## 16. Final thesis statement

A clean thesis for this version is:

**Energy-transition and energy-cost shocks have heterogeneous effects across sectors, and sectors with higher pre-shock energy intensity exhibit larger increases in financial distress after those shocks.**

That is much tighter than the original firm-level version and better matched to the available energy data. The reason is straightforward: your energy inputs are naturally sectoral, the World Bank indicators are country-year, and the EIA international data is explicitly structured around country-sector-subsector annual consumption rather than firm-level exposure. ([U.S. Energy Information Administration][1])

If you want, I can turn this into a **full README.md draft plus starter `requirements.txt` and the first three Python scripts**.

[1]: https://www.eia.gov/todayinenergy/detail.php?id=67384&utm_source=chatgpt.com "Today in Energy"
[2]: https://databank.worldbank.org/metadataglossary/environment-social-and-governance-%28esg%29-data/series/EG.EGY.PRIM.PP.KD?utm_source=chatgpt.com "Metadata Glossary - DataBank - World Bank"
[3]: https://databank.worldbank.org/metadataglossary/world-development-indicators/series/EG.FEC.RNEW.ZS?utm_source=chatgpt.com "Metadata Glossary - DataBank - World Bank"
[4]: https://fredhelp.stlouisfed.org/fred/about/about-fred/what-is-fred/?utm_source=chatgpt.com "What is FRED? | Getting To Know FRED - FRED Help"

