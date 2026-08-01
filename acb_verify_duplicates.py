#!/usr/bin/env python3
"""Verify Hot Products in WP vs ACB Data/converted source folders."""
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import pymysql

SOURCE = Path(r"D:\Downloads\ACB Data")
CONVERTED = SOURCE / "converted"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
DB = dict(host="127.0.0.1", port=10005, user="root", password="root", database="local", charset="utf8mb4")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def folder_product_name(rel: str) -> str:
    """Normalize ACB folder name to approximate product name."""
    name = Path(rel).name
    name = re.sub(r"^ACB\s+", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def scan_source_folders():
    folders = []
    for root, _, files in os.walk(SOURCE):
        rp = Path(root)
        if "converted" in rp.parts:
            continue
        imgs = [f for f in files if Path(f).suffix.lower() in IMAGE_EXTS]
        if imgs:
            rel = str(rp.relative_to(SOURCE))
            folders.append(
                {
                    "rel": rel,
                    "leaf": Path(rel).name,
                    "norm_leaf": norm(folder_product_name(rel)),
                    "image_count": len(imgs),
                    "images": sorted(imgs),
                }
            )
    return folders


def scan_converted():
    entries = []
    for root, _, files in os.walk(CONVERTED):
        webps = [f for f in files if f.lower().endswith(".webp")]
        if webps:
            rel = str(Path(root).relative_to(CONVERTED))
            entries.append({"rel": rel, "webp_count": len(webps), "files": sorted(webps)})
    return entries


def get_hot_products(conn):
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(
        """
        SELECT p.ID, p.post_title, p.post_name, p.post_status
        FROM wp_posts p
        INNER JOIN wp_term_relationships tr ON p.ID = tr.object_id
        INNER JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
        INNER JOIN wp_terms t ON tt.term_id = t.term_id
        WHERE p.post_type='product'
          AND tt.taxonomy='product_cat'
          AND t.slug='hot-products'
        ORDER BY p.post_title
        """
    )
    return cur.fetchall()


def get_all_products(conn):
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(
        """
        SELECT ID, post_title, post_name, post_status
        FROM wp_posts
        WHERE post_type='product'
          AND post_status IN ('publish','draft','private')
        ORDER BY post_title
        """
    )
    return cur.fetchall()


def dup_details(items, key_fn):
    counts = Counter(key_fn(x) for x in items)
    dups = {k: c for k, c in counts.items() if c > 1}
    detail = defaultdict(list)
    for item in items:
        k = key_fn(item)
        if counts[k] > 1:
            detail[k].append(item)
    return dups, detail


def match_folders_to_products(folders, products):
    by_norm_title = defaultdict(list)
    for p in products:
        by_norm_title[norm(p["post_title"])].append(p)

    matched = []
    unmatched_folders = []
    multi_match_folders = []

    for f in folders:
        candidates = by_norm_title.get(f["norm_leaf"], [])
        if not candidates:
            # fuzzy: slug contains or title contains folder words
            for p in products:
                if f["norm_leaf"] in norm(p["post_title"]) or norm(p["post_name"]) in f["norm_leaf"]:
                    candidates.append(p)
            # dedupe
            seen = set()
            uniq = []
            for c in candidates:
                if c["ID"] not in seen:
                    seen.add(c["ID"])
                    uniq.append(c)
            candidates = uniq

        if len(candidates) == 1:
            matched.append({"folder": f["rel"], "product_id": candidates[0]["ID"], "product": candidates[0]["post_title"]})
        elif len(candidates) > 1:
            multi_match_folders.append(
                {
                    "folder": f["rel"],
                    "candidates": [{"id": c["ID"], "title": c["post_title"], "slug": c["post_name"]} for c in candidates],
                }
            )
        else:
            unmatched_folders.append(f["rel"])

    # products matched by multiple folders
    prod_folder_map = defaultdict(list)
    for m in matched:
        prod_folder_map[m["product_id"]].append(m["folder"])
    products_with_multi_folders = {pid: fl for pid, fl in prod_folder_map.items() if len(fl) > 1}

    return matched, unmatched_folders, multi_match_folders, products_with_multi_folders


def main():
    folders = scan_source_folders()
    converted = scan_converted()

    conn = pymysql.connect(**DB)
    hot = get_hot_products(conn)
    all_products = get_all_products(conn)
    conn.close()

    # Source folder duplicate leaf names
    leaf_map = defaultdict(list)
    for f in folders:
        leaf_map[f["norm_leaf"]].append(f["rel"])
    dup_source_names = {k: v for k, v in leaf_map.items() if len(v) > 1}

    hot_dup_titles, hot_title_detail = dup_details(hot, lambda p: norm(p["post_title"]))
    hot_dup_slugs, hot_slug_detail = dup_details(hot, lambda p: p["post_name"])
    site_dup_titles, site_title_detail = dup_details(all_products, lambda p: norm(p["post_title"]))
    site_dup_slugs, site_slug_detail = dup_details(all_products, lambda p: p["post_name"])

    matched, unmatched_folders, multi_match_folders, products_with_multi_folders = match_folders_to_products(
        folders, hot
    )

    report = {
        "source_image_folders": len(folders),
        "converted_webp_folders": len(converted),
        "converted_total_webp_files": sum(c["webp_count"] for c in converted),
        "hot_products_in_wp": len(hot),
        "total_wp_products": len(all_products),
        "hot_duplicate_titles_count": len(hot_dup_titles),
        "hot_duplicate_slugs_count": len(hot_dup_slugs),
        "site_duplicate_titles_count": len(site_dup_titles),
        "site_duplicate_slugs_count": len(site_dup_slugs),
        "duplicate_source_folder_names_count": len(dup_source_names),
        "folder_to_product_matched": len(matched),
        "folder_to_product_unmatched": len(unmatched_folders),
        "folder_multi_product_matches": len(multi_match_folders),
        "products_with_multiple_source_folders": len(products_with_multi_folders),
        "verdict": "",
    }

    issues = []
    if hot_dup_titles:
        issues.append(f"{len(hot_dup_titles)} duplicate title(s) in Hot Products")
    if hot_dup_slugs:
        issues.append(f"{len(hot_dup_slugs)} duplicate slug(s) in Hot Products")
    if site_dup_titles:
        issues.append(f"{len(site_dup_titles)} duplicate title(s) site-wide")
    if site_dup_slugs:
        issues.append(f"{len(site_dup_slugs)} duplicate slug(s) site-wide")
    if products_with_multi_folders:
        issues.append(f"{len(products_with_multi_folders)} product(s) linked to multiple source folders")

    report["verdict"] = "NO DUPLICATION ISSUES" if not issues else "DUPLICATION / OVERLAP FOUND"
    report["issues"] = issues

    out = {
        "summary": report,
        "hot_duplicate_titles": {k: [{"id": p["ID"], "title": p["post_title"], "slug": p["post_name"]} for p in hot_title_detail[k]] for k in hot_dup_titles},
        "hot_duplicate_slugs": {k: [{"id": p["ID"], "title": p["post_title"], "slug": p["post_name"]} for p in hot_slug_detail[k]] for k in hot_dup_slugs},
        "duplicate_source_folder_names": dup_source_names,
        "unmatched_source_folders": unmatched_folders[:50],
        "folder_multi_product_matches": multi_match_folders[:30],
        "products_with_multiple_source_folders": {
            str(pid): {"product": next(p["post_title"] for p in hot if p["ID"] == pid), "folders": fl}
            for pid, fl in list(products_with_multi_folders.items())[:30]
        },
        "hot_product_list": [{"id": p["ID"], "title": p["post_title"], "slug": p["post_name"]} for p in hot],
    }

    out_path = Path(r"E:\America Custom Boxes\acb_duplicate_check_report.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if issues:
        print("\nISSUES:")
        for i in issues:
            print(f"  - {i}")
    print(f"\nFull report: {out_path}")


if __name__ == "__main__":
    main()
