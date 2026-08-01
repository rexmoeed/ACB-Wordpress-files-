#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    "https://americacustomboxes.com/product/hair-extension-tuck-boxes/"
).read().decode("utf-8", "replace")

start = html.find('data-id="5cfb8e5"')
end = html.find('data-id="e45c370"', start)
if end < 0:
    end = start + 30000
chunk = html[start:end]

for token in ("5cfb8e5", "dd570a0", "ae0988c", "729f645", "63ce159", "adf987d", "acbquote1", "acbspecs1"):
    positions = [m.start() for m in re.finditer(re.escape(token), chunk)]
    print(f"{token}: {positions}")

print("\n--- e-con-inner count ---", chunk.count("e-con-inner"))

# show snippet around each key widget
for token in ("acbquote1", "acbspecs1", "ae0988c", "dd570a0"):
    i = chunk.find(token)
    if i >= 0:
        snippet = chunk[max(0, i - 120) : i + 200].replace("\n", " ")
        print(f"\n[{token}] ...{snippet}...")
