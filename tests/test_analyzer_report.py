import unittest

from analyzer.base import OpportunityScore
from analyzer.report import render_report


class TestRenderReport(unittest.TestCase):
    def _score(self):
        return OpportunityScore(
            niche_id="a", niche_name="Niche A", score=88.0, provenance="REAL",
            demand_n=1.0, competition_n=0.0, margin_n=1.0, seasonality=1.0,
            margin_mxn=160.0, detail={"listing_count": 100, "total_sold": 500,
                                      "price_median_mxn": 300, "unit_margin_mxn": 160,
                                      "top_seller_share": 0.2, "seasonality_fit": 1.0})

    def test_renders_table_detail_and_caveats(self):
        md = render_report([self._score()], [{"id": "a", "name": "Niche A"}],
                           {"site": "MLM"}, month=6)
        self.assertIn("# MX Market Opportunity Report", md)
        self.assertIn("| 1 | Niche A | 88.0 |", md)
        self.assertIn("## Top niches - detail", md)
        self.assertIn("provenance", md.lower())
        self.assertIn("Amazon MX is EST-only", md)
        self.assertIn("REAL", md)

    def test_handles_missing_numbers_with_dash(self):
        s = OpportunityScore("b", "Niche B", 0.0, "EST", 0.0, 0.0, 0.0, 0.0,
                             None, {"listing_count": None, "total_sold": None,
                                    "price_median_mxn": None, "unit_margin_mxn": None,
                                    "top_seller_share": None, "seasonality_fit": None})
        md = render_report([s], [{"id": "b", "name": "Niche B"}], {"site": "MLM"}, month=6)
        self.assertIn("Niche B", md)
        self.assertIn("-", md)  # missing numbers render as a dash, no crash


if __name__ == "__main__":
    unittest.main()
