"""CLI: ``python3 -m analyzer.cli analyzer/niches.json`` -> writes market-report.md.

Exit codes: 0 success; 1 on bad input (missing/garbled files, malformed niches,
out-of-range ``--month``); 3 when ``--strict`` is set and no niche yielded REAL
marketplace data. For offline runs, set ``ANALYZER_ML_FIXTURE_DIR`` so the Mercado
Libre source reads canned ``<niche_id>.json`` responses instead of the network.
"""
import argparse
import datetime
import json
import os
import sys

from analyzer.report import render_report
from analyzer.sources.amazon_research import AmazonResearchSource
from analyzer.sources.amazon_spapi import AmazonSpApiSource
from analyzer.sources.mercadolibre import MercadoLibreSource
from analyzer.sources.seasonality import SeasonalitySource
from analyzer.synthesize import synthesize

REQUIRED_NICHE_KEYS = ("id", "name", "query", "pod_base_cost_mxn", "ship_mxn")


def _current_month():
    return datetime.date.today().month


def _validate_niches(niches):
    """Raise ValueError with a clear message if any niche entry is malformed."""
    if not isinstance(niches, list) or not niches:
        raise ValueError("'niches' must be a non-empty list")
    seen = set()
    for i, niche in enumerate(niches):
        if not isinstance(niche, dict):
            raise ValueError(f"niche[{i}] must be an object")
        missing = [k for k in REQUIRED_NICHE_KEYS if k not in niche]
        if missing:
            raise ValueError(f"niche[{i}] ({niche.get('id', '?')}) missing keys: {missing}")
        if niche["id"] in seen:
            raise ValueError(f"duplicate niche id: {niche['id']}")
        seen.add(niche["id"])


def build_sources(config, month, cache_dir=None):
    # Real Amazon-MX data when SP-API credentials are configured; else EST.
    amazon = AmazonSpApiSource.from_env() or AmazonResearchSource()
    return [
        MercadoLibreSource(site=config.get("site", "MLM"),
                           limit=config.get("ml_search_limit", 50),
                           cache_dir=cache_dir),
        amazon,
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
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero (3) if no niche yields REAL data")
    args = parser.parse_args(argv)

    month = args.month if args.month is not None else _current_month()
    if not 1 <= month <= 12:
        print(f"--month must be 1-12, got {month}", file=sys.stderr)
        return 1

    try:
        with open(args.config) as f:
            config = json.load(f)
        with open(args.niches) as f:
            niches = json.load(f)["niches"]
        _validate_niches(niches)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Failed to load inputs: {exc}", file=sys.stderr)
        return 1

    sources = build_sources(config, month, cache_dir=args.cache_dir)
    metrics_by_niche = {
        niche["id"]: [s.analyze_niche(niche) for s in sources] for niche in niches
    }
    scores = synthesize(metrics_by_niche, niches, config)
    with open(args.out, "w") as f:
        f.write(render_report(scores, niches, config, month))

    real = sum(1 for s in scores if s.provenance == "REAL")
    print(f"Wrote {args.out}: {len(scores)} niches ranked, {real} with REAL data.")
    if real == 0:
        print("WARNING: no REAL marketplace data this run (all niches fell back to "
              "EST). Set ML_TOKEN for live Mercado Libre data.", file=sys.stderr)
        if args.strict:
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
