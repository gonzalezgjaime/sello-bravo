import os
import tempfile
import unittest

from analyzer.http import fetch_json


class TestFetchJson(unittest.TestCase):
    def test_transport_injection_parses_json(self):
        status, data = fetch_json("https://x", transport=lambda u, h: (200, b'{"a": 1}'))
        self.assertEqual(status, 200)
        self.assertEqual(data, {"a": 1})

    def test_non_200_returns_status_and_none_on_empty_body(self):
        status, data = fetch_json("https://x", transport=lambda u, h: (401, b""))
        self.assertEqual(status, 401)
        self.assertIsNone(data)

    def test_bad_body_returns_none(self):
        status, data = fetch_json("https://x", transport=lambda u, h: (200, b"not json"))
        self.assertEqual(status, 200)
        self.assertIsNone(data)

    def test_cache_round_trips_and_is_read_without_transport(self):
        with tempfile.TemporaryDirectory() as d:
            calls = []

            def transport(url, headers):
                calls.append(url)
                return 200, b'{"v": 7}'

            s1, d1 = fetch_json("https://x", transport=transport, cache_dir=d)
            s2, d2 = fetch_json("https://x",
                                transport=lambda u, h: (500, b""), cache_dir=d)
            self.assertEqual(d1, {"v": 7})
            self.assertEqual(d2, {"v": 7})  # served from cache, transport not used
            self.assertEqual(len(calls), 1)
            self.assertTrue(os.listdir(d))


if __name__ == "__main__":
    unittest.main()
