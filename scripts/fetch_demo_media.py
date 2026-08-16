"""Restore external Civitas demo media from the manifest.

Open-licensed files use their manifest source_url. Locally contributed files
use CIVITAS_DEMO_MEDIA_BASE_URL + remote_key. Every download is SHA-256
verified before replacement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"datasets/demo_data/manifest.json"

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def source_for(item: dict) -> str | None:
    if item.get("source_url"): return item["source_url"]
    base=os.environ.get("CIVITAS_DEMO_MEDIA_BASE_URL","").rstrip("/")
    key=item.get("remote_key")
    return f"{base}/{key.lstrip('/')}" if base and key else None

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--force",action="store_true"); ap.add_argument("--only",choices=["images","videos"]); args=ap.parse_args()
    data=json.loads(MANIFEST.read_text(encoding="utf-8")); failures=0
    groups=[args.only] if args.only else ["images","videos"]
    for group in groups:
        for item in data.get(group,[]):
            target=ROOT/item["file"]; expected=item.get("sha256")
            if target.exists() and not args.force and (not expected or sha256(target)==expected):
                print(f"ok   {target.relative_to(ROOT)}"); continue
            url=source_for(item)
            if not url:
                print(f"skip {target.relative_to(ROOT)} (no source_url and CIVITAS_DEMO_MEDIA_BASE_URL not set)"); failures+=1; continue
            target.parent.mkdir(parents=True,exist_ok=True); tmp=target.with_suffix(target.suffix+".part")
            try:
                print(f"get  {target.relative_to(ROOT)}")
                req=urllib.request.Request(url,headers={"User-Agent":"Civitas-demo-media/1.0"})
                with urllib.request.urlopen(req,timeout=60) as resp, tmp.open("wb") as out:
                    while True:
                        chunk=resp.read(1024*1024)
                        if not chunk: break
                        out.write(chunk)
                if expected and sha256(tmp)!=expected:
                    got=sha256(tmp); tmp.unlink(missing_ok=True); raise RuntimeError(f"SHA-256 mismatch: expected {expected}, got {got}")
                tmp.replace(target)
            except Exception as exc:
                tmp.unlink(missing_ok=True); failures+=1; print(f"FAIL {target.relative_to(ROOT)}: {exc}",file=sys.stderr)
    return 1 if failures else 0
if __name__=="__main__": raise SystemExit(main())
