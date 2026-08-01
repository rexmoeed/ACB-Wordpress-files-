#!/usr/bin/env python3
"""Verify homepage quote form nonce + optional test AJAX (no real email if dry)."""
import json
import re
import urllib.parse
import urllib.request

LIVE = "https://americacustomboxes.com/"


def fetch_home():
    req = urllib.request.Request(LIVE, headers={"User-Agent": "ACB/1.0", "Cache-Control": "no-cache"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")


def extract_nonce(html: str) -> str | None:
    m = re.search(r'window\.acbQuoteFormNonce\s*=\s*"([^"]+)"', html)
    if m:
        return m.group(1)
    m = re.search(r"window\.acbQuoteFormNonce\s*=\s*'([^']+)'", html)
    return m.group(1) if m else None


def test_ajax(nonce: str) -> dict:
    data = urllib.parse.urlencode(
        {
            "action": "acb_submit_instant_quote",
            "quote_nonce": nonce,
            "full_name": "Test User",
            "email": "test@example.com",
            "phone": "555",
            "quantity": "100–499",
            "message": "automated nonce test — ignore",
        }
    ).encode()
    req = urllib.request.Request(
        "https://americacustomboxes.com/wp-admin/admin-ajax.php",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "ACB/1.0"},
        method="POST",
    )
    raw = urllib.request.urlopen(req, timeout=60).read().decode()
    return json.loads(raw)


def main():
    html = fetch_home()
    has_globals = "acb-quote-form-globals" in html
    nonce = extract_nonce(html)
    print("globals_script:", has_globals)
    print("nonce_found:", bool(nonce), ("len=" + str(len(nonce or ""))))
    if not nonce:
        return
    res = test_ajax(nonce)
    print("ajax_success:", res.get("success"))
    msg = (res.get("data") or {}).get("message", "")
    print("ajax_message:", msg[:120])


if __name__ == "__main__":
    main()
