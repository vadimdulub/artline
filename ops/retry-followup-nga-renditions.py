#!/usr/bin/env python3
"""Resolve only explicit same-image NGA 303 rendition URLs; no access-control bypass."""
import argparse,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('nga',ROOT/'ops/followup-nga-direct-images.py');nga=importlib.util.module_from_spec(s);s.loader.exec_module(nga);core=nga.core

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path,action='append',required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    fetch=core.Fetcher(a.run/'metadata');selected=[];held=[]
    ids=[aid for ref in a.reference for aid,e in core.latest_events(ref).items() if e.get('outcome')=='failed' and '303' in str(e)]
    with nga.nga.ro('postgres://localhost/artline') as db:
        already={r['id'] for r in db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[]) AND primary_media_id IS NOT NULL',(ids,)).fetchall()}
    for ref in a.reference:
        for aid,event in core.latest_events(ref).items():
            if event.get('outcome')!='failed' or '303' not in str(event):continue
            if aid in already:continue
            im=json.loads((ref/'selected'/nga.PROVIDER/(aid+'.json')).read_text());nga.verify(im);original=im['source_image_url']
            core.provider_rate_slot('api.nga.gov')
            with fetch.session.get(original,timeout=(15,45),stream=True,allow_redirects=False) as response:
                if response.status_code!=303:
                    held.append({'artwork_id':aid,'reason':'No explicit 303 rendering redirect','status':response.status_code});continue
                location=urljoin(original,response.headers.get('Location',''))
            base=im['raw']['published_image']['iiifurl']
            if not re.fullmatch(re.escape(base)+r'__\d+/full/!1000,1000/0/default\.jpg',location):
                held.append({'artwork_id':aid,'reason':'Redirect changes source identity, host, crop or rendition'});continue
            im['raw']['museum_rendition_redirect']={'status':303,'requested_url':original,'location':location,'retrieved_at':core.now()};im['source_image_url']=location
            nga.verify(im);core.save_new(a.run/'selected'/nga.PROVIDER/(aid+'.json'),im);selected.append(im)
    core.save_new(a.run/'candidates.json',{'created_at':core.now(),'candidates':selected});core.save_new(a.run/'held.json',held)
    print('Approved same-image rendition redirects',len(selected),'held',len(held),flush=True)

if __name__=='__main__':main()
