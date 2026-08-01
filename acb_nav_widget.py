import json
import pymysql

conn = pymysql.connect(host="127.0.0.1", port=10005, user="root", password="root", database="local", charset="utf8mb4")
cur = conn.cursor(pymysql.cursors.DictCursor)
cur.execute("SELECT meta_value FROM wp_postmeta WHERE post_id=106 AND meta_key='_elementor_data'")
data = json.loads(cur.fetchone()['meta_value'])

def find(el, target):
    if el.get('id') == target:
        return el
    for c in el.get('elements', []):
        r = find(c, target)
        if r:
            return r
    return None

for root in data:
    w = find(root, '117f122f')
    if w:
        print(json.dumps(w, indent=2))
        break

# page titles for menu
cur.execute("SELECT ID, post_title, post_name FROM wp_posts WHERE ID IN (78,82,92,84)")
print("\nPAGES:")
for r in cur.fetchall():
    print(r)

conn.close()
