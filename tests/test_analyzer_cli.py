import json
import os
import subprocess
import sys
import tempfile
import unittest


class TestCli(unittest.TestCase):
    def _write_ml_fixture(self, fixtures_dir, niche_id, total, price, sold):
        body = {"paging": {"total": total},
                "results": [{"price": price, "sold_quantity": sold, "seller": {"id": 1}}]}
        with open(os.path.join(fixtures_dir, f"{niche_id}.json"), "w") as f:
            json.dump(body, f)

    def test_end_to_end_offline(self):
        with tempfile.TemporaryDirectory() as d:
            fixtures = os.path.join(d, "ml")
            os.makedirs(fixtures)
            self._write_ml_fixture(fixtures, "n1", total=200, price=250, sold=80)
            self._write_ml_fixture(fixtures, "n2", total=9000, price=250, sold=2)
            niches = {"niches": [
                {"id": "n1", "name": "N1", "query": "q1", "product_type": "mug",
                 "pod_base_cost_mxn": 75, "ship_mxn": 65},
                {"id": "n2", "name": "N2", "query": "q2", "product_type": "mug",
                 "pod_base_cost_mxn": 75, "ship_mxn": 65},
            ]}
            npath = os.path.join(d, "niches.json")
            with open(npath, "w") as f:
                json.dump(niches, f)
            out = os.path.join(d, "report.md")
            env = dict(os.environ, ANALYZER_ML_FIXTURE_DIR=fixtures)
            proc = subprocess.run(
                [sys.executable, "-m", "analyzer.cli", npath, "--out", out, "--month", "6"],
                capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("2 niches ranked", proc.stdout)
            with open(out) as f:
                content = f.read()
            self.assertIn("# MX Market Opportunity Report", content)
            self.assertIn("REAL", content)
            # n1 (low competition, high demand) should outrank n2 (saturated, low demand).
            self.assertLess(content.index("| 1 | N1 |"), content.index("| 2 | N2 |"))

    def test_missing_niches_file_returns_1(self):
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, "-m", "analyzer.cli", os.path.join(d, "nope.json"),
                 "--out", os.path.join(d, "o.md")],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
