import json
import os
import tempfile
import unittest
from unittest import mock

from analyzer.sources.amazon_research import AmazonResearchSource
from analyzer.sources.mercadolibre import MercadoLibreSource
from analyzer.sources.seasonality import SeasonalitySource

NICHE = {"id": "taza-x", "name": "Taza X", "query": "taza x",
         "product_type": "mug", "pod_base_cost_mxn": 75, "ship_mxn": 65}


def _ml_body():
    return {
        "paging": {"total": 1234},
        "results": [
            {"price": 199, "sold_quantity": 50, "seller": {"id": 1}},
            {"price": 149, "sold_quantity": 10, "seller": {"id": 1}},
            {"price": 249, "sold_quantity": 5, "seller": {"id": 2}},
        ],
    }


class TestMercadoLibre(unittest.TestCase):
    def test_parses_real_metrics(self):
        src = MercadoLibreSource(
            transport=lambda u, h: (200, json.dumps(_ml_body()).encode()))
        m = src.analyze_niche(NICHE)
        self.assertEqual(m.provenance, "REAL")
        self.assertEqual(m.listing_count, 1234)
        self.assertEqual(m.total_sold, 65)
        self.assertEqual(m.price_median_mxn, 199)
        self.assertEqual(m.price_min_mxn, 149)
        self.assertEqual(m.price_max_mxn, 249)
        self.assertAlmostEqual(m.top_seller_share, 2 / 3, places=2)

    def test_hard_fail_marks_est_not_real(self):
        m = MercadoLibreSource(transport=lambda u, h: (500, b"")).analyze_niche(NICHE)
        self.assertEqual(m.provenance, "EST")          # no data measured -> EST
        self.assertIsNone(m.listing_count)
        self.assertIn("failed", m.notes.lower())

    def test_403_retries_with_token_then_succeeds(self):
        calls = []

        def transport(url, headers):
            calls.append(headers or {})
            if (headers or {}).get("Authorization"):
                return 200, json.dumps(_ml_body()).encode()
            return 403, b'{"error":"forbidden"}'

        with mock.patch.dict(os.environ, {"ML_TOKEN": "tok"}, clear=False):
            os.environ.pop("ANALYZER_ML_FIXTURE_DIR", None)
            m = MercadoLibreSource(transport=transport).analyze_niche(NICHE)
        self.assertEqual(m.provenance, "REAL")
        self.assertEqual(m.listing_count, 1234)
        self.assertEqual(len(calls), 2)               # anon 403, then bearer 200

    def test_403_without_token_is_est_with_actionable_hint(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ML_TOKEN", None)
            os.environ.pop("ANALYZER_ML_FIXTURE_DIR", None)
            m = MercadoLibreSource(
                transport=lambda u, h: (403, b'{"error":"forbidden"}')).analyze_niche(NICHE)
        self.assertEqual(m.provenance, "EST")
        self.assertIn("ML_TOKEN", m.notes)

    def test_no_sold_quantity_yields_none_demand(self):
        body = {"paging": {"total": 10},
                "results": [{"price": 200, "seller": {"id": 1}}]}  # no sold_quantity
        m = MercadoLibreSource(
            transport=lambda u, h: (200, json.dumps(body).encode())).analyze_niche(NICHE)
        self.assertIsNone(m.total_sold)                # unmeasured, not 0
        self.assertEqual(m.price_median_mxn, 200)

    def test_non_mxn_prices_excluded(self):
        body = {"paging": {"total": 2},
                "results": [{"price": 50, "currency_id": "USD", "seller": {"id": 1}},
                            {"price": 200, "currency_id": "MXN", "seller": {"id": 2}}]}
        m = MercadoLibreSource(
            transport=lambda u, h: (200, json.dumps(body).encode())).analyze_niche(NICHE)
        self.assertEqual(m.price_median_mxn, 200)      # USD listing dropped

    def test_missing_fields_are_tolerated(self):
        body = {"paging": {}, "results": [{"title": "no price no seller"}]}
        m = MercadoLibreSource(
            transport=lambda u, h: (200, json.dumps(body).encode())).analyze_niche(NICHE)
        self.assertIsNone(m.listing_count)
        self.assertIsNone(m.price_median_mxn)
        self.assertIsNone(m.top_seller_share)
        self.assertIsNone(m.total_sold)

    def test_fixture_hit_loads_offline(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, NICHE["id"] + ".json"), "w") as f:
                json.dump(_ml_body(), f)
            with mock.patch.dict(os.environ, {"ANALYZER_ML_FIXTURE_DIR": d}):
                # transport would raise if reached -> proves no network on a hit
                m = MercadoLibreSource(
                    transport=lambda u, h: (_ for _ in ()).throw(
                        AssertionError("network used"))).analyze_niche(NICHE)
        self.assertEqual(m.listing_count, 1234)

    def test_fixture_miss_is_offline_not_network(self):
        def boom(url, headers):
            raise AssertionError("network called in fixture mode")
        with tempfile.TemporaryDirectory() as d:  # empty dir -> every niche misses
            with mock.patch.dict(os.environ, {"ANALYZER_ML_FIXTURE_DIR": d}):
                m = MercadoLibreSource(transport=boom).analyze_niche(NICHE)
        self.assertEqual(m.provenance, "EST")
        self.assertIsNone(m.listing_count)


class TestAmazonResearch(unittest.TestCase):
    def test_returns_est_with_no_numbers(self):
        m = AmazonResearchSource().analyze_niche(NICHE)
        self.assertEqual(m.provenance, "EST")
        self.assertIsNone(m.listing_count)
        self.assertIsNone(m.total_sold)
        self.assertIsNone(m.price_median_mxn)


class TestSeasonality(unittest.TestCase):
    def test_in_season_madres_in_may(self):
        niche = {"id": "t", "name": "Taza dia de las madres", "query": "taza madres"}
        self.assertEqual(SeasonalitySource(month=5).analyze_niche(niche).seasonality_fit, 1.0)

    def test_evergreen_is_mid(self):
        niche = {"id": "t", "name": "Taza ingeniero", "query": "taza ingeniero"}
        self.assertEqual(SeasonalitySource(month=5).analyze_niche(niche).seasonality_fit, 0.5)

    def test_off_season_decays_below_mid(self):
        niche = {"id": "t", "name": "Taza dia de las madres", "query": "madres"}
        self.assertLess(SeasonalitySource(month=11).analyze_niche(niche).seasonality_fit, 0.5)


if __name__ == "__main__":
    unittest.main()
