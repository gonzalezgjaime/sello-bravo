"""Tiny stdlib JSON HTTP helpers with an on-disk cache and injectable transports.

The transport seam lets tests run fully offline. ``fetch_json`` (GET) uses
``transport(url, headers) -> (status:int, body:bytes)``; ``post_form`` (POST
form-encoded) uses ``transport(url, data:bytes, headers) -> (status, body)``.
Default transports use ``urllib`` and never raise on HTTP errors (they return the
error status + body).
"""
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request


def _default_transport(url, headers):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def fetch_json(url, *, headers=None, transport=None, cache_dir=None):
    """GET ``url`` and return ``(status:int, data:dict|list|None)``.

    Returns ``data=None`` when the body is empty or not valid JSON. Only
    successful (200) JSON responses are written to ``cache_dir``.
    """
    transport = transport or _default_transport
    cache_path = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        cache_path = os.path.join(cache_dir, f"{key}.json")
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                return 200, json.load(f)
    status, body = transport(url, headers)
    data = _parse(body)
    if status == 200 and data is not None and cache_path:
        with open(cache_path, "w") as f:
            json.dump(data, f)
    return status, data


def _default_post(url, data, headers):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def post_form(url, fields, *, headers=None, transport=None):
    """POST ``fields`` as ``application/x-www-form-urlencoded``; return ``(status, data)``."""
    transport = transport or _default_post
    body = urllib.parse.urlencode(fields).encode("utf-8")
    hdrs = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    status, raw = transport(url, body, hdrs)
    return status, _parse(raw)


def _parse(body):
    if not body:
        return None
    try:
        return json.loads(body)
    except (ValueError, TypeError):
        return None
