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

rows = []
for product in products:
    images = product.get("images") or []
    featured = 1 if images else 0
    gallery = max(0, len(images) - 1)
    rows.append(
        {
            "name": product["name"],
            "slug": product["slug"],
            "featured": featured,
            "gallery": gallery,
            "total": len(images),
        }
    )

rows.sort(key=lambda r: (r["gallery"], r["name"].lower()))

no_gallery = [r for r in rows if r["gallery"] == 0]
partial = [r for r in rows if 1 <= r["gallery"] <= 3]
good = [r for r in rows if r["gallery"] >= 4]

print("LIVE_GALLERY_AUDIT")
print(f"TOTAL={len(rows)}")
print(f"GALLERY_4PLUS={len(good)}")
print(f"GALLERY_1_3={len(partial)}")
print(f"GALLERY_0={len(no_gallery)}")
print()
print("NO_GALLERY_IMAGES")
for r in no_gallery:
    print(f"{r['name']}|{r['slug']}|featured={r['featured']}|gallery={r['gallery']}")
print()
print("PARTIAL_GALLERY_1_3")
for r in partial:
    print(f"{r['name']}|{r['slug']}|gallery={r['gallery']}")
print()
print("GOOD_GALLERY_4PLUS")
for r in good:
    print(f"{r['name']}|{r['slug']}|gallery={r['gallery']}")

with open(r"E:\America Custom Boxes\acb_live_gallery_report.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

print()
print("REPORT=E:\\America Custom Boxes\\acb_live_gallery_report.json")
