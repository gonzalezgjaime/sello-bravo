"""Mercado Libre OAuth helper (Mexico). Stdlib only.

One-time setup: create a Mercado Libre developer app
(developers.mercadolibre.com.mx) to get a ``client_id`` + ``client_secret`` and a
redirect URI. Then:

    # 1. Authorize once (prints an authorize URL, you paste back the ?code=).
    #    Prefer the env var for the secret (avoids it showing up in `ps`/history):
    ML_CLIENT_SECRET=SECRET python3 -m analyzer.ml_auth login \
        --client-id ID --redirect-uri https://your/redirect

    # 2. Mint/reuse an access token whenever you run the analyzer:
    export ML_TOKEN="$(python3 -m analyzer.ml_auth token)"
    python3 -m analyzer.cli analyzer/niches.json

The flow uses **PKCE** (S256) — harmless if the app doesn't require it, necessary
if it does. Tokens live in a local token file (default ``.ml_token.json``,
git-ignored, written atomically with mode 600). It holds the client secret +
refresh token, so keep it private. The ``token`` subcommand prints ONLY the access
token to stdout (pipeable) and **reuses** the cached token while it is still valid
(access tokens last 6 h); ``refresh`` always mints a new one. Mercado Libre rotates
the refresh token on each refresh — the new one is persisted.
"""
import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import tempfile
import time
from urllib.parse import quote_plus

from analyzer.http import post_form

AUTHORIZE_URL = "https://auth.mercadolibre.com.mx/authorization"
TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
DEFAULT_TOKEN_FILE = ".ml_token.json"
EXPIRY_SKEW_SECONDS = 300  # refresh a bit before the real expiry


class TokenError(RuntimeError):
    """Raised when a Mercado Libre token request does not return an access token."""


def _pkce_pair():
    """Return (code_verifier, code_challenge) for the PKCE S256 flow."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def build_authorize_url(client_id, redirect_uri, *, code_challenge=None, state=None):
    parts = [f"{AUTHORIZE_URL}?response_type=code",
             f"client_id={quote_plus(client_id)}",
             f"redirect_uri={quote_plus(redirect_uri)}"]
    if code_challenge:
        parts += [f"code_challenge={quote_plus(code_challenge)}",
                  "code_challenge_method=S256"]
    if state:  # CSRF guard; not verified in the manual paste-the-code flow
        parts.append(f"state={quote_plus(state)}")
    return "&".join(parts)


def _request_token(fields, transport=None):
    status, data = post_form(TOKEN_URL, fields, transport=transport)
    if status != 200 or not isinstance(data, dict) or "access_token" not in data:
        raise TokenError(f"Mercado Libre token request failed (status {status}): {data}")
    return data


def exchange_code(client_id, client_secret, code, redirect_uri, *,
                  code_verifier=None, transport=None):
    fields = {
        "grant_type": "authorization_code", "client_id": client_id,
        "client_secret": client_secret, "code": code, "redirect_uri": redirect_uri,
    }
    if code_verifier:
        fields["code_verifier"] = code_verifier
    return _request_token(fields, transport=transport)


def refresh(client_id, client_secret, refresh_token, *, transport=None):
    return _request_token({
        "grant_type": "refresh_token", "client_id": client_id,
        "client_secret": client_secret, "refresh_token": refresh_token,
    }, transport=transport)


def _save(token_file, record):
    """Write the token record atomically with owner-only (0600) permissions."""
    target_dir = os.path.dirname(os.path.abspath(token_file)) or "."
    fd, tmp = tempfile.mkstemp(dir=target_dir, prefix=".tok-")  # mkstemp creates 0600
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(record, f, indent=2)
        os.replace(tmp, token_file)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _still_valid(rec, now):
    obtained, expires = rec.get("obtained_at"), rec.get("expires_in")
    return bool(rec.get("access_token") and obtained and expires
               and now() < obtained + expires - EXPIRY_SKEW_SECONDS)


def main(argv=None, *, transport=None, now=None):
    now = now or time.time
    parser = argparse.ArgumentParser(description="Mercado Libre OAuth helper (Mexico).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_login = sub.add_parser("login", help="Authorize once and store tokens")
    p_login.add_argument("--client-id", required=True)
    p_login.add_argument("--client-secret", help="Or set ML_CLIENT_SECRET (preferred)")
    p_login.add_argument("--redirect-uri", required=True)
    p_login.add_argument("--code", help="Authorization code (omit to be prompted)")
    p_login.add_argument("--token-file", default=DEFAULT_TOKEN_FILE)
    for name in ("refresh", "token"):
        p = sub.add_parser(name, help="Refresh (or reuse, for `token`) the access token")
        p.add_argument("--token-file", default=DEFAULT_TOKEN_FILE)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "login":
            secret = args.client_secret or os.environ.get("ML_CLIENT_SECRET")
            if not secret:
                print("Provide --client-secret or set ML_CLIENT_SECRET.", file=sys.stderr)
                return 1
            verifier, challenge = _pkce_pair()
            url = build_authorize_url(args.client_id, args.redirect_uri,
                                      code_challenge=challenge, state=secrets.token_urlsafe(16))
            code = args.code
            if not code:
                print("Open this URL, authorize, then paste the `code` from the redirect:",
                      file=sys.stderr)
                print(url, file=sys.stderr)
                code = input("code: ").strip()
            tok = exchange_code(args.client_id, secret, code, args.redirect_uri,
                                code_verifier=verifier, transport=transport)
            _save(args.token_file, {
                "client_id": args.client_id, "client_secret": secret,
                "redirect_uri": args.redirect_uri,
                "refresh_token": tok.get("refresh_token"),
                "access_token": tok["access_token"],
                "expires_in": tok.get("expires_in"), "obtained_at": now(),
            })
            print('Saved. Use:  export ML_TOKEN="$(python3 -m analyzer.ml_auth token)"',
                  file=sys.stderr)
            print(tok["access_token"])
            return 0

        with open(args.token_file) as f:
            rec = json.load(f)
        if args.cmd == "token" and _still_valid(rec, now):
            print(rec["access_token"])  # reuse the still-valid cached token
            return 0
        tok = refresh(rec["client_id"], rec["client_secret"], rec["refresh_token"],
                      transport=transport)
        rec.update(access_token=tok["access_token"],
                   refresh_token=tok.get("refresh_token", rec["refresh_token"]),
                   expires_in=tok.get("expires_in"), obtained_at=now())
        _save(args.token_file, rec)
        if args.cmd == "refresh":
            print(f"Refreshed; saved to {args.token_file}.", file=sys.stderr)
        print(tok["access_token"])  # stdout = just the token, for $(...)
        return 0
    except (TokenError, OSError, KeyError, ValueError) as exc:
        print(f"ml_auth: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
