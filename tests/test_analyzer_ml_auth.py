import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock

from analyzer import ml_auth


def _token_transport(*bodies):
    """A post_form transport yielding the given JSON bodies in sequence (200)."""
    seq = iter(bodies)
    return lambda url, data, headers: (200, next(seq))


def _login(tf, transport, now=lambda: 1000.0, **extra):
    args = ["login", "--client-id", "cid", "--client-secret", "sec",
            "--redirect-uri", "https://r", "--code", "abc", "--token-file", tf]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return ml_auth.main(args, transport=transport, now=now, **extra)


class TestMlAuthFunctions(unittest.TestCase):
    def test_authorize_url_includes_pkce_and_state(self):
        url = ml_auth.build_authorize_url("CID", "https://app/cb",
                                          code_challenge="CHAL", state="ST")
        self.assertIn("auth.mercadolibre.com.mx/authorization", url)
        self.assertIn("client_id=CID", url)
        self.assertIn("redirect_uri=https%3A%2F%2Fapp%2Fcb", url)
        self.assertIn("code_challenge=CHAL", url)
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn("state=ST", url)

    def test_authorize_url_without_pkce(self):
        url = ml_auth.build_authorize_url("CID", "https://app/cb")
        self.assertIn("response_type=code", url)
        self.assertNotIn("code_challenge", url)

    def test_pkce_pair_verifier_and_s256_challenge(self):
        import base64
        import hashlib
        v, c = ml_auth._pkce_pair()
        self.assertGreaterEqual(len(v), 43)
        expect = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(c, expect)

    def test_exchange_code_sends_verifier_and_grant(self):
        captured = {}

        def transport(url, data, headers):
            captured["body"] = data.decode()
            return 200, b'{"access_token":"A","refresh_token":"R"}'
        ml_auth.exchange_code("c", "s", "code", "uri", code_verifier="V123", transport=transport)
        self.assertIn("grant_type=authorization_code", captured["body"])
        self.assertIn("code_verifier=V123", captured["body"])

    def test_missing_access_token_or_non_200_raises(self):
        with self.assertRaises(ml_auth.TokenError):
            ml_auth.exchange_code("c", "s", "code", "uri",
                                  transport=lambda u, d, h: (200, b'{"error":"bad"}'))
        with self.assertRaises(ml_auth.TokenError):
            ml_auth.refresh("c", "s", "R",
                            transport=lambda u, d, h: (400, b'{"error":"invalid_grant"}'))


class TestMlAuthCli(unittest.TestCase):
    def test_login_then_cached_token_then_expired_refresh_rotates(self):
        transport = _token_transport(
            b'{"access_token":"AT1","refresh_token":"RT1","expires_in":21600}',
            b'{"access_token":"AT2","refresh_token":"RT2","expires_in":21600}')
        with tempfile.TemporaryDirectory() as d:
            tf = os.path.join(d, "tok.json")
            self.assertEqual(_login(tf, transport, now=lambda: 1000.0), 0)
            self.assertEqual(oct(os.stat(tf).st_mode & 0o777), oct(0o600))  # owner-only

            # Still valid -> cached AT1, no network (transport not consumed).
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                rc = ml_auth.main(["token", "--token-file", tf],
                                  transport=transport, now=lambda: 2000.0)
            self.assertEqual(rc, 0)
            self.assertEqual(out.getvalue().strip(), "AT1")

            # Expired -> refresh -> AT2, refresh token rotates to RT2 and is persisted.
            out2 = io.StringIO()
            with contextlib.redirect_stdout(out2), contextlib.redirect_stderr(io.StringIO()):
                rc = ml_auth.main(["token", "--token-file", tf],
                                  transport=transport, now=lambda: 1000.0 + 21600 + 1)
            self.assertEqual(rc, 0)
            self.assertEqual(out2.getvalue().strip(), "AT2")
            with open(tf) as f:
                rec = json.load(f)
            self.assertEqual(rec["access_token"], "AT2")
            self.assertEqual(rec["refresh_token"], "RT2")

    def test_refresh_keeps_old_refresh_token_when_response_omits_it(self):
        with tempfile.TemporaryDirectory() as d:
            tf = os.path.join(d, "tok.json")
            with open(tf, "w") as f:
                json.dump({"client_id": "c", "client_secret": "s", "refresh_token": "RTx",
                           "access_token": "old", "expires_in": 1, "obtained_at": 0}, f)
            transport = lambda u, dta, h: (200, b'{"access_token":"ATnew","expires_in":21600}')
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                rc = ml_auth.main(["refresh", "--token-file", tf],
                                  transport=transport, now=lambda: 5000.0)
            self.assertEqual(rc, 0)
            self.assertEqual(out.getvalue().strip(), "ATnew")
            with open(tf) as f:
                rec = json.load(f)
            self.assertEqual(rec["access_token"], "ATnew")
            self.assertEqual(rec["refresh_token"], "RTx")  # kept; response omitted it

    def test_login_reads_secret_from_env(self):
        transport = _token_transport(b'{"access_token":"AT","refresh_token":"RT","expires_in":21600}')
        with tempfile.TemporaryDirectory() as d:
            tf = os.path.join(d, "tok.json")
            args = ["login", "--client-id", "cid", "--redirect-uri", "https://r",
                    "--code", "abc", "--token-file", tf]
            with mock.patch.dict(os.environ, {"ML_CLIENT_SECRET": "envsec"}), \
                    contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                rc = ml_auth.main(args, transport=transport, now=lambda: 1.0)
            self.assertEqual(rc, 0)
            with open(tf) as f:
                self.assertEqual(json.load(f)["client_secret"], "envsec")

    def test_token_failure_returns_1_and_writes_no_file(self):
        with tempfile.TemporaryDirectory() as d:
            tf = os.path.join(d, "tok.json")
            rc = _login(tf, lambda u, dta, h: (400, b'{"error":"invalid_grant"}'), now=lambda: 1.0)
            self.assertEqual(rc, 1)
            self.assertFalse(os.path.exists(tf))


if __name__ == "__main__":
    unittest.main()
