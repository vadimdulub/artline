#!/usr/bin/env python3
"""Painter-by-painter review of selected Cleveland gaps; local CC0 downloads only."""
import argparse
import collections
import importlib.util
import io
import json
from pathlib import Path
import re

from PIL import Image
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-selected-cleveland-works.py')
delivery=importlib.util.module_from_spec(spec);spec.loader.exec_module(delivery)
imp=delivery.imp;museum=delivery.museum;core=delivery.core
REFERENCE=ROOT/'docs/research/open-access-followup-20260919/cleveland-discovery'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--max-downloads',type=int,default=30);a=p.parse_args()
    if not 1<=a.max_downloads<=50:raise ValueError('Selected batch must be at most 50 downloads')
    a.run.mkdir(parents=True,exist_ok=True)
    leads=json.loads((REFERENCE/'source-leads.json').read_text())
    candidates=[imp.candidate(lead) for lead in leads]
    with museum.ro('postgres://localhost/artline') as db:
        people={r['slug']:r for r in delivery.profiles(db,sorted({c['artist_slug'] for c in candidates}))}
        state=imp.snapshot(db,candidates)
        represented={r['external_id'] for r in state['identifiers'] if r['scheme'] in state['schemes']}
        accessioned={museum.norm(w['accession_number']) for w in state['works'] if w['accession_number'] and (w['current_institution_id']==state['institution_id'] or w['museum_holding'])}
    groups=collections.defaultdict(list)
    for lead in leads:groups[lead['artist']['slug']].append(lead)
    fetch=core.Fetcher(a.run/'metadata');fetch.defer_long_cooldowns=True
    reviews=[];selected=[];paused=False
    for slug,group in sorted(groups.items(),key=lambda x:people[x[0]]['display_name']):
        painter={'slug':slug,'name':people[slug]['display_name'],'works':[]}
        for lead in sorted(group,key=lambda x:x['source_object_id']):
            oid=lead['source_object_id'];item={'object_id':oid,'title':lead['title']}
            if oid in represented or museum.norm(lead['accession_number']) in accessioned:
                item['outcome']='already_represented';painter['works'].append(item);continue
            try:
                url='https://openaccess-api.clevelandart.org/api/artworks/'+oid
                raw=fetch.metadata(url)['data']
                c=imp.candidate(lead);museum.source_match(c,raw);delivery.fresh_life_check(people[slug],raw)
                if people[slug]['qid']!=c['artist_qid']:raise ValueError('Catalogue painter authority changed')
                capture=json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_text())
                c=imp.candidate(dict(lead,object=raw,metadata_capture=capture))
                _,conflicts=imp.conflicts([c],state)
                item.update(outcome='source_verified',source_page=c['page'],date=c['date_display'],rights='CC0',
                            catalogue_review=conflicts[0]['reason'] if conflicts else 'requires both-target import preflight')
                c['catalogue_review']=item['catalogue_review'];selected.append(c)
            except Exception as error:
                item.update(outcome='held',reason=str(error)[:400])
                if isinstance(error,core.SourceCooldown) or isinstance(error,requests.HTTPError) and error.response.status_code in (403,429):paused=True
            painter['works'].append(item)
            if paused:break
        reviews.append(painter)
        print('Reviewed painter',painter['name'],dict(collections.Counter(w['outcome'] for w in painter['works'])),flush=True)
        if paused:break
    # Balance image downloads across painters before taking second/third works.
    balanced=[];byartist=collections.defaultdict(list)
    for c in selected:byartist[c['artist_slug']].append(c)
    for rank in range(max(map(len,byartist.values()),default=0)):
        for slug,group in sorted(byartist.items(),key=lambda x:people[x[0]]['display_name']):
            if rank<len(group):balanced.append(group[rank])
    selected=balanced[:a.max_downloads]
    core.save_new(a.run/'painter-review.json',{'at':core.now(),'painters':reviews,'selected_downloads':len(selected),
        'note':'Current exact museum objects reviewed painter by painter. Same-title objects remain separate review leads, not assumed duplicates or new published records.'})
    core.save_new(a.run/'selected.json',{'records':selected})
    downloaded=[];failures=[]
    for c in selected:
        oid=c['external_id']
        try:
            data,headers=fetch.get(c['source_image_url'],20_000_000)
            with Image.open(io.BytesIO(data)) as image:image.verify()
            compressed,w,h,quality=core.compress(data)
            path=a.run/'images'/(oid+'-'+core.sha(compressed)[:16]+'.jpg')
            core.save_new(path,compressed)
            receipt={'object_id':oid,'artist':c['artist'],'artist_slug':c['artist_slug'],'title':c['title'],
                'source_page':c['page'],'source_image_url':c['source_image_url'],'license_url':museum.CC0,
                'source_sha256':core.sha(data),'source_bytes':len(data),'source_headers':headers,
                'path':str(path.resolve()),'sha256':core.sha(compressed),'bytes':len(compressed),'width':w,'height':h,
                'quality':quality,'checked_at':core.now(),'catalogue_review':c['catalogue_review'],
                'transform':'Full-frame proportional resize and JPEG compression; no crop or generated content',
                'status':'downloaded_for_review_not_attached'}
            core.save_new(a.run/'receipts'/(oid+'.json'),receipt);downloaded.append(receipt)
            print('Downloaded <=100KB',c['artist'],oid,len(compressed),flush=True)
        except Exception as error:
            failures.append({'object_id':oid,'reason':str(error)[:400]})
            if isinstance(error,core.SourceCooldown) or isinstance(error,requests.HTTPError) and error.response.status_code in (403,429):break
    report={'at':core.now(),'painters_reviewed':len(reviews),'artworks_reviewed':sum(len(r['works']) for r in reviews),
        'review_outcomes':dict(collections.Counter(w['outcome'] for r in reviews for w in r['works'])),
        'downloaded':len(downloaded),'download_painters':len({r['artist_slug'] for r in downloaded}),
        'bytes':sum(r['bytes'] for r in downloaded),'maximum_bytes':max((r['bytes'] for r in downloaded),default=0),
        'database_writes':0,'cloud_uploads':0,'failures':failures,'images':downloaded}
    core.save_new(a.run/'download-report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='images'},indent=2),flush=True)


if __name__=='__main__':main()
