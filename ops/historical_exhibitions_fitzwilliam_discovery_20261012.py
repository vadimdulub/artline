#!/usr/bin/env python3
"""Capture the public museum exhibition index; no database mutations."""
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import exhibitions_common as c
import historical_exhibitions_nga_histories_20261012 as n
OUT=n.OUT.parent/'fitzwilliam-exhibitions'
def page(number):
 path=OUT/f'index-page-{number:02d}.json'
 if path.exists():return c.load(path)
 raw,rc=c.capture(f'https://data.fitzmuseum.cam.ac.uk/id/exhibition?page={number}')
 soup=BeautifulSoup(raw,'html.parser')
 links=[dict(title=a.get_text(' ',strip=True),url=a.get('href'))for a in soup.select('a[href]')if '/id/exhibition/'in a.get('href','')]
 assert 1<=len(links)<=50,(number,len(links))
 result=dict(page=number,receipt=rc,leads=links)
 c.save(path,result);print('Captured page',number,'references',len(links),flush=True);return result
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=2)as pool:pages=list(pool.map(page,range(1,66)))
 leads=[l for p in pages for l in p['leads']];assert len({x['url']for x in leads})==len(leads)==3231
 c.save(OUT/'index-discovery.json.gz',dict(at=c.now(),pages=len(pages),references=len(leads),leads=leads,basis='Public museum index. Not all references are historical eligible held exhibitions; do not ingest without detail review.'))
 print('Verified unique index references',len(leads),flush=True)
