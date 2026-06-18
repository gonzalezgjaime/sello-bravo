# MX Market Analyzer

Pluggable, stdlib-only Python tool that ranks Mexican marketplace niches into an
opportunity matrix. It pulls **real Mercado Libre (MX / site `MLM`) data** and
combines it with MX seasonality (and, later, Amazon SP-API) to score niches on
**demand, competition, margin, and seasonality**. It is the analyst behind the
Stream-A pick and doubles as the web app's backend engine.

## Run

```bash
# Live (real Mercado Libre data):
python3 -m analyzer.cli analyzer/niches.json            # -> market-report.md

# Offline (canned responses; CI / deterministic):
ANALYZER_ML_FIXTURE_DIR=path/to/fixtures \
  python3 -m analyzer.cli analyzer/niches.json --month 6
```

`niches.json` entries: `{id, name, query, product_type, pod_base_cost_mxn, ship_mxn}`.
Scoring weights live in `analyzer/config.json` (single source of truth).

## Architecture

`Source` adapters (`analyzer/sources/`) each measure one niche → `NicheMetrics`;
`synthesize.py` merges them (REAL preferred over EST), min-max normalizes, and
weights into ranked `OpportunityScore`s; `report.py` renders `market-report.md`.
HTTP goes through `http.py` (injectable transport → tests never hit the network).

## Adding a source (no rewrite)

Implement `analyzer.base.Source.analyze_niche(niche) -> NicheMetrics`, set
`provenance` (`REAL`/`EST`), and add it to `cli.build_sources`. Planned next:
`amazon_spapi.py` (replaces the EST `amazon_research.py` once a seller account
exists), `etsy.py`, and live Google Trends.

## Tests

`python3 -m unittest discover -s tests` — adapters are tested with injected canned
JSON; the CLI integration test runs fully offline via `ANALYZER_ML_FIXTURE_DIR`.
