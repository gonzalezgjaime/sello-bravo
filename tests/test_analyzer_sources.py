import json
import unittest

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

    def test_failed_request_returns_empty_metrics(self):
        src = MercadoLibreSource(transport=lambda u, h: (500, b""))
        m = src.analyze_niche(NICHE)
        self.assertIsNone(m.listing_count)
        self.assertIsNone(m.total_sold)
        self.assertIn("failed", m.notes.lower())

    def test_missing_fields_are_tolerated(self):
        body = {"paging": {}, "results": [{"title": "no price no seller"}]}
        src = MercadoLibreSource(transport=lambda u, h: (200, json.dumps(body).encode()))
        m = src.analyze_niche(NICHE)
        self.assertIsNone(m.listing_count)
        self.assertIsNone(m.price_median_mxn)
        self.assertIsNone(m.top_seller_share)
        self.assertEqual(m.total_sold, 0)


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
