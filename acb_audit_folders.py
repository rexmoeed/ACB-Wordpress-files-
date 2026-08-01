import json
import os
import urllib.request

CONVERTED = r"D:\Downloads\ACB Data\converted"
WEBP = r"D:\Downloads\ACB Data\New Images WebP"


def folder_stats(base: str) -> dict[str, int]:
    stats: dict[str, int] = {}
    for root, _, files in os.walk(base):
        imgs = [f for f in files if f.lower().endswith((".webp", ".jpg", ".jpeg", ".png"))]
        if imgs:
            rel = root.replace(base + os.sep, "")
            stats[rel] = len(imgs)
    return stats


def fetch_products() -> list[dict]:
    products: list[dict] = []
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
    return products


converted = folder_stats(CONVERTED)
webp = folder_stats(WEBP)

print("=== FOLDER SUMMARY ===")
print(f"converted: {len(converted)} folders, {sum(converted.values())} images")
print(f"webp:      {len(webp)} folders, {sum(webp.values())} images")
print()

print("=== DISPLAY BOX FOLDERS (converted) ===")
for path, count in sorted(converted.items()):
    if "display" in path.lower():
        print(f"  {count} imgs | {path}")

print()
print("=== DISPLAY BOX FOLDERS (webp) ===")
for path, count in sorted(webp.items()):
    if "display" in path.lower():
        print(f"  {count} imgs | {path}")

print()
print("=== LIVE DISPLAY PRODUCTS ===")
for product in fetch_products():
    name = product["name"]
    if "display" not in name.lower():
        continue
    imgs = product.get("images") or []
    print(f"  {len(imgs)} imgs | {name} | {product['slug']}")

print()
print("=== LIVE PRODUCTS WITH <=2 IMAGES ===")
for product in fetch_products():
    imgs = product.get("images") or []
    if len(imgs) <= 2:
        print(f"  {len(imgs)} imgs | {product['name']} | {product['slug']}")
