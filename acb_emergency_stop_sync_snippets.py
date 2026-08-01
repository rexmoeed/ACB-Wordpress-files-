#!/usr/bin/env python3
"""
Emergency: stop heavy Yoast sync snippets breaking page load/cache.
Marks sync options complete so init hooks exit instantly.
"""
import base64
import json
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"

MARKER_SNIPPET = """add_action( 'init', static function () {
\tif ( get_option( 'acb_emergency_sync_flags_set' ) ) {
\t\treturn;
\t}
\tupdate_option( 'acb_yoast_terms_synced_v4', 1, false );
\tupdate_option( 'acb_yoast_products_synced_v2', 1, false );
\tupdate_option( 'acb_emergency_sync_flags_set', 1, false );
}, 1 );"""


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

    for sid in (20, 21):
        s = next((x for x in snippets if x.get("id") == sid), None)
        if not s:
            continue
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
        print("OFF snippet", sid)

    existing = next((s for s in snippets if s.get("name") == "ACB Emergency Sync Flags"), None)
    payload = {
        "name": "ACB Emergency Sync Flags",
        "desc": "One-time: mark Yoast bulk sync complete (prevents heavy init on every page).",
        "code": MARKER_SNIPPET,
        "scope": "global",
        "active": True,
        "priority": 1,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
    else:
        api("POST", "/wp-json/code-snippets/v1/snippets", payload)
    print("Emergency flags snippet active")

    for _ in range(2):
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{LIVE}/?nocache={__import__('time').time()}",
                    headers={"User-Agent": "ACB/1.0", "Cache-Control": "no-cache"},
                ),
                timeout=90,
            )
        except urllib.error.URLError as exc:
            print("load", exc)
    print("Done — purge LiteSpeed in WP admin if layout still broken.")


if __name__ == "__main__":
    main()
