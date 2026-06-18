"""Mercado Libre (Mexico / site MLM) source — REAL data via the public search API.

Endpoint: ``GET https://api.mercadolibre.com/sites/MLM/search?q=<query>&limit=N``.
Search is normally public; if the API answers 401 and a token is in the
environment, the request is retried with a bearer token. For offline tests/CLI
runs, set ``ANALYZER_ML_FIXTURE_DIR`` to a directory containing
``<niche_id>.json`` raw search responses.
"""
import json
import os
import statistics
from urllib.parse import quote_plus

from analyzer.base import NicheMetrics, Source
from analyzer.http import fetch_json


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
        """Return ``(status, data)`` for a niche, honoring the offline fixture dir."""
        fixture_dir = os.environ.get(self.fixture_dir_env)
        if fixture_dir:
            path = os.path.join(fixture_dir, f"{niche['id']}.json")
            if os.path.exists(path):
                with open(path) as f:
                    return 200, json.load(f)
        url = (f"https://api.mercadolibre.com/sites/{self.site}/search"
               f"?q={quote_plus(niche['query'])}&limit={self.limit}")
        status, data = fetch_json(url, transport=self.transport, cache_dir=self.cache_dir)
        if status == 401:  # search may require auth; retry with a bearer token if present
            token = os.environ.get(self.token_env)
            if token:
                status, data = fetch_json(
                    url, headers={"Authorization": f"Bearer {token}"},
                    transport=self.transport, cache_dir=self.cache_dir)
        return status, data

    def analyze_niche(self, niche):
        status, data = self._load(niche)
        if status != 200 or not isinstance(data, dict):
            return NicheMetrics(
                niche_id=niche["id"], source=self.name, provenance=self.provenance,
                notes=f"Mercado Libre request failed (status {status}); no data.")
        results = data.get("results") or []
        total = (data.get("paging") or {}).get("total")
        prices = [r["price"] for r in results
                  if isinstance(r.get("price"), (int, float)) and not isinstance(r.get("price"), bool)]
        sold = sum(r.get("sold_quantity") or 0 for r in results)
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
            total_sold=sold if results else None,
            price_median_mxn=statistics.median(prices) if prices else None,
            price_min_mxn=min(prices) if prices else None,
            price_max_mxn=max(prices) if prices else None,
            top_seller_share=top_share,
            notes=(f"{len(results)} listings sampled. Mercado Libre's public API "
                   f"may report sold_quantity as 0 or omit it."),
        )
