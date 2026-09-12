#!/usr/bin/env python3
"""Apply reviewed evidence chunks with per-chunk receipts and checksum checks.

Build cmd/stage-research first. DATABASE_URL is inherited, never logged. This
uploads research evidence only; it does not create visible catalogue entities.
Back up the target database before using --apply.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--target", choices=["local", "cloud-sql-proxy"], required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    root = args.review.parent.resolve()
    # Validate the complete inventory before allowing the first transaction.
    chunks = []
    for chunk in review["chunks"]:
        path = (root / chunk["file"]).resolve()
        if path.parent != root or not path.is_file():
            raise ValueError("invalid chunk path")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != chunk["sha256"]:
            raise ValueError("changed chunk: " + path.name)
        rows = json.loads(data)
        if len(rows) != chunk["records"] or not 1 <= len(rows) <= 5000:
            raise ValueError("invalid chunk size")
        if any(row["source_url"] != review["source_url"] for row in rows):
            raise ValueError("source reference mismatch")
        chunks.append((path, chunk))
    if sum(c[1]["records"] for c in chunks) != review["counts"]["staged_distinct_csv_rows"]:
        raise ValueError("inventory count mismatch")
    if not os.environ.get("DATABASE_URL"):
        raise ValueError("DATABASE_URL must explicitly select the target")
    args.receipts.mkdir(mode=0o700, parents=False, exist_ok=False)
    total = 0
    for path, chunk in chunks:
        command = [str(args.binary.resolve()), "-file", str(path), "-sha", chunk["sha256"],
                   "-name", "Expanded CSV 2026-09-12 " + path.stem,
                   "-target", args.target, "-report", str(args.receipts / path.name)]
        if args.apply:
            command.append("-apply")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        receipt = json.loads(result.stdout)
        if receipt["records"] != chunk["records"] or receipt["sha256"] != chunk["sha256"]:
            raise ValueError("receipt mismatch")
        total += receipt["records"]
        print(f'{args.target}: {path.name}: {receipt["records"]} records, '
              f'applied={receipt["applied"]}, replayed={receipt["replayed"]}', flush=True)
    print(f"Verified receipt total: {total}", flush=True)


if __name__ == "__main__":
    main()
