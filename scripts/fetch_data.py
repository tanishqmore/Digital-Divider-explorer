"""
Regenerate data/dataset.json from live Our World in Data / World Bank sources.

Usage:
    pip install pandas requests
    python3 scripts/fetch_data.py

This re-downloads the three indicators used by the dashboard for the
countries listed below, and rewrites data/dataset.json in the same shape
the site expects. Edit COUNTRIES to add or remove countries — just make
sure the country name matches the "Entity" column in the OWID CSVs.
"""

import json
import requests
import pandas as pd

COUNTRIES = ["Brazil", "China", "Egypt", "Ethiopia", "Chile", "Colombia"]
YEAR_MIN, YEAR_MAX = 2000, 2024

SOURCES = {
    "internet_pct": (
        "https://ourworldindata.org/grapher/share-of-individuals-using-the-internet.csv"
        "?v=1&csvType=full&useColumnShortNames=false"
    ),
    "internet_users": (
        "https://ourworldindata.org/grapher/number-of-internet-users.csv"
        "?v=1&csvType=full&useColumnShortNames=false"
    ),
    "gdp_growth_pct": (
        "https://ourworldindata.org/grapher/gdp-per-capita-growth.csv"
        "?v=1&csvType=full&useColumnShortNames=false"
    ),
}


def fetch_metric(url: str) -> pd.DataFrame:
    df = pd.read_csv(url, storage_options={"User-Agent": "digital-divide-explorer/1.0"})
    value_col = df.columns[-1]
    df = df.rename(columns={value_col: "value"})
    return df[["Entity", "Year", "value"]]


def main():
    years = list(range(YEAR_MIN, YEAR_MAX + 1))
    frames = {metric: fetch_metric(url) for metric, url in SOURCES.items()}

    countries_out = {}
    for country in COUNTRIES:
        entry = {}
        for metric, df in frames.items():
            sub = df[df["Entity"] == country].set_index("Year")["value"]
            entry[metric] = [
                float(sub[y]) if y in sub.index and pd.notna(sub[y]) else None
                for y in years
            ]
        countries_out[country] = entry

    out = {
        "meta": {
            "title": "Digital Divide Explorer dataset",
            "years_range": [YEAR_MIN, YEAR_MAX],
            "sources": [
                {"metric": m, "url": u} for m, u in SOURCES.items()
            ],
            "license": "CC BY 4.0 (Our World in Data / World Bank)",
        },
        "years": years,
        "countries": countries_out,
    }

    with open("data/dataset.json", "w") as f:
        json.dump(out, f, indent=2)

    print(f"Wrote data/dataset.json with {len(countries_out)} countries.")


if __name__ == "__main__":
    main()
