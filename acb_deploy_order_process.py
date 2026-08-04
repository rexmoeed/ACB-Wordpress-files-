#!/usr/bin/env python3
"""Update homepage four-step order section HTML (content only) in Elementor widget."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
PAGE_ID = 78
WIDGET_ID = "82a07b0"
DEPLOY_KEY = "acbOrderDeploy2026"


def api(method: str, path: str, payload=None):
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    html = (ROOT / "elementor-widgets" / "acb-order-process.html").read_text(encoding="utf-8")
    if "ACB_ORDER_HTML" in html:
        raise SystemExit("HTML contains forbidden marker")

    php = """
add_action('init', function () {
	if (!isset($_GET['acb_order_deploy']) || $_GET['acb_order_deploy'] !== '__DEPLOY_KEY__') {
		return;
	}
	$html = <<<'ACB_ORDER_HTML'
__ACB_HTML__
ACB_ORDER_HTML;
	$raw = get_post_meta(__PAGE_ID__, '_elementor_data', true);
	$data = is_string($raw) ? json_decode($raw, true) : $raw;
	if (!is_array($data)) {
		status_header(500);
		echo 'ACB_ORDER_BAD_DATA';
		exit;
	}
	$updated = false;
	$widget_id = '__WIDGET_ID__';
	$walk = function (&$nodes) use (&$walk, &$updated, $html, $widget_id) {
		if (!is_array($nodes)) {
			return;
		}
		foreach ($nodes as &$n) {
			if (!is_array($n)) {
				continue;
			}
			if (($n['id'] ?? '') === $widget_id && ($n['widgetType'] ?? '') === 'html') {
				$n['settings']['html'] = $html;
				$updated = true;
			}
			if (!empty($n['elements'])) {
				$walk($n['elements']);
			}
		}
		unset($n);
	};
	$walk($data);
	if (!$updated) {
		status_header(500);
		echo 'ACB_ORDER_WIDGET_NOT_FOUND';
		exit;
	}
	update_post_meta(__PAGE_ID__, '_elementor_data', wp_slash(wp_json_encode($data)));
	delete_post_meta(__PAGE_ID__, '_elementor_css');
	if (class_exists('\\Elementor\\Plugin')) {
		\\Elementor\\Plugin::$instance->files_manager->clear_cache();
	}
	status_header(200);
	echo 'ACB_ORDER_OK';
	exit;
}, 1);
"""
    php = (
        php.replace("__ACB_HTML__", html)
        .replace("__PAGE_ID__", str(PAGE_ID))
        .replace("__WIDGET_ID__", WIDGET_ID)
        .replace("__DEPLOY_KEY__", DEPLOY_KEY)
    )

    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    name = "ACB Deploy Order Process HTML Once"
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "One-shot: update homepage four-step section HTML",
        "code": php,
        "scope": "global",
        "active": True,
        "priority": 1,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
    else:
        api("POST", "/wp-json/code-snippets/v1/snippets", payload)

    url = f"{LIVE}/?acb_order_deploy={DEPLOY_KEY}"
    req = urllib.request.Request(url, headers={"User-Agent": "acb-deploy"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", "replace")
    print(body[:200])
    if "ACB_ORDER_OK" not in body:
        raise SystemExit("Deploy failed")

    if existing:
        api(
            "PUT",
            f"/wp-json/code-snippets/v1/snippets/{existing['id']}",
            {**payload, "active": False},
        )
    print("OK")


if __name__ == "__main__":
    main()
