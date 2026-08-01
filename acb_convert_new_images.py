#!/usr/bin/env python3
"""Convert New Images folder to WebP (max 80KB) into a separate output tree."""
import json
import os
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from PIL import Image

SOURCE = Path(r"D:\Downloads\ACB Data\New Images")
OUTPUT = Path(r"D:\Downloads\ACB Data\New Images WebP")
MAX_BYTES = 80 * 1024
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif"}


def save_under_limit(img: Image.Image, dest: Path) -> tuple[int, int, float]:
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB")

    best = None
    base_w, base_h = img.size
    pixels = base_w * base_h

    if pixels > 2_000_000:
        scales = (0.35, 0.3, 0.25, 0.2, 0.15, 0.12, 0.1)
    elif pixels > 800_000:
        scales = (0.5, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15)
    elif pixels > 300_000:
        scales = (0.7, 0.6, 0.5, 0.4, 0.35, 0.3, 0.25)
    else:
        scales = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.35, 0.3, 0.25, 0.2)

    for scale in scales:
        w = max(1, int(base_w * scale))
        h = max(1, int(base_h * scale))
        working = img if scale == 1.0 else img.resize((w, h), Image.Resampling.LANCZOS)

        for quality in range(85, 9, -5):
            buf = BytesIO()
            save_kwargs = {"format": "WEBP", "quality": quality, "method": 6}
            if working.mode == "RGBA":
                save_kwargs["lossless"] = False
            working.save(buf, **save_kwargs)
            size = buf.tell()
            if size <= MAX_BYTES:
                dest.write_bytes(buf.getvalue())
                return size, quality, scale
            if best is None or size < best[0]:
                best = (size, quality, scale, buf.getvalue())

    if best is None:
        raise RuntimeError("Could not encode image")

    dest.write_bytes(best[3])
    return best[0], best[1], best[2]


def collect_files() -> list[tuple[Path, Path]]:
    files: list[tuple[Path, Path]] = []
    for root, _, names in os.walk(SOURCE):
        root_path = Path(root)
        for name in sorted(names):
            src = root_path / name
            if src.suffix.lower() not in IMAGE_EXTS:
                continue
            rel = src.relative_to(SOURCE)
            dest = OUTPUT / rel.with_suffix(".webp")
            files.append((src, dest))
    return files


def main() -> int:
    if not SOURCE.exists():
        print(f"Source not found: {SOURCE}")
        return 1

    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = collect_files()
    total = len(files)
    ok = 0
    skipped = 0
    failed: list[dict] = []
    over_limit: list[dict] = []

    print(f"Source:  {SOURCE}")
    print(f"Output:  {OUTPUT}")
    print(f"Images:  {total}")
    print(f"Max size: {MAX_BYTES // 1024}KB\n")

    for i, (src, dest) in enumerate(files, 1):
        dest.parent.mkdir(parents=True, exist_ok=True)
        rel = src.relative_to(SOURCE)

        if dest.exists() and dest.stat().st_size <= MAX_BYTES:
            skipped += 1
            ok += 1
            if i % 50 == 0:
                print(f"[{i}/{total}] skip existing {rel}", flush=True)
            continue

        try:
            with Image.open(src) as img:
                img.load()
                size, quality, scale = save_under_limit(img, dest)
            ok += 1
            flag = " OVER" if size > MAX_BYTES else ""
            if i % 25 == 0 or size > MAX_BYTES:
                print(
                    f"[{i}/{total}] {rel} -> {size // 1024}KB q={quality} s={scale:.2f}{flag}",
                    flush=True,
                )
            if size > MAX_BYTES:
                over_limit.append({"file": str(rel), "bytes": size})
        except Exception as exc:
            failed.append({"file": str(rel), "error": str(exc)})
            print(f"[{i}/{total}] FAILED {rel}: {exc}", flush=True)

    report = {
        "source": str(SOURCE),
        "output": str(OUTPUT),
        "max_kb": MAX_BYTES // 1024,
        "total": total,
        "success": ok,
        "skipped_existing": skipped,
        "failed_count": len(failed),
        "over_limit_count": len(over_limit),
        "failed": failed[:50],
        "over_limit": over_limit[:50],
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }

    report_path = Path(r"E:\America Custom Boxes\acb_new_images_webp_report.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nDone.")
    print(f"Success: {ok}/{total}")
    print(f"Skipped (already OK): {skipped}")
    print(f"Failed: {len(failed)}")
    print(f"Over {MAX_BYTES // 1024}KB (best effort): {len(over_limit)}")
    print(f"Report: {report_path}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
