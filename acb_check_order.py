import pymysql
conn = pymysql.connect(host='127.0.0.1', port=10005, user='root', password='root', database='local', charset='utf8mb4')
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("SELECT option_value FROM wp_options WHERE option_name='acb_hot_menu_version'")
print('version:', cur.fetchone())
cur.execute("""
SELECT p.ID, p.menu_order, p.post_title,
  MAX(CASE WHEN pm.meta_key='_menu_item_type' THEN pm.meta_value END) AS t,
  MAX(CASE WHEN pm.meta_key='_menu_item_object_id' THEN pm.meta_value END) AS oid,
  MAX(CASE WHEN pm.meta_key='_menu_item_menu_item_parent' THEN pm.meta_value END) AS par
FROM wp_posts p
JOIN wp_term_relationships tr ON p.ID=tr.object_id
JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id=tt.term_taxonomy_id AND tt.term_id=6
LEFT JOIN wp_postmeta pm ON p.ID=pm.post_id
WHERE p.post_type='nav_menu_item'
GROUP BY p.ID, p.menu_order, p.post_title
ORDER BY p.menu_order, p.ID
""")
for r in cur.fetchall():
    if r['par']=='0':
        print(r)
conn.close()
