#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    "https://americacustomboxes.com/product/hair-extension-tuck-boxes/"
).read().decode("utf-8", "replace")

body = re.search(r"<body[^>]*class=\"([^\"]*)\"", html)
print("body classes:", body.group(1) if body else "none")

for cls in ("elementor-464", "elementor-page-464", "single-product"):
    print(f"{cls} in html:", cls in html)

# find element with elementor-464
for m in re.finditer(r'class="[^"]*elementor-464[^"]*"', html):
    print("match:", m.group(0)[:120])
    break

# find what's outputting mobile css - look before the style tag
idx = html.find("acb-single-product-mobile-css")
print("\nbefore mobile css:", html[max(0, idx - 500) : idx][-300:])
