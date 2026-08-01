import pymysql

conn = pymysql.connect(host='127.0.0.1', port=10005, user='root', password='root', database='local', charset='utf8mb4')
cur = conn.cursor(pymysql.cursors.DictCursor)

# Set subcategory thumbnails from first product featured image
for slug in ['bakery', 'candles', 'cbd', 'by-industry']:
    cur.execute("SELECT term_id FROM wp_terms WHERE slug=%s", (slug,))
    row = cur.fetchone()
    if not row:
        print('missing term', slug)
        continue
    term_id = row['term_id']
    cur.execute(
        """
        SELECT pm.meta_value AS thumb
        FROM wp_term_relationships tr
        JOIN wp_term_taxonomy tt ON tr.term_taxonomy_id = tt.term_taxonomy_id
        JOIN wp_posts p ON tr.object_id = p.ID
        JOIN wp_postmeta pm ON p.ID = pm.post_id AND pm.meta_key = '_thumbnail_id'
        WHERE tt.term_id = %s AND p.post_type = 'product' AND p.post_status = 'publish'
        LIMIT 1
        """,
        (term_id,),
    )
    thumb = cur.fetchone()
    if thumb and thumb['thumb']:
        cur.execute("SELECT meta_id FROM wp_termmeta WHERE term_id=%s AND meta_key='thumbnail_id'", (term_id,))
        if cur.fetchone():
            cur.execute("UPDATE wp_termmeta SET meta_value=%s WHERE term_id=%s AND meta_key='thumbnail_id'", (thumb['thumb'], term_id))
        else:
            cur.execute("INSERT INTO wp_termmeta (term_id, meta_key, meta_value) VALUES (%s, 'thumbnail_id', %s)", (term_id, thumb['thumb']))
        print(f'{slug}: thumb {thumb["thumb"]}')

cur.execute("SELECT COUNT(*) c FROM wp_posts WHERE post_type='product'")
print('total products:', cur.fetchone()['c'])

cur.execute("""
SELECT t.name, t.slug, tt.count FROM wp_terms t
JOIN wp_term_taxonomy tt ON t.term_id=tt.term_id
WHERE tt.taxonomy='product_cat' AND t.slug IN ('by-industry','bakery','candles','cbd','hot-products')
""")
for r in cur.fetchall():
    print(r)

conn.commit()
conn.close()
