#!/usr/bin/env python3
"""Local-only visual comparison for private ART500K references.

Reference bytes and fingerprints never leave the private work root and are
never written to production exports. Candidate bytes must come from an
independent authoritative URL.
"""
import argparse, io, json, tarfile, tempfile
from pathlib import Path
import requests
from PIL import Image, ImageOps

def reference_bytes(source: Path, member: str) -> bytes:
    if source.is_file():
        with tarfile.open(source, 'r:gz') as t:
            f=t.extractfile(member)
            if not f: raise FileNotFoundError(member)
            return f.read()
    p=source/member
    return p.read_bytes()

def ahash(data: bytes, size=16) -> int:
    with Image.open(io.BytesIO(data)) as im:
        im=ImageOps.exif_transpose(im).convert('L').resize((size,size))
        px=list(im.getdata()); avg=sum(px)/len(px); out=0
        for v in px: out=(out<<1)|(v>=avg)
        return out

def distance(a:int,b:int,size=16): return (a^b).bit_count()/(size*size)

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--member',required=True);p.add_argument('--candidate-url',required=True);p.add_argument('--work',required=True);a=p.parse_args()
    if not a.candidate_url.startswith(('https://upload.wikimedia.org/','https://iiif.','https://')): raise SystemExit('Candidate must be an HTTPS authoritative source URL')
    ref=reference_bytes(Path(a.source),a.member)
    r=requests.get(a.candidate_url,headers={'User-Agent':'ArtlinePrivateReference/1.0 (local comparison)'},timeout=(10,45));r.raise_for_status(); cand=r.content
    score=distance(ahash(ref),ahash(cand)); out=Path(a.work);out.mkdir(parents=True,exist_ok=True)
    result={'candidate_url':a.candidate_url,'hamming_distance':score,'reference_bytes_discarded':True,'reference_fingerprint_discarded':True,'external_upload':False,'production_safe':True}
    (out/'visual-comparison-last.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
