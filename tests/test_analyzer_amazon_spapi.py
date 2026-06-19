import json
import os
import unittest
from unittest import mock

from analyzer.sources.amazon_spapi import AmazonSpApiSource

NICHE = {"id": "n", "name": "N", "query": "taza guadalajara"}


def _catalog_body():
    return {
        "numberOfResults": 320,
        "items": [
            {"asin": "X", "salesRanks": [
                {"marketplaceId": "A1AM78C64UM0Y8",
                 "classificationRanks": [{"classificationId": "1", "rank": 1500}],
                 "displayGroupRanks": [{"websiteDisplayGroup": "g", "rank": 800}]}]},
            {"asin": "Y", "salesRanks": []},
        ],
    }


def _lwa_ok(url, data, headers):
    return 200, b'{"access_token":"AT-123","token_type":"bearer","expires_in":3600}'


def _get_ok(url, headers):
    return 200, json.dumps(_catalog_body()).encode()


class TestAmazonSpApi(unittest.TestCase):
    def test_from_env_requires_all_three_creds(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(AmazonSpApiSource.from_env())
        with mock.patch.dict(os.environ, {"AMZ_LWA_CLIENT_ID": "a",
                                          "AMZ_LWA_CLIENT_SECRET": "b",
                                          "AMZ_SPAPI_REFRESH_TOKEN": "c"}, clear=True):
            self.assertIsInstance(AmazonSpApiSource.from_env(), AmazonSpApiSource)

    def test_real_competition_and_best_mx_bsr(self):
        src = AmazonSpApiSource("a", "b", "c", transport=_get_ok, post_transport=_lwa_ok)
        m = src.analyze_niche(NICHE)
        self.assertEqual(m.provenance, "REAL")
        self.assertEqual(m.listing_count, 320)
        self.assertIn("best MX BSR 800", m.notes)   # min(1500, 800), MX only
        self.assertIn("ESTIMATED", m.notes)         # honest competition caveat
        self.assertIsNone(m.total_sold)
        self.assertIsNone(m.price_median_mxn)

    def test_sales_ranks_filtered_to_mx_marketplace(self):
        body = {"numberOfResults": 10, "items": [
            {"asin": "X", "salesRanks": [
                {"marketplaceId": "A1AM78C64UM0Y8",
                 "classificationRanks": [{"classificationId": "1", "rank": 900}]},
                {"marketplaceId": "ATVPDKIKX0DER",  # US — must be ignored
                 "classificationRanks": [{"classificationId": "1", "rank": 3}]}]}]}
        src = AmazonSpApiSource(
            "a", "b", "c", transport=lambda u, h: (200, json.dumps(body).encode()),
            post_transport=_lwa_ok)
        self.assertIn("best MX BSR 900", src.analyze_niche(NICHE).notes)

    def test_sends_lwa_token_header_targets_mx_and_caches_token(self):
        captured = {}
        post_calls = []

        def post(url, data, headers):
            post_calls.append(url)
            return _lwa_ok(url, data, headers)

        def get(url, headers):
            captured["url"], captured["headers"] = url, headers
            return _get_ok(url, headers)

        src = AmazonSpApiSource("a", "b", "c", transport=get, post_transport=post)
        src.analyze_niche(NICHE)
        src.analyze_niche({"id": "n2", "name": "N2", "query": "q2"})
        self.assertEqual(captured["headers"]["x-amz-access-token"], "AT-123")
        self.assertIn("marketplaceIds=A1AM78C64UM0Y8", captured["url"])
        self.assertIn("catalog/2022-04-01/items", captured["url"])
        self.assertEqual(len(post_calls), 1)  # LWA token minted once, reused

    def test_lwa_failure_marks_est(self):
        src = AmazonSpApiSource(
            "a", "b", "c", transport=_get_ok,
            post_transport=lambda u, d, h: (400, b'{"error":"invalid_grant"}'))
        m = src.analyze_niche(NICHE)
        self.assertEqual(m.provenance, "EST")
        self.assertIn("LWA", m.notes)

    def test_catalog_403_surfaces_sp_api_error_detail(self):
        body = b'{"errors":[{"code":"Unauthorized","message":"Access denied"}]}'
        src = AmazonSpApiSource("a", "b", "c", transport=lambda u, h: (403, body),
                                post_transport=_lwa_ok)
        m = src.analyze_niche(NICHE)
        self.assertEqual(m.provenance, "EST")
        self.assertIn("403", m.notes)
        self.assertIn("Unauthorized", m.notes)
        self.assertIn("Access denied", m.notes)

    def test_catalog_200_non_dict_is_est(self):
        src = AmazonSpApiSource("a", "b", "c", transport=lambda u, h: (200, b"[]"),
                                post_transport=_lwa_ok)
        self.assertEqual(src.analyze_niche(NICHE).provenance, "EST")

    def test_best_rank_na_when_unranked(self):
        body = {"numberOfResults": 5, "items": [{"asin": "Z", "salesRanks": []}]}
        src = AmazonSpApiSource(
            "a", "b", "c", transport=lambda u, h: (200, json.dumps(body).encode()),
            post_transport=_lwa_ok)
        m = src.analyze_niche(NICHE)
        self.assertEqual(m.listing_count, 5)
        self.assertIn("n/a", m.notes)


if __name__ == "__main__":
    unittest.main()
