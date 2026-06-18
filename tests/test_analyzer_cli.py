import json
import os
import subprocess
import sys
import tempfile
import unittest

VALID_NICHE = {"name": "N", "query": "q", "product_type": "mug",
               "pod_base_cost_mxn": 75, "ship_mxn": 65}


def _run(args, env=None):
    return subprocess.run([sys.executable, "-m", "analyzer.cli", *args],
                          capture_output=True, text=True, env=env)


class TestCli(unittest.TestCase):
    def _write_ml_fixture(self, fixtures_dir, niche_id, total, price, sold):
        body = {"paging": {"total": total},
                "results": [{"price": price, "sold_quantity": sold,
                             "currency_id": "MXN", "seller": {"id": 1}}]}
        with open(os.path.join(fixtures_dir, f"{niche_id}.json"), "w") as f:
            json.dump(body, f)

    def _niches_file(self, d, niches):
        path = os.path.join(d, "niches.json")
        with open(path, "w") as f:
            json.dump({"niches": niches}, f)
        return path

    def test_end_to_end_offline_real_data(self):
        with tempfile.TemporaryDirectory() as d:
            fixtures = os.path.join(d, "ml")
            os.makedirs(fixtures)
            self._write_ml_fixture(fixtures, "n1", total=200, price=250, sold=80)
            self._write_ml_fixture(fixtures, "n2", total=9000, price=250, sold=2)
            npath = self._niches_file(d, [
                {**VALID_NICHE, "id": "n1", "name": "N1"},
                {**VALID_NICHE, "id": "n2", "name": "N2"}])
            out = os.path.join(d, "report.md")
            env = dict(os.environ, ANALYZER_ML_FIXTURE_DIR=fixtures)
            proc = _run([npath, "--out", out, "--month", "6"], env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("2 niches ranked", proc.stdout)
            with open(out) as f:
                content = f.read()
            self.assertIn("# MX Market Opportunity Report", content)
            self.assertNotIn("WARNING - no REAL", content)
            # n1 (low competition, real demand) outranks n2 (saturated).
            self.assertLess(content.index("| 1 | N1 |"), content.index("| 2 | N2 |"))

    def test_all_est_warns_and_strict_exits_3(self):
        with tempfile.TemporaryDirectory() as d:
            empty = os.path.join(d, "ml")            # empty -> every ML load misses
            os.makedirs(empty)
            npath = self._niches_file(d, [{**VALID_NICHE, "id": "n1", "name": "N1"}])
            out = os.path.join(d, "report.md")
            env = dict(os.environ, ANALYZER_ML_FIXTURE_DIR=empty)
            proc = _run([npath, "--out", out, "--month", "6"], env=env)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("0 with REAL data", proc.stdout)
            self.assertIn("WARNING", proc.stderr)
            with open(out) as f:
                self.assertIn("WARNING - no REAL", f.read())
            strict = _run([npath, "--out", out, "--month", "6", "--strict"], env=env)
            self.assertEqual(strict.returncode, 3)

    def test_invalid_month_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            npath = self._niches_file(d, [{**VALID_NICHE, "id": "n1"}])
            proc = _run([npath, "--out", os.path.join(d, "o.md"), "--month", "99"])
            self.assertEqual(proc.returncode, 1)
            self.assertIn("month", proc.stderr.lower())

    def test_malformed_niche_rejected_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            npath = self._niches_file(d, [
                {"id": "n1", "name": "N1", "pod_base_cost_mxn": 75, "ship_mxn": 65}])  # no query
            proc = _run([npath, "--out", os.path.join(d, "o.md")])
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(proc.stdout, "")
            self.assertIn("query", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)

    def test_missing_niches_file_returns_1(self):
        with tempfile.TemporaryDirectory() as d:
            proc = _run([os.path.join(d, "nope.json"), "--out", os.path.join(d, "o.md")])
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
