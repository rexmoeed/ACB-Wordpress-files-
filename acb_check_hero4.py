#!/usr/bin/env python3
import urllib.request

html = urllib.request.urlopen(
    "https://americacustomboxes.com/product/hair-extension-tuck-boxes/"
).read().decode("utf-8", "replace")

start = html.find('data-id="5cfb8e5"')
print(html[start : start + 2500])
