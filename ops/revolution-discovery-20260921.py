#!/usr/bin/env python3
"""Source-led local review for dates, highlights and revolutionary art.

Captures are metadata only. Apply stages are added only for reviewed manifests;
source capture does not authorize publication or unrestricted image harvesting.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row
import requests

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/revolution-discovery-20260921'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/revolution-discovery-20260921'
DSN='postgres://localhost/artline'

def now(): return datetime.now(timezone.utc).isoformat()

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=data if isinstance(data,bytes) else (json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n').encode()
    if path.exists():
        assert path.read_bytes()==raw, f'Preserve prior evidence: {path}'
    else:path.write_bytes(raw)

def capture(url):
    path=RUN/'captures'/(hashlib.sha256(url.encode()).hexdigest()[:24]+'.raw')
    receipt=path.with_suffix('.json')
    if receipt.exists():
        data=json.loads(receipt.read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==data['sha256']
        return path,data
    response=requests.get(url,headers={'User-Agent':'Artline/1.0 (selected collection metadata research)'},timeout=(15,45))
    response.raise_for_status();assert len(response.content)<20_000_000
    data={'url':url,'final_url':response.url,'retrieved_at':now(),'path':str(path.relative_to(ROOT)),
          'sha256':hashlib.sha256(response.content).hexdigest(),'bytes':len(response.content)}
    save(path,response.content);save(receipt,data)
    if 'html' in response.headers.get('Content-Type',''):
        soup=BeautifulSoup(response.content,'html.parser')
        for node in soup(['script','style','noscript']):node.decompose()
        save(path.with_suffix('.txt'),soup.get_text('\n',strip=True).encode())
    time.sleep(.5)
    return path,data

def backup():
    receipt=RUN/'local-backup.json'
    if receipt.exists():print('Preserving the existing pre-apply backup');return
    BACKUP.mkdir(parents=True,exist_ok=True);path=BACKUP/'local-before.dump'
    with path.open('xb') as output:
        subprocess.run(['pg_dump','--dbname',DSN,'--format=custom','--no-owner','--no-privileges'],stdout=output,check=True)
    listing=subprocess.run(['pg_restore','--list',str(path)],capture_output=True,check=True)
    assert b'TABLE DATA public artworks' in listing.stdout and b'TABLE DATA public book_records' in listing.stdout
    save(receipt,{'at':now(),'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    print('Backup verified:',path)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['capture','backup']);parser.add_argument('urls',nargs='*')
    args=parser.parse_args()
    if args.stage=='backup':backup()
    else:
        for url in args.urls:
            try:
                _,receipt=capture(url);print(json.dumps(receipt),flush=True)
            except Exception as error:print(json.dumps({'url':url,'error':str(error)}),flush=True)
