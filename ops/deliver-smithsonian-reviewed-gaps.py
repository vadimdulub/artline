#!/usr/bin/env python3
"""Deliver eight individually reviewed Smithsonian creator-name variants."""
import argparse
import concurrent.futures
import importlib.util
import json
import re
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('saam',ROOT/'ops/overnight-saam-images.py')
saam=importlib.util.module_from_spec(spec);spec.loader.exec_module(saam)
core=saam.core
# Reviewed name reorderings, initials, and De Camp spacing. Both museum life
# dates, native object ID, accession, title and artwork date must independently agree.
VARIANTS={
 'gerald-ira-d-cassidy-nga-33281':('Ira D. Gerald Cassidy',1879,1934),
 'william-mcgregor-paxton-nga-33868':('William M. Paxton',1869,1941),
 'dwight-william-tryon-nga-42495':('Dwight W. Tryon',1849,1925),
 'morgan-c-mcilhenney-nga-33773':('C. Morgan McIlhenney',1858,1904),
 'joseph-rodefer-decamp-nga-38653':('Joseph De Camp',1858,1923),
}

def select(run):
    inventory=json.loads((run/'catalogue-gaps.json').read_text())
    artists={r['slug']:r['record'] for r in inventory['artists']}
    selected=[]
    for original in inventory['records']:
        if len(original['artist_slugs'])!=1 or original['artist_slugs'][0] not in VARIANTS:continue
        c=dict(original);slug=c['artist_slugs'][0];name,birth,death=VARIANTS[slug]
        artist=artists[slug]
        if (artist['birth_year'],artist['death_year'])!=(birth,death):raise ValueError('Catalogue creator life dates differ')
        captured=json.loads((run/'objects'/(c['external_id']+'.json')).read_text());o=captured['object']
        receipt=captured['metadata_capture'];shard=run/'metadata'/receipt['url'].rsplit('/',1)[-1]
        if core.sha(shard.read_bytes())!=receipt['sha256']:raise ValueError('Source capture changed')
        source_names=saam.fields(o['content']['freetext'],'name','Artist')
        if len(source_names)!=1 or source_names[0].split(', born ')[0]!=name:raise ValueError('Reviewed creator name differs')
        if [int(y) for y in re.findall(r'\b\d{4}\b',source_names[0])]!=[birth,death]:raise ValueError('Source creator life dates differ')
        c['aliases']=c['aliases']+[name]
        im,url,facts=saam.source_match(c,o)
        c['identity_review']={'original_artist':artist['display_name'],'reviewed_source_alias':name,
            'birth_year':birth,'death_year':death,'source_object_id':c['external_id'],
            'reason':'Reviewed name variant; exact matching birth/death, object ID, accession, title and creation date. No artist metadata or alias-table changes.'}
        ft=o['content']['freetext'];page=o['content']['descriptiveNonRepeating']['record_link']
        credit=c['artist']+'; '+('; '.join(saam.fields(ft,'creditLine')) or 'Smithsonian American Art Museum')
        checked=core.now()
        c.update(provider='night-saam',scheme='saam-object',target_ids={'local':c['artwork_id']},
            source_image_url=url,page=page,raw=captured,scope_evidence=facts,
            policy_url=saam.CC0,rights_status='cc0',license_label='CC0 1.0',checked_at=checked,
            creator_credit=credit,attribution_text=c['artist']+'. '+c['title']+'. '+credit+'. CC0 1.0 ('+saam.CC0+'). Full-frame proportional resize and JPEG compression.')
        selected.append(c)
    dsn=core.cloud_dsn()
    keys=('title','creation_year_start','creation_year_end','date_precision','artist_slugs','roles','status','work_type','accession_number')
    backup_root=Path('/Users/vadimdulub/Library/Application Support/Artline/backups')/run.parent.name/'smithsonian'
    manifests={}
    for target,d in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with saam.ro(d) as db:
            rows=db.execute(saam.QUERY+' AND e.external_id=ANY(%s)',([c['external_id'] for c in selected],)).fetchall()
            index={r['external_id']:r for r in rows}
            if len(rows)!=len(selected):raise ValueError('Target selection missing or duplicated')
            institutions=db.execute("SELECT id::text FROM institutions WHERE slug='smithsonian-american-art-museum' OR website_url='https://americanart.si.edu/'").fetchall()
            places=db.execute("SELECT id::text FROM places WHERE name='Washington, DC' AND country_code='US'").fetchall()
            if len(institutions)!=1 or len(places)!=1:raise ValueError('Existing museum identity must be unambiguous')
            for c in selected:
                r=index[c['external_id']]
                if any(r[k]!=c[k] for k in keys) or r['primary_media_id']:raise ValueError('Target facts or media changed')
                c['target_ids'][target]=r['artwork_id']
                c.setdefault('institution_ids',{})[target]=institutions[0]['id']
                c.setdefault('place_ids',{})[target]=places[0]['id']
            ids=[c['target_ids'][target] for c in selected]
            before=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
            assertions=db.execute('SELECT to_jsonb(l) assertion FROM artwork_location_assertions l WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
            path=backup_root/(target+'-before-images.json')
            core.save_new(path,{'artworks':before,'location_assertions':assertions})
            manifests[target]={'path':str(path),'sha256':core.sha(path.read_bytes())}
            byid={str(r['artwork']['id']):r['artwork'] for r in before}
            for c in selected:c.setdefault('before',{})[target]=byid[c['target_ids'][target]]
    core.save_new(run/'backups.json',manifests)
    core.save_new(run/'candidates.json',{'candidates':selected})
    for c in selected:core.save_new(run/'selected/night-saam'/(c['artwork_id']+'.json'),c)
    print('Selected',len(selected),'CC0 paintings across',len(VARIANTS),'painters',flush=True)

original_attach=core.attach
def attach(db,im,target):
    with db.transaction():
        record=db.execute('SELECT to_jsonb(a) record FROM artworks a WHERE id=%s FOR UPDATE',(im['target_ids'][target],)).fetchone()['record']
        excluded={'primary_media_id','updated_at','updated_by','revision'}
        if {k:v for k,v in record.items() if k not in excluded}!={k:v for k,v in im['before'][target].items() if k not in excluded}:raise ValueError('Catalogue metadata changed since review')
        return original_attach(db,im,target)
core.attach=attach

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['select','prepare','apply']);p.add_argument('--run',required=True,type=Path);a=p.parse_args()
    if a.phase=='select':select(a.run);return
    for entry in json.loads((a.run/'backups.json').read_text()).values():
        if core.sha(Path(entry['path']).read_bytes())!=entry['sha256']:raise ValueError('Recovery checksum differs')
    rows=json.loads((a.run/'candidates.json').read_text())['candidates']
    latest=core.latest_events(a.run)
    if a.phase=='apply':
        reviews={r['artwork_id']:r['sha256'] for r in json.loads((a.run/'reviewed-images.json').read_text())['images']}
        rows=[r for r in rows if r['artwork_id'] in reviews and latest.get(r['artwork_id'],{}).get('outcome')!='complete']
        for c in rows:
            im=json.loads((a.run/'images/night-saam'/(c['artwork_id']+'.json')).read_text())
            if im['sha256']!=reviews[c['artwork_id']]:raise ValueError('Reviewed image checksum differs')
            saam.source_match(im,im['raw']['object'])
    else:rows=[r for r in rows if latest.get(r['artwork_id'],{}).get('outcome') not in ('prepared','complete')]
    dsn=core.cloud_dsn() if a.phase=='apply' else None
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs=[pool.submit(core.worker,'night-saam',rows[i::3],SimpleNamespace(run=a.run,prepare_only=a.phase=='prepare',upload_prepared_only=a.phase=='apply'),dsn) for i in range(3) if rows[i::3]]
        for job in jobs:job.result()
    print(json.dumps(core.latest_events(a.run),indent=2),flush=True)
if __name__=='__main__':main()
