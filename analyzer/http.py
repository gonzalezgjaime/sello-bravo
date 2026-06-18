"""Tiny stdlib JSON GET with an on-disk cache and an injectable transport.

The transport seam lets tests run fully offline: pass ``transport=fake`` where
``fake(url, headers) -> (status:int, body:bytes)``. The default transport uses
``urllib`` and never raises on HTTP errors (it returns the error status + body).
"""
import hashlib
import json
import os
import urllib.error
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
    data = None
    if body:
        try:
            data = json.loads(body)
        except (ValueError, TypeError):
            data = None
    if status == 200 and data is not None and cache_path:
        with open(cache_path, "w") as f:
            json.dump(data, f)
    return status, data
