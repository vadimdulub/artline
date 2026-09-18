#!/usr/bin/env python3
"""Capture bounded, already selected official museum metadata; never image bytes."""
import argparse, importlib.util, json, time
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location('core', ROOT/'ops/enrich-artwork-images.py')
core = importlib.util.module_from_spec(s); s.loader.exec_module(core)
core.HOSTS.add('collection.nationalmuseum.se')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--run',type=Path,required=True); p.add_argument('--limit',type=int,default=1000); p.add_argument('--deadline',type=float,required=True); a=p.parse_args()
    rows=json.loads((a.run/'bounded-primary-leads.json').read_text())
    if isinstance(rows,dict):rows=rows['records']
    fetch=core.Fetcher(a.run/'http-cache')
    for n,lead in enumerate(rows[:a.limit],1):
        if time.time()>=a.deadline:break
        oid=lead['native_id']; path=a.run/'current-records'/(oid+'.json')
        if path.exists():continue
        url='https://collection.nationalmuseum.se/en/collection/item/'+oid+'/'
        try:
            payload,headers=fetch.get(url,4_000_000)
            soup=BeautifulSoup(payload,'html.parser'); data=json.loads(soup.find('script',id='__NEXT_DATA__').string)
            item=data['props']['pageProps']['data']['item']; assert str(item['Id'])==oid
            # Preserve the exact public metadata and how the site's own HTML links its image.
            evidence={'url':url,'retrieved_at':core.now(),'sha256':core.sha(payload),'headers':headers,'item':item,
                      'rendered_image_paths':sorted({im.get('src') for im in soup.find_all('img') if im.get('src','').startswith('/multimedia/')})}
            core.save_new(path,evidence)
        except Exception as exc:
            core.event(a.run,{'provider':'followup-nationalmuseum','external_id':oid,'outcome':'capture_error','reason':str(exc)[:300]})
            if '403' in str(exc) or '429' in str(exc):raise
        if n%20==0:print(core.now(),'Current Nationalmuseum records',n,'of',min(len(rows),a.limit),flush=True)

if __name__=='__main__':main()
