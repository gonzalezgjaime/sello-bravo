import json
import os
import tempfile
import unittest

from engine.score import load_config, DIMENSIONS

CONFIG_PATH = os.path.join("engine", "config.json")


class TestLoadConfig(unittest.TestCase):
    def test_loads_real_config_with_all_dimensions(self):
        config = load_config(CONFIG_PATH)
        self.assertEqual(set(config["weights"]), set(DIMENSIONS))
        self.assertEqual(config["capital_ceiling_usd"], 200)

    def test_missing_weights_key_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"capital_ceiling_usd": 200, "archetypes": []}, f)
            path = f.name
        try:
            with self.assertRaises(ValueError):
                load_config(path)
        finally:
            os.unlink(path)


def make_candidate(**overrides):
    base = {
        "id": "es-pod-mugs",
        "name": "Spanish-language POD mugs/merch",
        "archetype": "pod_physical",
        "capital_usd": 50,
        "not_scam_legal_safe": True,
        "scores": {
            "runs_on_its_own": 4,
            "leverages_advantage": 5,
            "distribution": 5,
            "demand_evidence": 4,
            "time_to_first_dollar": 4,
            "revenue_ceiling": 3,
            "defensibility": 2,
        },
        "evidence": "Marketplaces give built-in buyers; proven prior MX mug sales.",
        "why_fits_you": "Repeats your proven MX playbook with ES designs.",
        "first_dollar_path": "List 20 ES mug designs on Mercado Libre + Etsy.",
        "kill_criteria": "Drop if no sale within 4 weeks of 20 live designs.",
    }
    base.update(overrides)
    return base


class TestScoreCandidate(unittest.TestCase):
    def setUp(self):
        self.config = load_config(CONFIG_PATH)

    def test_golden_score(self):
        from engine.score import score_candidate
        result = score_candidate(make_candidate(), self.config)
        # 4*3 + 5*3 + 5*3 + 4*2 + 4*2 + 3*1 + 2*1 = 63
        self.assertEqual(result["score"], 63)
        self.assertFalse(result["rejected"])
        self.assertEqual(result["reject_reasons"], [])

    def test_capital_gate_rejects(self):
        from engine.score import score_candidate
        result = score_candidate(make_candidate(capital_usd=500), self.config)
        self.assertTrue(result["rejected"])
        self.assertTrue(any("capital" in r for r in result["reject_reasons"]))

    def test_scam_gate_rejects(self):
        from engine.score import score_candidate
        result = score_candidate(
            make_candidate(not_scam_legal_safe=False), self.config)
        self.assertTrue(result["rejected"])
        self.assertTrue(any("scam" in r for r in result["reject_reasons"]))


class TestRankAndRender(unittest.TestCase):
    def setUp(self):
        self.config = load_config(CONFIG_PATH)
        self.data = {
            "candidates": [
                make_candidate(id="b-lower", name="Lower", capital_usd=10,
                               scores={k: 3 for k in DIMENSIONS}),   # 3*15 = 45
                make_candidate(id="a-higher", name="Higher"),        # 63
                make_candidate(id="c-rejected", name="Rejected",
                               capital_usd=900),                     # gated out
            ]
        }

    def test_rank_orders_survivors_desc_and_excludes_rejected(self):
        from engine.score import rank
        survivors, rejected = rank(self.data, self.config)
        self.assertEqual([s["id"] for s in survivors], ["a-higher", "b-lower"])
        self.assertEqual([r["id"] for r in rejected], ["c-rejected"])

    def test_render_has_table_top5_and_rejected_sections(self):
        from engine.score import rank, render_shortlist
        survivors, rejected = rank(self.data, self.config)
        md = render_shortlist(survivors, rejected, self.data, self.config)
        self.assertIn("# Ranked Shortlist", md)
        self.assertIn("## Top 5", md)
        self.assertIn("Kill-criteria", md)
        self.assertIn("Higher", md)
        self.assertIn("## Rejected", md)
        self.assertIn("Rejected", md)


if __name__ == "__main__":
    unittest.main()
