#!/usr/bin/env python3
"""Deliver a bounded, current CC0 Met selection; retain new artworks in review."""
import argparse
import collections
import concurrent.futures
import fcntl
import importlib.util
import json
import re
from pathlib import Path
from types import SimpleNamespace
import requests
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('imp',ROOT/'ops/import-overnight-met-selection.py')
imp=importlib.util.module_from_spec(spec);spec.loader.exec_module(imp)
research=imp.research;campaign=research.campaign;core=imp.core
imp.SOURCE='met-top-europe-selected-20260920'
imp.BACKUP_ROOT=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/met-top-europe-20260920')
BASE='https://artline-web-lpuqqlugnq-ew.a.run.app'


def profiles(db,slugs):
    return db.execute('''SELECT p.slug,to_jsonb(p) profile,
        (SELECT jsonb_agg(to_jsonb(c) ORDER BY c.country_code,c.relationship_type)
         FROM artist_countries c WHERE c.artist_id=p.id) countries
        FROM artists p WHERE slug=ANY(%s) ORDER BY slug''',(slugs,)).fetchall()


def life_agrees(c,profile):
    """Unknown life years stay unknown; exact contradictory years require review."""
    for source_key,local_key in (('artistBeginDate','birth_year'),('artistEndDate','death_year')):
        value=str(c['object'].get(source_key) or '').strip()
        if re.fullmatch(r'\d{4}',value) and profile.get(local_key) is not None and int(value)!=profile[local_key]:return False
    return True


def select(a):
    if (a.run/'plan.json').exists():raise ValueError('Pinned selection already exists')
    leads=json.loads((a.reference/'source-candidates.json').read_text());records=[]
    for lead in leads:
        path=a.reference/'verified'/(lead['source_object_id']+'.json')
        if not path.exists():continue
        c=json.loads(path.read_text());fresh=research.verify(lead,c['object'])
        if any(c[k]!=v for k,v in fresh.items()):raise ValueError('Fresh source differs')
        records.append(c)
    states={};people={};held=[]
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with campaign.read_only(dsn) as db:
            state=imp.snapshot(db,records);accepted,conflicts=imp.conflicts(records,state)
            held.extend(dict(r,target=target) for r in conflicts)
            records=[{k:v for k,v in r.items() if k not in ('already_present','target_artist_id')} for r in accepted if not r['already_present']]
            people[target]=profiles(db,sorted({c['artist_slug'] for c in records}));states[target]=state
            current={r['slug']:r['profile'] for r in people[target]}
            for c in records:
                if not life_agrees(c,current[c['artist_slug']]):held.append({'source_object_id':c['external_id'],'target':target,'reason':'Current catalogue creator life dates conflict with museum'})
            records=[c for c in records if life_agrees(c,current[c['artist_slug']])]
    records=records[:a.limit]
    if not records or len(records)>50:raise ValueError('Select 1–50 verified works')
    manifests={}
    for c in records:
        c.update(target_ids={'local':c['artwork_id'],'cloud':c['artwork_id']},
            institution_ids={t:s['institution_id'] for t,s in states.items()})
    for target,state in states.items():
        path=imp.BACKUP_ROOT/a.run.name/(target+'-before-selection.json')
        core.save_new(path,{'at':core.now(),'state':state,'artist_profiles':people[target],
            'new_artwork_ids':[c['artwork_id'] for c in records]})
        manifests[target]={'path':str(path),'sha256':core.sha(path.read_bytes())}
    data={'at':core.now(),'source_root':str(a.reference),'records':records,'held':held,
        'policy':'User-approved selected museum works; exact creator authority, current object CC0 and dates through 1970. Review only, holding evidence only; no display or publication claim.'}
    core.save_new(a.run/'plan.json',data)
    core.save_new(a.run/'plan-manifest.json',{'sha256':core.sha((a.run/'plan.json').read_bytes()),'count':len(records)})
    core.save_new(a.run/'backups.json',{'targets':manifests})
    core.save_new(a.run/'candidates.json',{'created_at':data['at'],'candidates':records})
    fetch=core.Fetcher(a.reference/'fresh-api')
    for c in records:
        im=core.image_record(c,fetch,{},{});core.validate_source_image_identity(im)
        core.save_new(a.run/'selected/met'/(c['artwork_id']+'.json'),im)
    print(json.dumps({'selected':len(records),'painters':len({c['artist_slug'] for c in records}),
        'countries':dict(collections.Counter(code for c in records for code in c['country_codes'])),'held':held}),flush=True)


def pinned(run):
    if core.sha((run/'plan.json').read_bytes())!=json.loads((run/'plan-manifest.json').read_text())['sha256']:raise ValueError('Pinned plan differs')
    for entry in json.loads((run/'backups.json').read_text())['targets'].values():
        if core.sha(Path(entry['path']).read_bytes())!=entry['sha256']:raise ValueError('Recovery preimage differs')
    return json.loads((run/'plan.json').read_text())['records']


def phase(a):
    records=pinned(a.run);latest=core.latest_events(a.run)
    if a.phase=='apply':
        reviewed={r['artwork_id']:r['sha256'] for r in json.loads((a.run/'reviewed-images.json').read_text())['images']}
        if set(reviewed)!={c['artwork_id'] for c in records}:raise ValueError('All selected images require visual review')
        for c in records:
            im=json.loads((a.run/'images/met'/(c['artwork_id']+'.json')).read_text())
            data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
            if core.sha(data)!=im['sha256'] or im['sha256']!=reviewed[c['artwork_id']] or len(data)>100000:raise ValueError('Reviewed image bytes differ')
        for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
            with campaign.read_only(dsn) as db:
                accepted,held=imp.conflicts(records,imp.snapshot(db,records))
                if held or len(accepted)!=len(records):raise ValueError('Catalogue preflight changed: '+target)
                current={r['slug']:r['profile'] for r in profiles(db,sorted({c['artist_slug'] for c in records}))}
                if any(not life_agrees(c,current[c['artist_slug']]) for c in records):raise ValueError('Creator life date check changed: '+target)
        imp.apply(a.run,'local',0,emit_image_candidates=False)
        imp.apply(a.run,'cloud',0,emit_image_candidates=False)
        todo=[c for c in records if latest.get(c['artwork_id'],{}).get('outcome')!='complete'];dsn=core.cloud_dsn()
    else:
        todo=[c for c in records if latest.get(c['artwork_id'],{}).get('outcome') not in ('prepared','complete')];dsn=None
    core.worker('met',todo,SimpleNamespace(run=a.run,prepare_only=a.phase=='prepare',upload_prepared_only=a.phase=='apply'),dsn)
    print(core.now(),dict(collections.Counter(e['outcome'] for e in core.latest_events(a.run).values())),flush=True)


def contact(a):
    records=pinned(a.run)
    for start in range(0,len(records),12):
        canvas=Image.new('RGB',(1440,1320),'white');draw=ImageDraw.Draw(canvas)
        for i,c in enumerate(records[start:start+12]):
            im=json.loads((a.run/'images/met'/(c['artwork_id']+'.json')).read_text())
            with Image.open(ROOT/'apps/web/public'/im['path'].lstrip('/')) as original:
                tile=original.copy();tile.thumbnail((342,330))
            x=(i%4)*360;y=(i//4)*440;canvas.paste(tile,(x+(360-tile.width)//2,y))
            draw.text((x+5,y+335),str(start+i+1)+' | '+c['external_id']+' | '+c['artist'][:35],fill='black')
            for j in range(0,min(len(c['title']),140),43):draw.text((x+5,y+355+j//43*16),c['title'][j:j+43],fill='black')
        canvas.save(a.run/('contact-sheet-'+str(start//12+1)+'.jpg'),quality=90)


def verify(a):
    records=pinned(a.run);errors=[];databases={};receipts={}
    for c in records:receipts[c['artwork_id']]=json.loads((a.run/'images/met'/(c['artwork_id']+'.json')).read_text())
    slugs=sorted({c['artist_slug'] for c in records})
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with campaign.read_only(dsn) as db:
            accepted,held=imp.conflicts(records,imp.snapshot(db,records))
            if held or len(accepted)!=len(records) or not all(c['already_present'] for c in accepted):errors.append({'target':target,'error':'Object metadata/identity differs','held':held})
            rows=db.execute('''SELECT a.id::text,a.primary_media_id::text,a.status,a.published_at,a.research_candidate,
                artline_has_selection_evidence(a.id) selected,
                artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope
                FROM artworks a WHERE a.id=ANY(%s::uuid[])''',([c['artwork_id'] for c in records],)).fetchall()
            if len(rows)!=len(records) or any(r['primary_media_id']!=receipts[r['id']]['media_id'] or r['status']!='review' or r['published_at'] or not r['research_candidate'] or not r['selected'] or r['scope']!='eligible' for r in rows):errors.append({'target':target,'error':'Review or image attachment differs'})
            claims=db.execute('''SELECT artwork_id::text,claim_type,institution_id::text,source_url,review_state,context
                FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])''',([c['artwork_id'] for c in records],)).fetchall()
            for c in records:
                actual=[r for r in claims if r['artwork_id']==c['artwork_id']]
                expected={'artwork_id':c['artwork_id'],'claim_type':'holding','institution_id':c['institution_ids'][target],
                    'source_url':c['page'],'review_state':'accepted','context':'collection'}
                if actual!=[expected]:errors.append({'target':target,'artwork_id':c['artwork_id'],'error':'Unexpected location claims'})
            before=json.loads(Path(json.loads((a.run/'backups.json').read_text())['targets'][target]['path']).read_text())
            expected=[p for p in before['artist_profiles'] if p['slug'] in slugs]
            unchanged=profiles(db,slugs)==expected
            if not unchanged:errors.append({'target':target,'error':'Existing artist profile or countries changed'})
            databases[target]={'verified_artworks':len(rows),'holding_claims':len(claims),'artist_profiles_unchanged':unchanged}
    def public(c):
        im=receipts[c['artwork_id']];response=requests.get(BASE+im['path'],timeout=30)
        ok=response.status_code==200 and core.sha(response.content)==im['sha256']
        url=BASE+'/api/backend/v1/artists/'+c['artist_slug']+'/works/'+c['artwork_id']
        api=requests.get(url,timeout=30);obj=api.json() if api.status_code==200 else {}
        api_ok=api.status_code==200 and all(obj.get(k)==v for k,v in {'title':c['title'],'media_url':im['path'],'status':'review','license_url':research.CC0,'source_page_url':c['page']}.items())
        return {'artwork_id':c['artwork_id'],'image_verified':ok,'image_status':response.status_code,'api_verified':api_ok,'api_status':api.status_code}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(public,records))
    errors.extend({'artwork_id':r['artwork_id'],'error':'Public image/API check failed'} for r in checks if not r['image_verified'] or not r['api_verified'])
    report={'at':core.now(),'new_artworks':len(records),'painters':len(slugs),'country_memberships':dict(collections.Counter(code for c in records for code in c['country_codes'])),
        'max_bytes':max(im['bytes'] for im in receipts.values()),'total_bytes':sum(im['bytes'] for im in receipts.values()),'databases':databases,'public_checks':checks,'errors':errors}
    core.save_new(a.run/'catalogue-public-verification.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='public_checks'},indent=2),flush=True)
    if errors:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['select','prepare','contact','apply','verify']);p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--limit',type=int,default=50)
    a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    with (a.run/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.phase in ('prepare','apply'):phase(a)
        else:globals()[a.phase](a)
