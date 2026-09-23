# World Wired — Digital Divide Explorer

A small, real-data dashboard comparing internet adoption and income growth
across six countries (Brazil, China, Egypt, Ethiopia, Chile, Colombia) from
2000–2024. Built as a simple, self-contained "big data" style project: pull
public indicators, ship a clean interactive front end, keep the pipeline
reproducible.

**Live demo:** open `index.html` via a local server or GitHub Pages (see below).

## What it shows

Three real indicators, per country, per year:

| Metric | Source |
|---|---|
| Internet users (% of population) | ITU / World Bank WDI, via Our World in Data |
| Internet users (absolute count) | ITU/World Bank + UN population data, via Our World in Data |
| GDP per capita growth (annual %) | National accounts / World Bank staff estimates, via Our World in Data |

Full citations and source URLs are in `data/dataset.json` under `meta.sources`.
All data is CC BY 4.0.

## Project structure

```
.
├── index.html              # the dashboard (vanilla JS + Chart.js via CDN)
├── data/
│   └── dataset.json        # the actual dataset the page reads
├── scripts/
│   └── fetch_data.py       # re-pulls fresh data from Our World in Data
└── README.md
```

## Running it locally

Browsers block `fetch()` of local JSON files opened via `file://`, so serve
the folder instead of double-clicking `index.html`:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Updating the data

```bash
pip install pandas requests
python3 scripts/fetch_data.py
```

This rewrites `data/dataset.json` with the latest available values for the
countries listed in `scripts/fetch_data.py`. Add or remove countries there —
just match the country name spelling used in the Our World in Data CSVs
(their "Entity" column).

## Putting this on GitHub

```bash
git init
git add .
git commit -m "Initial commit: Digital Divide Explorer"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

Then, to host it for free with GitHub Pages: go to the repo's **Settings →
Pages**, set the source branch to `main` and folder to `/ (root)`, save, and
GitHub will give you a public URL in a minute or two.

## Ideas to extend it

- Add more countries or years by editing `scripts/fetch_data.py`.
- Add a fourth indicator (mobile subscriptions, electricity access, literacy).
- Compute and chart a "digital divide gap" — the spread between the richest
  and poorest country's internet adoption each year.
- Deploy `scripts/fetch_data.py` as a scheduled GitHub Action so the dataset
  refreshes automatically.

## License

Code in this repo: MIT (see `LICENSE`). Data: CC BY 4.0, attributed to
Our World in Data / World Bank as noted in `data/dataset.json`.
