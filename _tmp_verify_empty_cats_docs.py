#!/usr/bin/env python3
"""Cross-check empty live categories against D:\\Downloads\\ACB Data\\Documents."""
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

DOCS = Path(r"D:\Downloads\ACB Data\Documents")
ROOT = Path(__file__).resolve().parent

EMPTY = [
    "cardboard-boxes",
    "cbd-boxes",
    "chocolate-packaging",
    "custom-mylar-bags",
    "display-boxes",
    "kraft-boxes",
    "labels-stickers",
    "pizza-boxes",
    "rigid-boxes",
    "stand-up-pouches",
    "wine-packaging",
    "bakery",
    "candles",
    "cbd",
]

BATCH_LIVE = {
    "cosmetics": "Batch1",
    "food": "Batch1",
    "popcorn-boxes": "Batch1",
    "bakery-boxes": "Batch2",
    "candle-boxes": "Batch2",
    "event-boxes": "Batch2",
    "mailer-boxes": "Batch3",
    "product-boxes": "Batch3",
    "tuck-boxes": "Batch3",
    "pod-boxes": "Batch4",
    "pharmaceutical-boxes": "Batch4",
    "pet-boxes": "Batch4",
}

# Live empty slug -> doc batch slug if content exists elsewhere
ALIAS = {
    "bakery": "bakery-boxes",
    "candles": "candle-boxes",
}


def docx_join(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    parts = []
    for para in root.iter(ns + "p"):
        t = "".join(x.text or "" for x in para.iter(ns + "t"))
        if t.strip():
            parts.append(t.strip())
    return "\n".join(parts)


def category_page_slugs(text: str) -> list[str]:
    slugs = []
    for m in re.finditer(r"URL Slug:\s*([^\n]+)", text):
        slugs.append(m.group(1).strip().strip("/").split("/")[-1] or m.group(1))
    return slugs


def main() -> None:
    files = sorted(DOCS.glob("*.docx"))
    corpus = {}
    all_cat_markers = []
    for f in files:
        try:
            text = docx_join(f)
        except Exception as exc:
            corpus[f.name] = {"error": str(exc)}
            continue
        markers = re.findall(r"ACB CATEGORY PAGE\s*·\s*([A-Z0-9 &]+)", text)
        corpus[f.name] = {
            "text_len": len(text),
            "category_markers": markers,
            "url_slugs": category_page_slugs(text),
        }
        for m in markers:
            all_cat_markers.append((f.name, m.strip()))

    structured = set(json.loads((ROOT / "acb_archive_structured.json").read_text(encoding="utf-8")).keys())

    print("Documents folder:", DOCS)
    print("Docx files:", [f.name for f in files])
    print("\n=== Category archive pages in Documents (ACB CATEGORY PAGE) ===")
    for fn, m in all_cat_markers:
        print(f"  {fn}: {m}")
    print(f"Total category pages in docs: {len(all_cat_markers)} (expected 12 in Batch1-4)\n")

    print("=== Empty LIVE categories vs Documents ===\n")
    for slug in EMPTY:
        batch_key = ALIAS.get(slug, slug)
        in_structured = batch_key in structured
        batch_file = None
        if batch_key in BATCH_LIVE:
            batch_file = BATCH_LIVE[batch_key]

        product_mentions = []
        slug_pat = re.escape(slug.replace("-", " "))
        for fn, meta in corpus.items():
            if "error" in meta:
                continue
            raw = docx_join(DOCS / fn) if fn.endswith(".docx") else ""
            if re.search(slug_pat, raw, re.I) or slug in raw:
                if fn.startswith("ACB-Category-Pages"):
                    continue
                product_mentions.append(fn)

        if in_structured and batch_file:
            status = f"YES — full category copy in {batch_file} (live slug `{batch_key}`, deployed as archive v2)"
        elif slug in ("bakery", "candles"):
            status = f"YES — same copy as `{batch_key}` in Batch2, but By Industry slug `{slug}` has NO separate doc"
        elif slug == "cbd":
            status = "NO — no `ACB CATEGORY PAGE · CBD`; Hot Products `cbd-boxes` also has no batch doc"
        else:
            status = "NO — no dedicated category page in Batch1–4"

        prod_note = ""
        if product_mentions and not in_structured:
            prod_note = f" (product names mention in: {', '.join(sorted(set(product_mentions))[:3])}…)"
        elif product_mentions and in_structured:
            prod_note = " (also product-level mentions in catalogs)"

        print(f"{slug}")
        print(f"  Archive category doc: {status}{prod_note}")
        print()


if __name__ == "__main__":
    main()
