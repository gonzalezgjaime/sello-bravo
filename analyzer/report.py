"""Render ranked OpportunityScores to a markdown market report."""


def _fmt(value, suffix=""):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:,.0f}{suffix}" if abs(value) >= 100 else f"{value:.2f}{suffix}"
    return f"{value:,}{suffix}"


def render_report(scores, niches, config, month):
    real = sum(1 for s in scores if s.provenance == "REAL")
    lines = ["# MX Market Opportunity Report", ""]
    lines.append(f"_Site: Mercado Libre {config.get('site', 'MLM')} - month: {month} - "
                 f"{len(scores)} niches - {real} with REAL marketplace data._")
    lines += ["",
              "| Rank | Niche | Score | Demand | Comp. | Margin (MXN) | Season | Data |",
              "|---|---|--:|--:|--:|--:|--:|---|"]
    for i, s in enumerate(scores, 1):
        lines.append(
            f"| {i} | {s.niche_name} | {s.score} | {s.demand_n} | {s.competition_n} | "
            f"{_fmt(s.margin_mxn)} | {s.seasonality} | {s.provenance} |")

    lines += ["", "## Top niches - detail"]
    for s in scores[:5]:
        d = s.detail
        lines += [
            "",
            f"### {s.niche_name}  (score {s.score} - {s.provenance})",
            f"- Listings (competition): {_fmt(d.get('listing_count'))}",
            f"- Units sold (sampled demand): {_fmt(d.get('total_sold'))}",
            f"- Median price: {_fmt(d.get('price_median_mxn'))} MXN - "
            f"est. unit margin: {_fmt(d.get('unit_margin_mxn'))} MXN",
            f"- Top-seller share of sampled listings: {_fmt(d.get('top_seller_share'))}",
            f"- Seasonality fit (month {month}): {s.seasonality}",
        ]

    lines += [
        "", "## Data provenance & caveats",
        "- **REAL** = live Mercado Libre (MX / site MLM) search data. **EST** = "
        "estimated (no real measured data for that niche).",
        "- Mercado Libre's public API may report `sold_quantity` as 0 or omit it; "
        "treat 'units sold' as a relative signal, not an absolute.",
        "- Amazon MX is EST-only until an SP-API seller account is connected; it does "
        "not yet contribute to scores.",
        "- Scores are min-max normalized across the niches in this run; adding or "
        "removing niches re-scales them.",
    ]
    return "\n".join(lines) + "\n"
