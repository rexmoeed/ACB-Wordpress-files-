#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://americacustomboxes.com/?nocache=icons2",
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")

# Extract style block containing acb-features
m = re.search(r"<style[^>]*>[\s\S]*?\.acb-features[\s\S]*?</style>", html)
if m:
    print("=== FEATURES CSS ===")
    print(m.group(0))
else:
    print("no style with acb-features")

# Extract banner HTML widget style
m2 = re.search(r"<style[^>]*>[\s\S]*?\.acb-banner-section[\s\S]*?</style>", html)
# There may be multiple - get the first one in body content (widget style)
styles = re.findall(r"<style>([\s\S]*?\.acb-banner-section[\s\S]*?)</style>", html)
print("\nbanner style blocks", len(styles))
for i, s in enumerate(styles[:2]):
    print(f"\n=== BANNER STYLE {i} ===")
    print(s[:2000])

# features parent elementor id
j = html.find('class="acb-features"')
print("\nfeatures parent:\n", html[j - 500 : j + 200])
