import json
import urllib.request

products = []
for page in range(1, 5):
    url = f"https://americacustomboxes.com/wp-json/wc/store/products?per_page=100&page={page}"
    req = urllib.request.Request(url, headers={"User-Agent": "ACB/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        batch = json.loads(resp.read().decode())
    if not batch:
        break
    products.extend(batch)
    if len(batch) < 100:
        break

complete = partial = featured_only = no_images = 0
incomplete = []

for product in products:
    count = len(product.get("images") or [])
    if count == 0:
        no_images += 1
        incomplete.append((count, product["name"], product["slug"]))
    elif count == 1:
        featured_only += 1
        incomplete.append((count, product["name"], product["slug"]))
    elif count <= 3:
        partial += 1
        incomplete.append((count, product["name"], product["slug"]))
    else:
        complete += 1

print(f"TOTAL={len(products)}")
print(f"COMPLETE_4PLUS={complete}")
print(f"PARTIAL_2_3={partial}")
print(f"FEATURED_ONLY_1={featured_only}")
print(f"NO_IMAGES={no_images}")
print(f"INCOMPLETE_TOTAL={len(incomplete)}")
print("---INCOMPLETE---")
for count, name, slug in incomplete:
    print(f"{count}|{name}|{slug}")
