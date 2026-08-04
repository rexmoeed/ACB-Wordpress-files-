#!/usr/bin/env python3
"""Build and deploy About Us page snippet + enable quote form on about-us."""
from __future__ import annotations

import base64
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ABOUT_PAGE_ID = 82
YOAST_TITLE = "About America Custom Boxes | Custom Packaging Co."
YOAST_DESC = (
    "Learn about America Custom Boxes, a custom packaging manufacturer offering "
    "free design, free die & plate setup, eco-friendly materials and free US shipping."
)
YOAST_FOCUS = "custom packaging manufacturer"
YOAST_DEPLOY_KEY = "acbAboutYoast2026"


def api(method: str, path: str, payload=None):
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode() or "{}")


def strip_php(code: str) -> str:
    code = code.strip()
    if code.startswith("<?php"):
        code = code[5:].lstrip()
    return code


def build_about_snippet_php() -> str:
    css = (ROOT / "elementor-widgets" / "acb-about-us-page.css").read_text(encoding="utf-8")
    css += "\n" + (ROOT / "elementor-widgets" / "acb-quote-form-styles.css").read_text(encoding="utf-8")
    css += """
.page-id-82 .site-main,
.page-id-82 .entry-content {
	max-width: 100%;
	width: 100%;
	padding-left: 0;
	padding-right: 0;
}
.page-id-82 .acb-about-page {
	padding-bottom: 0;
}
@media (max-width: 767px) {
	body.page-id-82 {
		overflow-x: clip;
		max-width: 100%;
	}
	body.page-id-82 .acb-quote-section {
		display: grid !important;
		grid-template-columns: minmax(0, 1fr) !important;
		width: 100% !important;
		max-width: 100% !important;
		padding-left: 16px !important;
		padding-right: 16px !important;
		box-sizing: border-box !important;
	}
	body.page-id-82 .acb-quote-form-col,
	body.page-id-82 .acb-quote-image-col,
	body.page-id-82 .acb-qf-wrap {
		width: 100% !important;
		max-width: 100% !important;
		box-sizing: border-box !important;
	}
	body.page-id-82 .acb-quote-image-col img {
		width: 100% !important;
		height: auto !important;
		max-width: 100% !important;
	}
}
"""
    body = (ROOT / "elementor-widgets" / "acb-about-us-page.html").read_text(encoding="utf-8")
    quote = (ROOT / "elementor-widgets" / "acb-about-us-quote-form.html").read_text(encoding="utf-8")
    combined = body + quote
    if "ACB_ABOUT_BODY_END" in combined or "ACB_ABOUT_BODY_END" in css:
        raise SystemExit("Forbidden delimiter in about us assets")

    return f"""<?php
/**
 * About Us page (ID {ABOUT_PAGE_ID}): doc content + instant quote form.
 */
define( 'ACB_ABOUT_US_PAGE_ID', {ABOUT_PAGE_ID} );
define( 'ACB_ABOUT_YOAST_TITLE', {json.dumps(YOAST_TITLE)} );
define( 'ACB_ABOUT_YOAST_DESC', {json.dumps(YOAST_DESC)} );
define( 'ACB_ABOUT_YOAST_FOCUS', {json.dumps(YOAST_FOCUS)} );

add_filter(
	'wpseo_title',
	static function ( $title ) {{
		return acb_about_us_is_target_page() ? ACB_ABOUT_YOAST_TITLE : $title;
	}},
	20
);
add_filter(
	'wpseo_metadesc',
	static function ( $desc ) {{
		return acb_about_us_is_target_page() ? ACB_ABOUT_YOAST_DESC : $desc;
	}},
	20
);
add_filter(
	'wpseo_opengraph_title',
	static function ( $title ) {{
		return acb_about_us_is_target_page() ? ACB_ABOUT_YOAST_TITLE : $title;
	}},
	20
);
add_filter(
	'wpseo_opengraph_desc',
	static function ( $desc ) {{
		return acb_about_us_is_target_page() ? ACB_ABOUT_YOAST_DESC : $desc;
	}},
	20
);
add_filter(
	'wpseo_twitter_title',
	static function ( $title ) {{
		return acb_about_us_is_target_page() ? ACB_ABOUT_YOAST_TITLE : $title;
	}},
	20
);
add_filter(
	'wpseo_twitter_description',
	static function ( $desc ) {{
		return acb_about_us_is_target_page() ? ACB_ABOUT_YOAST_DESC : $desc;
	}},
	20
);

add_action(
	'wp_head',
	static function () {{
		if ( ! acb_about_us_is_target_page() ) {{
			return;
		}}
		?>
<style id="acb-about-us-css">
{css}
</style>
		<?php
	}},
	104
);

add_filter(
	'the_content',
	static function ( $content ) {{
		if ( ! acb_about_us_is_target_page() || ! in_the_loop() || ! is_main_query() ) {{
			return $content;
		}}
		if ( str_contains( (string) $content, 'acb-about-page' ) ) {{
			return $content;
		}}
		$html = <<<'ACB_ABOUT_BODY_END'
{combined}
ACB_ABOUT_BODY_END;
		return $html;
	}},
	5
);

function acb_about_us_is_target_page(): bool {{
	return function_exists( 'is_page' ) && ( is_page( ACB_ABOUT_US_PAGE_ID ) || is_page( 'about-us' ) );
}}
"""


def patch_instant_quote(code: str) -> str:
    old = "is_page( 'contact-us' ) || is_page( 'get-quote' ) || is_page( 88 )"
    new = "is_page( 'contact-us' ) || is_page( 'get-quote' ) || is_page( 'about-us' ) || is_page( 88 ) || is_page( 82 )"
    if old not in code and new in code:
        return code
    if old not in code:
        raise SystemExit("Instant quote snippet pattern not found")
    return code.replace(old, new, 1)


def deploy_about_yoast_meta() -> None:
    title = json.dumps(YOAST_TITLE)
    desc = json.dumps(YOAST_DESC)
    focus = json.dumps(YOAST_FOCUS)
    php = f"""
add_action('init', function () {{
	if (!isset($_GET['acb_about_yoast']) || $_GET['acb_about_yoast'] !== '{YOAST_DEPLOY_KEY}') {{
		return;
	}}
	$page_id = {ABOUT_PAGE_ID};
	$title = {title};
	$desc = {desc};
	$focus = {focus};
	update_post_meta($page_id, '_yoast_wpseo_title', $title);
	update_post_meta($page_id, '_yoast_wpseo_metadesc', $desc);
	update_post_meta($page_id, '_yoast_wpseo_focuskw', $focus);
	update_post_meta($page_id, '_yoast_wpseo_linkdex', '75');
	if (class_exists('WPSEO_Meta')) {{
		WPSEO_Meta::set_value('title', $title, $page_id);
		WPSEO_Meta::set_value('metadesc', $desc, $page_id);
		WPSEO_Meta::set_value('focuskw', $focus, $page_id);
	}}
	if (function_exists('YoastSEO')) {{
		try {{
			$builder = YoastSEO()->classes->get(\\Yoast\\WP\\SEO\\Builders\\Indexable_Builder::class);
			if ($builder) {{
				$builder->build_for_id_and_type($page_id, 'post');
			}}
		}} catch (Throwable $e) {{
			// Indexable rebuild optional.
		}}
	}}
	clean_post_cache($page_id);
	status_header(200);
	echo 'ACB_ABOUT_YOAST_OK|' . get_post_meta($page_id, '_yoast_wpseo_title', true);
	exit;
}}, 1);
"""
    name = "ACB Deploy About Us Yoast Once"
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "One-shot: Yoast meta for About Us page",
        "code": php,
        "scope": "global",
        "active": True,
        "priority": 1,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        sid = existing["id"]
    else:
        sid = api("POST", "/wp-json/code-snippets/v1/snippets", payload).get("id")
    url = f"{LIVE}/?acb_about_yoast={YOAST_DEPLOY_KEY}"
    req = urllib.request.Request(url, headers={"User-Agent": "acb-deploy"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", "replace")
    if "ACB_ABOUT_YOAST_OK" not in body:
        raise SystemExit(f"Yoast deploy failed: {body[:300]}")
    api("PUT", f"/wp-json/code-snippets/v1/snippets/{sid}", {**payload, "active": False})
    print("Yoast meta OK")


def deploy_snippet(name: str, desc: str, code: str, priority: int) -> None:
    code = strip_php(code) if code.lstrip().startswith("<?php") else code
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": desc,
        "code": code,
        "scope": "global",
        "active": True,
        "priority": priority,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        print("Updated", name, existing["id"])
    else:
        created = api("POST", "/wp-json/code-snippets/v1/snippets", payload)
        print("Created", name, created.get("id"))


def main() -> None:
    about_php = build_about_snippet_php()
    deploy_snippet(
        "ACB About Us Page",
        "About Us page content, styling, and quote form from brand doc.",
        about_php,
        108,
    )

    iq_path = ROOT / "acb-instant-quote-snippet.php"
    deploy_snippet(
        "Instant Quote",
        "Instant quote AJAX handler + form globals on key pages.",
        iq_path.read_text(encoding="utf-8"),
        10,
    )

    print("OK")


if __name__ == "__main__":
    main()
