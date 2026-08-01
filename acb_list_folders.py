import os
from pathlib import Path

keywords = ["tuck", "label", "sticker", "event", "vape", "gift", "welcome", "wedding", "favor", "barcode", "qr", "shipping", "tamper"]
for base in [Path(r"D:\Downloads\ACB Data\converted"), Path(r"D:\Downloads\ACB Data\New Images WebP")]:
    print("===", base.name, "===")
    for dp, _, fs in os.walk(base):
        if not any(f.lower().endswith(".webp") for f in fs):
            continue
        rel = str(Path(dp).relative_to(base))
        if any(k in rel.lower() for k in keywords):
            print(len([f for f in fs if f.lower().endswith(".webp")]), rel)
