#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request(
        "https://americacustomboxes.com/",
        headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"},
    ),
    timeout=60,
).read().decode("utf-8", "replace")

for pat in ["post-78", "elementor-78", "page-id-78", "elementor-post", "e-con", "elementor-kit"]:
    print(pat, html.count(pat))

# all elementor css links
for url in re.findall(r'href="([^"]*elementor[^"]*\.css[^"]*)"', html, re.I):
    print("css:", url[:120])

# inline elementor css
inline = re.findall(r'<style[^>]*id="([^"]*elementor[^"]*)"', html, re.I)
print("inline elementor styles", inline[:15], "count", len(inline))

# check if post css embedded
if "elementor-post-78" in html or ".elementor-78" in html:
    idx = html.find("elementor-78")
    print("sample", html[idx : idx + 200])
