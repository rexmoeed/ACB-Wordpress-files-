#!/usr/bin/env python3
"""Update Code Snippets 'Instant Quote' on live."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
CODE = (Path(__file__).parent / "acb-instant-quote-snippet.php").read_text(encoding="utf-8").strip()


def api(method, path, payload=None):
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main():
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    target = None
    for s in snippets:
        name = (s.get("name") or "").lower()
        if "instant quote" in name:
            target = s
            break
    if not target:
        print("Instant Quote snippet not found; creating...")
        created = api(
            "POST",
            "/wp-json/code-snippets/v1/snippets",
            {
                "name": "Instant Quote",
                "desc": "AJAX email handler for acb quote forms",
                "code": CODE,
                "scope": "global",
                "active": True,
                "priority": 5,
            },
        )
        print("Created id", created.get("id"))
        return
    api(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{target['id']}",
        {
            "name": target.get("name", "Instant Quote"),
            "code": CODE,
            "scope": target.get("scope", "global"),
            "active": True,
            "priority": target.get("priority", 5),
        },
    )
    print(f"Updated snippet id={target['id']} name={target.get('name')}")


if __name__ == "__main__":
    main()
