from pathlib import Path

p = Path(r"e:\America Custom Boxes\acb_deploy_detailed_quote.py")
text = p.read_text(encoding="utf-8")
start = text.index("def deploy_elementor_form")
end = text.index("def main()")

new_fn = r'''def deploy_elementor_form(html: str) -> None:
    if "ACB_DQF_HTML" in html:
        raise SystemExit("HTML contains forbidden nowdoc marker")
    # Avoid f-strings: CSS braces in HTML would break formatting.
    php = """
add_action('init', function () {
	if (!isset($_GET['acb_dqf_deploy']) || $_GET['acb_dqf_deploy'] !== 'acbDeployQuote2026') {
		return;
	}
	if (get_option('acb_dqf_form_deployed_v2')) {
		status_header(200);
		echo 'ACB_DQF_ALREADY';
		exit;
	}
	$html = <<<'ACB_DQF_HTML'
__ACB_HTML__
ACB_DQF_HTML;
	$raw = get_post_meta(__PAGE_ID__, '_elementor_data', true);
	$data = is_string($raw) ? json_decode($raw, true) : $raw;
	if (!is_array($data)) {
		status_header(500);
		echo 'ACB_DQF_BAD_DATA';
		exit;
	}
	$updated = false;
	$widget_id = '__WIDGET_ID__';
	$walk = function (&$nodes) use (&$walk, &$updated, $html, $widget_id) {
		if (!is_array($nodes)) {
			return;
		}
		foreach ($nodes as &$n) {
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
		echo 'ACB_DQF_WIDGET_NOT_FOUND';
		exit;
	}
	update_post_meta(__PAGE_ID__, '_elementor_data', wp_slash(wp_json_encode($data)));
	delete_post_meta(__PAGE_ID__, '_elementor_css');
	if (class_exists('\\Elementor\\Plugin')) {
		\\Elementor\\Plugin::$instance->files_manager->clear_cache();
	}
	update_option('acb_dqf_form_deployed_v2', 1, false);
	status_header(200);
	echo 'ACB_DQF_OK';
	exit;
}, 1);
"""
    php = (
        php.replace("__ACB_HTML__", html)
        .replace("__PAGE_ID__", str(PAGE_ID))
        .replace("__WIDGET_ID__", WIDGET_ID)
    )
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    name = "ACB Deploy Detailed Quote HTML Once"
    existing = next((s for s in snippets if s.get("name") == name), None)
    reset_php = "delete_option('acb_dqf_form_deployed_v2');\n"
    payload = {
        "name": name,
        "desc": "One-shot: replace get-quote form HTML widget then auto-deactivate",
        "code": reset_php + php,
        "scope": "global",
        "active": True,
        "priority": 1,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        sid = existing["id"]
        print("Updated one-shot deploy snippet", sid)
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        sid = created.get("id")
        print("Created one-shot deploy snippet", sid)

    req = urllib.request.Request(
        f"{LIVE}/?acb_dqf_deploy=acbDeployQuote2026&nocache=1",
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    print("Deploy response:", body[:200])
    if "ACB_DQF_OK" not in body and "ACB_DQF_ALREADY" not in body:
        raise SystemExit("Deploy failed: " + body[:300])

    api(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{sid}",
        {**payload, "active": False, "code": "// deactivated after deploy"},
    )
    print("Deactivated one-shot")


'''

p.write_text(text[:start] + new_fn + text[end:], encoding="utf-8")
print("patched ok")
