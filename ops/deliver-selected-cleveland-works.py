#!/usr/bin/env python3
"""Refresh, visually gate, import and deliver a bounded new Cleveland selection."""
import argparse
import collections
import concurrent.futures
import fcntl
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace
import requests

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('imp',ROOT/'ops/import-overnight-cleveland-selection.py')
imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)
museum=imp.museum;core=imp.core
BASE='https://artline-web-lpuqqlugnq-ew.a.run.app'
imp.SOURCE='open-access-selected-cleveland-20260919'
imp.BACKUP_ROOT=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/open-access-new-artworks-20260919')

def profiles(db,slugs):
    return db.execute('''SELECT slug,id::text,display_name,birth_year,death_year,status,
        (SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artist'
          AND e.entity_id=p.id AND e.scheme='wikidata') qid
        FROM artists p WHERE slug=ANY(%s) ORDER BY slug''',(slugs,)).fetchall()

def fresh_life_check(artist,obj):
    maker=museum.primary_maker(obj);agreements=0
    for key in ('birth_year','death_year'):
        value=str(maker.get(key) or '')
        if re.fullmatch(r'\d{4}',value) and artist.get(key) is not None:
            if int(value)!=artist[key]:raise ValueError('Current museum creator life dates conflict')
            agreements+=1
    if not agreements:raise ValueError('No creator life year independently corroborates the match')

def select(a):
    if (a.run/'plan.json').exists():raise ValueError('Pinned plan exists; resume prepare/apply')
    draft=json.loads((a.reference/'plan.json').read_text())['records']
    if not 1<=len(draft)<=50:raise ValueError('Use a bounded pre-reviewed batch of 1–50 works')
    leads={r['source_object_id']:r for r in json.loads((a.reference/'source-leads.json').read_text())}
    slugs=sorted({c['artist_slug'] for c in draft})
    with museum.ro('postgres://localhost/artline') as db:
        current={r['slug']:r for r in profiles(db,slugs)}
    fetch=core.Fetcher(a.run/'fresh-api');candidates=[];held=[]
    for old in draft:
        oid=old['external_id'];lead=dict(leads[oid]);artist=current[old['artist_slug']]
        url='https://openaccess-api.clevelandart.org/api/artworks/'+oid
        try:
            if any(artist[k]!=lead['artist'][k] for k in ('id','slug','display_name','birth_year','death_year','qid')):raise ValueError('Existing painter identity changed since discovery')
            raw=fetch.metadata(url)['data']
            museum.source_match(old,raw);fresh_life_check(artist,raw)
            receipt=json.loads((fetch.cache/(core.sha(url.encode())+'.receipt.json')).read_text())
            lead.update(object=raw,metadata_capture=receipt)
            c=imp.candidate(lead);c.update(status='review',research_candidate=True)
            candidates.append(c)
            print('Current CC0 object verified',oid,c['title'],flush=True)
        except Exception as error:
            held.append({'external_id':oid,'title':old['title'],'reason':str(error)[:500]})
    dsn=core.cloud_dsn();manifests={};states={};people={}
    for target,d in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with museum.ro(d) as db:
            state=imp.snapshot(db,candidates);accepted,conflicts=imp.conflicts(candidates,state)
            held.extend(dict(c,target=target) for c in conflicts)
            already=[c for c in accepted if c['already_present']]
            held.extend({'external_id':c['external_id'],'reason':'Already present; not a new import','target':target} for c in already)
            accepted=[c for c in accepted if not c['already_present']]
            candidates=[{k:v for k,v in c.items() if k not in ('already_present','target_artist_id')} for c in accepted]
            people[target]=profiles(db,sorted({c['artist_slug'] for c in candidates}))
            states[target]=state
    if not candidates:raise ValueError('No new candidates survive both catalogue checks')
    for c in candidates:
        c['target_ids']={'local':c['artwork_id'],'cloud':c['artwork_id']}
        c['institution_ids']={target:state['institution_id'] for target,state in states.items()}
    for target,state in states.items():
        path=imp.BACKUP_ROOT/a.run.name/(target+'-before-selection.json')
        core.save_new(path,{'at':core.now(),'state':state,'artist_profiles':people[target],
            'new_artwork_ids':[c['artwork_id'] for c in candidates]})
        manifests[target]={'path':str(path),'sha256':core.sha(path.read_bytes())}
    data={'at':core.now(),'records':candidates,'held':held,
        'policy':'User approved new museum artworks for existing painters. Current exact object CC0, creator, life dates, creation interval, ownership and image identity checked. Duplicate guards passed in both catalogues. Review only; no display claim.'}
    core.save_new(a.run/'plan.json',data)
    core.save_new(a.run/'plan-manifest.json',{'sha256':core.sha((a.run/'plan.json').read_bytes()),'count':len(candidates)})
    core.save_new(a.run/'backups.json',{'targets':manifests})
    core.save_new(a.run/'candidates.json',{'created_at':data['at'],'candidates':candidates,'production_metadata_pending':True})
    for c in candidates:core.save_new(a.run/'selected/night-cleveland'/(c['artwork_id']+'.json'),c)
    print(json.dumps({'selected':len(candidates),'painters':len({c['artist_slug'] for c in candidates}),'held':held},indent=2),flush=True)

def pinned(run):
    if core.sha((run/'plan.json').read_bytes())!=json.loads((run/'plan-manifest.json').read_text())['sha256']:raise ValueError('Plan checksum differs')
    for entry in json.loads((run/'backups.json').read_text())['targets'].values():
        if core.sha(Path(entry['path']).read_bytes())!=entry['sha256']:raise ValueError('Recovery preimage differs')
    return json.loads((run/'plan.json').read_text())['records']

def run_phase(a):
    records=pinned(a.run);latest=core.latest_events(a.run)
    for c in records:museum.source_match(c,c['raw']['object'])
    if a.phase=='apply':
        reviewed={r['artwork_id']:r['sha256'] for r in json.loads((a.run/'reviewed-images.json').read_text())['images']}
        if set(reviewed)!={c['artwork_id'] for c in records}:raise ValueError('Every selected work needs a checksum-pinned visual review before import')
        for c in records:
            image=json.loads((a.run/'images/night-cleveland'/(c['artwork_id']+'.json')).read_text())
            if image['sha256']!=reviewed[c['artwork_id']]:raise ValueError('Reviewed image differs')
        # Both targets pass again before the first catalogue mutation.
        for target,d in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
            with museum.ro(d) as db:
                accepted,held=imp.conflicts(records,imp.snapshot(db,records))
                if held or len(accepted)!=len(records):raise ValueError('Current duplicate/identity review differs for '+target)
                people={p['slug']:p for p in profiles(db,sorted({c['artist_slug'] for c in records}))}
                for c in records:fresh_life_check(people[c['artist_slug']],c['raw']['object'])
        imp.apply(a.run,'local');imp.apply(a.run,'cloud')
        todo=[c for c in records if latest.get(c['artwork_id'],{}).get('outcome')!='complete']
        dsn=core.cloud_dsn()
    else:
        todo=[c for c in records if latest.get(c['artwork_id'],{}).get('outcome') not in ('prepared','complete')];dsn=None
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs=[pool.submit(core.worker,'night-cleveland',todo[i::3],SimpleNamespace(run=a.run,prepare_only=a.phase=='prepare',upload_prepared_only=a.phase=='apply'),dsn) for i in range(3) if todo[i::3]]
        for job in jobs:job.result()
    print(core.now(),dict(collections.Counter(e['outcome'] for e in core.latest_events(a.run).values())),flush=True)

def verify(a):
    records=pinned(a.run);errors=[];databases={};receipts={}
    for c in records:
        im=json.loads((a.run/'images/night-cleveland'/(c['artwork_id']+'.json')).read_text())
        museum.source_match(im,im['raw']['object']);receipts[c['artwork_id']]=im
    for target,d in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with museum.ro(d) as db:
            rows=db.execute(museum.QUERY+' AND a.id=ANY(%s::uuid[])',([c['artwork_id'] for c in records],)).fetchall()
            byid={r['artwork_id']:r for r in rows}
            checks=0
            for c in records:
                row=byid.get(c['artwork_id']);im=receipts[c['artwork_id']]
                fields=('title','accession_number','creation_year_start','creation_year_end','date_precision','date_display','work_type','artist_slugs','roles','status','research_candidate')
                if not row or any(row[k]!=c[k] for k in fields) or row['primary_media_id']!=im['media_id'] or row['current_institution_id']!=c['institution_ids'][target]:
                    errors.append({'target':target,'artwork_id':c['artwork_id'],'error':'Imported metadata or image differs'})
                else:checks+=1
            counts=db.execute('''SELECT count(*) total,
                count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate
                  AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible'
                  AND artline_has_selection_evidence(id)) eligible_review
                FROM artworks WHERE id=ANY(%s::uuid[])''',([c['artwork_id'] for c in records],)).fetchone()
            holding=db.execute('''SELECT artwork_id::text,claim_type,institution_id::text,source_url,review_state,context
                FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])''',([c['artwork_id'] for c in records],)).fetchall()
            for c in records:
                claims=[r for r in holding if r['artwork_id']==c['artwork_id']]
                expected={'artwork_id':c['artwork_id'],'claim_type':'holding','institution_id':c['institution_ids'][target],
                    'source_url':c['page'],'review_state':'accepted','context':'collection'}
                if claims!=[expected]:errors.append({'target':target,'artwork_id':c['artwork_id'],'error':'Holding assertion differs or unexpected display claim'})
            before=json.loads(Path(json.loads((a.run/'backups.json').read_text())['targets'][target]['path']).read_text())
            after=profiles(db,[c['artist_slug'] for c in records])
            expected=[p for p in before['artist_profiles'] if p['slug'] in {c['artist_slug'] for c in records}]
            if after!=expected:errors.append({'target':target,'error':'Existing painter profiles changed'})
            if counts['total']!=len(records) or counts['eligible_review']!=len(records):errors.append({'target':target,'error':'Review/creation scope check failed'})
            databases[target]={'matched_records':checks,'counts':counts,'holding_claims':len(holding),'artist_profiles_unchanged':after==expected}
    def public(c):
        im=receipts[c['artwork_id']];res=requests.get(BASE+im['path'],timeout=30)
        image_ok=res.status_code==200 and res.headers.get('Content-Type','').startswith('image/jpeg') and core.sha(res.content)==im['sha256']
        url=BASE+'/api/backend/v1/artists/'+c['artist_slug']+'/works/'+c['artwork_id'];api=requests.get(url,timeout=30)
        actual=api.json() if api.status_code==200 else {}
        api_ok=api.status_code==200 and all(actual.get(k)==v for k,v in {'title':c['title'],'media_url':im['path'],'status':'review','license_url':c['policy_url'],'source_page_url':c['page']}.items())
        return {'artwork_id':c['artwork_id'],'image_http_status':res.status_code,'image_verified':image_ok,'api_url':url,'api_http_status':api.status_code,'api_verified':api_ok}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(public,records))
    errors.extend({'artwork_id':r['artwork_id'],'error':'Public image/API check failed'} for r in checks if not r['image_verified'] or not r['api_verified'])
    result={'at':core.now(),'new_artworks':len(records),'painters':len({c['artist_slug'] for c in records}),
        'types':dict(collections.Counter(c['work_type'] for c in records)),'databases':databases,'public_checks':checks,'errors':errors}
    core.save_new(a.run/'catalogue-public-verification.json',result);print(json.dumps(result,indent=2),flush=True)
    if errors:raise SystemExit(1)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['select','prepare','apply','verify']);p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    with (a.run/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.phase=='select':select(a)
        elif a.phase=='verify':verify(a)
        else:run_phase(a)
if __name__=='__main__':main()
