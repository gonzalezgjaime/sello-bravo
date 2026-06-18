import unittest

from analyzer.base import NicheMetrics
from analyzer.synthesize import NEUTRAL, _normalize, synthesize

NICHES = [
    {"id": "a", "name": "A", "pod_base_cost_mxn": 75, "ship_mxn": 65},
    {"id": "b", "name": "B", "pod_base_cost_mxn": 75, "ship_mxn": 65},
    {"id": "c", "name": "C", "pod_base_cost_mxn": 75, "ship_mxn": 65},
    {"id": "r1", "name": "R1", "pod_base_cost_mxn": 75, "ship_mxn": 65},
    {"id": "r2", "name": "R2", "pod_base_cost_mxn": 75, "ship_mxn": 65},
    {"id": "d1", "name": "D1", "pod_base_cost_mxn": 75, "ship_mxn": 65},
]
CONFIG = {"weights": {"demand": 3, "competition": 3, "margin": 2, "seasonality": 1}}


class TestNormalize(unittest.TestCase):
    def test_all_none_is_neutral(self):
        self.assertEqual(_normalize([("a", None), ("b", None)]), {"a": NEUTRAL, "b": NEUTRAL})

    def test_single_value_is_neutral_uninformative(self):
        self.assertEqual(_normalize([("a", 5)]), {"a": NEUTRAL})

    def test_all_equal_is_neutral(self):
        self.assertEqual(_normalize([("a", 7), ("b", 7)]), {"a": NEUTRAL, "b": NEUTRAL})

    def test_negative_range_normalizes(self):
        out = _normalize([("a", -50), ("b", 100), ("c", -200)])
        self.assertEqual(out, {"a": 0.5, "b": 1.0, "c": 0.0})

    def test_missing_maps_to_neutral_alongside_measured(self):
        out = _normalize([("a", 0), ("b", 10), ("c", None)])
        self.assertEqual(out["a"], 0.0)
        self.assertEqual(out["b"], 1.0)
        self.assertEqual(out["c"], NEUTRAL)


class TestSynthesize(unittest.TestCase):
    def test_best_on_every_dimension_scores_100(self):
        metrics = {
            "a": [NicheMetrics("a", "mercadolibre", "REAL", listing_count=100,
                               total_sold=500, price_median_mxn=300),
                  NicheMetrics("a", "seasonality", "EST", seasonality_fit=1.0)],
            "b": [NicheMetrics("b", "mercadolibre", "REAL", listing_count=5000,
                               total_sold=10, price_median_mxn=200),
                  NicheMetrics("b", "seasonality", "EST", seasonality_fit=1.0)],
        }
        scores = synthesize(metrics, NICHES, CONFIG)
        self.assertEqual(scores[0].niche_id, "a")
        self.assertEqual(scores[0].provenance, "REAL")
        self.assertEqual(scores[0].score, 100.0)
        self.assertGreater(scores[0].score, scores[1].score)

    def test_identical_signals_tiebreak_by_id_ascending(self):
        def m(nid):
            return [NicheMetrics(nid, "mercadolibre", "REAL", listing_count=100,
                                 total_sold=100, price_median_mxn=300),
                    NicheMetrics(nid, "seasonality", "EST", seasonality_fit=0.5)]
        scores = synthesize({"b": m("b"), "a": m("a")}, NICHES, CONFIG)
        self.assertEqual([s.niche_id for s in scores], ["a", "b"])

    def test_real_niche_beats_dataless_est_niche(self):
        # Regression for the "missing competition rewarded as best" bug: a niche
        # we know nothing about must NOT outrank a measured low-competition niche.
        metrics = {
            "r1": [NicheMetrics("r1", "mercadolibre", "REAL", listing_count=200),
                   NicheMetrics("r1", "seasonality", "EST", seasonality_fit=1.0)],
            "r2": [NicheMetrics("r2", "mercadolibre", "REAL", listing_count=9000),
                   NicheMetrics("r2", "seasonality", "EST", seasonality_fit=1.0)],
            "d1": [NicheMetrics("d1", "amazon_research", "EST"),
                   NicheMetrics("d1", "seasonality", "EST", seasonality_fit=1.0)],
        }
        scores = synthesize(metrics, NICHES, CONFIG)
        order = [s.niche_id for s in scores]
        self.assertEqual(scores[0].niche_id, "r1")          # measured low-competition wins
        self.assertLess(order.index("r1"), order.index("d1"))
        self.assertEqual({s.niche_id: s.provenance for s in scores}["d1"], "EST")

    def test_constant_demand_does_not_max_out(self):
        # All niches report total_sold=0 (or unmeasured) -> demand is uninformative
        # and must normalize to neutral 0.5, not 1.0.
        metrics = {
            "a": [NicheMetrics("a", "mercadolibre", "REAL", listing_count=100, total_sold=0)],
            "b": [NicheMetrics("b", "mercadolibre", "REAL", listing_count=200, total_sold=0)],
        }
        scores = synthesize(metrics, NICHES, CONFIG)
        self.assertTrue(all(s.demand_n == NEUTRAL for s in scores))

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

    def test_negative_margin_normalizes_worst_and_is_kept_raw(self):
        metrics = {
            "a": [NicheMetrics("a", "mercadolibre", "REAL", listing_count=10,
                               price_median_mxn=100)],   # margin 100 - 140 = -40
            "b": [NicheMetrics("b", "mercadolibre", "REAL", listing_count=10,
                               price_median_mxn=300)],   # margin 160
        }
        scores = synthesize(metrics, NICHES, CONFIG)
        by_id = {s.niche_id: s for s in scores}
        self.assertEqual(by_id["a"].margin_mxn, -40)
        self.assertEqual(by_id["a"].margin_n, 0.0)
        self.assertEqual(by_id["b"].margin_n, 1.0)


if __name__ == "__main__":
    unittest.main()
