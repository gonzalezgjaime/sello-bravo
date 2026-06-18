"""Render ranked OpportunityScores to a markdown market report."""


def _fmt(value, suffix=""):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:,.0f}{suffix}" if abs(value) >= 100 else f"{value:.2f}{suffix}"
    return f"{value:,}{suffix}"


def _margin_cell(margin):
    """Format a unit margin, flagging non-positive (loss-making) margins."""
    if margin is None:
        return "-"
    flag = " (loss)" if margin <= 0 else ""
    return f"{_fmt(margin)}{flag}"


def render_report(scores, niches, config, month):
    real = sum(1 for s in scores if s.provenance == "REAL")
    lines = ["# MX Market Opportunity Report", ""]
    lines.append(f"_Site: Mercado Libre {config.get('site', 'MLM')} - month: {month} - "
                 f"{len(scores)} niches - {real} with REAL marketplace data._")

    if real == 0:
        lines += [
            "",
            "> **WARNING - no REAL marketplace data this run.** Every niche fell back "
            "to EST, so the ranking is driven only by MX seasonality and a "
            "price-minus-cost margin guess, *not* by live demand/competition. Connect "
            "Mercado Libre (set `ML_TOKEN` from a developer app) for real signals.",
        ]

    lines += ["",
              "| Rank | Niche | Score | Demand | Comp. | Margin (MXN) | Season | Data |",
              "|---|---|--:|--:|--:|--:|--:|---|"]
    for i, s in enumerate(scores, 1):
        lines.append(
            f"| {i} | {s.niche_name} | {s.score} | {s.demand_n} | {s.competition_n} | "
            f"{_margin_cell(s.margin_mxn)} | {s.seasonality} | {s.provenance} |")

    lines += ["", "## Top niches - detail"]
    for s in scores[:5]:
        d = s.detail
        lines += [
            "",
            f"### {s.niche_name}  (score {s.score} - {s.provenance})",
            f"- Listings (competition): {_fmt(d.get('listing_count'))}",
            f"- Units sold (sampled demand): {_fmt(d.get('total_sold'))}",
            f"- Median price: {_fmt(d.get('price_median_mxn'))} MXN - "
            f"est. unit margin: {_margin_cell(d.get('unit_margin_mxn'))} MXN",
            f"- Top-seller share of sampled listings: {_fmt(d.get('top_seller_share'))}",
            f"- Seasonality fit (month {month}): {s.seasonality}",
        ]

    lines += [
        "", "## Data provenance & caveats",
        "- **REAL** = live Mercado Libre (MX / site MLM) search data. **EST** = "
        "estimated (no real measured data for that niche).",
        "- Mercado Libre's public API now requires an OAuth app token and typically "
        "omits `sold_quantity`; when demand is unmeasured it is treated as neutral "
        "(not zero, not max), so a blank demand does not inflate or sink a niche.",
        "- Mixed granularity: **competition** is the whole-marketplace listing count "
        "(`paging.total`), while **demand, price, and top-seller share** come only "
        "from the sampled top `limit` results. Top-seller share is sampled "
        "concentration, not true market share.",
        "- Amazon MX is EST-only until an SP-API seller account is connected; it does "
        "not yet contribute to scores.",
        "- Missing or uninformative (all-equal) signals normalize to a neutral 0.5; "
        "only genuinely-varying measured values span the full range. Scores are "
        "relative to the niches in this run; adding/removing niches re-scales them.",
    ]
    return "\n".join(lines) + "\n"
