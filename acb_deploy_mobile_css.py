#!/usr/bin/env python3
"""Deploy ACB single product mobile CSS to Elementor snippet #2054."""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
SNIPPET_ID = 2054
PHP_FILE = Path(__file__).parent / "acb-snippet-mobile-product.php"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def extract_css_from_php() -> str:
    text = PHP_FILE.read_text(encoding="utf-8")
    m = re.search(r"<style id=\"acb-single-product-mobile-css\">(.*?)</style>", text, re.S)
    if not m:
        raise RuntimeError("Could not extract CSS from PHP snippet file")
    return m.group(1).strip()


def api(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{LIVE}{path}",
        data=data,
        headers=auth_header(),
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path} failed ({exc.code}): {body}") from exc


def main() -> int:
    css = extract_css_from_php()
    php_code = (
        "<?php\n"
        "add_action(\n"
        "\t'wp_head',\n"
        "\tstatic function () {\n"
        "\t\tif ( ! function_exists( 'is_product' ) || ! is_product() ) {\n"
        "\t\t\treturn;\n"
        "\t\t}\n"
        "\t\t?>\n"
        f"<style id=\"acb-single-product-mobile-css\">\n{css}\n</style>\n"
        "\t\t<?php\n"
        "\t},\n"
        "\t100\n"
        ");\n"
    )

    result = api(
        "POST",
        f"/wp-json/wp/v2/elementor_snippet/{SNIPPET_ID}",
        {
            "meta": {
                "_elementor_location": "elementor_head",
                "_elementor_priority": 100,
                "_elementor_code": php_code,
            }
        },
    )
    print(f"Updated snippet {SNIPPET_ID}: {result.get('title', {}).get('rendered', SNIPPET_ID)}")
    print(f"Modified: {result.get('modified', 'unknown')}")
    print(f"CSS bytes: {len(css)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
