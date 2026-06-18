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


if __name__ == "__main__":
    unittest.main()
