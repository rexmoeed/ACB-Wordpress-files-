#!/usr/bin/env python3
"""Update homepage features mobile CSS: 5 icons in one horizontal row."""
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

	/* 5 feature icons: one single row on mobile */
	body.home .acb-features {
		display: flex !important;
		flex-wrap: nowrap !important;
		flex-direction: row !important;
		justify-content: space-between !important;
		align-items: flex-start !important;
		gap: 4px !important;
		padding: 16px 8px 12px !important;
		width: 100% !important;
		max-width: 100% !important;
		margin: 0 auto !important;
		box-sizing: border-box !important;
		grid-template-columns: none !important;
	}
	body.home .acb-feature-item {
		flex: 1 1 0 !important;
		width: auto !important;
		max-width: none !important;
		min-width: 0 !important;
		text-align: center !important;
		margin: 0 !important;
		grid-column: auto !important;
		justify-self: auto !important;
	}
	body.home .acb-feature-item img {
		width: 100% !important;
		max-width: 64px !important;
		height: auto !important;
		margin: 0 auto !important;
		display: block !important;
	}
	body.home .acb-feature-item:last-child {
		grid-column: auto !important;
		width: auto !important;
		max-width: none !important;
		justify-self: auto !important;
	}
}

@media (max-width: 380px) {
	body.home .acb-features {
		gap: 2px !important;
		padding: 14px 6px 10px !important;
	}
	body.home .acb-feature-item img {
		max-width: 56px !important;
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
        "desc": "Front page only: mobile banner + 5 feature icons in one row. Desktop unchanged.",
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
    print("OK")


if __name__ == "__main__":
    main()
