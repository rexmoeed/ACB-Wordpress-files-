#!/usr/bin/env python3
"""Deploy mobile CSS to Code Snippets plugin entry #14 on live."""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
SNIPPET_ID = 14
PHP_FILE = Path(__file__).parent / "acb-snippet-mobile-product.php"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def extract_php() -> str:
    return PHP_FILE.read_text(encoding="utf-8").strip()


def api(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{LIVE}{path}", data=data, headers=auth_header(), method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} ({exc.code}): {exc.read().decode()}") from exc


def main() -> int:
    php = extract_php()
    current = api("GET", f"/wp-json/code-snippets/v1/snippets/{SNIPPET_ID}")
    print("Current snippet:", current.get("name"), "scope:", current.get("scope"))

    result = api(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{SNIPPET_ID}",
        {
            "name": current.get("name", "ACB Single Product Mobile CSS"),
            "code": php,
            "scope": current.get("scope", "front-end"),
            "active": True,
            "priority": current.get("priority", 10),
        },
    )
    print("Updated snippet", SNIPPET_ID, "active:", result.get("active"))
    if "grid-template-areas" in result.get("code", ""):
        print("Verified: deployed code contains grid-template-areas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
