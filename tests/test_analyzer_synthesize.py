import unittest

from analyzer.base import NicheMetrics
from analyzer.synthesize import synthesize

NICHES = [
    {"id": "a", "name": "A", "pod_base_cost_mxn": 75, "ship_mxn": 65},
    {"id": "b", "name": "B", "pod_base_cost_mxn": 75, "ship_mxn": 65},
]
CONFIG = {"weights": {"demand": 3, "competition": 3, "margin": 2, "seasonality": 1}}


class TestSynthesize(unittest.TestCase):
    def test_high_demand_low_competition_wins(self):
        metrics = {
            "a": [NicheMetrics("a", "mercadolibre", "REAL", listing_count=100,
                               total_sold=500, price_median_mxn=300),
                  NicheMetrics("a", "seasonality", "EST", seasonality_fit=1.0)],
            "b": [NicheMetrics("b", "mercadolibre", "REAL", listing_count=5000,
                               total_sold=10, price_median_mxn=300),
                  NicheMetrics("b", "seasonality", "EST", seasonality_fit=1.0)],
        }
        scores = synthesize(metrics, NICHES, CONFIG)
        self.assertEqual(scores[0].niche_id, "a")
        self.assertEqual(scores[0].provenance, "REAL")
        self.assertGreater(scores[0].score, scores[1].score)
        self.assertEqual(scores[0].score, 100.0)  # best on every dimension

    def test_identical_signals_tiebreak_by_id_ascending(self):
        def m(nid):
            return [NicheMetrics(nid, "mercadolibre", "REAL", listing_count=100,
                                 total_sold=100, price_median_mxn=300),
                    NicheMetrics(nid, "seasonality", "EST", seasonality_fit=0.5)]
        scores = synthesize({"b": m("b"), "a": m("a")}, NICHES, CONFIG)
        self.assertEqual([s.niche_id for s in scores], ["a", "b"])

    def test_no_real_data_marks_est_and_ranks_on_seasonality(self):
        metrics = {
            "a": [NicheMetrics("a", "amazon_research", "EST"),
                  NicheMetrics("a", "seasonality", "EST", seasonality_fit=0.5)],
            "b": [NicheMetrics("b", "amazon_research", "EST"),
                  NicheMetrics("b", "seasonality", "EST", seasonality_fit=1.0)],
        }
        scores = synthesize(metrics, NICHES, CONFIG)
        self.assertTrue(all(s.provenance == "EST" for s in scores))
        self.assertEqual(scores[0].niche_id, "b")

    def test_margin_uses_real_price_minus_costs(self):
        metrics = {
            "a": [NicheMetrics("a", "mercadolibre", "REAL", listing_count=10,
                               total_sold=10, price_median_mxn=300)],
        }
        scores = synthesize(metrics, NICHES, CONFIG)
        self.assertEqual(scores[0].margin_mxn, 300 - (75 + 65))
        self.assertEqual(scores[0].detail["unit_margin_mxn"], 160)


if __name__ == "__main__":
    unittest.main()
