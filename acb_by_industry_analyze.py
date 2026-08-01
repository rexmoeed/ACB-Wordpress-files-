#!/usr/bin/env python3
"""Analyze By Industry import: docs, WebP folders, WP overlap."""
from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import html
import pymysql

import sys

sys.path.insert(0, str(Path(__file__).parent))
from acb_import_products import (  # noqa: E402
    normalize,
    parse_products_from_doc,
    find_doc_for_db_product,
    build_doc_lookups,
)
from acb_import_by_industry import (  # noqa: E402
    DOCS,
    WEBP_ROOT,
    DB,
    PARENT_CAT,
    INDUSTRY_SUBCATS,
    FOLDER_ALIASES,
    clean_folder_label,
    collect_webp_folders,
    dedupe_folders,
    match_folder_to_doc,
    load_doc_catalog,
    slugify,
)

HOT_PRODUCTS_TERM_ID = 23
OUTPUT = Path(r"E:\America Custom Boxes\acb_by_industry_analysis.json")


def parse_all_docs() -> dict:
    doc_counts = {}
    all_products: dict[str, dict] = {}
    by_slug: dict[str, dict] = {}

    for doc in DOCS:
        p = Path(doc)
        if not p.exists():
            doc_counts[p.name] = {"exists": False, "count": 0}
            continue
        prods = parse_products_from_doc(doc)
        doc_counts[p.name] = {
            "exists": True,
            "count": len(prods),
            "with_slug": sum(1 for x in prods if x.get("slug")),
            "with_meta_title": sum(1 for x in prods if x.get("meta_title")),
            "with_meta_description": sum(1 for x in prods if x.get("meta_description")),
            "with_focus_keyword": sum(1 for x in prods if x.get("focus_keyword")),
        }
        for prod in prods:
            key = normalize(prod["name"])
            if key not in all_products:
                all_products[key] = prod
            slug = prod.get("slug", "")
            if slug and slug not in by_slug:
                by_slug[slug] = prod

    products_list = []
    for key, prod in sorted(all_products.items(), key=lambda x: x[1]["name"].lower()):
        products_list.append(
            {
                "name": prod["name"],
                "slug": prod.get("slug", ""),
                "meta_title": prod.get("meta_title", ""),
                "meta_description": prod.get("meta_description", ""),
                "focus_keyword": prod.get("focus_keyword", ""),
                "source": prod.get("source", ""),
            }
        )

    return {
        "doc_files": doc_counts,
        "unique_product_count": len(all_products),
        "unique_with_slug": sum(1 for p in all_products.values() if p.get("slug")),
        "unique_with_seo": sum(
            1
            for p in all_products.values()
            if p.get("meta_title") and p.get("meta_description")
        ),
        "products": products_list,
        "all_products": all_products,
        "by_slug": by_slug,
    }


def resolve_alias(leaf: str) -> str:
    """Apply FOLDER_ALIASES checking both raw and ACB-stripped forms."""
    for candidate in (leaf.lower(), clean_folder_label(leaf).lower()):
        if candidate in FOLDER_ALIASES and FOLDER_ALIASES[candidate]:
            return FOLDER_ALIASES[candidate]
    return clean_folder_label(leaf)


def list_webp_folders() -> dict:
    raw = collect_webp_folders()
    deduped = dedupe_folders(raw)

    by_industry_raw: dict[str, list] = defaultdict(list)
    all_raw_entries = []
    for f in sorted(raw, key=lambda x: x["rel"].lower()):
        entry = {
            "path": f["rel"].replace("\\", "/"),
            "industry": f["industry"],
            "leaf_folder": f["leaf"],
            "normalized_leaf": f["norm_leaf"],
            "clean_label": clean_folder_label(f["leaf"]),
            "image_count": len(f["images"]),
        }
        all_raw_entries.append(entry)
        by_industry_raw[f["industry"]].append(entry)

    by_industry: dict[str, list] = defaultdict(list)
    folder_entries = []
    for f in sorted(deduped, key=lambda x: x["rel"].lower()):
        entry = {
            "path": f["rel"].replace("\\", "/"),
            "industry": f["industry"],
            "leaf_folder": f["leaf"],
            "normalized_leaf": f["norm_leaf"],
            "clean_label": clean_folder_label(f["leaf"]),
            "image_count": len(f["images"]),
        }
        folder_entries.append(entry)
        by_industry[f["industry"]].append(entry)

    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    for f in raw:
        groups[(f["industry"], f["norm_leaf"])].append(f["rel"].replace("\\", "/"))
    duplicate_groups = [
        {"industry": k[0], "normalized_leaf": k[1], "paths": v}
        for k, v in sorted(groups.items())
        if len(v) > 1
    ]

    return {
        "webp_root": str(WEBP_ROOT),
        "raw_leaf_folder_count": len(raw),
        "deduped_leaf_folder_count": len(deduped),
        "duplicate_group_count": len(duplicate_groups),
        "total_webp_files": sum(len(x["images"]) for x in raw),
        "top_level_industries": sorted(by_industry_raw.keys()),
        "raw_folders_by_industry": {k: len(v) for k, v in sorted(by_industry_raw.items())},
        "deduped_folders_by_industry": {k: len(v) for k, v in sorted(by_industry.items())},
        "all_raw_leaf_folders": all_raw_entries,
        "deduped_leaf_folders": folder_entries,
        "duplicate_groups": duplicate_groups,
        "deduped_folders_raw": deduped,
    }


def query_hot_products(conn) -> list[dict]:
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(
        """
        SELECT p.ID, p.post_name AS slug, p.post_title AS title, p.post_status
        FROM wp_posts p
        INNER JOIN wp_term_relationships tr ON p.ID = tr.object_id
        INNER JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
        WHERE tt.term_id = %s
          AND p.post_type = 'product'
          AND p.post_status IN ('publish', 'draft', 'private')
        ORDER BY p.post_title
        """,
        (HOT_PRODUCTS_TERM_ID,),
    )
    return cur.fetchall()


def query_all_product_slugs(conn) -> set[str]:
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute(
        """
        SELECT post_name FROM wp_posts
        WHERE post_type = 'product'
          AND post_status IN ('publish', 'draft', 'private')
        """
    )
    return {row["post_name"] for row in cur.fetchall()}


def folder_slug_guess(folder: dict) -> str:
    return slugify(resolve_alias(folder["leaf"]))


def match_folder_to_doc_improved(folder: dict, by_name: dict, by_slug: dict) -> dict | None:
    """Match folder to doc with fixed alias lookup."""
    leaf = resolve_alias(folder["leaf"])
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

    for c in candidates:
        if normalize(c["name"]) == nleaf:
            return c
    return candidates[0]


def compute_overlap(
    folders: list[dict],
    by_name: dict,
    by_slug: dict,
    hot_products: list[dict],
    all_slugs: set[str],
) -> dict:
    hot_by_slug = {p["slug"]: p for p in hot_products}
    hot_by_title_norm = {normalize(p["title"]): p for p in hot_products}

    matched_existing_all_wp = []
    matched_existing_hot_only = []
    matched_new = []
    unmatched_folders = []
    mapping_samples = []

    for folder in sorted(folders, key=lambda x: x["rel"].lower()):
        doc_p = match_folder_to_doc_improved(folder, by_name, by_slug)
        slug_guess = folder_slug_guess(folder)
        rel = folder["rel"].replace("\\", "/")

        if doc_p:
            slug = doc_p.get("slug") or slugify(doc_p["name"])
            title = doc_p["name"]
            match_method = "doc_match"
        else:
            slug = slug_guess
            title = clean_folder_label(folder["leaf"])
            match_method = "slug_guess_only"

        in_wp = slug in all_slugs
        in_hot = slug in hot_by_slug

        entry = {
            "folder_path": rel,
            "industry": folder["industry"],
            "leaf_folder": folder["leaf"],
            "clean_label": clean_folder_label(folder["leaf"]),
            "normalized_leaf": folder["norm_leaf"],
            "slug_guess": slug_guess,
            "mapped_slug": slug,
            "mapped_title": title,
            "doc_matched": doc_p is not None,
            "match_method": match_method,
            "exists_in_wp": in_wp,
            "exists_in_hot_products": in_hot,
            "wp_product_id": hot_by_slug.get(slug, {}).get("ID") if in_hot else None,
        }

        if doc_p:
            entry["doc_source"] = doc_p.get("source", "")
            entry["doc_meta_title"] = doc_p.get("meta_title", "")

        if in_wp:
            matched_existing_all_wp.append(entry)
            if in_hot:
                matched_existing_hot_only.append(entry)
        elif doc_p:
            matched_new.append(entry)
        else:
            unmatched_folders.append(entry)

        if len(mapping_samples) < 15 and doc_p:
            mapping_samples.append(
                {
                    "folder": rel,
                    "leaf": folder["leaf"],
                    "doc_name": doc_p["name"],
                    "doc_slug": doc_p.get("slug", ""),
                    "industry": folder["industry"],
                    "status": "existing_in_wp" if in_wp else "new",
                    "in_hot_products": in_hot,
                }
            )

    # Also check doc products vs hot products overlap by slug
    hot_slugs = set(hot_by_slug.keys())
    doc_slugs = set(by_slug.keys())
    doc_hot_overlap = sorted(hot_slugs & doc_slugs)
    doc_hot_only_in_wp = sorted(hot_slugs - doc_slugs)
    doc_only_not_in_wp = sorted(doc_slugs - hot_slugs)

    new_by_industry: dict[str, int] = defaultdict(int)
    for e in matched_new:
        new_by_industry[e["industry"]] += 1

    existing_all_by_industry: dict[str, int] = defaultdict(int)
    for e in matched_existing_all_wp:
        existing_all_by_industry[e["industry"]] += 1

    existing_hot_by_industry: dict[str, int] = defaultdict(int)
    for e in matched_existing_hot_only:
        existing_hot_by_industry[e["industry"]] += 1

    # Folders with doc match not yet in WP (import candidates)
    import_candidates = [e for e in matched_new if e["doc_matched"]]

    baseline_new_folders = []
    baseline_hot_overlap = []
    for folder in sorted(folders, key=lambda x: x["rel"].lower()):
        doc_p = match_folder_to_doc_improved(folder, by_name, by_slug)
        if not doc_p:
            continue
        slug = doc_p.get("slug") or slugify(doc_p["name"])
        rel = folder["rel"].replace("\\", "/")
        entry = {
            "folder_path": rel,
            "mapped_slug": slug,
            "mapped_title": doc_p["name"],
            "industry": folder["industry"],
        }
        if slug in hot_slugs:
            baseline_hot_overlap.append(entry)
        else:
            baseline_new_folders.append(entry)

    baseline_new_by_industry: dict[str, int] = defaultdict(int)
    for e in baseline_new_folders:
        baseline_new_by_industry[e["industry"]] += 1

    return {
        "overlap_with_all_wp_count": len(matched_existing_all_wp),
        "overlap_with_hot_products_count": len(matched_existing_hot_only),
        "new_product_count": len(matched_new),
        "import_candidates_count": len(import_candidates),
        "unmatched_folder_count": len(unmatched_folders),
        "doc_matched_folder_count": len(matched_existing_all_wp) + len(matched_new),
        "new_by_industry": dict(sorted(new_by_industry.items())),
        "existing_all_wp_by_industry": dict(sorted(existing_all_by_industry.items())),
        "existing_hot_by_industry": dict(sorted(existing_hot_by_industry.items())),
        "doc_hot_slug_overlap_count": len(doc_hot_overlap),
        "doc_hot_slug_overlap": doc_hot_overlap,
        "hot_products_not_in_docs_count": len(doc_hot_only_in_wp),
        "hot_products_not_in_docs": doc_hot_only_in_wp[:20],
        "docs_not_in_hot_products_count": len(doc_only_not_in_wp),
        "matched_existing_all_wp": matched_existing_all_wp,
        "matched_existing_hot_only": matched_existing_hot_only,
        "matched_new": matched_new,
        "unmatched_folders": unmatched_folders,
        "sample_mappings": mapping_samples,
        "baseline_at_83_hot_products": {
            "overlap_with_hot_products": len(baseline_hot_overlap),
            "new_to_import": len(baseline_new_folders),
            "new_by_industry": dict(sorted(baseline_new_by_industry.items())),
            "new_products": baseline_new_folders,
            "hot_overlaps": baseline_hot_overlap,
        },
    }


def propose_category_tree(folders_by_industry: dict[str, int]) -> dict:
    subcats = []
    for key, count in sorted(folders_by_industry.items()):
        cfg = INDUSTRY_SUBCATS.get(key, {})
        display = cfg.get("name") or key.title()
        slug = cfg.get("slug") or slugify(key)
        if key.lower() == "candles":
            display = "Candle Boxes"
            slug = "candle-boxes"
        elif key.upper() == "CBD":
            display = "CBD Boxes"
            slug = "cbd-boxes"
        elif key.lower() == "bakery":
            display = "Bakery"
            slug = "bakery"
        subcats.append(
            {
                "folder_key": key,
                "name": display,
                "slug": slug,
                "expected_product_count": count,
            }
        )

    return {
        "parent": PARENT_CAT,
        "subcategories": subcats,
        "total_products_in_tree": sum(folders_by_industry.values()),
    }


def propose_mapping_strategy() -> dict:
    return {
        "overview": (
            "Map each WebP leaf folder to a catalog doc product using normalized "
            "folder names, slug guesses, and explicit aliases for typos/abbreviations."
        ),
        "steps": [
            "Strip 'ACB ' prefix from folder name and collapse whitespace.",
            "Apply FOLDER_ALIASES for known typos (e.g. 'acb tealight canle' -> tealight candle packaging).",
            "Normalize to alphanumeric key via normalize() and match against doc product names.",
            "Fallback: slugify(clean_label) and match doc slugs (exact, prefix, or contains).",
            "If doc match found, use doc slug/title/SEO; skip import if slug already exists in WP.",
            "Assign product_cat: parent 'By Industry' + subcat from top-level WebP folder (Bakery, candles, CBD).",
        ],
        "normalization_rules": {
            "prefix_strip": "^ACB\\s+",
            "normalize_fn": "lowercase, remove non-alphanumeric",
            "slugify_fn": "ascii fold, hyphenate spaces, lowercase",
        },
        "known_aliases": FOLDER_ALIASES,
        "dedupe_rule": (
            "When multiple folders normalize to same industry+leaf key, prefer non-ACB-prefixed "
            "name and folder with more images."
        ),
    }


def main() -> int:
    docs = parse_all_docs()
    webp = list_webp_folders()

    conn = pymysql.connect(**DB)
    try:
        hot_products = query_hot_products(conn)
        all_slugs = query_all_product_slugs(conn)
    finally:
        conn.close()

    by_name, by_slug, _ = load_doc_catalog()
    overlap = compute_overlap(
        webp["deduped_folders_raw"],
        by_name,
        by_slug,
        hot_products,
        all_slugs,
    )

    category_tree = propose_category_tree(webp["deduped_folders_by_industry"])

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "documents_dir": str(Path(DOCS[0]).parent),
            "product_catalog_docs": [Path(d).name for d in DOCS],
            "skipped_category_docs": [
                "ACB-Category-Pages-Batch1.docx",
                "ACB-Category-Pages-Batch2.docx",
            ],
            "webp_root": webp["webp_root"],
            "wordpress": {
                "host": DB["host"],
                "port": DB["port"],
                "database": DB["database"],
                "hot_products_term_id": HOT_PRODUCTS_TERM_ID,
            },
        },
        "summary": {
            "unique_doc_products": docs["unique_product_count"],
            "doc_products_with_slug": docs["unique_with_slug"],
            "doc_products_with_full_seo": docs["unique_with_seo"],
            "webp_raw_leaf_folders": webp["raw_leaf_folder_count"],
            "webp_deduped_leaf_folders": webp["deduped_leaf_folder_count"],
            "webp_duplicate_groups": webp["duplicate_group_count"],
            "webp_total_files": webp["total_webp_files"],
            "existing_hot_products": len(hot_products),
            "existing_all_wp_products": len(all_slugs),
            "folder_wp_overlap_all": overlap["overlap_with_all_wp_count"],
            "folder_hot_products_overlap": overlap["overlap_with_hot_products_count"],
            "new_products_to_import": overlap["new_product_count"],
            "import_candidates_with_doc": overlap["import_candidates_count"],
            "folders_without_doc_match": overlap["unmatched_folder_count"],
            "baseline_new_at_83_hot_products": overlap["baseline_at_83_hot_products"]["new_to_import"],
            "note": (
                "WP currently has 127 total products: 83 in Hot Products + 44 already imported under By Industry. "
                "baseline_new_at_83_hot_products is the count if starting from 83 Hot Products only."
            ),
        },
        "documents": {
            "per_file_counts": docs["doc_files"],
            "unique_products": docs["products"],
        },
        "webp_folders": {
            "top_level_industries": webp["top_level_industries"],
            "raw_by_industry_counts": webp["raw_folders_by_industry"],
            "deduped_by_industry_counts": webp["deduped_folders_by_industry"],
            "duplicate_groups": webp["duplicate_groups"],
            "all_raw_leaf_folders": webp["all_raw_leaf_folders"],
            "deduped_leaf_folders": webp["deduped_leaf_folders"],
        },
        "existing_wp_hot_products": [
            {"id": p["ID"], "slug": p["slug"], "title": p["title"], "status": p["post_status"]}
            for p in hot_products
        ],
        "overlap_analysis": {
            "new_product_count": overlap["new_product_count"],
            "overlap_with_all_wp_count": overlap["overlap_with_all_wp_count"],
            "overlap_with_hot_products_count": overlap["overlap_with_hot_products_count"],
            "unmatched_folder_count": overlap["unmatched_folder_count"],
            "doc_matched_folder_count": overlap["doc_matched_folder_count"],
            "new_by_industry": overlap["new_by_industry"],
            "existing_all_wp_by_industry": overlap["existing_all_wp_by_industry"],
            "existing_hot_by_industry": overlap["existing_hot_by_industry"],
            "doc_hot_slug_overlap_count": overlap["doc_hot_slug_overlap_count"],
            "hot_products_not_in_docs_count": overlap["hot_products_not_in_docs_count"],
            "docs_not_in_hot_products_count": overlap["docs_not_in_hot_products_count"],
            "baseline_at_83_hot_products": overlap["baseline_at_83_hot_products"],
        },
        "folder_to_product_mapping": {
            "strategy": propose_mapping_strategy(),
            "sample_mappings": overlap["sample_mappings"],
            "matched_existing_all_wp": overlap["matched_existing_all_wp"],
            "matched_existing_hot_only": overlap["matched_existing_hot_only"],
            "matched_new": overlap["matched_new"],
            "unmatched_folders": overlap["unmatched_folders"],
        },
        "category_tree_proposal": category_tree,
    }

    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"\nWritten: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
