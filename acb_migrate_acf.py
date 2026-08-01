#!/usr/bin/env python3
"""
Migrate product post_content HTML into ACF fields for all WooCommerce products.
Also activates ACF plugin and updates Elementor template #464.
"""
import json
import re
import html as htmlmod
import pymysql
import phpserialize
from pathlib import Path

DB = dict(host='127.0.0.1', port=10005, user='root', password='root', database='local', charset='utf8mb4')
SITE_URL = 'http://localhost:10004'
ELEMENTOR_TEMPLATE_ID = 464

# ACF field keys (must match acb-acf-fields.php)
FIELD_KEYS = {
    'acb_quick_specs': 'field_acb_quick_specs',
    'material': 'field_acb_spec_material',
    'printing': 'field_acb_spec_printing',
    'finishes': 'field_acb_spec_finishes',
    'minimum_order': 'field_acb_spec_moq',
    'turnaround': 'field_acb_spec_turnaround',
    'free_with_order': 'field_acb_spec_free',
    'acb_why_choose_title': 'field_acb_why_title',
    'acb_why_choose': 'field_acb_why_points',
    'point': 'field_acb_why_point',
    'acb_popular_styles': 'field_acb_popular_styles',
    'title': 'field_acb_style_title',
    'description': 'field_acb_style_desc',
    'acb_customization': 'field_acb_customization',
    'label': 'field_acb_cust_label',
    'content': 'field_acb_cust_content',
    'acb_sustainability': 'field_acb_sustainability',
    'acb_faq': 'field_acb_faq',
    'question': 'field_acb_faq_q',
    'answer': 'field_acb_faq_a',
}

SPEC_MAP = {
    'Material': 'material',
    'Printing': 'printing',
    'Finishes': 'finishes',
    'Minimum Order': 'minimum_order',
    'Turnaround': 'turnaround',
    'Free With Order': 'free_with_order',
}


def strip_tags(text):
    return htmlmod.unescape(re.sub(r'<[^>]+>', '', text or '')).strip()


def parse_product_content(content):
    """Parse post_content HTML into ACF-ready structures."""
    if not content or '<h2>' not in content:
        return None

    sections = {}
    parts = re.split(r'<h2>(.*?)</h2>', content, flags=re.IGNORECASE)
    for i in range(1, len(parts), 2):
        title = strip_tags(parts[i])
        body = parts[i + 1] if i + 1 < len(parts) else ''
        sections[title] = body

    data = {
        'specs': {},
        'why_title': '',
        'why_points': [],
        'popular_styles': [],
        'customization': [],
        'sustainability': '',
        'faq': [],
    }

    specs_body = sections.get('Quick Specs', '')
    for label, key in SPEC_MAP.items():
        m = re.search(rf'<strong>{re.escape(label)}:</strong>\s*(.*?)</p>', specs_body, re.DOTALL | re.IGNORECASE)
        if m:
            data['specs'][key] = strip_tags(m.group(1))

    for title in sections:
        if title.startswith('Why Choose'):
            data['why_title'] = title
            body = sections[title]
            for m in re.finditer(r'<p><strong>(.*?):</strong>\s*(.*?)</p>', body, re.DOTALL):
                pt = f"{strip_tags(m.group(1))}: {strip_tags(m.group(2))}"
                data['why_points'].append(pt)
            break

    styles_body = sections.get('Popular Styles & Options', '')
    for m in re.finditer(r'<p><strong>(.*?):</strong>\s*(.*?)</p>', styles_body, re.DOTALL):
        data['popular_styles'].append({
            'title': strip_tags(m.group(1)),
            'description': strip_tags(m.group(2)),
        })

    cust_body = sections.get('Customization Options', '')
    for m in re.finditer(r'<p>(Materials|Printing|Finishes|Add-ons):\s*(.*?)</p>', cust_body, re.DOTALL | re.IGNORECASE):
        data['customization'].append({
            'label': m.group(1),
            'content': strip_tags(m.group(2)),
        })

    sustain_body = sections.get('Sustainable Packaging Options', '')
    if sustain_body:
        data['sustainability'] = strip_tags(sustain_body)

    faq_body = sections.get('Frequently Asked Questions', '')
    for m in re.finditer(r'<h3>(.*?)</h3>\s*<p>(.*?)</p>', faq_body, re.DOTALL):
        data['faq'].append({
            'question': strip_tags(m.group(1)),
            'answer': strip_tags(m.group(2)),
        })

    has_any = (
        data['specs'] or data['why_title'] or data['why_points']
        or data['popular_styles'] or data['customization']
        or data['sustainability'] or data['faq']
    )
    return data if has_any else None


def update_meta(cur, post_id, key, value):
    cur.execute("SELECT meta_id FROM wp_postmeta WHERE post_id=%s AND meta_key=%s", (post_id, key))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE wp_postmeta SET meta_value=%s WHERE post_id=%s AND meta_key=%s", (value, post_id, key))
    else:
        cur.execute("INSERT INTO wp_postmeta (post_id, meta_key, meta_value) VALUES (%s, %s, %s)", (post_id, key, value))


def delete_meta_prefix(cur, post_id, prefix):
    cur.execute(
        "DELETE FROM wp_postmeta WHERE post_id=%s AND (meta_key=%s OR meta_key LIKE %s OR meta_key LIKE %s)",
        (post_id, prefix, f'{prefix}_%', f'_{prefix}%'),
    )


def set_text_field(cur, post_id, name, value, field_key):
    if not value:
        return
    update_meta(cur, post_id, name, value)
    update_meta(cur, post_id, f'_{name}', field_key)


def set_group_field(cur, post_id, group_name, subfields, group_key):
    if not subfields:
        return
    update_meta(cur, post_id, f'_{group_name}', group_key)
    for sub_name, value in subfields.items():
        if value:
            fk = FIELD_KEYS[sub_name]
            set_text_field(cur, post_id, f'{group_name}_{sub_name}', value, fk)


def set_repeater(cur, post_id, repeater_name, rows, subfield_name, subfield_key, repeater_key):
    delete_meta_prefix(cur, post_id, repeater_name)
    if not rows:
        return
    update_meta(cur, post_id, repeater_name, str(len(rows)))
    update_meta(cur, post_id, f'_{repeater_name}', repeater_key)
    for i, row in enumerate(rows):
        if isinstance(row, dict):
            val = row.get(subfield_name, '')
        else:
            val = row
        if val:
            fname = f'{repeater_name}_{i}_{subfield_name}'
            update_meta(cur, post_id, fname, val)
            update_meta(cur, post_id, f'_{fname}', subfield_key)


def write_acf_data(cur, post_id, data):
    delete_meta_prefix(cur, post_id, 'acb_quick_specs')
    delete_meta_prefix(cur, post_id, 'acb_why_choose')
    delete_meta_prefix(cur, post_id, 'acb_popular_styles')
    delete_meta_prefix(cur, post_id, 'acb_customization')
    delete_meta_prefix(cur, post_id, 'acb_sustainability')
    delete_meta_prefix(cur, post_id, 'acb_faq')

    set_group_field(cur, post_id, 'acb_quick_specs', data['specs'], FIELD_KEYS['acb_quick_specs'])
    set_repeater(cur, post_id, 'acb_why_choose', data['why_points'], 'point', FIELD_KEYS['point'], FIELD_KEYS['acb_why_choose'])
    set_text_field(cur, post_id, 'acb_why_choose_title', data['why_title'], FIELD_KEYS['acb_why_choose_title'])
    set_repeater(cur, post_id, 'acb_popular_styles', data['popular_styles'], 'title', FIELD_KEYS['title'], FIELD_KEYS['acb_popular_styles'])
    for i, row in enumerate(data['popular_styles']):
        if row.get('description'):
            fname = f'acb_popular_styles_{i}_description'
            update_meta(cur, post_id, fname, row['description'])
            update_meta(cur, post_id, f'_{fname}', FIELD_KEYS['description'])
    set_repeater(cur, post_id, 'acb_customization', data['customization'], 'label', FIELD_KEYS['label'], FIELD_KEYS['acb_customization'])
    for i, row in enumerate(data['customization']):
        if row.get('content'):
            fname = f'acb_customization_{i}_content'
            update_meta(cur, post_id, fname, row['content'])
            update_meta(cur, post_id, f'_{fname}', FIELD_KEYS['content'])
    set_text_field(cur, post_id, 'acb_sustainability', data['sustainability'], FIELD_KEYS['acb_sustainability'])
    # FAQ repeater with two subfields
    delete_meta_prefix(cur, post_id, 'acb_faq')
    if data['faq']:
        update_meta(cur, post_id, 'acb_faq', str(len(data['faq'])))
        update_meta(cur, post_id, '_acb_faq', FIELD_KEYS['acb_faq'])
        for i, row in enumerate(data['faq']):
            qname = f'acb_faq_{i}_question'
            aname = f'acb_faq_{i}_answer'
            update_meta(cur, post_id, qname, row['question'])
            update_meta(cur, post_id, f'_{qname}', FIELD_KEYS['question'])
            update_meta(cur, post_id, aname, row['answer'])
            update_meta(cur, post_id, f'_{aname}', FIELD_KEYS['answer'])


def activate_acf(cur):
    cur.execute("SELECT option_value FROM wp_options WHERE option_name='active_plugins'")
    row = cur.fetchone()
    raw = row['option_value'] if isinstance(row, dict) else row[0]
    plugins = phpserialize.loads(raw.encode('utf-8'), decode_strings=True)
    if isinstance(plugins, dict):
        plugins = list(plugins.values())
    acf_plugin = 'advanced-custom-fields/acf.php'
    if acf_plugin not in plugins:
        plugins.append(acf_plugin)
        serialized = phpserialize.dumps(plugins).decode('utf-8')
        cur.execute("UPDATE wp_options SET option_value=%s WHERE option_name='active_plugins'", (serialized,))
        print(f'Activated ACF plugin')
    else:
        print('ACF already active')


def update_elementor_template(cur):
    cur.execute("SELECT meta_value FROM wp_postmeta WHERE post_id=%s AND meta_key='_elementor_data'", (ELEMENTOR_TEMPLATE_ID,))
    row = cur.fetchone()
    if not row:
        print(f'WARNING: No _elementor_data for template {ELEMENTOR_TEMPLATE_ID}')
        return

    raw = row['meta_value'] if isinstance(row, dict) else row[0]
    data = json.loads(raw)
    replaced = False

    def walk(elements):
        nonlocal replaced
        for el in elements:
            if el.get('widgetType') == 'woocommerce-product-content':
                el['widgetType'] = 'shortcode'
                el['settings'] = {
                    'shortcode': '[acb_product_content]',
                    '_margin': {
                        'unit': 'px', 'top': '30', 'right': '0', 'bottom': '0', 'left': '0', 'isLinked': False,
                    },
                }
                replaced = True
            if el.get('elements'):
                walk(el['elements'])

    walk(data)
    if not replaced:
        print('WARNING: woocommerce-product-content widget not found in template')
        return

    new_json = json.dumps(data, separators=(',', ':'))
    cur.execute(
        "UPDATE wp_postmeta SET meta_value=%s WHERE post_id=%s AND meta_key='_elementor_data'",
        (new_json, ELEMENTOR_TEMPLATE_ID),
    )
    # Clear elementor CSS cache for this template
    cur.execute("DELETE FROM wp_postmeta WHERE post_id=%s AND meta_key='_elementor_css'", (ELEMENTOR_TEMPLATE_ID,))
    cur.execute("DELETE FROM wp_options WHERE option_name LIKE '_transient_elementor%%'")
    print(f'Updated Elementor template #{ELEMENTOR_TEMPLATE_ID} — replaced product-content with [acb_product_content]')


def migrate_products(cur):
    cur.execute("""
        SELECT ID, post_title, post_name, post_content
        FROM wp_posts
        WHERE post_type='product' AND post_status IN ('publish','draft','private')
        ORDER BY post_title
    """)
    products = cur.fetchall()
    migrated = 0
    skipped = 0
    results = []

    for p in products:
        post_id = p['ID']
        parsed = parse_product_content(p['post_content'])
        if not parsed:
            skipped += 1
            continue
        write_acf_data(cur, post_id, parsed)
        migrated += 1
        results.append({'id': post_id, 'slug': p['post_name'], 'title': p['post_title']})

    return migrated, skipped, results


def main():
    conn = pymysql.connect(**DB)
    cur = conn.cursor(pymysql.cursors.DictCursor)

    print('=== Activating ACF ===')
    activate_acf(cur)

    print('\n=== Migrating product content to ACF ===')
    migrated, skipped, results = migrate_products(cur)
    print(f'Migrated: {migrated}, Skipped (no parseable content): {skipped}')

    print('\n=== Updating Elementor template ===')
    update_elementor_template(cur)

    conn.commit()

    print('\n=== Sample migrated products ===')
    for r in results[:5]:
        print(f"  [{r['id']}] {r['title']} — {SITE_URL}/product/{r['slug']}/")

    report = {
        'migrated': migrated,
        'skipped': skipped,
        'elementor_template_id': ELEMENTOR_TEMPLATE_ID,
        'sample_urls': [f"{SITE_URL}/product/{r['slug']}/" for r in results[:10]],
    }
    report_path = Path(r'E:\America Custom Boxes\acb_acf_migration_report.json')
    report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'\nReport: {report_path}')
    conn.close()
    return report


if __name__ == '__main__':
    main()
