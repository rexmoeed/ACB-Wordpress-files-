#!/usr/bin/env python3
"""
Fix WooCommerce product gallery images on live americacustomboxes.com via REST API.

Reads acb_live_gallery_report.json, matches local image folders to products,
uploads missing images, and sets featured + gallery (target 4-6 gallery images).

Auth: set ACB_WP_USER / ACB_WP_APP_PASSWORD (WordPress application password),
or WC_CONSUMER_KEY / WC_CONSUMER_SECRET for WooCommerce-only endpoints.
Falls back to USER/PASSWORD constants below (login password rarely works for REST).
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from acb_import_by_industry import (  # noqa: E402
    FOLDER_ALIASES,
    clean_folder_label,
    collect_webp_folders,
    dedupe_folders,
    load_doc_catalog,
    match_folder_to_doc,
    slugify,
)
from acb_import_products import normalize  # noqa: E402

LIVE = "https://americacustomboxes.com"
USER = os.environ.get("ACB_WP_USER", "admin")
PASSWORD = os.environ.get("ACB_WP_APP_PASSWORD", "Moeed@0096@#")
WC_KEY = os.environ.get("WC_CONSUMER_KEY", "")
WC_SECRET = os.environ.get("WC_CONSUMER_SECRET", "")

CONVERTED = Path(r"D:\Downloads\ACB Data\converted")
WEBP = Path(r"D:\Downloads\ACB Data\New Images WebP")
AUDIT = ROOT / "acb_live_gallery_report.json"
REPORT = ROOT / "acb_live_gallery_fix_report.json"

MIN_GALLERY = 4
MAX_GALLERY = 6
IMG_EXT = {".webp", ".jpg", ".jpeg", ".png"}

# Manual slug -> folder path substring (converted or webp)
MANUAL_SLUG_FOLDER_REL = {
    "cardboard-gift-boxes": "Kraft Gift Boxes",
    "cbd-vape-cartridge-boxes": "CBD CORRUGATED MAILER",
    "corporate-welcome-kits": "Chocolate Gift Boxes",
    "cosmetic-labels": "TAMPER-EVIDENT CBD SEALS",
    "custom-barcode-labels": "TAMPER-EVIDENT CBD SEALS",
    "custom-bottle-labels": "TAMPER-EVIDENT CBD SEALS",
    "custom-jar-labels": "TAMPER-EVIDENT CBD SEALS",
    "custom-product-labels": "TAMPER-EVIDENT CBD SEALS",
    "custom-qr-code-stickers": "TAMPER-EVIDENT CBD SEALS",
    "custom-shipping-labels": "TAMPER-EVIDENT CBD SEALS",
    "disposable-vape-pen-boxes": "CBD CORRUGATED MAILER",
    "hair-extension-tuck-boxes": "Eco Kraft Tuck Boxes",
    "lipstick-tuck-boxes": "Eco Kraft Tuck Boxes",
    "medicine-vial-tuck-boxes": "Eco Kraft Tuck Boxes",
    "personalized-favor-boxes": "Chocolate Gift Boxes",
    "reverse-tuck-end-boxes": "Eco Kraft Tuck Boxes",
    "serum-bottle-boxes-with-inserts": "Skincare",
    "soap-wrap-tuck-boxes": "Eco Kraft Tuck Boxes",
    "straight-tuck-end-boxes": "Eco Kraft Tuck Boxes",
    "tamper-proof-seal-stickers": "TAMPER-EVIDENT CBD SEALS",
    "wedding-invitation-boxes": "Chocolate Gift Boxes",
    "cbd-bath-bomb-gift-boxes": "CBD Bath Bomb",
    "cbd-starter-kit-boxes": "CBD STARTER KIT",
    "custom-cbd-cream-boxes": "CBD Cream",
}

DIELINE_RE = re.compile(r"dieline|die[_\-]line|die-line|template|flat\.pack", re.I)
FEATURED_POSITIVE = re.compile(r"product|render|photo|front|hero|main|mockup|box", re.I)
FEATURED_NEGATIVE = re.compile(r"dieline|die[_\-]line|template|flat\.pack|open|inside|back", re.I)


def wp_auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "User-Agent": "ACB-GalleryFix/1.0",
    }


def wc_auth_query() -> str:
    if WC_KEY and WC_SECRET:
        from urllib.parse import quote

        return f"consumer_key={quote(WC_KEY)}&consumer_secret={quote(WC_SECRET)}"
    return ""


def api_json(
    method: str,
    path: str,
    payload: dict | None = None,
    *,
    use_wp_auth: bool = True,
    timeout: int = 120,
) -> dict | list:
    sep = "&" if "?" in path else "?"
    wc_q = wc_auth_query()
    url = f"{LIVE}{path}{sep}{wc_q}" if wc_q and "/wc/v3/" in path else f"{LIVE}{path}"

    headers: dict[str, str] = {"User-Agent": "ACB-GalleryFix/1.0"}
    if use_wp_auth and not (wc_q and "/wc/v3/" in path):
        headers.update(wp_auth_header())
    elif use_wp_auth and "/wc/v3/" in path and not wc_q:
        headers.update(wp_auth_header())

    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> {exc.code}: {body[:600]}") from exc


def test_auth() -> dict:
    results: dict = {"wp_user": None, "wc_products": None, "media": None}
    try:
        me = api_json("GET", "/wp-json/wp/v2/users/me")
        results["wp_user"] = {"ok": True, "name": me.get("name"), "id": me.get("id")}
    except Exception as exc:
        results["wp_user"] = {"ok": False, "error": str(exc)}

    try:
        batch = api_json("GET", "/wp-json/wc/v3/products?per_page=1&status=publish")
        results["wc_products"] = {"ok": True, "count": len(batch) if isinstance(batch, list) else 0}
    except Exception as exc:
        results["wc_products"] = {"ok": False, "error": str(exc)}

    return results


def store_products() -> list[dict]:
    out: list[dict] = []
    for page in range(1, 10):
        req = urllib.request.Request(
            f"{LIVE}/wp-json/wc/store/products?per_page=100&page={page}",
            headers={"User-Agent": "ACB-GalleryFix/1.0"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            batch = json.loads(resp.read().decode())
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
    return out


def wc_products() -> list[dict]:
    out: list[dict] = []
    for page in range(1, 10):
        batch = api_json("GET", f"/wp-json/wc/v3/products?per_page=100&page={page}&status=publish")
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
    return out


def collect_converted_folders() -> list[dict]:
    folders: list[dict] = []
    if not CONVERTED.exists():
        return folders
    for dirpath, _, filenames in os.walk(CONVERTED):
        imgs = sorted(
            Path(dirpath) / f for f in filenames if Path(f).suffix.lower() in IMG_EXT
        )
        if not imgs:
            continue
        rel = str(Path(dirpath).relative_to(CONVERTED))
        leaf = Path(dirpath).name
        folders.append(
            {
                "source": "converted",
                "rel": rel,
                "leaf": leaf,
                "norm_leaf": normalize(clean_folder_label(leaf)),
                "images": imgs,
            }
        )
    return folders


def collect_all_folders() -> list[dict]:
    webp = dedupe_folders(collect_webp_folders())
    converted = collect_converted_folders()
    return webp + converted


def is_dieline(path: Path) -> bool:
    text = f"{path.name} {path.parent.name}"
    return bool(DIELINE_RE.search(text))


def featured_score(path: Path) -> int:
    if is_dieline(path):
        return -1000
    name = path.stem.lower()
    score = 0
    if FEATURED_POSITIVE.search(name):
        score += 10
    if FEATURED_NEGATIVE.search(name):
        score -= 8
    if re.fullmatch(r"\d+", name) or name in ("01", "1", "main", "hero"):
        score += 5
    return score


def product_images_only(paths: list[Path]) -> list[Path]:
    product = [p for p in paths if not is_dieline(p)]
    return product if product else list(paths)


def pick_featured_and_gallery(
    paths: list[Path],
    *,
    min_gallery: int = MIN_GALLERY,
    max_gallery: int = MAX_GALLERY,
) -> tuple[Path | None, list[Path]]:
    """Return (best featured, gallery list up to max_gallery)."""
    candidates = product_images_only(paths)
    if not candidates:
        return None, []

    ranked = sorted(candidates, key=lambda p: (-featured_score(p), p.name.lower()))
    featured = ranked[0]
    gallery_pool = [p for p in ranked if p != featured]
    gallery_pool.sort(key=lambda p: p.name.lower())

    take = min(max_gallery, max(min_gallery, len(gallery_pool)))
    if len(gallery_pool) >= min_gallery:
        take = min(max_gallery, len(gallery_pool))
    else:
        take = len(gallery_pool)

    return featured, gallery_pool[:take]


def score_folder(product_name: str, product_slug: str, folder: dict) -> int:
    pn = normalize(html.unescape(product_name))
    ps = normalize(product_slug.replace("-", ""))
    leaf = folder["norm_leaf"]
    raw_leaf = normalize(clean_folder_label(folder["leaf"]))

    if leaf == pn or raw_leaf == pn:
        return 100
    if normalize(product_slug) == normalize(slugify(folder["leaf"])):
        return 95
    if leaf and (leaf in pn or pn in leaf):
        return 80
    if raw_leaf and (raw_leaf in pn or pn in raw_leaf):
        return 75
    if ps and (ps in leaf or leaf in ps):
        return 70

    alias = FOLDER_ALIASES.get(folder["leaf"].lower(), "")
    if alias and normalize(alias) == pn:
        return 90
    return 0


def best_folder_direct(product_name: str, product_slug: str, folders: list[dict]) -> dict | None:
    scored = [(score_folder(product_name, product_slug, f), f) for f in folders]
    scored = [x for x in scored if x[0] >= 65]
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], -len(x[1]["images"]), x[1]["rel"]))
    return scored[0][1]


def folder_by_rel_substring(folders: list[dict], needle: str) -> dict | None:
    needle_norm = needle.replace("/", "\\").lower()
    matches = [f for f in folders if needle_norm in f["rel"].lower()]
    if not matches:
        return None
    matches.sort(key=lambda f: (-len(f["images"]), f["rel"]))
    return matches[0]


def match_product_to_folder(
    product_name: str,
    product_slug: str,
    folders: list[dict],
    by_name: dict,
    by_slug: dict,
) -> tuple[dict | None, str]:
    """Match live product to local image folder (manual + direct + doc-bridge + fuzzy)."""
    manual = MANUAL_SLUG_FOLDER_REL.get(product_slug)
    if manual:
        found = folder_by_rel_substring(folders, manual)
        if found:
            return found, "manual"

    direct = best_folder_direct(product_name, product_slug, folders)
    if direct:
        return direct, "direct"

    doc = by_slug.get(product_slug) or by_name.get(normalize(html.unescape(product_name)))
    if doc:
        for folder in folders:
            matched = match_folder_to_doc(folder, by_name, by_slug)
            if not matched:
                continue
            if matched.get("slug") == product_slug:
                return folder, "doc_slug"
            if normalize(matched["name"]) == normalize(doc["name"]):
                return folder, "doc_name"

        fuzzy = best_folder_direct(doc["name"], doc.get("slug") or product_slug, folders)
        if fuzzy:
            return fuzzy, "doc_fuzzy"

    return None, "none"


def filename_key(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "", path.stem.lower())


def existing_image_keys(images: list[dict]) -> set[str]:
    keys: set[str] = set()
    for img in images:
        src = img.get("src") or ""
        name = img.get("name") or src.split("/")[-1]
        keys.add(filename_key(Path(name)))
        keys.add(re.sub(r"[^a-z0-9]+", "", src.lower()))
    return keys


def upload_media(image_path: Path) -> dict:
    data = image_path.read_bytes()
    mime = mimetypes.guess_type(str(image_path))[0] or "image/webp"
    headers = wp_auth_header()
    headers["Content-Disposition"] = f'attachment; filename="{image_path.name}"'
    headers["Content-Type"] = mime

    req = urllib.request.Request(
        f"{LIVE}/wp-json/wp/v2/media",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"media upload {image_path.name} -> {exc.code}: {body[:600]}") from exc


def build_image_entry(media: dict) -> dict:
    title = media.get("title") or {}
    name = title.get("rendered") if isinstance(title, dict) else str(title)
    return {
        "id": media["id"],
        "src": media.get("source_url", ""),
        "name": name or media.get("slug", ""),
    }


def update_product_images(product_id: int, image_payload: list[dict]) -> dict:
    slim = [{"id": img["id"]} for img in image_payload]
    return api_json("PUT", f"/wp-json/wc/v3/products/{product_id}", {"images": slim})


def fix_product(
    wc_p: dict,
    store_p: dict,
    folder: dict,
    *,
    dry_run: bool = False,
) -> dict:
    name = html.unescape(wc_p.get("name", ""))
    slug = wc_p.get("slug", "")
    product_id = wc_p["id"]
    existing = store_p.get("images") or []
    gallery_before = max(0, len(existing) - 1)

    featured_local, gallery_local = pick_featured_and_gallery(folder["images"])
    if not featured_local and not gallery_local:
        raise RuntimeError("no usable source images after dieline filter")

    existing_keys = existing_image_keys(existing)
    image_payload: list[dict] = []
    uploaded = 0

    # Featured: keep existing if present, else upload best local
    if existing:
        image_payload.append(
            {"id": existing[0]["id"], "src": existing[0].get("src"), "name": existing[0].get("name")}
        )
    elif featured_local:
        if dry_run:
            image_payload.append({"id": 0, "src": str(featured_local), "name": featured_local.name})
        else:
            media = upload_media(featured_local)
            image_payload.append(build_image_entry(media))
            uploaded += 1
            time.sleep(0.25)

    # Gallery: keep existing gallery entries, then add local until 4-6
    for img in existing[1:]:
        image_payload.append({"id": img["id"], "src": img.get("src"), "name": img.get("name")})

    gallery_count = len(image_payload) - (1 if image_payload else 0)
    for img_path in gallery_local:
        if gallery_count >= MAX_GALLERY:
            break
        key = filename_key(img_path)
        if key in existing_keys:
            continue
        if dry_run:
            image_payload.append({"id": 0, "src": str(img_path), "name": img_path.name})
            gallery_count += 1
            continue
        media = upload_media(img_path)
        entry = build_image_entry(media)
        image_payload.append(entry)
        existing_keys.add(key)
        uploaded += 1
        gallery_count += 1
        time.sleep(0.25)

    gallery_after = max(0, len(image_payload) - 1)
    available = len(gallery_local)
    min_required = min(MIN_GALLERY, available) if available else MIN_GALLERY
    if gallery_after < min_required and not dry_run:
        raise RuntimeError(
            f"only {gallery_after} gallery images after upload (need {min_required}+, folder has {available})"
        )

    if not dry_run and image_payload:
        update_product_images(product_id, image_payload)

    return {
        "slug": slug,
        "name": name,
        "product_id": product_id,
        "folder": folder["rel"],
        "folder_source": folder.get("source", "webp"),
        "before_gallery": gallery_before,
        "after_gallery": gallery_after,
        "total_images": len(image_payload),
        "uploaded": uploaded,
        "dry_run": dry_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fix live WooCommerce product galleries")
    parser.add_argument("--test-auth", action="store_true", help="Only test API authentication")
    parser.add_argument("--dry-run", action="store_true", help="Match and plan without uploading")
    args = parser.parse_args()

    print("Testing live API auth...", flush=True)
    auth = test_auth()
    print(json.dumps(auth, indent=2), flush=True)

    if args.test_auth:
        ok = auth.get("wp_user", {}).get("ok") or auth.get("wc_products", {}).get("ok")
        if not ok:
            print(
                "\nAuth failed. Create a WordPress Application Password for user 'admin' "
                "(Users -> Profile -> Application Passwords) and set ACB_WP_APP_PASSWORD, "
                "or set WC_CONSUMER_KEY / WC_CONSUMER_SECRET.",
                flush=True,
            )
        return 0 if ok else 1

    if not auth.get("wp_user", {}).get("ok"):
        print(
            "ERROR: WordPress auth failed — media upload requires a valid application password.\n"
            "Set ACB_WP_APP_PASSWORD or fix credentials before running fixes.",
            flush=True,
        )
        return 1

    if not auth.get("wc_products", {}).get("ok"):
        print("ERROR: WooCommerce v3 auth failed — cannot update products.", flush=True)
        return 1

    if not AUDIT.exists():
        print(f"ERROR: Audit file not found: {AUDIT}", flush=True)
        return 1

    audit_rows = json.loads(AUDIT.read_text(encoding="utf-8")) if AUDIT.exists() else []
    # Refresh counts from live store API (audit file may be stale after partial fixes)
    live_store = {p["slug"]: p for p in store_products()}
    refreshed = []
    for row in audit_rows:
        slug = row["slug"]
        live = live_store.get(slug)
        gallery = max(0, len(live.get("images") or []) - 1) if live else row.get("gallery", 0)
        refreshed.append({**row, "gallery": gallery})
    audit_rows = refreshed
    AUDIT.write_text(json.dumps(audit_rows, indent=2, ensure_ascii=False), encoding="utf-8")

    need_rows = [r for r in audit_rows if r.get("gallery", 0) < MIN_GALLERY]
    need_slugs = {r["slug"] for r in need_rows}

    folders = collect_all_folders()
    by_name, by_slug, _ = load_doc_catalog()

    print(f"Loaded {len(folders)} image folders, {len(need_slugs)} products need gallery fix", flush=True)

    store = {p["slug"]: p for p in store_products()}
    wc = {p["slug"]: p for p in wc_products()}

    fixed: list[dict] = []
    skipped: list[dict] = []
    failed: list[dict] = []
    no_folder: list[dict] = []

    for row in sorted(need_rows, key=lambda r: r["slug"]):
        slug = row["slug"]
        wc_p = wc.get(slug)
        st_p = store.get(slug)
        if not wc_p or not st_p:
            failed.append({"slug": slug, "error": "product not found in API"})
            continue

        name = html.unescape(wc_p.get("name", ""))
        current_gallery = max(0, len(st_p.get("images") or []) - 1)
        if current_gallery >= MIN_GALLERY:
            skipped.append(
                {"slug": slug, "name": name, "reason": "already ok", "gallery": current_gallery}
            )
            continue

        folder, match_method = match_product_to_folder(name, slug, folders, by_name, by_slug)
        if not folder:
            no_folder.append({"slug": slug, "name": name, "gallery": current_gallery})
            continue

        try:
            result = fix_product(wc_p, st_p, folder, dry_run=args.dry_run)
            result["match_method"] = match_method
            fixed.append(result)
            print(
                f"{'DRY ' if args.dry_run else ''}FIXED {name} ({slug}) "
                f"gallery {result['before_gallery']} -> {result['after_gallery']} "
                f"[{match_method} / {folder['rel']}]",
                flush=True,
            )
        except Exception as exc:
            failed.append(
                {
                    "slug": slug,
                    "name": name,
                    "folder": folder["rel"],
                    "match_method": match_method,
                    "error": str(exc),
                }
            )
            print(f"FAILED {name}: {exc}", flush=True)

    summary = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "live_site": LIVE,
        "auth": auth,
        "min_gallery": MIN_GALLERY,
        "max_gallery": MAX_GALLERY,
        "dry_run": args.dry_run,
        "audit_total": len(audit_rows),
        "needed": len(need_slugs),
        "fixed_count": len(fixed),
        "skipped_count": len(skipped),
        "no_folder_count": len(no_folder),
        "failed_count": len(failed),
        "fixed": fixed,
        "skipped": skipped,
        "no_folder": no_folder,
        "failed": failed,
    }
    REPORT.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== SUMMARY ===", flush=True)
    print(json.dumps({k: summary[k] for k in ("needed", "fixed_count", "skipped_count", "no_folder_count", "failed_count")}, indent=2))
    print(f"Report: {REPORT}", flush=True)
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
