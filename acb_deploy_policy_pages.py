#!/usr/bin/env python3
"""Deploy policy page content from local DOCX to live WordPress pages."""
from __future__ import annotations

import base64
import json
import re
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

LIVE = "https://americacustomboxes.com"
USER = "admin"
APP_PASSWORD = "XFxg 7dCD 7FE9 7K3z W6mN 5FIh"
POLICY_DIR = Path(r"D:\Downloads\ACB Data\ACB Policies")

EFFECTIVE = "August 4, 2026"

PAGE_MAP = {
    "04-Privacy-Policy-America-Custom-Boxes.docx": 94,
    "05-Shipping-Policy-America-Custom-Boxes.docx": 2104,
    "06-Refunds-and-Returns-America-Custom-Boxes.docx": 2107,
}

PAGE_TITLES = {
    94: "Privacy Policy",
    2104: "Shipping Policy",
    2107: "Refunds & Returns Policy",
}

SECTION_RE = re.compile(r"^(\d{1,2})\.\s+(.+)$")

STOP_MARKERS = (
    "On-Page SEO Assets",
    "Suggested Internal Links",
    "Schema Recommendation",
    "Implementation Notes",
)

SUBHEADING_HINTS = (
    "information you give us",
    "information we collect automatically",
    "information from third parties",
    "why the proof matters",
)


def api(method: str, path: str, payload: dict | None = None) -> dict:
    auth = base64.b64encode(f"{USER}:{APP_PASSWORD}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Content-Type": "application/json"}
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{LIVE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode() or "{}")


def docx_paras(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    paras: list[str] = []
    for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        texts = [
            t.text
            for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
            if t.text
        ]
        if texts:
            paras.append("".join(texts))
    return paras


def clean_line(text: str) -> str:
    text = text.replace("\u2014", "—").replace("\u2013", "–").replace("\u2019", "'").replace("\u201c", '"').replace(
        "\u201d", '"'
    )
    text = re.sub(r"\[Insert date\]", EFFECTIVE, text)
    text = re.sub(r"\[X\]", "7", text)
    text = re.sub(r"\[confirm privacy email\]", "sales@americacustomboxes.com", text, flags=re.I)
    text = re.sub(
        r"\[Confirm privacy/sales email[^\]]*\]",
        "sales@americacustomboxes.com",
        text,
        flags=re.I,
    )
    text = re.sub(r"\[Confirm full business address\]", "United States", text, flags=re.I)
    text = re.sub(r"\[CONFIRM DETAILS\]", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def should_stop(line: str) -> bool:
    return any(line.startswith(m) for m in STOP_MARKERS)


def is_table_header_row(a: str, b: str | None) -> bool:
    if not b:
        return False
    pairs = (
        ("Cookie Type", "Purpose"),
        ("Order Type", "Typical Production Time"),
        ("Stage", "Typical Timing"),
    )
    return (a, b) in pairs


def is_subheading(line: str) -> bool:
    if SECTION_RE.match(line) or " — " in line or len(line) > 55:
        return False
    if line.endswith(".") or line.endswith("?"):
        return False
    if ":" in line or "(" in line:
        return False
    low = line.lower()
    if any(h in low for h in SUBHEADING_HINTS):
        return True
    words = line.split()
    return len(words) <= 5 and line and line[0].isupper()


def is_list_line(line: str) -> bool:
    if line.startswith(("•", "-", "–")):
        return True
    if SECTION_RE.match(line):
        return False
    if " — " in line and len(line) < 220:
        return True
    return line.startswith(
        (
            "Bank-level",
            "Zero storage",
            "Advanced real-time",
            "Full buyer",
            "100% PCI",
            "Contact details",
            "Order details",
            "Communications",
            "Device and browser",
            "Pages visited",
            "Cookie and analytics",
            "Payment processors",
            "Shipping carriers",
            "Analytics and advertising",
            "IT, hosting",
            "Design approved",
            "Payment confirmed",
            "Final specs",
            "Standard shipping",
            "Expedited shipping",
            "Tracking:",
            "Manufacturing defects",
            "Wrong product",
            "Damage that occurred",
            "Quantity shortages",
            "Change of mind",
            "Errors approved",
            "Minor variation",
            "Damage caused",
            "SSL/TLS",
            "PCI-DSS",
            "Access controls",
            "Ongoing monitoring",
            "Access —",
            "Correction —",
            "Deletion —",
            "Opt-out —",
            "Portability —",
            "Non-discrimination —",
        )
    )


def body_lines(paras: list[str]) -> list[str]:
    i = 0
    while i < len(paras) and "Effective date" not in paras[i]:
        i += 1
    lines: list[str] = []
    while i < len(paras):
        line = clean_line(paras[i])
        i += 1
        if not line or should_stop(line):
            if should_stop(line):
                break
            continue
        lines.append(line)
    return lines


def escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def paras_to_html(paras: list[str]) -> str:
    lines = body_lines(paras)
    if not lines:
        return ""

    parts: list[str] = ['<div class="acb-policy-content">']
    i = 0
    while i < len(lines) and SECTION_RE.match(lines[i]) is None:
        parts.append(f"<p>{escape_html(lines[i])}</p>")
        i += 1

    while i < len(lines):
        line = lines[i]
        sec = SECTION_RE.match(line)
        if sec:
            parts.append(f'<h2 class="acb-policy-section-title">{escape_html(sec.group(2))}</h2>')
            i += 1
            continue

        if i + 1 < len(lines) and is_table_header_row(line, lines[i + 1]):
            parts.append('<div class="acb-policy-table-wrap"><table><thead><tr>')
            parts.append(f"<th>{escape_html(line)}</th><th>{escape_html(lines[i + 1])}</th>")
            parts.append("</tr></thead><tbody>")
            i += 2
            while i + 1 < len(lines):
                a, b = lines[i], lines[i + 1]
                if SECTION_RE.match(a) or SECTION_RE.match(b):
                    break
                parts.append(f"<tr><td>{escape_html(a)}</td><td>{escape_html(b)}</td></tr>")
                i += 2
            parts.append("</tbody></table></div>")
            continue

        if is_subheading(line):
            parts.append(f"<h3>{escape_html(line)}</h3>")
            i += 1
            continue

        if is_list_line(line):
            items: list[str] = []
            while i < len(lines) and is_list_line(lines[i]):
                items.append(re.sub(r"^[•\-–]\s*", "", lines[i]))
                i += 1
            parts.append("<ul>")
            for it in items:
                parts.append(f"<li>{escape_html(it)}</li>")
            parts.append("</ul>")
            continue

        parts.append(f"<p>{escape_html(line)}</p>")
        i += 1

    parts.append("</div>")
    return "\n".join(parts)


def build_html(docx_name: str, page_id: int) -> str:
    inner = paras_to_html(docx_paras(POLICY_DIR / docx_name))
    title = PAGE_TITLES[page_id]
    title_h2 = f'<h2 class="acb-policy-page-title">{escape_html(title)}</h2>'
    inner = inner.replace(
        '<div class="acb-policy-content">',
        f'<div class="acb-policy-content">\n{title_h2}',
        1,
    )
    css = """
<style>
.acb-policy-content {
  max-width: 820px;
  width: 100%;
  margin: 0 auto;
  padding: 24px 20px 48px;
  box-sizing: border-box;
  font-family: 'Titillium Web', sans-serif;
  color: #374151;
  line-height: 1.65;
  overflow-wrap: anywhere;
}
.acb-policy-page-title {
  color: #FF2E2E;
  font-size: clamp(1.75rem, 5vw, 2.35rem);
  font-weight: 700;
  line-height: 1.15;
  margin: 0 0 1.25rem;
  letter-spacing: -0.02em;
}
.acb-policy-content .acb-policy-section-title {
  color: #FF2E2E;
  font-size: clamp(1.15rem, 3.5vw, 1.35rem);
  margin: 2rem 0 0.75rem;
  font-weight: 700;
  line-height: 1.3;
}
.acb-policy-content h3 {
  color: #111827;
  font-size: clamp(1rem, 3vw, 1.05rem);
  margin: 1.25rem 0 0.5rem;
  font-weight: 600;
  line-height: 1.35;
}
.acb-policy-content p {
  margin: 0 0 1rem;
  font-size: clamp(0.9375rem, 2.8vw, 1rem);
}
.acb-policy-content ul {
  margin: 0 0 1rem 1.15rem;
  padding: 0;
}
.acb-policy-content li {
  margin-bottom: 0.35rem;
  font-size: clamp(0.9375rem, 2.8vw, 1rem);
}
.acb-policy-table-wrap {
  width: 100%;
  max-width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 0 0 1.25rem;
}
.acb-policy-content table {
  width: 100%;
  min-width: 280px;
  border-collapse: collapse;
  font-size: clamp(0.875rem, 2.6vw, 0.95rem);
}
.acb-policy-content th,
.acb-policy-content td {
  border: 1px solid #e5e7eb;
  padding: 10px 12px;
  text-align: left;
  vertical-align: top;
}
.acb-policy-content th {
  background: #f9fafb;
  font-weight: 600;
  color: #111827;
}
@media (max-width: 767px) {
  .acb-policy-content {
    padding: 16px 14px 36px;
  }
  .acb-policy-page-title {
    margin-bottom: 1rem;
  }
  .acb-policy-content .acb-policy-section-title {
    margin-top: 1.5rem;
  }
  .acb-policy-content th,
  .acb-policy-content td {
    padding: 8px 10px;
  }
}
</style>
"""
    return css + inner


def main() -> None:
    for docx_name, page_id in PAGE_MAP.items():
        html = build_html(docx_name, page_id)
        api("POST", f"/wp-json/wp/v2/pages/{page_id}", {"content": html, "status": "publish"})
        print("Updated page", page_id, docx_name, "h2", html.count("<h2>"))
    print("OK")


if __name__ == "__main__":
    main()
