"""Combine per-source NicheMetrics into ranked OpportunityScores. Deterministic.

Rule: REAL signals are preferred over EST. For each niche we pick the first REAL
``total_sold`` (demand), REAL ``listing_count`` (competition), and REAL
``price_median_mxn`` (for margin); seasonality comes from whichever source
provides it.

Missing-data policy (uniform across demand/competition/margin): a value that was
**not measured** for a niche, or a dimension that is **uninformative** (every
niche has the same value), normalizes to a NEUTRAL 0.5 — never to best or worst.
This stops data-less niches from being rewarded (missing competition) or punished
(missing demand), and stops a dead/constant signal (e.g. Mercado Libre's stripped
``sold_quantity``) from silently maxing out the score. Competition contributes
inverted (less competition = higher). Ties break by ``niche_id`` ascending.
"""
from analyzer.base import OpportunityScore

DIMENSIONS = ("demand", "competition", "margin", "seasonality")
NEUTRAL = 0.5  # score for a missing or uninformative (all-equal) dimension


def _normalize(items):
    """Min-max normalize ``[(id, value|None), ...]`` -> ``{id: 0..1}``.

    Missing values (None) and uninformative series (all measured values equal)
    map to ``NEUTRAL`` (0.5), so absence/constancy is neither rewarded nor
    punished. Only genuinely-measured, varying values span the full 0..1 range.
    """
    measured = [v for _, v in items if v is not None]
    if not measured:
        return {i: NEUTRAL for i, _ in items}
    lo, hi = min(measured), max(measured)
    span = hi - lo
    out = {}
    for i, v in items:
        if v is None or span == 0:
            out[i] = NEUTRAL
        else:
            out[i] = (v - lo) / span
    return out


def _first_real(metrics, attr):
    """First non-None value of ``attr`` among the niche's REAL-provenance metrics."""
    for m in metrics:
        if m.provenance == "REAL" and getattr(m, attr) is not None:
            return getattr(m, attr)
    return None


def synthesize(metrics_by_niche, niches, config):
    """``metrics_by_niche``: ``{niche_id: [NicheMetrics, ...]}``. Returns ranked list."""
    niche_by_id = {n["id"]: n for n in niches}
    weights = config["weights"]

    demand, competition, margin, season, prov, raw = {}, {}, {}, {}, {}, {}
    for nid, metrics in metrics_by_niche.items():
        niche = niche_by_id[nid]
        d_real = _first_real(metrics, "total_sold")
        c_real = _first_real(metrics, "listing_count")
        price = _first_real(metrics, "price_median_mxn")
        top_share = next((m.top_seller_share for m in metrics
                          if m.top_seller_share is not None), None)
        s_fit = next((m.seasonality_fit for m in metrics
                      if m.seasonality_fit is not None), None)

        cost = (niche.get("pod_base_cost_mxn") or 0) + (niche.get("ship_mxn") or 0)
        unit_margin = (price - cost) if price is not None else None

        demand[nid] = d_real
        competition[nid] = c_real
        margin[nid] = unit_margin
        season[nid] = s_fit if s_fit is not None else NEUTRAL
        prov[nid] = "REAL" if (d_real is not None or c_real is not None
                               or price is not None) else "EST"
        raw[nid] = {
            "listing_count": c_real, "total_sold": d_real,
            "price_median_mxn": price, "unit_margin_mxn": unit_margin,
            "top_seller_share": top_share, "seasonality_fit": s_fit,
        }

    dn = _normalize(list(demand.items()))
    cn = _normalize(list(competition.items()))   # higher = more competition
    mn = _normalize(list(margin.items()))

    wsum = sum(weights[d] for d in DIMENSIONS)
    scores = []
    for nid in metrics_by_niche:
        comp_inv = 1.0 - cn[nid]
        s = 100.0 * (weights["demand"] * dn[nid]
                     + weights["competition"] * comp_inv
                     + weights["margin"] * mn[nid]
                     + weights["seasonality"] * season[nid]) / wsum
        scores.append(OpportunityScore(
            niche_id=nid, niche_name=niche_by_id[nid].get("name", nid),
            score=round(s, 1), provenance=prov[nid],
            demand_n=round(dn[nid], 3), competition_n=round(cn[nid], 3),
            margin_n=round(mn[nid], 3), seasonality=round(season[nid], 3),
            margin_mxn=margin[nid], detail=raw[nid]))
    scores.sort(key=lambda s: (-s.score, s.niche_id))
    return scores
