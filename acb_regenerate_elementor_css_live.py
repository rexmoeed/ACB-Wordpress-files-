#!/usr/bin/env python3
"""One-time: regenerate Elementor CSS files (homepage post 78 was 404)."""
import base64
import json
import urllib.request

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"

REGEN_CODE = r"""add_action( 'init', static function () {
	if ( get_option( 'acb_elementor_css_regen_v1' ) ) {
		return;
	}
	if ( ! class_exists( '\Elementor\Plugin' ) ) {
		return;
	}
	$post_ids = array( 78, 106, 284, 11 );
	foreach ( $post_ids as $post_id ) {
		try {
			$css_file = \Elementor\Core\Files\CSS\Post::create( (int) $post_id );
			if ( $css_file ) {
				$css_file->update();
			}
		} catch ( \Throwable $e ) {
			error_log( '[ACB Elementor regen] post ' . $post_id . ': ' . $e->getMessage() );
		}
	}
	$files_manager = \Elementor\Plugin::$instance->files_manager;
	if ( $files_manager && method_exists( $files_manager, 'clear_cache' ) ) {
		$files_manager->clear_cache();
	}
	update_option( 'acb_elementor_css_regen_v1', 1, false );
}, 5 );"""


def auth():
    return {
        "Authorization": "Basic " + base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode(),
        "Content-Type": "application/json",
    }


def api(method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=auth(), method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def main():
    snippets = api("GET", "/wp-json/code-snippets/v1/snippets?per_page=100")
    name = "ACB Elementor CSS Regenerate"
    existing = next((s for s in snippets if s.get("name") == name), None)
    payload = {
        "name": name,
        "desc": "One-time regen Elementor post CSS (home/header/footer/kit).",
        "code": REGEN_CODE,
        "scope": "global",
        "active": True,
        "priority": 2,
    }
    if existing:
        api("PUT", f"/wp-json/code-snippets/v1/snippets/{existing['id']}", payload)
        sid = existing["id"]
    else:
        sid = api("POST", "/wp-json/code-snippets/v1/snippets", payload)["id"]
    print("Regen snippet id", sid, "active")

    for i in range(3):
        try:
            urllib.request.urlopen(
                urllib.request.Request(
                    f"{LIVE}/?acb_regen={i}",
                    headers={"User-Agent": "ACB/1.0", "Cache-Control": "no-cache"},
                ),
                timeout=120,
            )
            print("trigger load", i)
        except urllib.error.URLError as exc:
            print("load err", exc)

    # verify css file
    try:
        u = f"{LIVE}/wp-content/uploads/elementor/css/post-78.css"
        body = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "A"}), timeout=30).read()
        print("post-78.css bytes", len(body))
    except urllib.error.HTTPError as exc:
        print("post-78.css still", exc.code)

    # deactivate regen snippet
    api(
        "PUT",
        f"/wp-json/code-snippets/v1/snippets/{sid}",
        {**payload, "active": False},
    )
    print("Regen snippet deactivated")


if __name__ == "__main__":
    main()
