import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

p = Path(r"D:\Downloads\ACB Data\02-About-Us-America-Custom-Boxes.docx")
out = Path(r"e:\America Custom Boxes\_tmp_about_doc.txt")
with zipfile.ZipFile(p) as z:
    root = ET.fromstring(z.read("word/document.xml"))
lines = []
for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
    texts = [
        t.text
        for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
        if t.text
    ]
    if texts:
        lines.append("".join(texts))
out.write_text("\n".join(lines), encoding="utf-8")
print("lines", len(lines), "->", out)
