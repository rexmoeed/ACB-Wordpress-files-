#!/usr/bin/env python3
"""Deploy ACB Spam Protection + update Instant/Detailed Quote PHP handlers + detailed form honeypot."""
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
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode() or "{}")


def strip_php(code: str) -> str:
    code = code.strip()
    if code.startswith("<?php"):
        code = code[5:].lstrip()
    return code


def upsert_snippet(name: str, desc: str, code: str, priority: int = 5) -> int:
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": desc,
        "code": strip_php(code),
        "scope": "global",
        "active": True,
        "priority": priority,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        print("Updated", name, existing["id"])
        return int(existing["id"])
    created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("Created", name, created.get("id"))
    return int(created.get("id") or 0)


def main() -> None:
    upsert_snippet(
        "ACB Spam Protection",
        "reCAPTCHA v3 + honeypot + shared image/contact validation for quote forms",
        (ROOT / "acb-spam-protection-snippet.php").read_text(encoding="utf-8"),
        priority=4,
    )

    upsert_snippet(
        "ACB Detailed Quote Form",
        "AJAX + nonce for detailed quote form on /get-quote/",
        (ROOT / "acb-detailed-quote-snippet.php").read_text(encoding="utf-8"),
        priority=6,
    )

    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    instant = next(
        (
            s
            for s in snippets
            if (s.get("name") or "") in ("Instant Quote", "ACB Instant Quote")
            or "instant quote" in (s.get("name") or "").lower()
        ),
        None,
    )
    instant_code = strip_php((ROOT / "acb-instant-quote-snippet.php").read_text(encoding="utf-8"))
    if instant:
        api(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{instant['id']}",
            {
                "name": instant.get("name") or "Instant Quote",
                "desc": instant.get("desc") or "Instant Quote AJAX email handler",
                "code": instant_code,
                "scope": "global",
                "active": True,
                "priority": instant.get("priority") or 5,
            },
        )
        print("Updated Instant Quote", instant["id"])
    else:
        upsert_snippet("Instant Quote", "Instant Quote AJAX email handler", instant_code, 5)

    print("Done — handlers only (no layout). Purge LiteSpeed and test forms.")


if __name__ == "__main__":
    main()
