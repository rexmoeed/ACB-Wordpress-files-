#!/usr/bin/env python3
"""Mobile-only header alignment fix. Logo size unchanged. Desktop untouched."""
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
		?>
<style id="acb-mobile-header-align">
@media (max-width: 767px) {
	/* Single line: Logo | Search | Get A Quote | Hamburger */
	.elementor-106 .elementor-element-5743edce > .e-con-inner {
		display: flex !important;
		flex-direction: row !important;
		flex-wrap: nowrap !important;
		align-items: center !important;
		justify-content: flex-start !important;
		column-gap: 6px !important;
		row-gap: 0 !important;
		width: 100% !important;
		max-width: 100% !important;
		box-sizing: border-box !important;
		padding-left: 10px !important;
		padding-right: 10px !important;
	}

	/* 1) Logo — size capped, not enlarged */
	.elementor-106 .elementor-element-11fe0bb7 {
		order: 1 !important;
		width: auto !important;
		max-width: none !important;
		flex: 0 0 auto !important;
		--width: auto !important;
		--align-items: center !important;
		display: flex !important;
		align-items: center !important;
		justify-content: flex-start !important;
		min-width: 0 !important;
		margin: 0 !important;
		padding: 0 !important;
		align-self: center !important;
	}
	.elementor-106 .elementor-element-c3c6947,
	.elementor-106 .elementor-element-c3c6947 .elementor-widget-container,
	.elementor-106 .elementor-element-c3c6947 a {
		display: flex !important;
		align-items: center !important;
		margin: 0 !important;
		padding: 0 !important;
		line-height: 0 !important;
		width: auto !important;
		max-width: 100% !important;
	}
	.elementor-106 .elementor-element-c3c6947 img {
		display: block !important;
		margin: 0 !important;
		width: auto !important;
		max-width: 110px !important;
		height: auto !important;
		max-height: 48px !important;
		object-fit: contain !important;
	}

	/* 2) Search + Quote — same row, after logo */
	.elementor-106 .elementor-element-71b40442 {
		order: 2 !important;
		width: auto !important;
		flex: 0 0 auto !important;
		--width: auto !important;
		display: flex !important;
		flex-direction: row !important;
		flex-wrap: nowrap !important;
		align-items: center !important;
		justify-content: flex-start !important;
		gap: 6px !important;
		margin: 0 0 0 auto !important;
		padding: 0 !important;
		min-width: 0 !important;
		box-sizing: border-box !important;
	}
	.elementor-106 .elementor-element-5544ec35 {
		flex: 0 0 auto !important;
		width: auto !important;
		margin: 0 !important;
		padding: 0 !important;
	}
	.elementor-106 .elementor-element-5544ec35 .elementor-widget-container,
	.elementor-106 .elementor-element-5544ec35 a {
		display: flex !important;
		align-items: center !important;
		margin: 0 !important;
		padding: 0 !important;
	}
	.elementor-106 .elementor-element-18bf67d5 {
		flex: 0 1 auto !important;
		width: auto !important;
		max-width: 100% !important;
		margin: 0 !important;
		padding: 0 !important;
		min-width: 0 !important;
	}
	.elementor-106 .elementor-element-18bf67d5 .elementor-button {
		white-space: nowrap !important;
		padding: 8px 12px !important;
		font-size: 12px !important;
		line-height: 1.2 !important;
		min-height: 0 !important;
	}
	.elementor-106 .elementor-element-18bf67d5 .elementor-button-content-wrapper {
		gap: 4px !important;
	}

	/* 3) Hamburger — far right, same line */
	.elementor-106 .elementor-element-11e4942c {
		order: 3 !important;
		width: auto !important;
		flex: 0 0 auto !important;
		--width: auto !important;
		display: flex !important;
		align-items: center !important;
		justify-content: flex-end !important;
		margin: 0 !important;
		padding: 0 !important;
		align-self: center !important;
	}
	.elementor-106 .elementor-element-117f122f,
	.elementor-106 .elementor-element-117f122f .elementor-widget-container {
		display: flex !important;
		align-items: center !important;
		justify-content: flex-end !important;
		margin: 0 !important;
		padding: 0 !important;
	}
	/* Do not force flex on .ekit-wid-con — it owns the offcanvas panel */
	.elementor-106 .elementor-element-117f122f .ekit-wid-con {
		margin: 0 !important;
		padding: 0 !important;
	}
	.elementor-106 .elementskit-menu-hamburger {
		margin: 0 !important;
		padding: 6px !important;
		align-self: center !important;
		position: relative !important;
		z-index: 20 !important;
		pointer-events: auto !important;
		cursor: pointer !important;
	}

	/* Fix ElementsKit offcanvas: closed off-screen, open on .active */
	.elementor-106 .elementskit-menu-container.elementskit-menu-offcanvas-elements {
		left: -100vw !important;
		z-index: 100000 !important;
	}
	.elementor-106 .elementskit-menu-overlay {
		left: -100% !important;
		z-index: 99999 !important;
	}
	.elementor-106 .elementskit-menu-container.elementskit-menu-offcanvas-elements.active,
	.elementor-106 .elementskit-menu-overlay.active {
		left: 0 !important;
		visibility: visible !important;
		opacity: 1 !important;
		pointer-events: auto !important;
	}
}
</style>
		<?php
	},
	102
);"""


def api(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=AUTH, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    name = "ACB Mobile Header Alignment"
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "Mobile-only single-line header (logo | search | quote | hamburger). Logo not enlarged. Desktop unchanged.",
        "code": CODE,
        "scope": "global",
        "active": True,
        "priority": 102,
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
