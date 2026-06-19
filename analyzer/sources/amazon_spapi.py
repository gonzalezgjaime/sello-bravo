"""Amazon Mexico source via the Selling Partner API (SP-API). Stdlib only.

As of 2023+ SP-API no longer requires AWS SigV4 — authentication is a
Login-with-Amazon (LWA) access token sent in the ``x-amz-access-token`` header.
So this adapter is pure ``urllib``:

  1. mint an LWA access token from a refresh token
     (POST https://api.amazon.com/auth/o2/token, grant_type=refresh_token), then
  2. call Catalog Items ``searchCatalogItems`` for the niche keyword.

It contributes Amazon-MX **catalog breadth** (``numberOfResults``) as a competition
proxy and records the best MX sales rank (BSR) as context. Caveats kept honest:
- ``numberOfResults`` is, per Amazon's docs, an *estimated* count of catalog items
  matching the keyword — NOT a count of live offers/sellers. It is a coarse
  competition/breadth signal, not the live-listing count Mercado Libre gives.
- Catalog search exposes neither units-sold nor current price, so demand/price are
  left unmeasured (None) — enrich later with the Product Pricing API.
- The NA endpoint serves US/CA/MX/BR, so sales ranks are filtered to the MX
  marketplace before use.

The CLI activates this source only when LWA credentials are present
(``AmazonSpApiSource.from_env``); otherwise it uses the EST ``AmazonResearchSource``.
Credentials (env): ``AMZ_LWA_CLIENT_ID``, ``AMZ_LWA_CLIENT_SECRET``,
``AMZ_SPAPI_REFRESH_TOKEN``. Marketplace: Mexico = ``A1AM78C64UM0Y8`` (NA region).
``searchCatalogItems`` needs the app's "Product Listing" role; a missing role
surfaces as a 401/403 whose SP-API error is included in the EST note.

NOTE: structurally complete and unit-tested against canned responses, but not yet
validated against a live seller account (pending SP-API authorization).
"""
import os
from urllib.parse import quote_plus

from analyzer.base import NicheMetrics, Source
from analyzer.http import fetch_json, post_form

LWA_TOKEN_URL = "https://api.amazon.com/auth/o2/token"
SPAPI_HOST = "https://sellingpartnerapi-na.amazon.com"
MX_MARKETPLACE_ID = "A1AM78C64UM0Y8"


class AmazonSpApiSource(Source):
    name = "amazon_spapi"
    provenance = "REAL"

    def __init__(self, client_id, client_secret, refresh_token,
                 marketplace_id=MX_MARKETPLACE_ID, limit=20,
                 transport=None, post_transport=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.marketplace_id = marketplace_id
        self.limit = limit
        self.transport = transport            # catalog GET transport (tests)
        self.post_transport = post_transport  # LWA POST transport (tests)
        self._cached_token = None             # reused across niches within a run

    @classmethod
    def from_env(cls, **kwargs):
        """Return a configured source if all LWA env vars are set, else ``None``."""
        cid = os.environ.get("AMZ_LWA_CLIENT_ID")
        secret = os.environ.get("AMZ_LWA_CLIENT_SECRET")
        rt = os.environ.get("AMZ_SPAPI_REFRESH_TOKEN")
        if cid and secret and rt:
            return cls(cid, secret, rt, **kwargs)
        return None

    def _access_token(self):
        if self._cached_token:  # LWA tokens last ~1h; a CLI run is seconds
            return self._cached_token
        status, data = post_form(LWA_TOKEN_URL, {
            "grant_type": "refresh_token", "refresh_token": self.refresh_token,
            "client_id": self.client_id, "client_secret": self.client_secret,
        }, transport=self.post_transport)
        if status == 200 and isinstance(data, dict):
            self._cached_token = data.get("access_token")
        return self._cached_token

    def _best_mx_sales_rank(self, items):
        ranks = []
        for item in items:
            for sr in (item.get("salesRanks") or []):
                if sr.get("marketplaceId") not in (None, self.marketplace_id):
                    continue  # NA endpoint serves US/CA/BR too — keep MX only
                for group in ("classificationRanks", "displayGroupRanks"):
                    for r in (sr.get(group) or []):
                        rank = r.get("rank")
                        if isinstance(rank, int) and not isinstance(rank, bool):
                            ranks.append(rank)
        return min(ranks) if ranks else None

    @staticmethod
    def _error_detail(data):
        if isinstance(data, dict):
            errs = data.get("errors")
            if isinstance(errs, list) and errs and isinstance(errs[0], dict):
                return f" ({errs[0].get('code')}: {errs[0].get('message')})"
        return ""

    def analyze_niche(self, niche):
        token = self._access_token()
        if not token:
            return NicheMetrics(
                niche_id=niche["id"], source=self.name, provenance="EST",
                notes="SP-API LWA token request failed; no Amazon data. Check credentials.")
        url = (f"{SPAPI_HOST}/catalog/2022-04-01/items"
               f"?keywords={quote_plus(niche['query'])}"
               f"&marketplaceIds={self.marketplace_id}"
               f"&includedData=salesRanks,summaries&pageSize={self.limit}")
        status, data = fetch_json(url, headers={"x-amz-access-token": token},
                                  transport=self.transport)
        if status != 200 or not isinstance(data, dict):
            return NicheMetrics(
                niche_id=niche["id"], source=self.name, provenance="EST",
                notes=(f"SP-API catalog response not usable (status {status})"
                       f"{self._error_detail(data)}; no Amazon data."))
        items = data.get("items") or []
        best_rank = self._best_mx_sales_rank(items)
        return NicheMetrics(
            niche_id=niche["id"], source=self.name, provenance=self.provenance,
            listing_count=data.get("numberOfResults"),  # estimated catalog matches
            notes=(f"{len(items)} catalog matches sampled; best MX BSR "
                   f"{best_rank if best_rank is not None else 'n/a'}. listing_count is "
                   f"Amazon's ESTIMATED catalog-match count (not live offers); "
                   f"demand/price unmeasured (use the Pricing API)."),
        )
