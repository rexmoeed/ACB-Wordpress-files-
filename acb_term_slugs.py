import pymysql
c = pymysql.connect(host='127.0.0.1', port=10005, user='root', password='root', database='local', charset='utf8mb4')
cur = c.cursor(pymysql.cursors.DictCursor)
for slug in ['bakery','candles','cbd','by-industry']:
    cur.execute("""
        SELECT t.term_id, t.slug, tt.taxonomy, tt.parent, tt.count
        FROM wp_terms t
        LEFT JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
        WHERE t.slug = %s
    """, (slug,))
    print(slug, cur.fetchall())

cur.execute("""
SELECT t.term_id, t.name, t.slug, tt.parent, tt.count
FROM wp_terms t
JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id
WHERE tt.taxonomy = 'product_cat' AND tt.parent = 43
""")
print('children of 43:', cur.fetchall())
c.close()
