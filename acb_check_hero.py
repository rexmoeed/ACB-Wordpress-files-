#!/usr/bin/env python3
import re
import urllib.request

URL = "https://americacustomboxes.com/product/hair-extension-tuck-boxes/"
html = urllib.request.urlopen(URL).read().decode("utf-8", "replace")

idx = html.find('data-id="5cfb8e5"')
if idx < 0:
    idx = html.find("elementor-element-5cfb8e5")
if idx < 0:
    print("hero container not found")
    raise SystemExit(1)

chunk = html[idx : idx + 50000]
print("=== WIDGETS IN HERO ===")
for m in re.finditer(
    r'data-id="([a-f0-9]+)"[^>]*data-element_type="(widget|container)"[^>]*data-widget_type="([^"]*)"',
    chunk,
):
    print(m.group(2), m.group(1), m.group(3))

print("\n=== CUSTOM IDS ===")
for token in ("729f645", "63ce159", "adf987d", "acbquote1", "acbspecs1", "dd570a0", "ae0988c"):
    print(token, "found" if token in chunk else "MISSING")

print("\n=== NESTING (simplified) ===")
# strip inner HTML, keep opening tags only
tags = re.findall(r"<div[^>]*elementor-element-(5cfb8e5|dd570a0|ae0988c|729f645|63ce159|adf987d|acbquote1|acbspecs1)[^>]*>", chunk)
for t in tags[:20]:
    print(t)
