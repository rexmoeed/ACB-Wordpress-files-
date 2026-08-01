import os
from pathlib import Path

docs = Path(r"D:\Downloads\ACB Data\Documents")
webp = Path(r"D:\Downloads\ACB Data\New Images WebP")

print("Documents exists:", docs.exists())
if docs.exists():
    files = list(docs.rglob("*"))
    docx = [f for f in files if f.suffix.lower() == ".docx"]
    print("Documents total files:", len([f for f in files if f.is_file()]))
    print("Documents docx:", len(docx))
    for f in sorted(docx)[:30]:
        print(" ", f.relative_to(docs))

print("\nWebP exists:", webp.exists())
if webp.exists():
    webps = list(webp.rglob("*.webp"))
    print("WebP count:", len(webps))
    top = sorted({p.parts[len(webp.parts)] for p in webp.rglob("*") if p.is_dir() and len(p.relative_to(webp).parts)==1})
    print("Top folders:", top)
