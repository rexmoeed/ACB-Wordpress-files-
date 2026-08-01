#!/usr/bin/env python3
"""Homepage-only mobile overflow fix (banner 100vw + quote width). Does not touch archive/product."""
import base64
import json
import urllib.request

LIVE = "https://americacustomboxes.com"
AUTH = {
    "Authorization": "Basic "
    + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode(),
    "Content-Type": "application/json",
}

CODE = r"""add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_front_page' ) || ! is_front_page() ) {
			return;
		}
		?>
<style id="acb-home-mobile-fix">
@media (max-width: 767px) {
	html,
	body.home {
		overflow-x: clip;
		max-width: 100%;
	}
	body.home .acb-banner-section {
		width: 100% !important;
		max-width: 100% !important;
		left: auto !important;
		right: auto !important;
		margin-left: 0 !important;
		margin-right: -0 !important;
	}
	body.home .acb-quote-section {
		flex-direction: column !important;
		width: 100% !important;
		max-width: 100% !important;
		padding-left: 16px !important;
		padding-right: 16px !important;
		box-sizing: border-box !important;
	}
	body.home .acb-quote-form-col,
	body.home .acb-quote-image-col,
	body.home .acb-qf-wrap {
		width: 100% !important;
		max-width: 100% !important;
		box-sizing: border-box !important;
	}
	body.home .acb-quote-image-col img {
		width: 100% !important;
		height: auto !important;
		max-width: 100% !important;
	}
	body.home .elementor-78 .e-con,
	body.home .elementor-78 .e-con-inner,
	body.home .elementor-78 .elementor-widget-wrap {
		max-width: 100% !important;
		box-sizing: border-box;
	}
	body.home .elementor-78 .elementor-widget-container {
		overflow-wrap: anywhere;
		word-break: break-word;
	}
}
</style>
		<?php
	},
	100
);"""


def upsert(name, code, desc, priority=98):
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
        "ACB Homepage Mobile Fix",
        CODE,
        "Fixes 100vw banner overflow and quote section width on homepage mobile only.",
        98,
    )
    urllib.request.urlopen(
        urllib.request.Request(
            f"{LIVE}/?home_mobile_fix=1",
            headers={"User-Agent": "Mozilla/5.0 iPhone", "Cache-Control": "no-cache"},
        ),
        timeout=90,
    )
    print("Deployed ACB Homepage Mobile Fix — purge LiteSpeed cache on phone/browser.")


if __name__ == "__main__":
    main()
