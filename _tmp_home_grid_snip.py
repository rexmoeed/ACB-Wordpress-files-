import urllib.request

h = urllib.request.urlopen(
    "https://americacustomboxes.com/",
    timeout=90,
).read().decode("utf-8", "replace")
for needle in [
    '<div class="acb-products-wrapper">',
    "acb-products-heading",
    "Hot Products",
    "Our Best",
]:
    print(needle, h.count(needle))
positions = []
start = 0
while True:
    i = h.find('<div class="acb-products-wrapper">', start)
    if i < 0:
        break
    positions.append(i)
    start = i + 1
print("wrappers at", positions)
for n, i in enumerate(positions):
    print(f"--- wrapper {n+1} ---")
    print(h[i : i + 600])
