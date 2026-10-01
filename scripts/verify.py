"""Validate the local collection against its provenance manifest (stdlib only)."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    seen = set()
    errors = []
    total_bytes = 0
    for asset in catalog["assets"]:
        path = asset["path"]
        file = (ROOT / path).resolve()
        if not file.is_relative_to(ROOT):
            errors.append(f"Outside repository: {path}")
            continue
        if path in seen:
            errors.append(f"Duplicate entry: {path}")
        seen.add(path)
        if not file.is_file():
            errors.append(f"Missing: {path}")
            continue
        data = file.read_bytes()
        total_bytes += len(data)
        if hashlib.sha256(data).hexdigest() != asset["sha256"]:
            errors.append(f"SHA-256 mismatch: {path}")
        if len(data) != asset["bytes"]:
            errors.append(f"Size mismatch: {path}")
        if asset["source_id"] not in catalog["sources"]:
            errors.append(f"Unknown source: {path}")
        if asset.get("preview") and not (ROOT / asset["preview"]).is_file():
            errors.append(f"Missing preview: {path}")
    disk_assets = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "characters").rglob("*")
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    }
    errors.extend(f"Uncatalogued: {p}" for p in sorted(disk_assets - seen))
    for role in catalog["characters"]:
        if not (ROOT / "characters" / role["id"] / "README.md").is_file():
            errors.append(f"Missing character README: {role['id']}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Verified {len(seen)} assets, {len(catalog['characters'])} characters, "
          f"{total_bytes / 1024 / 1024:.1f} MiB. SHA-256 and local paths OK.")


if __name__ == "__main__":
    main()
