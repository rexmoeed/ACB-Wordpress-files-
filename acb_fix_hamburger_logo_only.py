#!/usr/bin/env python3
"""
Fix ONLY ElementsKit hamburger menu logo in header template #106.
Does not touch homepage or other templates.
"""
import base64
import json
import urllib.error
import urllib.request

LIVE = "https://americacustomboxes.com"
HEADER_ID = 106
AUTH = {
    "Authorization": "Basic "
    + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode(),
    "Content-Type": "application/json",
}

LOGO = {
    "id": 109,
    "url": "https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp",
}


def get_meta() -> tuple[str, dict]:
    req = urllib.request.Request(
        f"{LIVE}/wp-json/wp/v2/elementor_library/{HEADER_ID}?context=edit",
        headers=AUTH,
    )
    post = json.loads(urllib.request.urlopen(req, timeout=120).read())
    meta = post.get("meta") or {}
    if isinstance(meta, list):
        meta = {x["key"]: x.get("value") for x in meta}
    raw = meta.get("_elementor_data", "")
    return raw, meta


def walk_fix(node) -> bool:
    changed = False
    if isinstance(node, dict):
        if "elementskit_nav_menu_logo" in node:
            node["elementskit_nav_menu_logo"] = dict(LOGO)
            changed = True
        for v in node.values():
            if walk_fix(v):
                changed = True
    elif isinstance(node, list):
        for item in node:
            if walk_fix(item):
                changed = True
    return changed


def main():
    raw, _meta = get_meta()
    if isinstance(raw, str):
        data = json.loads(raw)
        as_string = True
    else:
        data = raw
        as_string = False

    if not walk_fix(data):
        raise SystemExit("elementskit_nav_menu_logo not found")

    new_raw = json.dumps(data, ensure_ascii=False) if as_string else data
    payload = json.dumps({"meta": {"_elementor_data": new_raw}}).encode("utf-8")
    req = urllib.request.Request(
        f"{LIVE}/wp-json/wp/v2/elementor_library/{HEADER_ID}",
        data=payload,
        headers=AUTH,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        resp.read()

    # Regenerate header CSS only
    regen = r"""add_action('init', static function () {
	if ( get_option('acb_hamburger_logo_fix_v3') ) return;
	if ( ! class_exists('\Elementor\Plugin') ) return;
	try { \Elementor\Core\Files\CSS\Post::create(106)->update(); } catch (\Throwable $e) {}
	update_option('acb_hamburger_logo_fix_v3', 1);
}, 5);"""
    snippets = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"{LIVE}/wp-json/code-snippets/v1/snippets?per_page=100",
                headers=AUTH,
            ),
            timeout=60,
        ).read()
    )
    name = "ACB Hamburger logo CSS regen"
    ex = next((s for s in snippets if s.get("name") == name), None)
    body = {
        "name": name,
        "code": regen,
        "scope": "global",
        "active": True,
        "priority": 1,
        "desc": "One-time header CSS after hamburger logo fix.",
    }
    if ex:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{LIVE}/wp-json/code-snippets/v1/snippets/{ex['id']}",
                data=json.dumps(body).encode(),
                headers=AUTH,
                method="PUT",
            ),
            timeout=60,
        )
    else:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{LIVE}/wp-json/code-snippets/v1/snippets",
                data=json.dumps(body).encode(),
                headers=AUTH,
                method="POST",
            ),
            timeout=60,
        )

    urllib.request.urlopen(
        urllib.request.Request(
            f"{LIVE}/?hamburger_fix=1",
            headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
        ),
        timeout=90,
    )

    import re

    html = urllib.request.urlopen(
        urllib.request.Request(
            f"{LIVE}/?v=hamburger3",
            headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    ).read().decode("utf-8", "replace")
    m = re.search(r'elementskit-nav-logo"[^>]*>.*?src="([^"]+)"', html, re.S)
    print("nav img src:", m.group(1) if m else "missing")
    print("broken url gone:", "http://Acb-logo" not in html)
    print("Fixly gone:", "Fixly" not in html)


if __name__ == "__main__":
    main()
