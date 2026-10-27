import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "dataset.json"

COUNTRIES = {
    "Brazil": "BRA",
    "China": "CHN",
    "Egypt": "EGY",
    "Ethiopia": "ETH",
    "Chile": "CHL",
    "Colombia": "COL",
    "India": "IND",
}

INDICATORS = {
    "internet_pct": "IT.NET.USER.ZS",
    "gdp_growth_pct": "NY.GDP.PCAP.KD.ZG",
    "population": "SP.POP.TOTL",
}

START_YEAR = 2000
END_YEAR = 2030


def fetch_indicator(country_code, indicator_code):
    url = (
        "https://api.worldbank.org/v2/country/"
        f"{country_code}/indicator/{indicator_code}"
        f"?date={START_YEAR}:{END_YEAR}&format=json&per_page=100"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Digital-Divide-Explorer/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not isinstance(payload, list) or len(payload) < 2:
        raise RuntimeError(
            f"Unexpected World Bank API response: {country_code}, "
            f"{indicator_code}"
        )

    result = {}
    for row in payload[1] or []:
        if row.get("value") is not None:
            result[int(row["date"])] = float(row["value"])

    return result


def main():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    updated_countries = {}

    for name, code in COUNTRIES.items():
        print(f"Downloading data for {name} ({code})...")

        internet = fetch_indicator(code, INDICATORS["internet_pct"])
        gdp = fetch_indicator(code, INDICATORS["gdp_growth_pct"])
        population = fetch_indicator(code, INDICATORS["population"])

        updated_countries[name] = {
            "internet_pct": internet,
            "gdp_growth_pct": gdp,
            "internet_users": {
                year: internet[year] * population[year] / 100
                for year in internet.keys() & population.keys()
            },
        }

    # Keep every year from 2000 through the latest year with
    # internet-adoption data for at least one selected country.
    available_years = [
        year
        for country in updated_countries.values()
        for year in country["internet_pct"]
    ]

    if not available_years:
        raise RuntimeError("No internet-adoption data was returned.")

    latest_year = max(available_years)
    years = list(range(START_YEAR, latest_year + 1))

    # Convert year-indexed data into the arrays expected by index.html.
    final_countries = {}

    for name, country in updated_countries.items():
        final_countries[name] = {}

        for metric in ("internet_pct", "internet_users", "gdp_growth_pct"):
            series = country[metric]
            final_countries[name][metric] = [
                round(series[year], 4) if year in series else None
                for year in years
            ]

    dataset["years"] = years
    dataset["countries"] = final_countries
    dataset["data_source"] = (
        "World Bank World Development Indicators; "
        "internet usage indicator sourced from ITU"
    )
    dataset["last_updated"] = "Retrieved from World Bank API when script ran"

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(dataset, file, indent=2, ensure_ascii=False, allow_nan=False)

    print("\nDataset updated successfully!")
    print(f"Countries: {len(final_countries)}")
    print(f"Year range: {years[0]}–{years[-1]}")

    for name, country in final_countries.items():
        internet = country["internet_pct"]
        available = [
            (years[i], value)
            for i, value in enumerate(internet)
            if value is not None
        ]

        if available:
            year, value = available[-1]
            print(f"{name}: latest internet adoption = {value:.2f}% ({year})")
        else:
            print(f"{name}: no internet-adoption observations")


if __name__ == "__main__":
    main()
