#!/usr/bin/env python3
"""Restore Yoast sync snippets + deploy minimal scoped form nonce only."""
import base64
import json
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
QUOTE_CODE = (Path(__file__).parent / "acb-instant-quote-snippet.php").read_text(encoding="utf-8").strip()


def auth():
    return {
        "Authorization": "Basic " + base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode(),
        "Content-Type": "application/json",
    }


def api(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=auth(), method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main():
    snippets = {s["id"]: s for s in api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")}

    q = next(s for s in snippets.values() if "instant quote" in (s.get("name") or "").lower())
    api(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{q['id']}",
        {
            "name": q.get("name", "Instant Quote"),
            "code": QUOTE_CODE,
            "scope": q.get("scope", "global"),
            "active": True,
            "priority": q.get("priority", 10),
        },
    )
    print("Instant Quote updated (nonce only on pages with quote form)")

    for sid in (20, 21):
        s = snippets.get(sid)
        if not s:
            continue
        api(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{sid}",
            {
                "name": s.get("name"),
                "code": s.get("code"),
                "scope": s.get("scope", "global"),
                "active": True,
                "priority": s.get("priority", 10),
            },
        )
        print(f"Re-activated snippet {sid}: {s.get('name')}")

    try:
        urllib.request.urlopen(
            urllib.request.Request(f"{LIVE}/?nocache=1", headers={"User-Agent": "ACB/1.0", "Cache-Control": "no-cache"}),
            timeout=30,
        )
    except urllib.error.URLError:
        pass
    print("Cache refresh requested")


if __name__ == "__main__":
    main()
