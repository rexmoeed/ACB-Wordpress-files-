import json
import pymysql

conn = pymysql.connect(host="127.0.0.1", port=10005, user="root", password="root", database="local", charset="utf8mb4")
cur = conn.cursor(pymysql.cursors.DictCursor)

cur.execute("SELECT t.term_id, t.name, t.slug FROM wp_terms t JOIN wp_term_taxonomy tt ON t.term_id=tt.term_id WHERE tt.taxonomy='nav_menu'")
menus = cur.fetchall()

menu_data = {}
for m in menus:
    cur.execute(
        """
        SELECT p.ID, p.post_title, p.menu_order,
               url.meta_value AS url,
               type.meta_value AS item_type,
               obj.meta_value AS object_id,
               parent.meta_value AS menu_item_parent
        FROM wp_posts p
        JOIN wp_term_relationships tr ON p.ID = tr.object_id
        JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
        LEFT JOIN wp_postmeta url ON p.ID = url.post_id AND url.meta_key = '_menu_item_url'
        LEFT JOIN wp_postmeta type ON p.ID = type.post_id AND type.meta_key = '_menu_item_type'
        LEFT JOIN wp_postmeta obj ON p.ID = obj.post_id AND obj.meta_key = '_menu_item_object'
        LEFT JOIN wp_postmeta parent ON p.ID = parent.post_id AND parent.meta_key = '_menu_item_menu_item_parent'
        WHERE tt.term_id = %s AND p.post_type = 'nav_menu_item'
        ORDER BY p.menu_order
        """,
        (m["term_id"],),
    )
    menu_data[m["name"]] = cur.fetchall()

cur.execute(
    """
    SELECT t.term_id, t.name, t.slug, tt.count, tt.parent
    FROM wp_terms t
    JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
    WHERE tt.taxonomy = 'product_cat'
    ORDER BY tt.parent, t.name
    """
)
cats = cur.fetchall()
hot = next((c for c in cats if c["slug"] == "hot-products"), None)
children = [c for c in cats if hot and c["parent"] == hot["term_id"]]

cur.execute("SELECT ID, post_title, post_name FROM wp_posts WHERE post_type='elementor_library' AND post_status='publish'")
templates = cur.fetchall()

cur.execute(
    """
    SELECT p.ID, p.post_title, pm.meta_value
    FROM wp_posts p
    JOIN wp_postmeta pm ON p.ID = pm.post_id
    WHERE p.post_type='elementor_library' AND pm.meta_key='_elementor_conditions'
    """
)
conditions = cur.fetchall()

print(json.dumps({"menus": menus, "menu_items": menu_data, "hot_products": hot, "hot_children": children, "elementor_templates": templates, "elementor_conditions": conditions}, indent=2, default=str))
conn.close()
