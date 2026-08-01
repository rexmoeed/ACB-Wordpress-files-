import json
import pymysql

conn = pymysql.connect(host="127.0.0.1", port=10005, user="root", password="root", database="local", charset="utf8mb4")
cur = conn.cursor(pymysql.cursors.DictCursor)

# menu item details
cur.execute(
    """
    SELECT p.ID, p.post_title, p.menu_order,
           MAX(CASE WHEN pm.meta_key='_menu_item_type' THEN pm.meta_value END) AS item_type,
           MAX(CASE WHEN pm.meta_key='_menu_item_object' THEN pm.meta_value END) AS obj,
           MAX(CASE WHEN pm.meta_key='_menu_item_object_id' THEN pm.meta_value END) AS object_id,
           MAX(CASE WHEN pm.meta_key='_menu_item_url' THEN pm.meta_value END) AS url,
           MAX(CASE WHEN pm.meta_key='_menu_item_menu_item_parent' THEN pm.meta_value END) AS parent
    FROM wp_posts p
    JOIN wp_term_relationships tr ON p.ID=tr.object_id
    JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id=tt.term_taxonomy_id
    JOIN wp_postmeta pm ON p.ID=pm.post_id
    WHERE tt.term_id=6 AND p.post_type='nav_menu_item'
    GROUP BY p.ID, p.post_title, p.menu_order
    ORDER BY p.menu_order
    """
)
print("MENU ITEMS:")
for row in cur.fetchall():
    print(row)

# header elementor data
cur.execute("SELECT meta_value FROM wp_postmeta WHERE post_id=106 AND meta_key='_elementor_data'")
row = cur.fetchone()
if row:
    data = json.loads(row['meta_value'])
    def walk(el, depth=0):
        wt = el.get('widgetType') or el.get('elType')
        settings = el.get('settings', {})
        title = settings.get('title') or settings.get('text') or settings.get('selected_icon', {}).get('value', '')
        menu = settings.get('menu') or settings.get('menu_name') or settings.get('nav_menu')
        shortcode = settings.get('shortcode', '')
        print('  '*depth + f"{el.get('id')} | {wt} | menu={menu} | title={title} | sc={shortcode[:60] if shortcode else ''}")
        for c in el.get('elements', []):
            walk(c, depth+1)
    for el in data:
        walk(el)

conn.close()
