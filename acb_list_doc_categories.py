#!/usr/bin/env python3
"""List every category page in the 4 Batch Word docs (from extract JSON)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
extract = json.loads((ROOT / "acb_category_docs_extract.json").read_text(encoding="utf-8-sig"))

BATCH_FILES = [
    "ACB-Category-Pages-Batch1.docx",
    "ACB-Category-Pages-Batch2.docx",
    "ACB-Category-Pages-Batch3.docx",
    "ACB-Category-Pages-Batch4.docx",
]

# Live slug used at deploy time (one content block per doc category — no duplicate)
DEPLOY_MAP = {
    "COSMETICS": ("cosmetics", None),
    "FOOD": ("food", None),
    "POPCORN": ("popcorn-boxes", "popcorn-boxes"),
    "BAKERY": ("bakery-boxes", "bakery-boxes"),
    "CANDLE": ("candle-boxes", "candle-boxes"),
    "EVENT": ("event-boxes", "event-boxes"),
    "MAILER BOXES": ("mailer-boxes", "mailer-boxes"),
    "PRODUCT BOXES": ("product-boxes", None),
    "TUCK BOXES": ("tuck-boxes", "tuck-boxes"),
    "POD BOXES": ("pod-boxes", None),
    "PHARMACEUTICAL": ("pharmaceutical-boxes", None),
    "PET": ("pet-boxes", "pet-boxes"),
}


def parse_batch(name: str, paras: list[str]) -> list[dict]:
    out = []
    i = 0
    while i < len(paras):
        p = paras[i]
        if p.startswith("ACB CATEGORY PAGE"):
            marker = p
            title = ""
            url_slug = ""
            meta_title = ""
            focus = ""
            j = i + 1
            while j < len(paras) and not paras[j].startswith("ACB CATEGORY PAGE"):
                t = paras[j].strip()
                if not title and t and not t.startswith("SEO") and "Meta Title" not in t and len(t) < 80:
                    if "Custom " in t or "Boxes" in t:
                        title = t
                if t.startswith("URL Slug:"):
                    url_slug = t.replace("URL Slug:", "").strip()
                if t.startswith("SEO Meta Title:"):
                    meta_title = t.replace("SEO Meta Title:", "").strip()
                if t.startswith("Primary Keyword:"):
                    focus = t.replace("Primary Keyword:", "").strip()
                j += 1
            key = None
            upper = marker.upper()
            for k in DEPLOY_MAP:
                if k in upper:
                    key = k
                    break
            planned, deployed = DEPLOY_MAP.get(key, (None, None)) if key else (None, None)
            out.append(
                {
                    "batch": name,
                    "marker": marker,
                    "h1_title": title,
                    "doc_url_slug": url_slug,
                    "meta_title": meta_title,
                    "focuskw": focus,
                    "deploy_key": key,
                    "planned_live_slug": planned,
                }
            )
            i = j
        else:
            i += 1
    return out


def main() -> None:
    all_cats = []
    for bf in BATCH_FILES:
        if bf not in extract:
            print(f"MISSING in extract: {bf}")
            continue
        cats = parse_batch(bf, extract[bf])
        all_cats.extend(cats)
        print(f"\n=== {bf} ({len(cats)} category pages) ===")
        for c in cats:
            print(f"  • {c['h1_title'] or c['marker']}")
            print(f"    Doc slug: {c['doc_url_slug']}")
            print(f"    Live slug (1:1, no duplicate): {c['planned_live_slug']}")

    print(f"\n=== TOTAL in 4 category docs: {len(all_cats)} pages (not 23) ===")
    print("\nNote: D:\\Downloads\\ACB Data\\Documents\\ has 4 OTHER files (product catalogs), not these category batches.")

    # Documents folder
    docs_path = Path(r"D:\Downloads\ACB Data\Documents")
    if docs_path.exists():
        print("\n=== Files in Documents\\ (product copy, NOT archive category pages) ===")
        for f in sorted(docs_path.glob("*.docx")):
            print(f"  - {f.name}")


if __name__ == "__main__":
    main()
