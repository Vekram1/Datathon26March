#!/usr/bin/env python3
"""
Build or update a gross-profit-margin history for S&P 500 companies using only
free public data:
  - current S&P 500 constituent table from Wikipedia
  - SEC companyfacts JSON from data.sec.gov

Behavior:
  - Fetch the current S&P 500 constituent list each run.
  - Rebuild full history for current constituents.
  - Preserve old history for companies that previously appeared in the output
    but are no longer current constituents, without updating them further.

Gross profit margin is computed as:
    gross_profit / revenue
where possible, with a fallback to:
    (revenue - cost_of_revenue) / revenue

Usage:
    python sp500_gross_margin.py \
        --user-agent "Your Name your_email@example.com" \
        --out-dir data
"""

from __future__ import annotations

import argparse
from io import StringIO
import time
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import requests

WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
WIKI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}
MIN_ANNUAL_DAYS = 300
MAX_ANNUAL_DAYS = 380

REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueNet",
    "Revenues",
]
GROSS_PROFIT_TAGS = ["GrossProfit"]
COST_TAGS = [
    "CostOfRevenue",
    "CostOfGoodsAndServicesSold",
    "CostOfGoodsSold",
    "CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization",
]

OUTPUT_COLUMNS = [
    "ticker",
    "security",
    "cik",
    "sector",
    "sub_industry",
    "fiscal_year",
    "gross_profit_margin",
    "gross_profit",
    "revenue",
    "cost_of_revenue",
    "gross_profit_source",
    "revenue_source",
    "cost_source",
    "form",
    "filed",
    "source",
    "is_current_constituent",
]


def make_session(user_agent: str) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        }
    )
    return s


def fetch_current_sp500_constituents() -> pd.DataFrame:
    resp = requests.get(WIKI_SP500_URL, headers=WIKI_HEADERS, timeout=30)
    resp.raise_for_status()

    # Avoid pandas/urllib fetching the URL directly; Wikipedia often 403s that path.
    tables = pd.read_html(StringIO(resp.text))
    if not tables:
        raise RuntimeError("Could not find any tables on the S&P 500 page.")

    df = tables[0].copy()
    expected = {"Symbol", "Security", "GICS Sector", "GICS Sub-Industry", "CIK"}
    missing = expected - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing expected columns from constituent table: {sorted(missing)}")

    df = df.rename(
        columns={
            "Symbol": "ticker",
            "Security": "security",
            "GICS Sector": "sector",
            "GICS Sub-Industry": "sub_industry",
            "CIK": "cik",
        }
    )

    # Some vendors encode tickers with dots, while SEC/other feeds often use dashes.
    df["ticker"] = df["ticker"].astype(str).str.strip().str.replace(".", "-", regex=False)
    df["cik"] = df["cik"].astype(str).str.extract(r"(\d+)", expand=False).str.zfill(10)

    # The index can contain multiple share classes for the same company/CIK.
    # Gross profit margin is company-level, so keep one row per CIK.
    df = df.sort_values(["cik", "ticker"]).drop_duplicates(subset=["cik"], keep="first")

    return df[["ticker", "security", "sector", "sub_industry", "cik"]].reset_index(drop=True)


def _fact_duration_days(fact: dict) -> Optional[int]:
    start = fact.get("start")
    end = fact.get("end")
    if not start or not end:
        return None
    try:
        return (pd.Timestamp(end) - pd.Timestamp(start)).days
    except Exception:
        return None


def _extract_best_annual_facts(companyfacts: dict, tags: Iterable[str]) -> pd.DataFrame:
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    rows: list[dict] = []

    for tag in tags:
        concept = us_gaap.get(tag)
        if not concept:
            continue

        units = concept.get("units", {})
        facts = units.get("USD", [])

        for fact in facts:
            form = fact.get("form")
            fy = fact.get("fy")
            val = fact.get("val")
            filed = fact.get("filed")
            duration_days = _fact_duration_days(fact)

            if form not in ANNUAL_FORMS:
                continue
            if fy is None or val is None or filed is None:
                continue
            if duration_days is None or not (MIN_ANNUAL_DAYS <= duration_days <= MAX_ANNUAL_DAYS):
                continue

            rows.append(
                {
                    "tag": tag,
                    "fiscal_year": int(fy),
                    "value": float(val),
                    "form": form,
                    "filed": pd.Timestamp(filed),
                    "end": pd.Timestamp(fact["end"]),
                    "duration_days": duration_days,
                }
            )

    if not rows:
        return pd.DataFrame(columns=["fiscal_year", "value", "tag", "form", "filed"])

    df = pd.DataFrame(rows)
    tag_rank = {tag: i for i, tag in enumerate(tags)}
    df["tag_rank"] = df["tag"].map(tag_rank).fillna(len(tag_rank)).astype(int)

    # One best observation per fiscal year:
    #   1) prefer earlier tag in caller priority
    #   2) prefer latest filing date
    #   3) prefer latest period end
    df = df.sort_values(["fiscal_year", "tag_rank", "filed", "end"], ascending=[True, True, False, False])
    df = df.drop_duplicates(subset=["fiscal_year"], keep="first")

    return df[["fiscal_year", "value", "tag", "form", "filed"]].reset_index(drop=True)


def build_company_history(session: requests.Session, constituent: pd.Series, pause_seconds: float) -> pd.DataFrame:
    cik = constituent["cik"]
    url = SEC_COMPANYFACTS_URL.format(cik=cik)

    resp = session.get(url, timeout=30)
    if resp.status_code == 404:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    resp.raise_for_status()
    companyfacts = resp.json()

    revenue = _extract_best_annual_facts(companyfacts, REVENUE_TAGS).rename(
        columns={"value": "revenue", "tag": "revenue_source", "form": "revenue_form", "filed": "revenue_filed"}
    )
    gross = _extract_best_annual_facts(companyfacts, GROSS_PROFIT_TAGS).rename(
        columns={"value": "gross_profit", "tag": "gross_profit_source", "form": "gross_form", "filed": "gross_filed"}
    )
    cost = _extract_best_annual_facts(companyfacts, COST_TAGS).rename(
        columns={"value": "cost_of_revenue", "tag": "cost_source", "form": "cost_form", "filed": "cost_filed"}
    )

    years = sorted(set(revenue.get("fiscal_year", [])) | set(gross.get("fiscal_year", [])) | set(cost.get("fiscal_year", [])))
    if not years:
        time.sleep(pause_seconds)
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    out = pd.DataFrame({"fiscal_year": years})
    out = out.merge(revenue, on="fiscal_year", how="left")
    out = out.merge(gross, on="fiscal_year", how="left")
    out = out.merge(cost, on="fiscal_year", how="left")

    # Fallback: if gross profit is absent but revenue and cost are present, compute it.
    missing_gp = out["gross_profit"].isna() & out["revenue"].notna() & out["cost_of_revenue"].notna()
    out.loc[missing_gp, "gross_profit"] = out.loc[missing_gp, "revenue"] - out.loc[missing_gp, "cost_of_revenue"]
    out.loc[missing_gp, "gross_profit_source"] = "derived:revenue_minus_cost"

    out["gross_profit_margin"] = out["gross_profit"] / out["revenue"]
    out.loc[(out["revenue"].isna()) | (out["revenue"] == 0), "gross_profit_margin"] = pd.NA

    # Pick a representative filing metadata field for the row.
    out["filed"] = out[[c for c in ["gross_filed", "revenue_filed", "cost_filed"] if c in out.columns]].bfill(axis=1).iloc[:, 0]
    out["form"] = out[[c for c in ["gross_form", "revenue_form", "cost_form"] if c in out.columns]].bfill(axis=1).iloc[:, 0]

    out["ticker"] = constituent["ticker"]
    out["security"] = constituent["security"]
    out["cik"] = constituent["cik"]
    out["sector"] = constituent["sector"]
    out["sub_industry"] = constituent["sub_industry"]
    out["source"] = "SEC companyfacts"
    out["is_current_constituent"] = True

    out = out[OUTPUT_COLUMNS].sort_values("fiscal_year").reset_index(drop=True)

    time.sleep(pause_seconds)
    return out


def rebuild_current_constituents(
    session: requests.Session,
    constituents: pd.DataFrame,
    pause_seconds: float,
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    total = len(constituents)

    for i, row in constituents.iterrows():
        ticker = row["ticker"]
        cik = row["cik"]
        try:
            part = build_company_history(session, row, pause_seconds=pause_seconds)
            parts.append(part)
            print(f"[{i + 1:>3}/{total}] {ticker:<8} CIK={cik} rows={len(part)}")
        except Exception as exc:
            print(f"[{i + 1:>3}/{total}] {ticker:<8} CIK={cik} ERROR: {exc}")

    if not parts:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    out = pd.concat(parts, ignore_index=True)
    out = out.drop_duplicates(subset=["cik", "fiscal_year"], keep="last")
    return out.sort_values(["ticker", "fiscal_year"]).reset_index(drop=True)


def merge_with_prior_history(current_hist: pd.DataFrame, prior_hist: pd.DataFrame, current_ciks: set[str]) -> pd.DataFrame:
    if prior_hist.empty:
        return current_hist.copy()

    removed_hist = prior_hist.loc[~prior_hist["cik"].astype(str).str.zfill(10).isin(current_ciks)].copy()
    if not removed_hist.empty:
        removed_hist["is_current_constituent"] = False

    merged = pd.concat([current_hist, removed_hist], ignore_index=True)
    merged["cik"] = merged["cik"].astype(str).str.zfill(10)
    merged = merged.drop_duplicates(subset=["cik", "fiscal_year"], keep="first")
    return merged.sort_values(["ticker", "fiscal_year"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user-agent",
        required=True,
        help='Contact string for SEC requests, e.g. "Jane Doe jane@example.com"',
    )
    parser.add_argument("--out-dir", default="data", help="Directory for outputs.")
    parser.add_argument(
        "--pause-seconds",
        type=float,
        default=0.35,
        help="Sleep between SEC requests so the run is polite.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    constituents_path = out_dir / "sp500_current_constituents.csv"
    history_path = out_dir / "sp500_gross_profit_margin_history.csv"

    session = make_session(args.user_agent)

    constituents = fetch_current_sp500_constituents()
    constituents.to_csv(constituents_path, index=False)
    print(f"Saved current constituents: {constituents_path}")

    current_hist = rebuild_current_constituents(session, constituents, pause_seconds=args.pause_seconds)

    if history_path.exists():
        prior_hist = pd.read_csv(history_path, dtype={"cik": str})
    else:
        prior_hist = pd.DataFrame(columns=OUTPUT_COLUMNS)

    merged_hist = merge_with_prior_history(
        current_hist=current_hist,
        prior_hist=prior_hist,
        current_ciks=set(constituents["cik"].astype(str).str.zfill(10)),
    )

    merged_hist.to_csv(history_path, index=False)
    print(f"Saved gross profit margin history: {history_path}")

    coverage = (
        merged_hist.groupby(["ticker", "security", "is_current_constituent"], dropna=False)["fiscal_year"]
        .agg(["min", "max", "count"])
        .reset_index()
        .rename(columns={"min": "first_year", "max": "last_year", "count": "n_years"})
        .sort_values(["is_current_constituent", "ticker"], ascending=[False, True])
    )
    coverage_path = out_dir / "sp500_gross_profit_margin_coverage.csv"
    coverage.to_csv(coverage_path, index=False)
    print(f"Saved coverage summary: {coverage_path}")


if __name__ == "__main__":
    main()
