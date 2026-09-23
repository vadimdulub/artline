#!/usr/bin/env python3
"""Read-only preservation and byte-exact public-delivery checks for gap uploads."""
import argparse
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import requests
import psycopg
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py')
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
BASE='https://artline-web-lpuqqlugnq-ew.a.run.app'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();images=[]
    for run in a.run:
        for e in core.latest_events(run).values():
            if e.get('outcome')=='complete':
                images.append(json.loads((run/'images'/e['provider']/(e['artwork_id']+'.json')).read_text()))
    errors=[];databases={}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=180000') as db:
            ids=[im['target_ids'][target] for im in images]
            records=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
            byid={r['record']['id']:r['record'] for r in records}
            holdings=db.execute('''SELECT artwork_id::text,institution_id::text,source_url,context
                FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])
                AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL''',(ids,)).fetchall()
            excluded={'primary_media_id','revision','updated_at','updated_by'}
            checked=0;verified_holdings=0
            for im in images:
                now=byid.get(im['target_ids'][target]);before=dict(im['before'][target])
                if im['provider']=='night-saam' and before['current_institution_id'] is None:
                    matches=[r for r in holdings if r['artwork_id']==im['target_ids'][target]]
                    if len(matches)==1 and matches[0]['institution_id']==im['institution_ids'][target] and matches[0]['source_url']==im['page'] and matches[0]['context']=='collection':
                        before['current_institution_id']=im['institution_ids'][target]
                        verified_holdings+=1
                if not now or {k:v for k,v in now.items() if k not in excluded}!={k:v for k,v in before.items() if k not in excluded}:
                    errors.append({'target':target,'artwork_id':im['artwork_id'],'error':'Non-media catalogue metadata differs from preimage',
                        'differences':{k:{'before':before.get(k),'after':(now or {}).get(k)} for k in set(before)|set(now or {}) if k not in excluded and before.get(k)!=(now or {}).get(k)}})
                elif now['primary_media_id']!=im['media_id']:
                    errors.append({'target':target,'artwork_id':im['artwork_id'],'error':'Expected primary image absent'})
                else:checked+=1
            links=db.execute('''SELECT aa.artwork_id::text,p.slug,aa.attribution_role FROM artwork_artists aa
                JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY p.slug''',(ids,)).fetchall()
            for im in images:
                rows=[r for r in links if r['artwork_id']==im['target_ids'][target]]
                if [r['slug'] for r in rows]!=im['artist_slugs'] or sorted(r['attribution_role'] for r in rows)!=im['roles']:
                    errors.append({'target':target,'artwork_id':im['artwork_id'],'error':'Creator attribution changed'})
            coverage=db.execute('''SELECT CASE WHEN e.scheme=ANY(%s) THEN 'Met'
                    WHEN e.scheme=ANY(%s) THEN 'Cleveland' ELSE 'Smithsonian' END museum,
                    count(DISTINCT a.id) artworks,count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NOT NULL) with_images
                FROM external_identifiers e JOIN artworks a ON a.id=e.entity_id
                WHERE e.entity_type='artwork' AND e.scheme=ANY(%s) AND a.status<>'archived'
                GROUP BY 1''',(['met-object','european-met-the-met-object'],
                ['cleveland-object','european-cleveland-cleveland-museum-of-art-object'],
                ['met-object','european-met-the-met-object','cleveland-object','european-cleveland-cleveland-museum-of-art-object','saam-object','fsg-object'])).fetchall()
            databases[target]={'artwork_metadata_preserved_except_verified_holdings':checked,'source_backed_holdings_added':verified_holdings,'creator_attributions_checked':len(images),'coverage':coverage,
                'statuses':{str(r['record']['id']):r['record']['status'] for r in records}}
    def check(im):
        url=BASE+im['path'];res=requests.get(url,timeout=30)
        ok=res.status_code==200 and res.headers.get('Content-Type','').startswith('image/jpeg') and len(res.content)==im['bytes'] and core.sha(res.content)==im['sha256']
        api_url=BASE+'/api/backend/v1/artists/'+im['artist_slugs'][0]+'/works/'+im['target_ids']['cloud']
        api=requests.get(api_url,timeout=30)
        record=api.json() if api.status_code==200 else {}
        api_ok=api.status_code==200 and all(record.get(k)==v for k,v in {
            'title':im['title'],'media_url':im['path'],'status':im['status'],
            'license_url':im['policy_url'],'source_page_url':im['page']}.items())
        return {'artwork_id':im['artwork_id'],'url':url,'http_status':res.status_code,'verified':ok,'bytes':len(res.content),
                'artwork_api':{'url':api_url,'http_status':api.status_code,'verified':api_ok}}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        checks=list(pool.map(check,images))
    errors.extend({'artwork_id':r['artwork_id'],'error':'Public image bytes differ or unavailable'} for r in checks if not r['verified'])
    errors.extend({'artwork_id':r['artwork_id'],'error':'Public artwork API differs or unavailable'} for r in checks if not r['artwork_api']['verified'])
    result={'at':core.now(),'new_images':len(images),'painters':len({s for im in images for s in im['artist_slugs']}),
        'databases':databases,'public_image_checks':checks,'errors':errors,
        'visibility_note':'Existing status, research_candidate flags, titles, dates and creator links are preserved. Any verified source-backed holding additions are counted per target above. No current-display claims, artist metadata edits, status publication or application deployment.'}
    core.save_new(a.output,result);print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)
if __name__=='__main__':main()
