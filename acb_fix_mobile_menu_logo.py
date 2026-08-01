#!/usr/bin/env python3
"""Replace Fixly mobile menu logo with ACB logo in Elementor header #106 only."""
import base64
import json
import urllib.error
import urllib.request

LIVE = "https://americacustomboxes.com"
HEADER_ID = 106
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"

OLD_URL = "https://americacustomboxes.com/wp-content/uploads/2026/07/Fixly-1.png"
NEW_URL = "https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp"
OLD_FILE = "Fixly-1.png"
NEW_FILE = "Acb-logo-landscape.webp"
NEW_ALT = "America Custom Boxes"


def auth_header():
    return {
        "Authorization": "Basic " + base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode(),
        "Content-Type": "application/json",
    }


def get_header():
    req = urllib.request.Request(
        f"{LIVE}/wp-json/wp/v2/elementor_library/{HEADER_ID}?context=edit",
        headers=auth_header(),
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def meta_to_dict(meta) -> dict:
    if isinstance(meta, dict):
        return dict(meta)
    if isinstance(meta, list):
        out = {}
        for row in meta:
            if isinstance(row, dict) and "key" in row:
                out[row["key"]] = row.get("value")
        return out
    return {}


def patch_elementor_json(node):
    """Recursively replace Fixly logo references in Elementor JSON tree."""
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, str):
                if OLD_URL in v:
                    node[k] = v.replace(OLD_URL, NEW_URL)
                if v == OLD_FILE or v.endswith(OLD_FILE):
                    node[k] = NEW_FILE
                if k in ("alt", "title") and v and "Fixly" in v:
                    node[k] = NEW_ALT
            else:
                patch_elementor_json(v)
        # ElementsKit nav logo often uses settings.ekit_nav_menu_logo
        if node.get("url") == OLD_URL or (isinstance(node.get("url"), str) and OLD_FILE in node.get("url", "")):
            node["url"] = NEW_URL
            if "id" in node:
                node["id"] = 109  # ACB logo attachment from site
    elif isinstance(node, list):
        for item in node:
            patch_elementor_json(item)


def main():
    post = get_header()
    meta = meta_to_dict(post.get("meta"))
    raw = meta.get("_elementor_data")
    if not raw:
        raise SystemExit("No _elementor_data on header 106")
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw

    before = json.dumps(data)
    if OLD_FILE not in before and OLD_URL not in before:
        raise SystemExit("Fixly not found in elementor data — already updated?")

    patch_elementor_json(data)
    after = json.dumps(data, ensure_ascii=False)

    if OLD_FILE in after or OLD_URL in after:
        # string replace fallback for any missed keys
        after = after.replace(OLD_URL, NEW_URL).replace(OLD_FILE, NEW_FILE)

    payload = {
        "meta": {
            "_elementor_data": after if isinstance(raw, str) else json.loads(after),
        }
    }

    req = urllib.request.Request(
        f"{LIVE}/wp-json/wp/v2/elementor_library/{HEADER_ID}",
        data=json.dumps(payload).encode("utf-8"),
        headers=auth_header(),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print("POST failed", exc.code, body[:500])
        raise

    # Regenerate header CSS
    regen = """add_action('init', static function () {
\tif ( get_option('acb_header_logo_css_regen') ) return;
\tif ( ! class_exists('\\Elementor\\Plugin') ) return;
\ttry { \\Elementor\\Core\\Files\\CSS\\Post::create(106)->update(); } catch (\\Throwable $e) {}
\tupdate_option('acb_header_logo_css_regen', 1);
}, 5);"""
    # skip regen snippet - user can purge cache

    html = urllib.request.urlopen(
        urllib.request.Request(LIVE + "/", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}),
        timeout=60,
    ).read().decode("utf-8", "replace")
    ok = OLD_FILE not in html and NEW_FILE in html
    print("live check fixly gone:", OLD_FILE not in html)
    print("live check acb in nav logo:", "elementskit-nav-logo" in html and NEW_FILE in html)
    print("OK" if ok else "Verify after LiteSpeed purge")


if __name__ == "__main__":
    main()
