import re
import urllib.request

h = urllib.request.urlopen(
    "https://americacustomboxes.com/?nocache=faqwid3", timeout=90
).read().decode("utf-8", "replace")
needle = "acb-faq-section"
i = h.find(needle)
print("section idx", i)
chunk = h[max(0, i - 2500) : i + 500]
ids = re.findall(r"elementor-element-([a-f0-9]{7,8})", chunk)
print("elementor ids:", ids)
for m in re.finditer(r'data-id="([a-f0-9]+)"', chunk):
    print("data-id", m.group(1))
# widget type html
if "widget-html" in chunk:
    print("has widget-html in chunk")
print(chunk[:400])
