#!/usr/bin/env python3
"""Deploy archive snippets (#15, #16, #17) and category content to live."""
from __future__ import annotations

import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
ROOT = Path(__file__).parent


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def api(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{LIVE}{path}", data=data, headers=auth_header(), method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} ({exc.code}): {exc.read().decode()}") from exc


def php_to_json_snippet(name: str, desc: str, php_path: Path, tags: list[str]) -> dict:
    return {
        "name": name,
        "desc": desc,
        "code": php_path.read_text(encoding="utf-8").strip(),
        "tags": tags,
        "scope": "global",
        "active": True,
    }


def build_seo_snippet(structured: dict) -> str:
    titles, descs, kws = {}, {}, {}
    for slug, data in structured.items():
        m = data.get("meta", {})
        if m.get("title"):
            titles[slug] = m["title"]
        if m.get("description"):
            descs[slug] = m["description"]
        if m.get("focuskw"):
            kws[slug] = m["focuskw"]

    def php_array(d: dict[str, str]) -> str:
        lines = ["array("]
        for k, v in sorted(d.items()):
            lines.append(f"\t\t'{k}' => '{v.replace(chr(39), chr(92)+chr(39))}',")
        lines.append("\t)")
        return "\n".join(lines)

    return f"""add_filter( 'wpseo_title', static function ( $title ) {{
\tif ( ! is_product_taxonomy() ) {{
\t\treturn $title;
\t}}
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) {{
\t\treturn $title;
\t}}
\t$map = {php_array(titles)};
\treturn $map[ $term->slug ] ?? $title;
}}, 20 );

add_filter( 'wpseo_metadesc', static function ( $desc ) {{
\tif ( ! is_product_taxonomy() ) {{
\t\treturn $desc;
\t}}
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) {{
\t\treturn $desc;
\t}}
\t$map = {php_array(descs)};
\treturn $map[ $term->slug ] ?? $desc;
}}, 20 );

add_filter( 'wpseo_focuskw', static function ( $kw ) {{
\tif ( ! is_product_taxonomy() ) {{
\t\treturn $kw;
\t}}
\t$term = get_queried_object();
\tif ( ! $term instanceof WP_Term ) {{
\t\treturn $kw;
\t}}
\t$map = {php_array(kws)};
\treturn $map[ $term->slug ] ?? $kw;
}}, 20 );"""


def main() -> int:
    structured = json.loads(
        (ROOT / "acb_archive_structured.json").read_text(encoding="utf-8")
    )

    # Snippet #17 — content renderer
    content = api("GET", "/wp-json/code-snippets/v1/snippets/17")
    content_code = (ROOT / "acb-archive-content-snippet.php").read_text(encoding="utf-8").strip()
    api(
        "PUT",
        "/wp-json/code-snippets/v1/snippets/17",
        {
            "name": content.get("name", "ACB Archive Category Content Styled"),
            "code": content_code,
            "scope": content.get("scope", "global"),
            "active": True,
            "priority": content.get("priority", 99),
        },
    )
    print("Updated snippet #17")

    # Snippet #15 — layout + mobile CSS
    layout = json.loads((ROOT / "archive-layout-snippet.json").read_text(encoding="utf-8-sig"))
    layout15 = api("GET", "/wp-json/code-snippets/v1/snippets/15")
    api(
        "PUT",
        "/wp-json/code-snippets/v1/snippets/15",
        {
            "name": layout.get("name", layout15.get("name")),
            "code": layout["code"],
            "scope": layout.get("scope", "global"),
            "active": True,
            "priority": layout.get("priority", 100),
        },
    )
    print("Updated snippet #15")

    # Snippet #16 — SEO
    seo16 = api("GET", "/wp-json/code-snippets/v1/snippets/16")
    seo_code = build_seo_snippet(structured)
    api(
        "PUT",
        "/wp-json/code-snippets/v1/snippets/16",
        {
            "name": seo16.get("name", "ACB Archive Yoast SEO Meta"),
            "code": seo_code,
            "scope": seo16.get("scope", "global"),
            "active": True,
            "priority": seo16.get("priority", 20),
        },
    )
    print(f"Updated snippet #16 with {len(structured)} category SEO entries")

    # Deploy category content
    cats = api("GET", "/wp-json/wc/v3/products/categories?per_page=100")
    live = {c["slug"]: c for c in cats}
    updated, unmatched = [], []
    for slug, data in sorted(structured.items()):
        if slug not in live:
            unmatched.append(slug)
            continue
        payload_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        wrapped = f"<!--acb-archive-v2-->{payload_json}<!--/acb-archive-v2-->"
        cat_id = live[slug]["id"]
        api(
            "POST",
            f"/wp-json/wp/v2/product_cat/{cat_id}",
            {
                "description": wrapped,
                "meta": {
                    "wpseo_title": data["meta"]["title"],
                    "wpseo_metadesc": data["meta"]["description"],
                    "wpseo_focuskw": data["meta"]["focuskw"],
                },
            },
        )
        updated.append(slug)
        print(f"  Deployed {slug} (id={cat_id})")

    report = {"updated": updated, "unmatched": unmatched, "snippets": [15, 16, 17]}
    (ROOT / "deploy_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Done: {len(updated)} categories updated, {len(unmatched)} unmatched")
    if unmatched:
        print("Unmatched:", ", ".join(unmatched))
    return 0


if __name__ == "__main__":
    sys.exit(main())
