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

links = re.findall(r'href="([^"]+post-78[^"]+\.css[^"]*)"', html, re.I)
print("post-78 css links", len(links))
for url in links:
    css = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "A"}), timeout=60).read()
    print(url.split("/")[-1], "bytes", len(css))
    text = css.decode("utf-8", "replace")
    if len(text) < 500:
        print("WARNING tiny css:", text)
    elif "elementor-element" not in text:
        print("WARNING no elementor rules")

# hero container ids on homepage
for eid in re.findall(r'data-id="([a-f0-9]+)"', html)[:15]:
    pass
print("elementor containers", len(re.findall(r'data-element_type="container"', html)))
