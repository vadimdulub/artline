#!/usr/bin/env python3
"""Bounded, read-only research of missing catalogue illustrations; no imports."""
import datetime
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/library-illustrations-20261001'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'captures').mkdir(exist_ok=True)
UA = 'ArtlineResearch/1.0 (selected catalogue illustrations; https://artlines.org/about)'

def fetch(url):
    path = OUT / 'captures' / (hashlib.sha256(url.encode()).hexdigest() + '.json')
    if path.exists():
        return json.loads(path.read_text())
    time.sleep(1.5)
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=45) as response:
        raw = response.read()
    result = json.loads(raw)
    if 'error' in result:
        raise ValueError(result['error'])
    path.write_bytes(raw)
    path.with_suffix('.receipt.json').write_text(json.dumps({'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'retrievedAt': datetime.datetime.now(datetime.timezone.utc).isoformat()}))
    return result

def query(sql):
    env = dict(os.environ, PGOPTIONS='-c default_transaction_read_only=on')
    return json.loads(subprocess.check_output(['psql', 'postgres://localhost/artline', '-X', '-At', '-c', 'SELECT coalesce(json_agg(x),\'[]\'::json) FROM (' + sql + ') x'], env=env))

def main():
    if (OUT / 'selected-images.json').exists():
        raise SystemExit('This campaign has been reviewed. Preserve its identities and captures; use a new campaign for further research.')
    covers = json.loads((ROOT / 'apps/server/internal/books/cover-selection.json').read_text())
    portraits = json.loads((ROOT / 'apps/server/internal/books/portrait-selection.json').read_text())
    quoted = lambda values: ','.join("'" + value.replace("'", "''") + "'" for value in values)
    books = query("SELECT b.id,b.source_id AS qid,b.title AS name,b.author_label AS creator,b.record->>'sourceUrl' AS source_url,b.end_year FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id AND d.book_checksum=b.source_checksum WHERE b.status<>'archived' AND b.end_year<=1930 AND b.id NOT IN (" + quoted([r['bookId'] for r in covers]) + ") ORDER BY coalesce(d.top100,false) DESC,b.end_year DESC,b.id LIMIT 100")
    authors = query("SELECT c.id,c.id AS qid,c.name,c.record->>'sourceUrl' AS source_url,c.record->>'death' AS death,count(DISTINCT b.id) AS books FROM book_creators c JOIN book_creator_links l ON l.creator_id=c.id JOIN book_records b ON b.id=l.book_id WHERE b.status<>'archived' AND c.record->>'kind'='person' AND c.id NOT IN (" + quoted([r['creatorId'] for r in portraits]) + ") AND c.record->>'death' ~ '^1[0-9]{3}$' AND (c.record->>'death')::int<=1950 GROUP BY c.id ORDER BY count(DISTINCT b.id) DESC,c.id LIMIT 45")
    events = query("SELECT id,source_id AS qid,title AS name,record->>'sourceUrl' AS source_url,start_year,end_year,kind FROM event_records WHERE status<>'archived' AND top100 AND start_year>=1400 AND end_year<=1970 ORDER BY start_year,id LIMIT 40")
    identities = [dict(row, category=category) for category, rows in [('books',books),('authors',authors),('events',events)] for row in rows]
    (OUT / 'identities.json').write_text(json.dumps(identities,ensure_ascii=False,indent=2)+'\n')
    entities = {}
    ids = sorted({r['qid'] for r in identities})
    for offset in range(0,len(ids),20):
        batch = ids[offset:offset+20]
        url='https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode({'action':'wbgetentities','format':'json','ids':'|'.join(batch),'props':'claims|labels','languages':'en'})
        try:
            entities.update(fetch(url)['entities'])
        except Exception as error:
            print('Entity batch failed:',error,flush=True)
        print('Entities',len(entities),'/',len(ids),flush=True)
    candidates = []
    for row in identities:
        entity=entities.get(row['qid'],{})
        claims=[c for c in entity.get('claims',{}).get('P18',[]) if c.get('rank')!='deprecated' and c.get('mainsnak',{}).get('datavalue')]
        claims.sort(key=lambda c:c.get('rank')!='preferred')
        for claim in claims[:2]:
            candidates.append(dict(row,file=claim['mainsnak']['datavalue']['value'],claimId=claim['id'],entityRevision=entity.get('lastrevid')))
    names=sorted({r['file'] for r in candidates});pages={}
    for offset in range(0,len(names),8):
        batch=names[offset:offset+8]
        url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url|size|mime|extmetadata|sha1','iiextmetadatalanguage':'en','iiurlwidth':640,'titles':'|'.join('File:'+name for name in batch),'redirects':1})
        try:
            data=fetch(url)['query'];by_title={p['title']:p for p in data.get('pages',{}).values()};renames={r['from']:r['to'] for r in data.get('normalized',[])+data.get('redirects',[])}
            for name in batch:
                title='File:'+name
                for _ in range(5):
                    if title not in renames:break
                    title=renames[title]
                pages[name]={'page':by_title.get(title,{}),'evidenceFile':str((OUT/'captures'/(hashlib.sha256(url.encode()).hexdigest()+'.json')).relative_to(ROOT))}
                p=ROOT/pages[name]['evidenceFile'];pages[name]['evidenceSha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception as error:
            print('Commons batch failed:',error,flush=True)
        print('Commons',len(pages),'/',len(names),flush=True)
    for row in candidates:row.update(pages.get(row['file'],{}))
    (OUT/'candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n')
    plain=lambda x:' '.join(html.unescape(re.sub('<[^>]*>',' ',str(x))).split())
    review=[]
    for row in candidates:
        info=row.get('page',{}).get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
        review.append({k:row.get(k) for k in ['id','qid','name','category','file']}|{k:plain(meta.get(k,{}).get('value','')) for k in ['LicenseShortName','Artist','Credit','DateTimeOriginal','Restrictions','Categories','ImageDescription']})
    (OUT/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
    print('Research complete:',len(candidates),'candidates; no image downloads or database writes.',flush=True)

if __name__=='__main__':main()
