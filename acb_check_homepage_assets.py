#!/usr/bin/env python3
import re
import urllib.request

url = "https://americacustomboxes.com/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")

# Elementor CSS for page 78 and kit 11
ids = re.findall(r"post-(\d+)\.css", html)
print("elementor css posts", sorted(set(ids))[:20])
missing = []
for link in re.findall(r'<link[^>]+href="([^"]+\.css[^"]*)"', html, re.I):
    if "elementor" in link or "hello-elementor" in link:
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(link, headers={"User-Agent": "A"}), timeout=20
            )
            if r.status != 200:
                missing.append(link)
        except Exception as exc:
            missing.append(f"{link} -> {exc}")

print("broken elementor css count", len(missing))
for m in missing[:5]:
    print(" ", m[:100])

# duplicate title tags
titles = re.findall(r"<title[^>]*>([^<]+)</title>", html, re.I)
print("title tags", len(titles), titles[:3])

# style tags in body (bad)
bi = html.lower().find("<body")
body = html[bi:]
style_in_body = body.count("<style")
print("style tags in body", style_in_body)

# visible broken PHP
for bad in ("<?php", "Parse error", "Fatal error", "acb-quote-form-globals"):
    print(bad, bad in html)
