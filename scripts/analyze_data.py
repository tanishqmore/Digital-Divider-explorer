
"""
World Wired — Statistical Analysis and Internet Adoption Forecasts

Reads:
    data/dataset.json

Writes:
    data/analytics.json

Run from the repository root:
    py scripts/analyze_data.py
"""

import json
import math
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error


ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = ROOT / "data" / "dataset.json"
OUTPUT_FILE = ROOT / "data" / "analytics.json"

FORECAST_YEARS = 5
TEST_YEARS = 5


def valid_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def pearson_correlation(pairs):
    """Calculate Pearson correlation from paired numeric observations."""
    if len(pairs) < 3:
        return None

    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]

    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)

    numerator = sum(
        (x - mean_x) * (y - mean_y)
        for x, y in zip(xs, ys)
    )

    denominator_x = math.sqrt(
        sum((x - mean_x) ** 2 for x in xs)
    )
    denominator_y = math.sqrt(
        sum((y - mean_y) ** 2 for y in ys)
    )

    denominator = denominator_x * denominator_y

    if denominator == 0:
        return None

    return numerator / denominator


def analyze_country(years, country_data):
    internet = country_data["internet_pct"]
    gdp = country_data["gdp_growth_pct"]

    observations = [
        (year, internet[index])
        for index, year in enumerate(years)
        if index < len(internet) and valid_number(internet[index])
    ]

    # Measure whether annual changes in internet adoption
    # move with annual GDP-per-capita growth.
    change_gdp_pairs = []

    for index in range(1, min(len(years), len(internet), len(gdp))):
        previous = internet[index - 1]
        current = internet[index]
        growth = gdp[index]

        if all(valid_number(v) for v in (previous, current, growth)):
            annual_change = current - previous
            change_gdp_pairs.append((annual_change, growth))

    correlation = pearson_correlation(change_gdp_pairs)

    result = {
        "correlation": {
            "method": "Pearson correlation",
            "variables": [
                "Annual change in internet adoption (percentage points)",
                "GDP per capita growth (annual percent)"
            ],
            "value": correlation,
            "observations": len(change_gdp_pairs)
        },
        "forecast": {
            "target": "Internet users (% of population)",
            "years": [],
            "values": [],
            "method": "Linear Regression",
            "evaluation": None
        }
    }

    if len(observations) < 8:
        result["forecast"]["status"] = (
            "Insufficient historical observations for forecasting."
        )
        return result

    # Hold out the last five available observations for evaluation.
    # The model is evaluated on years it did not train on.
    test_size = min(TEST_YEARS, max(1, len(observations) // 4))
    train = observations[:-test_size]
    test = observations[-test_size:]

    if len(train) < 3:
        result["forecast"]["status"] = (
            "Insufficient training observations."
        )
        return result

    train_x = [[year] for year, _ in train]
    train_y = [value for _, value in train]
    test_x = [[year] for year, _ in test]
    test_y = [value for _, value in test]

    evaluation_model = LinearRegression()
    evaluation_model.fit(train_x, train_y)
    predictions = evaluation_model.predict(test_x)

    mae = mean_absolute_error(test_y, predictions)
    rmse = math.sqrt(mean_squared_error(test_y, predictions))

    # Refit using all available historical observations.
    final_model = LinearRegression()
    final_model.fit(
        [[year] for year, _ in observations],
        [value for _, value in observations]
    )

    last_year = max(year for year, _ in observations)
    future_years = list(
        range(last_year + 1, last_year + FORECAST_YEARS + 1)
    )
    raw_predictions = final_model.predict(
        [[year] for year in future_years]
    )

    # Internet adoption is a percentage, so constrain predictions
    # to the valid 0–100 range. This does not guarantee accuracy.
    future_values = [
        round(max(0.0, min(100.0, float(value))), 2)
        for value in raw_predictions
    ]

    result["forecast"].update({
        "status": "ok",
        "years": future_years,
        "values": future_values,
        "evaluation": {
            "test_years": [year for year, _ in test],
            "mae_percentage_points": round(float(mae), 3),
            "rmse_percentage_points": round(float(rmse), 3),
            "training_observations": len(train),
            "testing_observations": len(test)
        }
    })

    return result


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {INPUT_FILE}"
        )

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    years = dataset["years"]
    countries = dataset["countries"]

    results = {}
    all_pairs = []

    for country, values in countries.items():
        results[country] = analyze_country(years, values)

        internet = values["internet_pct"]
        gdp = values["gdp_growth_pct"]

        for index in range(
            1, min(len(years), len(internet), len(gdp))
        ):
            previous = internet[index - 1]
            current = internet[index]
            growth = gdp[index]

            if all(valid_number(v) for v in (previous, current, growth)):
                all_pairs.append((current - previous, growth))

    output = {
        "meta": {
            "title": "World Wired Analytics",
            "source_dataset": "dataset.json",
            "forecast_method": "Scikit-learn LinearRegression",
            "forecast_horizon_years": FORECAST_YEARS,
            "correlation_method": (
                "Pearson correlation between annual internet-adoption "
                "change and GDP per capita growth"
            ),
            "note": (
                "Forecasts are experimental trend estimates, not guarantees. "
                "Correlation does not establish causation."
            )
        },
        "aggregate": {
            "internet_change_vs_gdp_growth": {
                "value": pearson_correlation(all_pairs),
                "observations": len(all_pairs)
            }
        },
        "countries": results
    }

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, allow_nan=False)

    print(f"Analytics written to: {OUTPUT_FILE}")
    print(f"Countries analyzed: {len(results)}")

    aggregate = output["aggregate"]["internet_change_vs_gdp_growth"]
    correlation = aggregate["value"]

    if correlation is None:
        print("Aggregate correlation: unavailable")
    else:
        print(f"Aggregate correlation: {correlation:.3f}")

    for country, result in results.items():
        forecast = result["forecast"]
        evaluation = forecast["evaluation"]

        if evaluation:
            print(
                f"{country}: MAE={evaluation['mae_percentage_points']:.2f} "
                f"percentage points; "
                f"RMSE={evaluation['rmse_percentage_points']:.2f}"
            )
        else:
            print(f"{country}: {forecast['status']}")


if __name__ == "__main__":
    main()
