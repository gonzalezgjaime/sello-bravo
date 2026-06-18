"""CLI: ``python3 -m analyzer.cli analyzer/niches.json`` -> writes market-report.md.

Exit codes: 0 success, 1 on input load failure (missing/garbled niches or config).
For offline runs, set ``ANALYZER_ML_FIXTURE_DIR`` so the Mercado Libre source
reads canned ``<niche_id>.json`` responses instead of calling the network.
"""
import argparse
import datetime
import json
import os
import sys

from analyzer.report import render_report
from analyzer.sources.amazon_research import AmazonResearchSource
from analyzer.sources.mercadolibre import MercadoLibreSource
from analyzer.sources.seasonality import SeasonalitySource
from analyzer.synthesize import synthesize


def _current_month():
    return datetime.date.today().month


def build_sources(config, month, cache_dir=None):
    return [
        MercadoLibreSource(site=config.get("site", "MLM"),
                           limit=config.get("ml_search_limit", 50),
                           cache_dir=cache_dir),
        AmazonResearchSource(),
        SeasonalitySource(month=month),
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Rank Mexican marketplace niches into an opportunity matrix.")
    parser.add_argument("niches", help="Path to niches.json")
    parser.add_argument(
        "--config", default=os.path.join(os.path.dirname(__file__), "config.json"))
    parser.add_argument("--out", default="market-report.md")
    parser.add_argument("--month", type=int, default=None,
                        help="1-12; defaults to the current month")
    parser.add_argument("--cache-dir", default=None,
                        help="Cache directory for marketplace API responses")
    args = parser.parse_args(argv)

    try:
        with open(args.config) as f:
            config = json.load(f)
        with open(args.niches) as f:
            niches = json.load(f)["niches"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Failed to load inputs: {exc}", file=sys.stderr)
        return 1

    month = args.month or _current_month()
    sources = build_sources(config, month, cache_dir=args.cache_dir)

    metrics_by_niche = {}
    for niche in niches:
        metrics_by_niche[niche["id"]] = [s.analyze_niche(niche) for s in sources]

    scores = synthesize(metrics_by_niche, niches, config)
    with open(args.out, "w") as f:
        f.write(render_report(scores, niches, config, month))
    real = sum(1 for s in scores if s.provenance == "REAL")
    print(f"Wrote {args.out}: {len(scores)} niches ranked, {real} with REAL data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
