#!/usr/bin/env python3
"""Deploy archive mobile overflow fix snippet to live."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
CODE = (Path(__file__).parent / "acb-archive-mobile-overflow-fix.php").read_text(encoding="utf-8").strip()


def api(method: str, path: str, payload: dict | None = None) -> dict:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def main() -> int:
    payload = {
        "name": "ACB Archive Mobile Overflow Fix",
        "desc": "Fix archive quote form overflow, FAQ padding, footer shift on mobile.",
        "code": CODE,
        "scope": "global",
        "active": True,
        "priority": 101,
    }

    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == payload["name"]), None)
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        print(f"Updated snippet #{existing['id']}")
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        print(f"Created snippet #{created['id']}")

    try:
        urllib.request.urlopen(f"{LIVE}/?litespeed_purge=all", timeout=30)
        print("Cache purged")
    except urllib.error.URLError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
