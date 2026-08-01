#!/usr/bin/env python3
import re
import urllib.request

html = urllib.request.urlopen(
    "https://americacustomboxes.com/product/hair-extension-tuck-boxes/"
).read().decode("utf-8", "replace")

idx = html.find('data-id="5cfb8e5"')
chunk = html[idx : idx + 8000]
# print opening structure
opens = re.findall(r"<div[^>]*data-id=\"(5cfb8e5|dd570a0|ae0988c|729f645|63ce159|adf987d|acbquote1|acbspecs1)\"[^>]*>", chunk)
print("OPEN ORDER:")
for o in opens:
    print(" ", o)

# Check for e-con-inner between 5cfb8e5 and columns
inner_idx = chunk.find("e-con-inner")
cfb_idx = chunk.find("5cfb8e5")
print("\ne-con-inner after 5cfb8e5:", inner_idx > cfb_idx and inner_idx < chunk.find("dd570a0"))

# Extract class list on 5cfb8e5
m = re.search(r'data-id="5cfb8e5"[^>]*class="([^"]*)"', chunk)
if m:
    print("\n5cfb8e5 classes:", m.group(1))

m2 = re.search(r'data-id="dd570a0"[^>]*class="([^"]*)"', chunk)
if m2:
    print("dd570a0 classes:", m2.group(1))
