"""Mercado Libre (Mexico / site MLM) source — REAL data via the search API.

Endpoint: ``GET https://api.mercadolibre.com/sites/MLM/search?q=<query>&limit=N``.

2026 reality (validated live): the public host now answers **403** (PolicyAgent)
to unauthenticated requests — anonymous search no longer works. Real data
therefore requires an OAuth app token in ``ML_TOKEN`` (create a free Mercado
Libre developer app). Without a token the source degrades honestly: every niche
returns no measured data and provenance ``EST`` (it is *not* labelled REAL when
nothing was measured), and the report flags the run as having no real data.

For offline tests/CLI runs, set ``ANALYZER_ML_FIXTURE_DIR`` to a directory of
``<niche_id>.json`` raw search responses. In fixture mode a missing file is a
hard offline miss (status 404) — the network is never touched.

Note on demand: Mercado Libre has stripped ``sold_quantity`` from public search
for most items. When no sampled listing reports it, ``total_sold`` is ``None``
(unmeasured), not ``0`` — so the synthesizer treats demand as neutral rather than
maxing it out.
"""
import json
import os
import statistics
from urllib.parse import quote_plus

from analyzer.base import NicheMetrics, Source
from analyzer.http import fetch_json

AUTH_REQUIRED_STATUSES = (401, 403)


class MercadoLibreSource(Source):
    name = "mercadolibre"
    provenance = "REAL"

    def __init__(self, site="MLM", limit=50, transport=None, cache_dir=None,
                 token_env="ML_TOKEN", fixture_dir_env="ANALYZER_ML_FIXTURE_DIR"):
        self.site = site
        self.limit = limit
        self.transport = transport
        self.cache_dir = cache_dir
        self.token_env = token_env
        self.fixture_dir_env = fixture_dir_env

    def _load(self, niche):
        """Return ``(status, data)``. In fixture mode the network is never used."""
        fixture_dir = os.environ.get(self.fixture_dir_env)
        if fixture_dir is not None:
            path = os.path.join(fixture_dir, f"{niche['id']}.json")
            if os.path.exists(path):
                with open(path) as f:
                    return 200, json.load(f)
            return 404, None  # offline mode: a miss never falls through to the network
        url = (f"https://api.mercadolibre.com/sites/{self.site}/search"
               f"?q={quote_plus(niche['query'])}&limit={self.limit}")
        status, data = fetch_json(url, transport=self.transport, cache_dir=self.cache_dir)
        if status in AUTH_REQUIRED_STATUSES:  # 2026: search needs an app token
            token = os.environ.get(self.token_env)
            if token:
                status, data = fetch_json(
                    url, headers={"Authorization": f"Bearer {token}"},
                    transport=self.transport, cache_dir=self.cache_dir)
        return status, data

    def analyze_niche(self, niche):
        status, data = self._load(niche)
        if status != 200 or not isinstance(data, dict):
            hint = ""
            if status in AUTH_REQUIRED_STATUSES:
                hint = (" Mercado Libre search now requires an OAuth app token; "
                        f"set {self.token_env} (free developer app).")
            # No data measured -> provenance EST, not REAL.
            return NicheMetrics(
                niche_id=niche["id"], source=self.name, provenance="EST",
                notes=f"Mercado Libre request failed (status {status}); no data.{hint}")

        results = data.get("results") or []
        total = (data.get("paging") or {}).get("total")
        prices = [r["price"] for r in results
                  if isinstance(r.get("price"), (int, float))
                  and not isinstance(r.get("price"), bool)
                  and r.get("currency_id") in (None, "MXN")]
        # Distinguish "no demand signal" (sold_quantity stripped) from "sold 0".
        sold_present = [r["sold_quantity"] for r in results
                        if isinstance(r.get("sold_quantity"), int)
                        and not isinstance(r.get("sold_quantity"), bool)]
        total_sold = sum(sold_present) if sold_present else None
        seller_ids = [str((r.get("seller") or {}).get("id")) for r in results
                      if (r.get("seller") or {}).get("id") is not None]
        top_share = None
        if seller_ids:
            counts = {}
            for sid in seller_ids:
                counts[sid] = counts.get(sid, 0) + 1
            top_share = round(max(counts.values()) / len(seller_ids), 3)
        return NicheMetrics(
            niche_id=niche["id"], source=self.name, provenance=self.provenance,
            listing_count=total,
            total_sold=total_sold,
            price_median_mxn=statistics.median(prices) if prices else None,
            price_min_mxn=min(prices) if prices else None,
            price_max_mxn=max(prices) if prices else None,
            top_seller_share=top_share,
            notes=(f"{len(results)} listings sampled. Mercado Libre's public API "
                   f"typically omits sold_quantity, so demand is often unmeasured."),
        )
