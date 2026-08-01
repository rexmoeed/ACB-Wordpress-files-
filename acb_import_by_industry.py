#!/usr/bin/env python3
"""
Import By Industry WooCommerce products from Documents + New Images WebP.
Skips products that already exist in WP (no duplication).
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pymysql

# Reuse parsers / ACF writers from existing scripts
import sys

sys.path.insert(0, str(Path(__file__).parent))
from acb_import_products import (  # noqa: E402
    DOCS as _OLD_DOCS,
    build_long_description,
    find_doc_for_db_product,
    get_db_products,
    normalize,
    parse_products_from_doc,
)
from acb_migrate_acf import parse_product_content, write_acf_data  # noqa: E402

DOCS = [
    r"D:\Downloads\ACB Data\Documents\ACB_Product_Copy_Master_Catalog.docx",
    r"D:\Downloads\ACB Data\Documents\ACB_Remaining_Products_Catalogue.docx",
    r"D:\Downloads\ACB Data\Documents\ACB_Remaining_Products_Catalogue (1).docx",
    r"D:\Downloads\ACB Data\Documents\ACB_Remaining_Products_Catalogue (2).docx",
]
WEBP_ROOT = Path(r"D:\Downloads\ACB Data\New Images WebP")
WP_UPLOADS = Path(
    r"C:\Users\moeed\Local Sites\americacustomboxes\app\public\wp-content\uploads\2026\07"
)
DB = dict(host="127.0.0.1", port=10005, user="root", password="root", database="local", charset="utf8mb4")
SITE_URL = "http://localhost:10004"

PARENT_CAT = {"name": "By Industry", "slug": "by-industry"}
INDUSTRY_SUBCATS = {
    "Bakery": {"name": "Bakery", "slug": "bakery"},
    "candles": {"name": "Candles", "slug": "candles"},
    "CBD": {"name": "CBD", "slug": "cbd"},
}

FOLDER_ALIASES = {
    "acb cupcack box": "cupcake boxes with inserts",
    "acb custom cake box": "custom cake boxes",
    "acb desert box": "dessert boxes",
    "acb drawer sliding candle": "drawer candle boxes",
    "acb tealight canle": "tealight candle packaging",
    "acb custom votice": "custom votive candle boxes",
    "acb cbd crugeted": "cbd corrugated mailer boxes",
    "acb cbd countr display": "cbd counter display boxes",
    "acb gumies edible": "",
}


def slugify(text: str) -> str:
    text = html.unescape(text or "")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def clean_folder_label(name: str) -> str:
    name = re.sub(r"^ACB\s+", "", name, flags=re.I).strip()
    return re.sub(r"\s+", " ", name)


def collect_webp_folders() -> list[dict]:
    folders = []
    for dirpath, _, filenames in os.walk(WEBP_ROOT):
        webps = sorted(f for f in filenames if f.lower().endswith(".webp"))
        if not webps:
            continue
        rel = Path(dirpath).relative_to(WEBP_ROOT)
        parts = rel.parts
        industry = parts[0] if parts else ""
        leaf = parts[-1] if parts else ""
        folders.append(
            {
                "rel": str(rel),
                "industry": industry,
                "leaf": leaf,
                "norm_leaf": normalize(clean_folder_label(leaf)),
                "images": [Path(dirpath) / f for f in webps],
            }
        )
    return folders


def dedupe_folders(folders: list[dict]) -> list[dict]:
    """Keep one folder per industry+normalized leaf (prefer cleaner name / more images)."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for f in folders:
        key = (f["industry"], f["norm_leaf"])
        groups.setdefault(key, []).append(f)

    picked = []
    for key, items in groups.items():
        items.sort(
            key=lambda x: (
                x["leaf"].lower().startswith("acb"),
                -len(x["images"]),
                x["leaf"].lower(),
            )
        )
        picked.append(items[0])
    return picked


def load_doc_catalog() -> tuple[dict, dict, dict]:
    all_products: dict[str, dict] = {}
    by_slug: dict[str, dict] = {}
    for doc in DOCS:
        if not Path(doc).exists():
            continue
        for p in parse_products_from_doc(doc):
            key = normalize(p["name"])
            if key not in all_products:
                all_products[key] = p
            slug = p.get("slug", "")
            if slug and slug not in by_slug:
                by_slug[slug] = p
    return all_products, by_slug, {normalize(v["name"]): v for v in all_products.values()}


def match_folder_to_doc(folder: dict, by_name: dict, by_slug: dict) -> dict | None:
    leaf = clean_folder_label(folder["leaf"])
    leaf_lower = leaf.lower()
    if leaf_lower in FOLDER_ALIASES and FOLDER_ALIASES[leaf_lower]:
        leaf = FOLDER_ALIASES[leaf_lower]

    candidates = []
    nleaf = normalize(leaf)
    if nleaf in by_name:
        candidates.append(by_name[nleaf])

    slug_guess = slugify(leaf)
    if slug_guess in by_slug:
        candidates.append(by_slug[slug_guess])

    for slug, prod in by_slug.items():
        if slug.startswith(slug_guess) or slug_guess.startswith(slug):
            candidates.append(prod)

    for key, prod in by_name.items():
        if nleaf in key or key in nleaf:
            candidates.append(prod)

    if not candidates:
        return None

    # Prefer exact normalized name match
    for c in candidates:
        if normalize(c["name"]) == nleaf:
            return c
    return candidates[0]


def get_existing_slugs(cur) -> set[str]:
    cur.execute(
        "SELECT post_name FROM wp_posts WHERE post_type='product' AND post_status IN ('publish','draft','private')"
    )
    return {row["post_name"] for row in cur.fetchall()}


def ensure_term(cur, name: str, slug: str, parent: int = 0) -> tuple[int, int]:
    cur.execute(
        """
        SELECT t.term_id, tt.term_taxonomy_id
        FROM wp_terms t
        JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
        WHERE tt.taxonomy = 'product_cat' AND t.slug = %s
        """,
        (slug,),
    )
    row = cur.fetchone()
    if row:
        term_id, tt_id = row["term_id"], row["term_taxonomy_id"]
        if parent:
            cur.execute("UPDATE wp_term_taxonomy SET parent=%s WHERE term_taxonomy_id=%s", (parent, tt_id))
        return term_id, tt_id

    cur.execute("INSERT INTO wp_terms (name, slug) VALUES (%s, %s)", (name, slug))
    term_id = cur.lastrowid
    cur.execute(
        "INSERT INTO wp_term_taxonomy (term_id, taxonomy, description, parent, count) VALUES (%s, 'product_cat', '', %s, 0)",
        (term_id, parent),
    )
    return term_id, cur.lastrowid


def assign_terms(cur, post_id: int, tt_ids: list[int]) -> None:
    for tt_id in tt_ids:
        cur.execute(
            "SELECT object_id FROM wp_term_relationships WHERE object_id=%s AND term_taxonomy_id=%s",
            (post_id, tt_id),
        )
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO wp_term_relationships (object_id, term_taxonomy_id, term_order) VALUES (%s, %s, 0)",
                (post_id, tt_id),
            )


def update_meta(cur, post_id: int, key: str, value: str) -> None:
    cur.execute("SELECT meta_id FROM wp_postmeta WHERE post_id=%s AND meta_key=%s", (post_id, key))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE wp_postmeta SET meta_value=%s WHERE post_id=%s AND meta_key=%s", (value, post_id, key))
    else:
        cur.execute(
            "INSERT INTO wp_postmeta (post_id, meta_key, meta_value) VALUES (%s, %s, %s)",
            (post_id, key, value),
        )


def copy_attachment(cur, src: Path, product_slug: str, index: int) -> int:
    WP_UPLOADS.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(str(src).encode()).hexdigest()[:8]
    filename = f"{product_slug}-{index}-{digest}.webp"
    dest = WP_UPLOADS / filename
    if not dest.exists():
        shutil.copy2(src, dest)

    rel_path = f"2026/07/{filename}"
    url = f"{SITE_URL}/wp-content/uploads/{rel_path}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        INSERT INTO wp_posts (
            post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt,
            post_status, comment_status, ping_status, post_password, post_name,
            to_ping, pinged, post_modified, post_modified_gmt, post_content_filtered,
            post_parent, guid, menu_order, post_type, post_mime_type, comment_count
        ) VALUES (
            1, %s, %s, '', %s, '', 'inherit', 'open', 'closed', '', %s,
            '', '', %s, %s, '', 0, %s, 0, 'attachment', 'image/webp', 0
        )
        """,
        (now, now, src.stem, f"{product_slug}-{index}-{digest}", now, now, url),
    )
    att_id = cur.lastrowid
    update_meta(cur, att_id, "_wp_attached_file", rel_path)
    update_meta(cur, att_id, "_wp_attachment_metadata", "")
    return att_id


def create_product(cur, doc_p: dict, images: list[Path], tt_ids: list[int]) -> int:
    slug = doc_p.get("slug") or slugify(doc_p["name"])
    title = doc_p["name"]
    excerpt = doc_p.get("short_description", "")
    content = doc_p.get("description", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """
        INSERT INTO wp_posts (
            post_author, post_date, post_date_gmt, post_content, post_title, post_excerpt,
            post_status, comment_status, ping_status, post_password, post_name,
            to_ping, pinged, post_modified, post_modified_gmt, post_content_filtered,
            post_parent, guid, menu_order, post_type, comment_count
        ) VALUES (
            1, %s, %s, %s, %s, %s, 'publish', 'open', 'closed', '', %s,
            '', '', %s, %s, '', 0, %s, 0, 'product', 0
        )
        """,
        (now, now, content, title, excerpt, slug, now, now, f"{SITE_URL}/?post_type=product&p=0"),
    )
    post_id = cur.lastrowid
    cur.execute("UPDATE wp_posts SET guid=%s WHERE ID=%s", (f"{SITE_URL}/?post_type=product&p={post_id}", post_id))

    for key, val in {
        "_sku": "",
        "_regular_price": "",
        "_price": "",
        "_stock_status": "instock",
        "_manage_stock": "no",
        "_virtual": "no",
        "_downloadable": "no",
        "_visibility": "visible",
        "_yoast_wpseo_title": doc_p.get("meta_title", ""),
        "_yoast_wpseo_metadesc": doc_p.get("meta_description", ""),
        "_yoast_wpseo_focuskw": doc_p.get("focus_keyword", ""),
    }.items():
        update_meta(cur, post_id, key, val)

    assign_terms(cur, post_id, tt_ids)

    attachment_ids = []
    for i, img in enumerate(images[:8]):
        attachment_ids.append(str(copy_attachment(cur, img, slug, i + 1)))

    if attachment_ids:
        update_meta(cur, post_id, "_thumbnail_id", attachment_ids[0])
        if len(attachment_ids) > 1:
            update_meta(cur, post_id, "_product_image_gallery", ",".join(attachment_ids[1:]))

    parsed = parse_product_content(content)
    if parsed:
        write_acf_data(cur, post_id, parsed)

    return post_id


def refresh_term_counts(cur, tt_ids: list[int]) -> None:
    for tt_id in tt_ids:
        cur.execute(
            """
            UPDATE wp_term_taxonomy tt SET count = (
                SELECT COUNT(DISTINCT tr.object_id)
                FROM wp_term_relationships tr
                JOIN wp_posts p ON tr.object_id = p.ID
                WHERE tr.term_taxonomy_id = tt.term_taxonomy_id
                  AND p.post_type = 'product' AND p.post_status = 'publish'
            ) WHERE tt.term_taxonomy_id = %s
            """,
            (tt_id,),
        )


def main() -> int:
    conn = pymysql.connect(**DB)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    by_name, by_slug, _ = load_doc_catalog()
    existing_slugs = get_existing_slugs(cur)
    folders = dedupe_folders(collect_webp_folders())

    parent_id, parent_tt = ensure_term(cur, PARENT_CAT["name"], PARENT_CAT["slug"], 0)
    subcat_tt: dict[str, int] = {}
    for industry_key, cfg in INDUSTRY_SUBCATS.items():
        _, subcat_tt[industry_key] = ensure_term(cur, cfg["name"], cfg["slug"], parent_id)

    created = []
    skipped_existing = []
    skipped_no_doc = []
    failed = []

    for folder in sorted(folders, key=lambda x: x["rel"].lower()):
        doc_p = match_folder_to_doc(folder, by_name, by_slug)
        if not doc_p:
            skipped_no_doc.append({"folder": folder["rel"], "leaf": folder["leaf"]})
            continue

        slug = doc_p.get("slug") or slugify(doc_p["name"])
        if slug in existing_slugs:
            skipped_existing.append({"folder": folder["rel"], "slug": slug, "title": doc_p["name"]})
            continue

        industry = folder["industry"]
        if industry not in subcat_tt:
            skipped_no_doc.append({"folder": folder["rel"], "reason": f"unknown industry {industry}"})
            continue

        try:
            post_id = create_product(cur, doc_p, folder["images"], [parent_tt, subcat_tt[industry]])
            existing_slugs.add(slug)
            created.append(
                {
                    "id": post_id,
                    "slug": slug,
                    "title": doc_p["name"],
                    "folder": folder["rel"],
                    "url": f"{SITE_URL}/product/{slug}/",
                }
            )
            print(f"CREATED [{post_id}] {doc_p['name']} <- {folder['rel']}", flush=True)
        except Exception as exc:
            failed.append({"folder": folder["rel"], "slug": slug, "error": str(exc)})
            print(f"FAILED {folder['rel']}: {exc}", flush=True)

    refresh_term_counts(cur, [parent_tt, *subcat_tt.values()])
    conn.commit()

    report = {
        "parent_category": PARENT_CAT,
        "subcategories": INDUSTRY_SUBCATS,
        "folders_scanned": len(folders),
        "created_count": len(created),
        "skipped_existing_count": len(skipped_existing),
        "skipped_no_doc_count": len(skipped_no_doc),
        "failed_count": len(failed),
        "created": created,
        "skipped_existing": skipped_existing[:50],
        "skipped_no_doc": skipped_no_doc[:50],
        "failed": failed,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    report_path = Path(r"E:\America Custom Boxes\acb_by_industry_import_report.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== DONE ===")
    print(f"Created: {len(created)}")
    print(f"Skipped (already in WP): {len(skipped_existing)}")
    print(f"Skipped (no doc match): {len(skipped_no_doc)}")
    print(f"Failed: {len(failed)}")
    print(f"Report: {report_path}")

    conn.close()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
