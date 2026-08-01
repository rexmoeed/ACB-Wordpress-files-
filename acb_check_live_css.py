#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    "https://americacustomboxes.com/product/hair-extension-tuck-boxes/?cb="
    + __import__("time").strftime("%Y%m%d%H%M%S")
).read().decode("utf-8", "replace")

matches = list(re.finditer(r"<style id=\"acb-single-product-mobile-css\">(.*?)</style>", html, re.S))
print("style block count:", len(matches))
for i, m in enumerate(matches):
    css = m.group(1)
    print(f"\n--- block {i+1} ({len(css)} chars) ---")
    print("grid:", "grid-template-areas" in css)
    print("flex column:", "flex-direction:column" in css)
    print("order:1:", "order:1" in css)
    print(css[:400])

# any other mobile css ids
for pat in re.findall(r"<style id=\"([^\"]+)\"", html):
    if "acb" in pat or "product" in pat or "mobile" in pat:
        print("style id:", pat)
