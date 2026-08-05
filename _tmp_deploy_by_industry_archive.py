#!/usr/bin/env python3
"""Copy Batch2 archive content onto By Industry bakery + candles slugs."""
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).resolve().parent

ALIAS = {
    "bakery": "bakery-boxes",
    "candles": "candle-boxes",
}


def api(method: str, path: str, payload=None):
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    structured = json.loads((ROOT / "acb_archive_structured.json").read_text(encoding="utf-8"))
    cats = api("GET", "/wp-json/wc/v3/products/categories?per_page=100")
    live = {c["slug"]: c for c in cats}

    for target, source in ALIAS.items():
        if source not in structured or target not in live:
            print("SKIP", target, "missing source or live term")
            continue
        data = structured[source]
        wrapped = (
            "<!--acb-archive-v2-->"
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            + "<!--/acb-archive-v2-->"
        )
        cat_id = live[target]["id"]
        api(
            "POST",
            f"/wp-json/wp/v2/product_cat/{cat_id}",
            {
                "description": wrapped,
                "meta": {
                    "wpseo_title": data["meta"]["title"],
                    "wpseo_metadesc": data["meta"]["description"],
                    "wpseo_focuskw": data["meta"]["focuskw"],
                },
            },
        )
        print(f"OK {target} <= {source} (id={cat_id})")

    try:
        urllib.request.urlopen(f"{LIVE}/?litespeed_purge=all", timeout=30)
    except urllib.error.URLError:
        pass


if __name__ == "__main__":
    main()
