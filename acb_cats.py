import pymysql
conn = pymysql.connect(host='127.0.0.1', port=10005, user='root', password='root', database='local', charset='utf8mb4')
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("SELECT t.term_id,t.name,t.slug,tt.parent,tt.count FROM wp_terms t JOIN wp_term_taxonomy tt ON t.term_id=tt.term_id WHERE tt.taxonomy='product_cat' ORDER BY tt.parent,t.name")
for r in cur.fetchall():
    print(r)
cur.execute("SELECT COUNT(*) AS c FROM wp_posts WHERE post_type='product'")
print('products:', cur.fetchone())
conn.close()
