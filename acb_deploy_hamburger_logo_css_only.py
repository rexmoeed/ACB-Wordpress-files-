#!/usr/bin/env python3
"""Mobile hamburger panel logo only — CSS override + Elementor cache clear. No layout CSS."""
import base64
import json
import urllib.request

LIVE = "https://americacustomboxes.com"
AUTH = {
    "Authorization": "Basic "
    + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode(),
    "Content-Type": "application/json",
}

LOGO = "https://americacustomboxes.com/wp-content/uploads/2026/07/Acb-logo-landscape.webp"

SNIPPET = f"""add_action(
	'wp_head',
	static function () {{
		?>
<style id="acb-mobile-menu-logo-only">
.elementskit-nav-identity-panel .elementskit-nav-logo img {{
	content: url('{LOGO}') !important;
	width: 168px !important;
	max-width: 72vw !important;
	height: auto !important;
	max-height: 52px !important;
	object-fit: contain !important;
	object-position: left center;
}}
</style>
		<?php
	}},
	99
);"""

REGEN = r"""add_action('init', static function () {
	if ( get_option('acb_ekit_logo_cache_clear_v1') ) return;
	if ( class_exists('\Elementor\Plugin') ) {
		\Elementor\Plugin::$instance->files_manager->clear_cache();
		try { \Elementor\Core\Files\CSS\Post::create(106)->update(); } catch (\Throwable $e) {}
	}
	update_option('acb_ekit_logo_cache_clear_v1', 1);
}, 5);"""


def upsert(name, code, desc, priority=50):
    snips = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"{LIVE}/wp-json/code-snippets/v1/snippets?per_page=100", headers=AUTH),
            timeout=60,
        ).read()
    )
    ex = next((s for s in snips if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": desc,
        "code": code,
        "scope": "global",
        "active": True,
        "priority": priority,
    }
    if ex:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{LIVE}/wp-json/code-snippets/v1/snippets/{ex['id']}",
                data=json.dumps(payload).encode(),
                headers=AUTH,
                method="PUT",
            ),
            timeout=60,
        )
    else:
        urllib.request.urlopen(
            urllib.request.Request(
                f"{LIVE}/wp-json/code-snippets/v1/snippets",
                data=json.dumps(payload).encode(),
                headers=AUTH,
                method="POST",
            ),
            timeout=60,
        )


def main():
    upsert(
        "ACB Mobile Hamburger Logo Only",
        SNIPPET,
        "Shows ACB logo in ElementsKit mobile menu panel only.",
        50,
    )
    upsert(
        "ACB Ekit logo cache clear",
        REGEN,
        "One-time Elementor cache clear after logo fix.",
        1,
    )
    urllib.request.urlopen(
        urllib.request.Request(LIVE + "/", headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"}),
        timeout=90,
    )
    print("Done. Purge LiteSpeed Cache in WP admin if menu still shows old logo HTML.")


if __name__ == "__main__":
    main()
