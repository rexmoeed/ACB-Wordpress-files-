#!/usr/bin/env python3
"""Parse category docs JSON, build structured archive content, deploy to live."""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
DOCS_JSON = Path(__file__).parent / "acb_category_docs_extract.json"
OUT_JSON = Path(__file__).parent / "acb_archive_structured.json"

SLUG_MAP = {
    "BAKERY": "bakery-boxes",
    "CANDLE": "candle-boxes",
    "EVENT": "event-boxes",
    "COSMETICS": "cosmetics",
    "FOOD": "food",
    "POPCORN": "popcorn-boxes",
    "POD BOXES": "pod-boxes",
    "PHARMACEUTICAL": "pharmaceutical-boxes",
    "PET": "pet-boxes",
    "MAILER BOXES": "mailer-boxes",
    "PRODUCT BOXES": "product-boxes",
    "TUCK BOXES": "tuck-boxes",
}

EM_DASH = re.compile(r"\s[\u2014\u2013]\s")
FAQ_STOP = re.compile(r"^(Ready to |Get Your Custom|Technical SEO|Request a Quote\s+·)", re.I)
SKIP = re.compile(
    r"^(SEO Meta Title|Meta Description|URL Slug|Primary Keyword|Secondary Keywords|"
    r"LSI Keywords|Long-Tail Keywords|Commercial Keywords|Transactional Keywords|"
    r"Search Intent|Target Market|H1:|Hero Description|Get a Quote|THE VERTEX|"
    r"SEO & On-Page|ACB CATEGORY|Packaging That Keeps|Get a Quote  )",
    re.I,
)

STYLE_STOP = {
    "Industries Served",
    "Applications",
    "Packaging Materials",
    "Event Packaging Guide",
    "Bakery Packaging Guide",
    "Popcorn Packaging Guide",
    "Tuck Box Guide",
    "Product Box Guide",
    "Mailer Box Guide",
    "Pet Packaging Guide",
    "Pharmaceutical Packaging Guide",
    "POD Packaging Guide",
    "Food Packaging Guide",
    "Cosmetic Packaging Guide",
    "Candle Packaging Guide",
    "Personalization & Variable Data",
    "Food Safety & Freshness Standards",
    "Packaging Specification Table",
}


def auth_header() -> dict[str, str]:
    token = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}


def api(method: str, path: str, payload: dict | None = None) -> dict | list:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{LIVE}{path}", data=data, headers=auth_header(), method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{method} {path} ({exc.code}): {exc.read().decode()}") from exc


def detect_slug(marker: str) -> str | None:
    upper = marker.upper()
    for key, slug in SLUG_MAP.items():
        if key in upper:
            return slug
    return None


def find_index(paras: list[str], *needles: str, start: int = 0) -> int | None:
    for i in range(start, len(paras)):
        p = paras[i].strip()
        for n in needles:
            if p == n or p.startswith(n):
                return i
    return None


def split_em_dash(line: str) -> tuple[str, str] | None:
    parts = EM_DASH.split(line.strip(), maxsplit=1)
    if len(parts) != 2:
        return None
    left, right = parts[0].strip(), parts[1].strip()
    if len(left) < 3 or len(right) < 5:
        return None
    return left, right


def slice_section(paras: list[str], start: int, stop_idx: int | None) -> list[str]:
    end = stop_idx if stop_idx is not None else len(paras)
    out = []
    for p in paras[start:end]:
        p = p.strip()
        if p and not SKIP.match(p):
            out.append(p)
    return out


def parse_bullets(lines: list[str], limit: int = 4) -> str:
    items = []
    for line in lines:
        if line.endswith(":") and len(line) < 90 and not EM_DASH.search(line):
            continue
        sp = split_em_dash(line)
        items.append(sp[1] if sp else line)
        if len(items) >= limit:
            break
    return " ".join(items)


def parse_category(paras: list[str]) -> dict:
    meta = {"title": "", "description": "", "focuskw": ""}
    for p in paras:
        if p.startswith("SEO Meta Title:"):
            meta["title"] = p.split(":", 1)[1].strip()
        elif p.startswith("Meta Description:"):
            meta["description"] = p.split(":", 1)[1].strip()
        elif p.startswith("Primary Keyword:"):
            meta["focuskw"] = p.split(":", 1)[1].strip()

    intro: list[str] = []
    why_title = ""
    why_items: list[dict] = []
    styles: list[dict] = []
    custom: list[dict] = []
    sustainability = ""
    faq: list[dict] = []

    intro_i = find_index(paras, "Introduction")
    why_i = find_index(paras, "Why Choose")
    benefits_i = find_index(paras, "Key Benefits")
    styles_i = find_index(paras, "Available Box Styles")
    materials_i = find_index(paras, "Packaging Materials")
    printing_i = find_index(paras, "Printing Options")
    finishing_i = find_index(paras, "Finishing Options")
    addons_i = find_index(paras, "Add-ons")
    sustain_i = find_index(paras, "Sustainable Packaging Options")
    faq_i = find_index(paras, "Frequently Asked Questions")

    if intro_i is not None and why_i is not None:
        intro = [p for p in slice_section(paras, intro_i + 1, why_i) if len(p) > 50]

    if why_i is not None:
        why_title = paras[why_i].strip()
        end = benefits_i if benefits_i is not None else (styles_i or len(paras))
        why_lines = slice_section(paras, why_i + 1, end)
        for line in why_lines:
            if line == "Key Benefits":
                break
            sp = split_em_dash(line)
            if sp and not sp[0].endswith(":") and not sp[1].rstrip().endswith(":"):
                why_items.append({"label": sp[0], "text": sp[1]})

    if styles_i is not None:
        stop = len(paras)
        for i in range(styles_i + 1, len(paras)):
            p = paras[i].strip()
            if p in STYLE_STOP or p.startswith("Packaging Specification"):
                stop = i
                break
        for line in slice_section(paras, styles_i + 1, stop):
            if line.startswith("Match the structure") or line.startswith("Choose the box"):
                continue
            sp = split_em_dash(line)
            if sp:
                styles.append({"title": sp[0], "description": sp[1]})

    def section_lines(start: int | None, end: int | None) -> list[str]:
        if start is None:
            return []
        return slice_section(paras, start + 1, end)

    next_after = lambda i: i + 1 if i is not None else None
    if materials_i is not None:
        end = printing_i or finishing_i or sustain_i
        custom.append({"label": "Materials", "content": parse_bullets(section_lines(materials_i, end))})
    if printing_i is not None:
        end = finishing_i or addons_i or sustain_i
        custom.append({"label": "Printing", "content": parse_bullets(section_lines(printing_i, end))})
    if finishing_i is not None:
        end = addons_i or sustain_i
        custom.append({"label": "Finishes", "content": parse_bullets(section_lines(finishing_i, end))})
    if addons_i is not None:
        end = sustain_i
        custom.append({"label": "Add-ons", "content": parse_bullets(section_lines(addons_i, end))})

    if sustain_i is not None:
        end = find_index(paras, "Our Manufacturing Process", start=sustain_i + 1)
        sustainability = parse_bullets(section_lines(sustain_i, end), limit=6)

    if faq_i is not None:
        i = faq_i + 1
        while i < len(paras):
            q = paras[i].strip()
            i += 1
            if not q or FAQ_STOP.match(q):
                break
            if i >= len(paras):
                break
            a = paras[i].strip()
            if not a or FAQ_STOP.match(a):
                break
            faq.append({"question": q, "answer": a})
            i += 1

    return {
        "meta": meta,
        "intro": intro,
        "why_title": why_title,
        "why_items": why_items,
        "styles": styles[:6],
        "customization": custom[:4],
        "sustainability": sustainability,
        "faq": faq[:14],
    }


def extract_all_categories(docs: dict) -> dict[str, dict]:
    blocks: dict[str, list[str]] = {}
    for doc_paras in docs.values():
        current_slug: str | None = None
        current: list[str] = []
        for p in doc_paras:
            if "ACB CATEGORY PAGE" in p:
                if current_slug and current:
                    blocks[current_slug] = current
                current_slug = detect_slug(p)
                current = []
                continue
            if current_slug:
                current.append(p)
        if current_slug and current:
            blocks[current_slug] = current
    return {slug: parse_category(paras) for slug, paras in blocks.items()}


def wrap_description(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"<!--acb-archive-v2-->{payload}<!--/acb-archive-v2-->"


def fetch_live_categories() -> dict[str, dict]:
    cats = api("GET", "/wp-json/wc/v3/products/categories?per_page=100")
    return {c["slug"]: c for c in cats}


def deploy_categories(structured: dict[str, dict], live: dict[str, dict]) -> list[dict]:
    results = []
    for slug, data in sorted(structured.items()):
        if slug not in live:
            results.append({"slug": slug, "status": "unmatched", "sections": section_count(data)})
            continue
        cat_id = live[slug]["id"]
        wrapped = wrap_description(data)
        payload = {
            "description": wrapped,
            "meta": {
                "wpseo_title": data["meta"]["title"],
                "wpseo_metadesc": data["meta"]["description"],
                "wpseo_focuskw": data["meta"]["focuskw"],
            },
        }
        api("POST", f"/wp-json/wp/v2/product_cat/{cat_id}", payload)
        results.append(
            {
                "slug": slug,
                "id": cat_id,
                "status": "updated",
                "sections": section_count(data),
                "desc_len": len(wrapped),
            }
        )
    return results


def section_count(data: dict) -> dict:
    return {
        "intro": len(data.get("intro", [])),
        "why": len(data.get("why_items", [])),
        "styles": len(data.get("styles", [])),
        "customization": len(data.get("customization", [])),
        "sustainability": 1 if data.get("sustainability") else 0,
        "faq": len(data.get("faq", [])),
    }


def build_seo_maps(structured: dict[str, dict]) -> tuple[dict, dict, dict]:
    titles, descs, kws = {}, {}, {}
    for slug, data in structured.items():
        m = data.get("meta", {})
        if m.get("title"):
            titles[slug] = m["title"]
        if m.get("description"):
            descs[slug] = m["description"]
        if m.get("focuskw"):
            kws[slug] = m["focuskw"]
    return titles, descs, kws


def main() -> int:
    docs = json.loads(DOCS_JSON.read_text(encoding="utf-8-sig"))
    structured = extract_all_categories(docs)
    OUT_JSON.write_text(json.dumps(structured, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Parsed {len(structured)} categories -> {OUT_JSON}")

    for slug, data in sorted(structured.items()):
        sc = section_count(data)
        print(
            f"  {slug}: intro={sc['intro']} why={sc['why']} styles={sc['styles']} "
            f"custom={sc['customization']} sustain={sc['sustainability']} faq={sc['faq']}"
        )

    if "--deploy" not in sys.argv:
        return 0

    live = fetch_live_categories()
    results = deploy_categories(structured, live)
    report = {
        "updated": [r for r in results if r["status"] == "updated"],
        "unmatched": [r for r in results if r["status"] == "unmatched"],
    }
    Path(__file__).parent.joinpath("deploy_results.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"Updated: {len(report['updated'])}, Unmatched: {len(report['unmatched'])}")
    for r in report["updated"]:
        print(f"  OK {r['slug']} ({r['id']}) sections={r['sections']}")
    for r in report["unmatched"]:
        print(f"  SKIP {r['slug']} (no live category)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
