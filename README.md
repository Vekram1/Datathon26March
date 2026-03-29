# Datathon26March

This repo builds and analyzes S&P 500 gross profit margin history and compares it with annual energy price data from [hackathondata.csv](/Users/vikramoddiraju/personalCode/Datathon26March/hackathondata.csv).

## What Is In This Repo

Core inputs:

* [sp500_gross_margin.py](/Users/vikramoddiraju/personalCode/Datathon26March/sp500_gross_margin.py)
  Builds gross profit margin history for current S&P 500 constituents using:
  * Wikipedia for the current constituent list
  * SEC `companyfacts` data for revenue, gross profit, and cost of revenue
* [hackathondata.csv](/Users/vikramoddiraju/personalCode/Datathon26March/hackathondata.csv)
  Annual energy price data by commodity

Generated data:

* [data/sp500_gross_profit_margin_history.csv](/Users/vikramoddiraju/personalCode/Datathon26March/data/sp500_gross_profit_margin_history.csv)
* [data/sp500_gross_profit_margin_history_15y.csv](/Users/vikramoddiraju/personalCode/Datathon26March/data/sp500_gross_profit_margin_history_15y.csv)
* [data/sp500_gross_margin_change_summary.csv](/Users/vikramoddiraju/personalCode/Datathon26March/data/sp500_gross_margin_change_summary.csv)
* [data/sp500_gross_profit_margin_coverage.csv](/Users/vikramoddiraju/personalCode/Datathon26March/data/sp500_gross_profit_margin_coverage.csv)

Generated outputs:

* charts in [outputs/figures](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures)
* tables in [outputs/tables](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/tables)

## Setup

Create and activate a virtual environment, then install the small set of dependencies used by the current script.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas requests lxml html5lib beautifulsoup4
```

Notes:

* `pandas.read_html` needs HTML parsing support, so `lxml` and `html5lib` are recommended.
* The SEC expects a real contact string in the `--user-agent` flag.

## Main Script

Run this to build the current S&P 500 gross profit margin history:

```bash
source .venv/bin/activate
python sp500_gross_margin.py \
  --user-agent "Your Name your_email@example.com" \
  --out-dir data
```

What it writes:

* [data/sp500_current_constituents.csv](/Users/vikramoddiraju/personalCode/Datathon26March/data/sp500_current_constituents.csv)
* [data/sp500_gross_profit_margin_history.csv](/Users/vikramoddiraju/personalCode/Datathon26March/data/sp500_gross_profit_margin_history.csv)
* [data/sp500_gross_profit_margin_coverage.csv](/Users/vikramoddiraju/personalCode/Datathon26March/data/sp500_gross_profit_margin_coverage.csv)

Important flags:

* `--user-agent`
  Required. Use a real name and email.
* `--out-dir`
  Output directory for generated CSVs. Defaults to `data`.
* `--pause-seconds`
  Sleep between SEC requests. Default is already set to a safer value in the script.

Example:

```bash
source .venv/bin/activate
python sp500_gross_margin.py \
  --user-agent "Vikram Oddiraju your_email@example.com" \
  --out-dir data \
  --pause-seconds 0.35
```

## Current Workflow

The current repo workflow is:

1. Build the gross-margin history with [sp500_gross_margin.py](/Users/vikramoddiraju/personalCode/Datathon26March/sp500_gross_margin.py).
2. Use [hackathondata.csv](/Users/vikramoddiraju/personalCode/Datathon26March/hackathondata.csv) as the annual energy-price panel.
3. Read the precomputed comparison outputs in [outputs/figures](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures) and [outputs/tables](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/tables).

There is currently only one executable Python script in the repo. The comparison charts and summary tables already present in `outputs/` were generated during analysis and are ready to use.

## Recommended Files To Open First

If you just want the finished outputs, start here.

Main comparison charts:

* [outputs/figures/gross_margin_vs_energy_indexed.svg](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures/gross_margin_vs_energy_indexed.svg)
* [outputs/figures/sector_margin_change_pre_post_shock.svg](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures/sector_margin_change_pre_post_shock.svg)
* [outputs/figures/gross_margin_high_vs_low_exposure.svg](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures/gross_margin_high_vs_low_exposure.svg)
* [outputs/figures/sector_multi_fuel_heatmap.svg](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures/sector_multi_fuel_heatmap.svg)

Commodity-specific sector charts:

* [outputs/figures/commodity_sensitivity](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures/commodity_sensitivity)

Useful summary tables:

* [outputs/tables/sector_multi_fuel_rank.csv](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/tables/sector_multi_fuel_rank.csv)
* [outputs/tables/sector_multi_fuel_sensitivity.csv](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/tables/sector_multi_fuel_sensitivity.csv)
* [outputs/tables/commodity_sensitivity_correlations.csv](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/tables/commodity_sensitivity_correlations.csv)
* [outputs/tables/sector_natgas_plus10pct_scenario.csv](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/tables/sector_natgas_plus10pct_scenario.csv)

## What The Data Means

Gross profit margin is computed as:

```text
gross_profit / revenue
```

or, if gross profit is missing:

```text
(revenue - cost_of_revenue) / revenue
```

Sector-level charts are built by aggregating company-level gross profit margins to a sector-year median.

## Known Limitations

* The gross-margin history is for current S&P 500 constituents, not a survivorship-bias-free index history.
* Coverage is uneven by company and by sector.
* The commodity comparison work is correlation-based, not causal.
* Annual data is noisy, so the ranked bar charts and heatmaps are more reliable than raw scatter plots.

## Quick Start

If you want the fastest path:

1. Activate the environment.
2. Run [sp500_gross_margin.py](/Users/vikramoddiraju/personalCode/Datathon26March/sp500_gross_margin.py) if you need to refresh the gross-margin data.
3. Open the charts in [outputs/figures](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/figures).
4. Use the ranked tables in [outputs/tables](/Users/vikramoddiraju/personalCode/Datathon26March/outputs/tables) for slide text or summaries.
