#!/usr/bin/env python3
import re
import urllib.request

url = "https://americacustomboxes.com/"
html = urllib.request.urlopen(
    urllib.request.Request(url, headers={"User-Agent": "ACB/1.0"}), timeout=60
).read().decode("utf-8", "replace")

needles = [
    "acbQuoteFormNonce",
    "quote_nonce",
    "acb_submit_instant_quote",
    "submit_instant_quote",
    "acb-qf-form",
    "acb_qf_full_name",
    "Get an Instant Quote",
]
for n in needles:
    print(n, html.count(n))

for m in re.finditer(r".{0,80}acbQuoteFormNonce.{0,120}", html):
    print("HIT:", m.group(0).replace("\n", " ")[:200])

m2 = re.search(r'name=["\']quote_nonce["\'][^>]*value=["\']([^"\']+)', html)
print("input quote_nonce:", (m2.group(1)[:24] + "...") if m2 else "NOT FOUND")

# alternate nonce field names
for name in ["nonce", "_wpnonce", "security", "quote_form_nonce"]:
    if name in html:
        print("contains", name)

# save form block excerpt
i = html.find("acb_qf_full_name")
if i >= 0:
    chunk = html[i : i + 3500]
    open(r"e:\America Custom Boxes\acb_homepage_form_snippet.html", "w", encoding="utf-8").write(chunk)
    print("wrote acb_homepage_form_snippet.html", len(chunk))
