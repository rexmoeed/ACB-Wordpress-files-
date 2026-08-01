#!/usr/bin/env python3
"""Deploy quote snippet fix + deactivate one-time Yoast sync snippets + purge cache."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
CODE = (Path(__file__).parent / "acb-instant-quote-snippet.php").read_text(encoding="utf-8").strip()


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
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    quote = next((s for s in snippets if "instant quote" in (s.get("name") or "").lower()), None)
    if quote:
        api(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{quote['id']}",
            {
                "name": quote.get("name", "Instant Quote"),
                "code": CODE,
                "scope": quote.get("scope", "global"),
                "active": True,
                "priority": quote.get("priority", 10),
            },
        )
        print("Updated Instant Quote id", quote["id"])

    for sid, label in [(20, "category yoast sync"), (21, "product yoast sync")]:
        s = next((x for x in snippets if x.get("id") == sid), None)
        if s and s.get("active"):
            api(
                "PUT",
                f"/wp-json/code-snippets/v1/snippets/{sid}",
                {
                    "name": s.get("name"),
                    "code": s.get("code"),
                    "scope": s.get("scope", "global"),
                    "active": False,
                    "priority": s.get("priority", 10),
                },
            )
            print(f"Deactivated snippet {sid} ({label})")

    for url in (f"{LIVE}/", f"{LIVE}/?litespeed_purge=all", f"{LIVE}/wp-admin/admin-ajax.php?action=litespeed_purge_all"):
        try:
            urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ACB/1.0"}), timeout=30)
            print("purge hit", url.split("?")[0])
        except urllib.error.URLError as exc:
            print("purge skip", url, exc)


if __name__ == "__main__":
    main()
