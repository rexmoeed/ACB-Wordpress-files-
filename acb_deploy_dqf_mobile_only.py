#!/usr/bin/env python3
"""Mobile-only CSS for Detailed Quote form (.acb-dqf-wrap). Desktop + other pages untouched."""
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

# Scoped to .acb-dqf-wrap + max-width only — never affects home or desktop.
CODE = r"""add_action(
	'wp_head',
	static function () {
		if ( ! function_exists( 'is_page' ) || ( ! is_page( 'get-quote' ) && ! is_page( 88 ) ) ) {
			return;
		}
		?>
<style id="acb-dqf-mobile-only">
/* ========== MOBILE ONLY — Detailed Quote form ========== */
@media (max-width: 767px) {
	.acb-dqf-wrap {
		width: 100% !important;
		max-width: 100% !important;
		box-sizing: border-box !important;
		padding: 16px 14px 36px !important;
		/* Room for floating chat widgets on the right */
		padding-right: 18px !important;
		overflow-x: hidden !important;
	}
	.acb-dqf-wrap .qf-header {
		margin-bottom: 22px !important;
		padding: 0 4px !important;
	}
	.acb-dqf-wrap .qf-header h1 {
		font-size: 1.35rem !important;
		line-height: 1.3 !important;
		letter-spacing: -0.3px !important;
		word-wrap: break-word !important;
	}
	.acb-dqf-wrap .qf-header p {
		font-size: 0.9rem !important;
		line-height: 1.55 !important;
		margin-top: 8px !important;
	}
	.acb-dqf-wrap .qf-header p br {
		display: none !important;
	}

	/* Stack all cards — never 2-col on phones */
	.acb-dqf-wrap .qf-grid {
		display: grid !important;
		grid-template-columns: 1fr !important;
		gap: 12px !important;
		margin-bottom: 14px !important;
		width: 100% !important;
	}
	.acb-dqf-wrap .qf-card,
	.acb-dqf-wrap .qf-notes,
	.acb-dqf-wrap .qf-why {
		width: 100% !important;
		max-width: 100% !important;
		min-width: 0 !important;
		box-sizing: border-box !important;
		padding: 16px 14px 14px !important;
		border-radius: 10px !important;
	}
	.acb-dqf-wrap .qf-card-title,
	.acb-dqf-wrap .qf-notes-title,
	.acb-dqf-wrap .qf-why h3 {
		font-size: 0.98rem !important;
		margin-bottom: 14px !important;
		padding-bottom: 8px !important;
		flex-wrap: wrap !important;
	}

	.acb-dqf-wrap .qf-field {
		margin-bottom: 12px !important;
	}
	.acb-dqf-wrap .qf-field label {
		font-size: 0.8rem !important;
	}

	/* 16px inputs = no iOS auto-zoom; full width */
	.acb-dqf-wrap .qf-field input[type="text"],
	.acb-dqf-wrap .qf-field input[type="email"],
	.acb-dqf-wrap .qf-field input[type="tel"],
	.acb-dqf-wrap .qf-field select,
	.acb-dqf-wrap .qf-field textarea,
	.acb-dqf-wrap .qf-notes textarea {
		width: 100% !important;
		max-width: 100% !important;
		font-size: 16px !important;
		line-height: 1.4 !important;
		min-height: 44px !important;
		box-sizing: border-box !important;
	}
	.acb-dqf-wrap .qf-notes textarea {
		min-height: 110px !important;
	}
	.acb-dqf-wrap .qf-field .qf-input-icon input[type="text"],
	.acb-dqf-wrap .qf-field .qf-input-icon input[type="email"],
	.acb-dqf-wrap .qf-field .qf-input-icon input[type="tel"] {
		padding: 11px 12px 11px 40px !important;
	}

	.acb-dqf-wrap .qf-radio-item,
	.acb-dqf-wrap .qf-check-item {
		min-height: 40px !important;
		padding: 4px 0 !important;
		font-size: 0.9rem !important;
		gap: 10px !important;
	}
	.acb-dqf-wrap .qf-radio-item input,
	.acb-dqf-wrap .qf-check-item input {
		width: 18px !important;
		height: 18px !important;
		min-width: 18px !important;
		min-height: 18px !important;
	}

	.acb-dqf-wrap .qf-file-box {
		padding: 16px 10px !important;
	}

	.acb-dqf-wrap .qf-bottom {
		display: grid !important;
		grid-template-columns: 1fr !important;
		gap: 12px !important;
	}
	.acb-dqf-wrap .qf-why-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
		gap: 12px 8px !important;
	}
	.acb-dqf-wrap .qf-why-item strong {
		font-size: 0.68rem !important;
	}
	.acb-dqf-wrap .qf-why-item span {
		font-size: 0.65rem !important;
	}

	.acb-dqf-wrap .qf-submit-wrap {
		padding: 4px 0 0 !important;
	}
	.acb-dqf-wrap .qf-submit-btn {
		width: 100% !important;
		max-width: 100% !important;
		justify-content: center !important;
		padding: 14px 16px !important;
		font-size: 0.92rem !important;
		letter-spacing: 0.5px !important;
		box-sizing: border-box !important;
	}
	.acb-dqf-wrap .qf-privacy {
		padding: 0 8px !important;
		line-height: 1.4 !important;
	}
	.acb-dqf-wrap .qf-msg-success,
	.acb-dqf-wrap .qf-msg-error {
		padding: 14px 12px !important;
		font-size: 0.9rem !important;
	}
}

/* Small phones */
@media (max-width: 380px) {
	.acb-dqf-wrap {
		padding: 12px 10px 32px !important;
	}
	.acb-dqf-wrap .qf-header h1 {
		font-size: 1.2rem !important;
	}
	.acb-dqf-wrap .qf-why-grid {
		grid-template-columns: 1fr 1fr !important;
	}
}
</style>
		<?php
	},
	40
);
"""


def api(method: str, path: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=AUTH, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    name = "ACB Detailed Quote Mobile Only"
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "Mobile-only styles for .acb-dqf-wrap on /get-quote/. Desktop + other pages untouched.",
        "code": CODE.strip(),
        "scope": "global",
        "active": True,
        "priority": 12,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        print("Updated", existing["id"], name)
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        print("Created", created.get("id"), name)
    print("OK — purge LiteSpeed, test phone only. Desktop unchanged.")


if __name__ == "__main__":
    main()
