#!/usr/bin/env python3
"""Find active snippets that run globally on homepage without guards."""
import base64
import json
import re
import urllib.request

LIVE = "https://americacustomboxes.com"
auth = {"Authorization": "Basic " + base64.b64encode(b"admin:XFxg 7dCD 7FE9 7K3z W6mN 5FIh").decode()}


def get_all():
    req = urllib.request.Request(f"{LIVE}/wp-json/code-snippets/v1/snippets?per_page=100", headers=auth)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def get_one(i):
    req = urllib.request.Request(f"{LIVE}/wp-json/code-snippets/v1/snippets/{i}", headers=auth)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def main():
    active = [s for s in get_all() if s.get("active")]
    print("ACTIVE", len(active))
    for s in active:
        code = get_one(s["id"]).get("code") or ""
        global_hooks = []
        for hook in ("wp_head", "wp_footer", "wp_enqueue_scripts", "init", "template_redirect"):
            if hook in code:
                global_hooks.append(hook)
        guards = []
        for g in (
            "is_front_page",
            "is_product",
            "is_product_taxonomy",
            "is_page(",
            "is_singular",
            "elementor",
            "return;",
        ):
            if g in code:
                guards.append(g)
        risky = global_hooks and not any(
            x in code
            for x in (
                "is_product_taxonomy",
                "is_product()",
                "is_front_page",
                "is_page(",
                "is_shop()",
            )
        )
        flag = " *** RISKY ON HOME ***" if risky and "wp_head" in global_hooks or (risky and "init" in global_hooks) else ""
        if global_hooks:
            print(f"\n#{s['id']} {s['name']}{flag}")
            print("  hooks:", ", ".join(global_hooks))
            print("  guards:", ", ".join(guards[:8]) or "NONE")
            if risky:
                print("  len", len(code))


if __name__ == "__main__":
    main()
