#!/usr/bin/env python3
"""
Sitewide mobile overflow/responsiveness fix.
- Does NOT edit Elementor templates or change desktop design
- Only constrains overflow + quote form grid on <=767px
"""
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

# Replace old homepage-only snippet with sitewide version
CODE = r"""add_action(
	'wp_head',
	static function () {
		?>
<style id="acb-sitewide-mobile-overflow">
@media (max-width: 767px) {
	html,
	body {
		max-width: 100% !important;
	}
	html {
		overflow-x: clip !important;
	}
	/* body must stay visible so fixed ElementsKit offcanvas can slide in */
	body {
		overflow-x: visible !important;
	}
	/* Constrain page content without clipping the nav drawer */
	#page,
	.site-content,
	.elementor-location-header > .elementor-section,
	.elementor-location-footer {
		max-width: 100% !important;
	}

	/* Kill 100vw full-bleed tricks that cause sideways shift */
	.acb-banner-section {
		width: 100% !important;
		max-width: 100% !important;
		left: auto !important;
		right: auto !important;
		margin-left: 0 !important;
		margin-right: 0 !important;
		position: relative !important;
	}

	/* Instant quote form: force single column (it is CSS GRID, not flex) */
	.acb-quote-section,
	.acb-quote-section.acb-quote-section--with-image {
		display: grid !important;
		grid-template-columns: minmax(0, 1fr) !important;
		width: 100% !important;
		max-width: 100% !important;
		margin-left: 0 !important;
		margin-right: 0 !important;
		padding-left: 12px !important;
		padding-right: 12px !important;
		box-sizing: border-box !important;
		gap: 20px !important;
	}

	.acb-quote-form-col,
	.acb-quote-image-col,
	.acb-qf-wrap {
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
		box-sizing: border-box !important;
	}

	.acb-quote-image-col {
		min-height: 220px !important;
	}

	.acb-quote-image-col img {
		width: 100% !important;
		max-width: 100% !important;
		height: auto !important;
		object-fit: cover !important;
	}

	.acb-qf-wrap {
		padding-left: 16px !important;
		padding-right: 16px !important;
	}

	.acb-qf-title,
	.acb-qf-sub,
	.acb-qf-field,
	.acb-qf-file-row,
	.acb-qf-submit {
		max-width: 100% !important;
		box-sizing: border-box !important;
	}

	/* Elementor containers: prevent children forcing page wider than screen */
	.elementor,
	.elementor-section,
	.elementor-container,
	.e-con,
	.e-con-inner,
	.elementor-widget,
	.elementor-widget-container,
	.elementor-widget-wrap {
		max-width: 100% !important;
		box-sizing: border-box !important;
		min-width: 0 !important;
	}

	.elementor img,
	.elementor video,
	.elementor iframe {
		max-width: 100% !important;
		height: auto;
	}

	.elementor-widget-container,
	.elementor-heading-title,
	.elementor-widget-text-editor,
	.elementor-widget-theme-post-content {
		overflow-wrap: anywhere;
		word-break: break-word;
	}

	/* Sticky "Get Instant Quote" tab should not shove layout */
	.acb-quote-btn,
	a.acb-quote-btn {
		z-index: 999 !important;
	}
}
</style>
		<?php
	},
	100
);"""


def api(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=AUTH, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")

    # Deactivate old homepage-only snippet if present (avoid duplicate/conflicting rules)
    old = next((s for s in snippets if s.get("name") == "ACB Homepage Mobile Fix"), None)
    if old and old.get("active"):
        api(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{old['id']}",
            {
                "name": old.get("name"),
                "code": old.get("code"),
                "scope": old.get("scope", "global"),
                "active": False,
                "priority": old.get("priority", 98),
            },
        )
        print("Deactivated old ACB Homepage Mobile Fix")

    name = "ACB Sitewide Mobile Overflow Fix"
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "Mobile-only: stop horizontal shift/overflow + force quote form single column. No template/design changes.",
        "code": CODE,
        "scope": "global",
        "active": True,
        "priority": 100,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        print("Updated snippet", existing["id"], name)
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        print("Created snippet", created.get("id"), name)

    for url in (
        f"{LIVE}/?nocache=sitewide1",
        f"{LIVE}/contact-us/?nocache=sitewide1",
    ):
        try:
            urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 iPhone", "Cache-Control": "no-cache"}),
                timeout=60,
            )
            print("warmed", url)
        except Exception as exc:
            print("warm fail", url, exc)


if __name__ == "__main__":
    main()
