import pymysql

SLUGS = [
    "corrugated-cardboard-mailer-boxes",
    "hair-extension-tuck-boxes",
    "serum-bottle-boxes-with-inserts",
    "tamper-proof-seal-stickers",
    "custom-qr-code-stickers",
    "custom-barcode-labels",
    "custom-shipping-labels",
    "child-resistant-mylar-bags",
    "corrugated-mailer-boxes",
    "custom-cbd-cream-boxes",
    "disposable-vape-pen-boxes",
    "vape-cartridge-window-boxes",
    "cbd-vape-cartridge-boxes",
    "custom-cbd-gummies-boxes",
]

conn = pymysql.connect(
    host="127.0.0.1",
    port=10005,
    user="root",
    password="root",
    database="local",
    charset="utf8mb4",
)
cur = conn.cursor(pymysql.cursors.DictCursor)

for slug in SLUGS:
    cur.execute(
        """
        SELECT p.post_title, pm.meta_value AS gallery, pm2.meta_value AS thumb
        FROM wp_posts p
        LEFT JOIN wp_postmeta pm ON p.ID = pm.post_id AND pm.meta_key = '_product_image_gallery'
        LEFT JOIN wp_postmeta pm2 ON p.ID = pm2.post_id AND pm2.meta_key = '_thumbnail_id'
        WHERE p.post_type = 'product' AND p.post_name = %s
        """,
        (slug,),
    )
    row = cur.fetchone()
    if not row:
        print(f"{slug}: NOT FOUND")
        continue
    gallery = (row["gallery"] or "").strip()
    count = len([x for x in gallery.split(",") if x.strip()]) if gallery else 0
    thumb = "yes" if row["thumb"] else "no"
    print(f"{row['post_title']}: gallery={count}, featured={thumb}")

conn.close()
