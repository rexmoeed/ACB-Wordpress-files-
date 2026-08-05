#!/usr/bin/env python3
"""Update homepage best-selling 9-card grid (Elementor HTML widget on page 78)."""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
PAGE_ID = 78
DEPLOY_KEY = "acbBestSelling2026"


def api(method: str, path: str, payload=None):
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode() or "{}")


def main() -> None:
    html = (ROOT / "elementor-widgets" / "acb-home-best-selling-grid.html").read_text(encoding="utf-8")
    if "ACB_BEST_SELLING_HTML" in html:
        raise SystemExit("HTML contains forbidden marker")

    php = """
add_action('init', function () {
	if (!isset($_GET['acb_best_selling_deploy']) || $_GET['acb_best_selling_deploy'] !== '__DEPLOY_KEY__') {
		return;
	}
	$html = <<<'ACB_BEST_SELLING_HTML'
__ACB_HTML__
ACB_BEST_SELLING_HTML;
	$raw = get_post_meta(__PAGE_ID__, '_elementor_data', true);
	$data = is_string($raw) ? json_decode($raw, true) : $raw;
	if (!is_array($data)) {
		status_header(500);
		echo 'ACB_BEST_SELLING_BAD_DATA';
		exit;
	}
	$updated = false;
	$walk = function (&$nodes) use (&$walk, &$updated, $html) {
		if (!is_array($nodes)) {
			return;
		}
		foreach ($nodes as &$n) {
			if (!is_array($n)) {
				continue;
			}
			$settings = $n['settings'] ?? null;
			if (is_array($settings) && isset($settings['html']) && is_string($settings['html'])) {
				$cur = $settings['html'];
				if (strpos($cur, 'Christmas Boxes') !== false && strpos($cur, 'Wine Packaging') !== false
					&& strpos($cur, 'Custom Chocolate Bar Packaging') === false) {
					$n['settings']['html'] = $html;
					$updated = true;
				}
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
		echo 'ACB_BEST_SELLING_WIDGET_NOT_FOUND';
		exit;
	}
	update_post_meta(__PAGE_ID__, '_elementor_data', wp_slash(wp_json_encode($data)));
	delete_post_meta(__PAGE_ID__, '_elementor_css');
	if (class_exists('\\Elementor\\Plugin')) {
		\\Elementor\\Plugin::$instance->files_manager->clear_cache();
	}
	status_header(200);
	echo 'ACB_BEST_SELLING_OK';
	exit;
}, 1);
"""
    php = php.replace("__ACB_HTML__", html).replace("__PAGE_ID__", str(PAGE_ID)).replace(
        "__DEPLOY_KEY__", DEPLOY_KEY
    )

    name = "ACB Deploy Home Best Selling Grid Once"
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "One-shot: homepage 9-card best selling grid + heading",
        "code": php,
        "scope": "global",
        "active": True,
        "priority": 1,
    }
    if existing:
        sid = existing["id"]
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", payload)
    else:
        sid = api("POST", "/wp-json/code-snippets/v1/snippets", payload).get("id")
    url = f"{LIVE}/?acb_best_selling_deploy={DEPLOY_KEY}"
    req = urllib.request.Request(url, headers={"User-Agent": "acb-deploy"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", "replace")
    if "ACB_BEST_SELLING_OK" not in body:
        raise SystemExit(f"Deploy failed: {body[:400]}")
    api("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", {**payload, "active": False})
    try:
        urllib.request.urlopen(f"{LIVE}/?litespeed_purge=all", timeout=30)
    except urllib.error.URLError:
        pass
    print("OK homepage best selling grid deployed")


if __name__ == "__main__":
    main()
