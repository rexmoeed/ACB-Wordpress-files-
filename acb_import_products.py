#!/usr/bin/env python3
"""
Extract product copy from ACB Word docs and update WooCommerce products.
Uses direct MySQL connection (Local WP MySQL on port 10005).
Yoast SEO meta keys: _yoast_wpseo_title, _yoast_wpseo_metadesc, _yoast_wpseo_focuskw
"""
import zipfile
import xml.etree.ElementTree as ET
import re
import json
import html
import pymysql
from pathlib import Path

# --- Config ---
DOCS = [
    r"D:\Downloads\ACB Data\ACB_Product_Copy_Master_Catalog.docx",
    r"D:\Downloads\ACB Data\ACB_Remaining_Products_Catalogue.docx",
    r"D:\Downloads\ACB Data\ACB_Remaining_Products_Catalogue (1).docx",
    r"D:\Downloads\ACB Data\ACB_Remaining_Products_Catalogue (2).docx",
]
# Category pages doc is NOT products - skip it
SKIP_DOCS = [
    r"D:\Downloads\ACB Data\ACB-Category-Pages-Batch1.docx",
]

DB = dict(host='127.0.0.1', port=10005, user='root', password='root', database='local', charset='utf8mb4')
SITE_URL = "http://localhost:10004"

W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def extract_paragraphs(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read('word/document.xml')
    root = ET.fromstring(xml)
    paragraphs = []
    for p in root.iter(f'{W_NS}p'):
        texts = []
        for t in p.iter(f'{W_NS}t'):
            if t.text:
                texts.append(t.text)
            if t.tail:
                texts.append(t.tail)
        line = ''.join(texts).strip()
        if line:
            paragraphs.append(line)
    return paragraphs


def clean_meta_value(text):
    """Strip char counts like (53 chars) from meta fields."""
    text = re.sub(r'\s*\(\d+\s*chars?\)', '', text, flags=re.I)
    return text.strip()


def slug_from_field(text):
    """Extract slug from 'URL Slug: /luxury-candle-packaging'"""
    text = text.strip()
    text = re.sub(r'^URL Slug:\s*', '', text, flags=re.I)
    text = text.strip('/')
    return text


def is_category_header(line):
    return line.startswith('CUSTOM ') and line.endswith(' BOXES') or \
           line.startswith('CUSTOM ') and ('PACKAGING' in line or 'POUCHES' in line or 'LABELS' in line or 'BAGS' in line or 'STICKERS' in line)


def is_skip_line(line):
    skip_prefixes = (
        'AMERICA CUSTOM BOXES', 'Product Copy', 'Remaining Products', "What's Inside",
        'Why Brands Choose', 'sales@americacustomboxes', 'Ready to order?',
        'Free design support', 'No minimum order', 'Free die-cutting',
        'Free US shipping', 'Free digital 3D', '24/7 support',
    )
    for p in skip_prefixes:
        if line.startswith(p):
            return True
    if re.match(r'^\d+ Products', line):
        return True
    if is_category_header(line):
        return True
    return False


def parse_products_from_doc(docx_path):
    paras = extract_paragraphs(docx_path)
    products = []
    i = 0
    while i < len(paras):
        line = paras[i]
        # Look for SEO METADATA marker - product name is line before it
        if line == 'SEO METADATA' and i >= 1:
            name = paras[i - 1]
            if is_skip_line(name) or name in ('SEO METADATA', 'Quick Specs'):
                i += 1
                continue

            meta = {}
            short_desc = ''
            long_parts = []
            j = i + 1

            while j < len(paras):
                pl = paras[j]
                if pl.startswith('Meta Title:'):
                    meta['meta_title'] = clean_meta_value(re.sub(r'^Meta Title:\s*', '', pl))
                elif pl.startswith('Meta Description:'):
                    meta['meta_description'] = clean_meta_value(re.sub(r'^Meta Description:\s*', '', pl))
                elif pl.startswith('URL Slug:'):
                    meta['slug'] = slug_from_field(pl)
                elif pl.startswith('Focus Keyword:'):
                    meta['focus_keyword'] = clean_meta_value(re.sub(r'^Focus Keyword:\s*', '', pl))
                    # Next non-empty line is short description
                    k = j + 1
                    while k < len(paras) and paras[k] in ('Quick Specs', 'SEO METADATA'):
                        k += 1
                    if k < len(paras) and not paras[k].startswith('Quick Specs'):
                        short_desc = paras[k]
                        j = k
                elif pl == 'Quick Specs':
                    # Start collecting long description from Quick Specs
                    k = j
                    while k < len(paras):
                        chunk = paras[k]
                        if chunk.startswith('Ready to order?'):
                            break
                        # Stop if we hit next product (line followed by SEO METADATA)
                        if k + 1 < len(paras) and paras[k + 1] == 'SEO METADATA':
                            break
                        long_parts.append(chunk)
                        k += 1
                    j = k - 1
                    break
                j += 1

            if meta.get('slug') or meta.get('meta_title'):
                long_desc = build_long_description(long_parts)
                products.append({
                    'name': name,
                    'short_description': short_desc,
                    'description': long_desc,
                    'meta_title': meta.get('meta_title', ''),
                    'meta_description': meta.get('meta_description', ''),
                    'focus_keyword': meta.get('focus_keyword', ''),
                    'slug': meta.get('slug', ''),
                    'source': Path(docx_path).name,
                })
        i += 1
    return products


def build_long_description(parts):
    """Convert flat paragraph list into HTML for post_content."""
    if not parts:
        return ''

    html_parts = []
    i = 0
    section_headers = {
        'Quick Specs', 'Why Choose', 'Popular Styles & Options',
        'Customization Options', 'Sustainable Packaging Options',
        'Frequently Asked Questions',
    }

    while i < len(parts):
        line = parts[i]

        # Detect "Why Choose X?" headers
        if line.startswith('Why Choose'):
            html_parts.append(f'<h2>{html.escape(line)}</h2>')
            i += 1
            continue

        if line in ('Quick Specs', 'Popular Styles & Options', 'Customization Options',
                    'Sustainable Packaging Options', 'Frequently Asked Questions'):
            html_parts.append(f'<h2>{html.escape(line)}</h2>')
            i += 1
            continue

        # Spec table: label followed by value
        spec_labels = ('Material', 'Printing', 'Finishes', 'Minimum Order', 'Turnaround', 'Free With Order')
        if line in spec_labels and i + 1 < len(parts):
            html_parts.append(f'<p><strong>{html.escape(line)}:</strong> {html.escape(parts[i+1])}</p>')
            i += 2
            continue

        # FAQ: question followed by answer
        if line.endswith('?') and i + 1 < len(parts) and not parts[i+1].endswith('?'):
            html_parts.append(f'<h3>{html.escape(line)}</h3>')
            html_parts.append(f'<p>{html.escape(parts[i+1])}</p>')
            i += 2
            continue

        # Bullet-style items with colon (Popular Styles)
        if ': ' in line and not line.startswith('Materials:') and not line.startswith('Printing:') and not line.startswith('Finishes:') and not line.startswith('Add-ons:'):
            colon_idx = line.index(': ')
            title = line[:colon_idx]
            body = line[colon_idx + 2:]
            if len(title) < 60:
                html_parts.append(f'<p><strong>{html.escape(title)}:</strong> {html.escape(body)}</p>')
                i += 1
                continue

        # Customization sub-items
        if line.startswith('Materials:') or line.startswith('Printing:') or line.startswith('Finishes:') or line.startswith('Add-ons:'):
            html_parts.append(f'<p>{html.escape(line)}</p>')
            i += 1
            continue

        # Bullet points (Why Choose items)
        if line and line[0].islower() is False and ':' in line and len(line) < 200:
            colon_idx = line.index(':')
            title = line[:colon_idx]
            body = line[colon_idx + 1:].strip()
            if body and len(title) < 80:
                html_parts.append(f'<p><strong>{html.escape(title)}:</strong> {html.escape(body)}</p>')
                i += 1
                continue

        html_parts.append(f'<p>{html.escape(line)}</p>')
        i += 1

    return '\n'.join(html_parts)


def normalize(s):
    s = html.unescape(s or '')
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def decode_title(s):
    return html.unescape(s or '').strip()


def get_db_products(conn):
    cur = conn.cursor(pymysql.cursors.DictCursor)
    cur.execute("""
        SELECT ID, post_title, post_name, post_excerpt, post_content
        FROM wp_posts
        WHERE post_type='product' AND post_status IN ('publish','draft','private')
        ORDER BY post_title
    """)
    return cur.fetchall()


def update_product_meta(cur, post_id, key, value):
    cur.execute("SELECT meta_id FROM wp_postmeta WHERE post_id=%s AND meta_key=%s", (post_id, key))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE wp_postmeta SET meta_value=%s WHERE post_id=%s AND meta_key=%s", (value, post_id, key))
    else:
        cur.execute("INSERT INTO wp_postmeta (post_id, meta_key, meta_value) VALUES (%s, %s, %s)", (post_id, key, value))


def build_doc_lookups(all_products):
    by_name = {}
    by_slug = {}
    for p in all_products.values():
        key = normalize(p['name'])
        if key not in by_name:
            by_name[key] = p
        slug = p.get('slug', '')
        if slug and slug not in by_slug:
            by_slug[slug] = p
    return by_name, by_slug


def find_doc_for_db_product(db_p, by_name, by_slug):
    """Match DB product to doc by exact title, then slug."""
    title = decode_title(db_p['post_title'])
    key = normalize(title)
    if key in by_name:
        return by_name[key]

    slug = db_p['post_name']
    if slug in by_slug:
        return by_slug[slug]

    # Slug prefix match (e.g. window-cake-boxes vs window-cake-boxes-6-inch-standard)
    for doc_slug, doc_p in by_slug.items():
        if slug.startswith(doc_slug + '-') or doc_slug.startswith(slug + '-'):
            return doc_p

    return None


def main():
    dry_run = False  # Set True to preview only

    # Parse all docs
    all_products = {}
    doc_counts = {}
    for doc in DOCS:
        if not Path(doc).exists():
            print(f"SKIP missing: {doc}")
            continue
        prods = parse_products_from_doc(doc)
        doc_counts[Path(doc).name] = len(prods)
        for p in prods:
            key = normalize(p['name'])
            if key not in all_products:
                all_products[key] = p
            else:
                # Prefer doc with more content
                existing = all_products[key]
                if len(p.get('description', '')) > len(existing.get('description', '')):
                    all_products[key] = p

    print(f"\n=== DOCS PARSED ===")
    for doc, count in doc_counts.items():
        print(f"  {doc}: {count} products")
    print(f"  Unique products total: {len(all_products)}")

    # Connect to DB
    conn = pymysql.connect(**DB)
    db_products = get_db_products(conn)
    print(f"\n=== DB PRODUCTS ===")
    print(f"  WooCommerce products in DB: {len(db_products)}")

    by_name, by_slug = build_doc_lookups(all_products)
    matched = []
    unmatched_db = []
    matched_doc_keys = set()

    for db_p in db_products:
        doc_p = find_doc_for_db_product(db_p, by_name, by_slug)
        if doc_p:
            matched.append((doc_p, db_p))
            matched_doc_keys.add(normalize(doc_p['name']))
        else:
            unmatched_db.append(db_p)

    unmatched_docs = [p for k, p in all_products.items() if k not in matched_doc_keys]

    print(f"\n=== MATCHING ===")
    print(f"  Matched: {len(matched)}")
    print(f"  Unmatched docs: {len(unmatched_docs)}")
    print(f"  Unmatched DB products: {len(unmatched_db)}")

    if unmatched_docs:
        print("\n  Unmatched doc products (first 20):")
        for p in unmatched_docs[:20]:
            print(f"    - {p['name']} (slug: {p.get('slug','')}) [{p['source']}]")

    if unmatched_db:
        print("\n  Unmatched DB products (first 20):")
        for p in unmatched_db[:20]:
            print(f"    - {p['post_title']} (slug: {p['post_name']}, ID: {p['ID']})")

    # Update products
    updated = 0
    cur = conn.cursor()
    results = []

    for doc_p, db_p in matched:
        post_id = db_p['ID']
        slug = doc_p.get('slug') or db_p['post_name']

        if not dry_run:
            cur.execute("""
                UPDATE wp_posts SET
                    post_excerpt = %s,
                    post_content = %s,
                    post_name = %s
                WHERE ID = %s
            """, (doc_p['short_description'], doc_p['description'], slug, post_id))

            # Yoast SEO meta
            if doc_p.get('meta_title'):
                update_product_meta(cur, post_id, '_yoast_wpseo_title', doc_p['meta_title'])
            if doc_p.get('meta_description'):
                update_product_meta(cur, post_id, '_yoast_wpseo_metadesc', doc_p['meta_description'])
            if doc_p.get('focus_keyword'):
                update_product_meta(cur, post_id, '_yoast_wpseo_focuskw', doc_p['focus_keyword'])

        updated += 1
        results.append({
            'id': post_id,
            'name': db_p['post_title'],
            'slug': slug,
            'url': f"{SITE_URL}/product/{slug}/",
            'meta_title': doc_p.get('meta_title', ''),
            'short_desc_len': len(doc_p.get('short_description', '')),
            'desc_len': len(doc_p.get('description', '')),
        })

    if not dry_run:
        conn.commit()

    print(f"\n=== UPDATED {updated} products ===")

    # Sample verification
    print("\n=== SAMPLE VERIFICATION (first 5) ===")
    for r in results[:5]:
        print(f"  [{r['id']}] {r['name']}")
        print(f"    URL: {r['url']}")
        print(f"    Meta Title: {r['meta_title'][:60]}...")
        print(f"    Short desc: {r['short_desc_len']} chars, Long desc: {r['desc_len']} chars")

    # Verify one product from DB
    if results and not dry_run:
        sample_id = results[0]['id']
        cur.execute("SELECT post_excerpt, post_name FROM wp_posts WHERE ID=%s", (sample_id,))
        row = cur.fetchone()
        cur.execute("SELECT meta_key, meta_value FROM wp_postmeta WHERE post_id=%s AND meta_key LIKE '_yoast%%'", (sample_id,))
        meta = cur.fetchall()
        print(f"\n=== DB VERIFY product ID {sample_id} ===")
        print(f"  post_name: {row[1]}")
        print(f"  excerpt: {row[0][:100]}...")
        for m in meta:
            print(f"  {m[0]}: {m[1][:80]}")

    # Save report
    report = {
        'docs_found': len(DOCS),
        'doc_counts': doc_counts,
        'unique_products_parsed': len(all_products),
        'db_products': len(db_products),
        'matched_updated': updated,
        'unmatched_docs': [{'name': p['name'], 'slug': p.get('slug',''), 'source': p['source']} for p in unmatched_docs],
        'unmatched_db': [{'id': p['ID'], 'title': p['post_title'], 'slug': p['post_name']} for p in unmatched_db],
        'sample_urls': [r['url'] for r in results[:10]],
    }
    report_path = r"E:\America Custom Boxes\acb_import_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved: {report_path}")

    conn.close()
    return report


if __name__ == '__main__':
    main()
