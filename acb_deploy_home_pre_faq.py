#!/usr/bin/env python3
"""Deploy homepage pre-FAQ content sections snippet."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"


def api(method: str, path: str, payload=None):
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def strip_php(code: str) -> str:
    code = code.strip()
    if code.startswith("<?php"):
        code = code[5:].lstrip()
    return code


def main() -> None:
    code = strip_php((ROOT / "acb-home-pre-faq-snippet.php").read_text(encoding="utf-8"))
    name = "ACB Home Pre-FAQ Sections"
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "Homepage only: doc sections before FAQ. Scoped CSS; no Elementor edits.",
        "code": code,
        "scope": "global",
        "active": True,
        "priority": 106,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        print("Updated", existing["id"])
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        print("Created", created.get("id"))
    print("OK")


if __name__ == "__main__":
    main()
