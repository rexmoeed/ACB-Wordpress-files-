import pymysql
conn = pymysql.connect(host='127.0.0.1', port=10005, user='root', password='root', database='local', charset='utf8mb4')
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("""
SELECT t.term_id, t.name, t.slug, tm.meta_value AS thumbnail_id
FROM wp_terms t
JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
LEFT JOIN wp_termmeta tm ON t.term_id = tm.term_id AND tm.meta_key = 'thumbnail_id'
WHERE tt.taxonomy = 'product_cat' AND tt.parent = 23
ORDER BY t.name
""")
for r in cur.fetchall():
    print(r)
conn.close()
