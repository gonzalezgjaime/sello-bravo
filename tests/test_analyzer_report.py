import unittest

from analyzer.base import OpportunityScore
from analyzer.report import render_report


def _score(**kw):
    base = dict(niche_id="a", niche_name="Niche A", score=88.0, provenance="REAL",
                demand_n=1.0, competition_n=0.0, margin_n=1.0, seasonality=1.0,
                margin_mxn=160.0,
                detail={"listing_count": 100, "total_sold": 500, "price_median_mxn": 300,
                        "unit_margin_mxn": 160, "top_seller_share": 0.2,
                        "seasonality_fit": 1.0})
    base.update(kw)
    return OpportunityScore(**base)


class TestRenderReport(unittest.TestCase):
    def test_renders_table_detail_and_caveats(self):
        md = render_report([_score()], [{"id": "a", "name": "Niche A"}],
                           {"site": "MLM"}, month=6)
        self.assertIn("# MX Market Opportunity Report", md)
        self.assertIn("| 1 | Niche A | 88.0 |", md)
        self.assertIn("## Top niches - detail", md)
        self.assertIn("provenance", md.lower())
        self.assertIn("Amazon MX is EST-only", md)
        self.assertIn("competition** is the whole-marketplace", md)  # granularity caveat
        self.assertNotIn("WARNING - no REAL", md)                    # REAL data present

    def test_missing_numbers_render_as_dash_cell_not_none(self):
        s = _score(provenance="EST", margin_mxn=None,
                   detail={"listing_count": None, "total_sold": None,
                           "price_median_mxn": None, "unit_margin_mxn": None,
                           "top_seller_share": None, "seasonality_fit": None})
        md = render_report([s], [{"id": "a", "name": "Niche A"}], {"site": "MLM"}, month=6)
        self.assertIn("| - |", md)        # margin cell renders a dash
        self.assertNotIn("None", md)      # never the literal string "None"

    def test_negative_margin_is_flagged(self):
        s = _score(margin_mxn=-40.0,
                   detail={**_score().detail, "unit_margin_mxn": -40})
        md = render_report([s], [{"id": "a", "name": "Niche A"}], {"site": "MLM"}, month=6)
        self.assertIn("(loss)", md)

    def test_all_est_run_shows_warning_banner(self):
        s = _score(provenance="EST")
        md = render_report([s], [{"id": "a", "name": "Niche A"}], {"site": "MLM"}, month=6)
        self.assertIn("WARNING - no REAL", md)


if __name__ == "__main__":
    unittest.main()
