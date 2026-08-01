#!/usr/bin/env python3
"""Homepage-only: improve banner + 5 feature icons on mobile. Desktop untouched."""
from __future__ import annotations

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
<style id="acb-home-banner-features-mobile">
@media (max-width: 767px) {
	/* Banner: taller crop so slide art stays readable on phones */
	body.home .acb-banner-section {
		width: 100% !important;
		max-width: 100% !important;
		aspect-ratio: 16 / 9 !important;
		left: auto !important;
		right: auto !important;
		margin: 0 !important;
		overflow: hidden !important;
		border-radius: 0;
	}
	body.home .acb-slider-track {
		height: 100% !important;
	}
	body.home .acb-slider-track img {
		object-fit: cover !important;
		object-position: center center !important;
	}

	/* 5 feature icons: neat 2-column grid, last icon centered */
	body.home .acb-features {
		display: grid !important;
		grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		justify-content: center !important;
		align-items: start !important;
		gap: 18px 14px !important;
		padding: 22px 20px 10px !important;
		width: 100% !important;
		max-width: 420px !important;
		margin: 0 auto !important;
		box-sizing: border-box !important;
		flex-wrap: unset !important;
	}
	body.home .acb-feature-item {
		width: 100% !important;
		max-width: none !important;
		text-align: center !important;
		margin: 0 !important;
	}
	body.home .acb-feature-item img {
		width: 92px !important;
		max-width: 100% !important;
		height: auto !important;
		margin: 0 auto !important;
		display: block !important;
	}
	body.home .acb-feature-item:last-child {
		grid-column: 1 / -1 !important;
		justify-self: center !important;
		width: 50% !important;
		max-width: 140px !important;
	}
}

@media (max-width: 380px) {
	body.home .acb-feature-item img {
		width: 78px !important;
	}
	body.home .acb-features {
		gap: 14px 10px !important;
		padding: 18px 14px 8px !important;
	}
}
</style>
		<?php
	},
	101
);"""


def api(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=AUTH, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    name = "ACB Homepage Banner + Features Mobile"
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "Front page only: better mobile banner aspect + 5 feature icons grid. Desktop unchanged.",
        "code": CODE,
        "scope": "global",
        "active": True,
        "priority": 101,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        print("Updated", existing["id"])
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        print("Created", created.get("id"))

    urllib.request.urlopen(
        urllib.request.Request(
            f"{LIVE}/?feat_fix=1",
            headers={"User-Agent": "Mozilla/5.0 iPhone", "Cache-Control": "no-cache"},
        ),
        timeout=60,
    )
    print("Done")


if __name__ == "__main__":
    main()
