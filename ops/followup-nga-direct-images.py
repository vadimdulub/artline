#!/usr/bin/env python3
"""Attach selected NGA CC0 resources with exact object, artist and image identities."""
import argparse, collections, concurrent.futures, csv, fcntl, importlib.util, io, json, re, time
from pathlib import Path
from types import SimpleNamespace
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('nga_reference', ROOT/'ops/overnight-nga-commons.py')
nga = importlib.util.module_from_spec(spec); spec.loader.exec_module(nga)
core = nga.core
PROVIDER = 'followup-nga'
POLICY = 'https://www.nga.gov/terms-and-notices'
CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
core.PROVIDERS[PROVIDER] = 'National Gallery of Art'
core.HOSTS.add('www.nga.gov')
core.VERSION = 'nga-exact-open-access-primary-v1'

def verify(im):
    raw = im['raw']; obj = raw['nga_object']; image = raw['published_image']
    nga.object_match(im, obj)
    if image.get('openaccess') != '1' or image.get('viewtype') != 'primary':
        raise ValueError('Exact image is not an open-access primary resource')
    if image.get('depictstmsobjectid') != im['external_id']:
        raise ValueError('Image depicts another museum object')
    if not re.fullmatch(r'[a-f0-9-]{36}', image.get('uuid', '')):
        raise ValueError('Image resource identifier is invalid')
    base = 'https://api.nga.gov/iiif/' + image['uuid']
    original=base+'/full/!1000,1000/0/default.jpg'
    if image.get('iiifurl') != base:raise ValueError('Image resource URL differs from the museum statement')
    if im['source_image_url']!=original:
        redirect=raw.get('museum_rendition_redirect',{})
        allowed=re.fullmatch(re.escape(base)+r'__\d+/full/!1000,1000/0/default\.jpg',im['source_image_url'])
        if not allowed or redirect.get('status')!=303 or redirect.get('requested_url')!=original or redirect.get('location')!=im['source_image_url'] or not redirect.get('retrieved_at'):
            raise ValueError('Unverified museum rendering redirect or changed image identity')
    relations = raw['artist_relations']
    if len(relations) != 1 or relations[0].get('role') not in ('artist','painter','engraver','etcher') or relations[0].get('prefix') or relations[0].get('suffix'):
        raise ValueError('Current museum attribution needs review')
    if relations[0].get('roletype') != 'artist' or relations[0].get('objectid') != im['external_id']:
        raise ValueError('Creator relation does not describe this object')
    if im['artist_authorities'] != [relations[0]['constituentid']]:
        raise ValueError('Catalogue artist is not the exact museum creator')
    policy = raw['image_policy']
    if policy.get('url') != POLICY or not policy.get('open_access_images_cc0') or not policy.get('sha256'):
        raise ValueError('Independent image CC0 policy evidence is absent')
    if im['policy_url'] != CC0 or im['rights_status'] != 'cc0':
        raise ValueError('Approved image licence differs')

def select(run, reference, only_ids=None):
    path = run/'candidates.json'
    if path.exists(): return json.loads(path.read_text())['candidates']
    fetch = core.Fetcher(run/'metadata')
    revision = fetch.metadata('https://api.github.com/repos/NationalGalleryOfArt/opendata/commits/main')['sha']
    captures = {}; data = {}
    for name, filename in [('objects','objects.csv'),('objects_constituents','objects_constituents.csv'),('nga-published-images','published_images.csv')]:
        receipt = json.loads((reference/(name+'.receipt.json')).read_text())
        payload = (reference/(name+'.csv')).read_bytes()
        if core.sha(payload) != receipt['sha256']: raise ValueError('Official source capture checksum differs')
        if '/'+revision+'/' not in receipt['url']: raise ValueError('Official CSV revision changed; refresh captures before selection')
        captures[name] = dict(receipt, revision_rechecked_at=core.now(), current_revision=revision)
        data[name] = list(csv.DictReader(io.StringIO(payload.decode('utf-8-sig'))))
    policy_bytes, headers = fetch.get(POLICY, 2_000_000)
    text = nga.plain(policy_bytes.decode())
    if 'Open Access Policy for Images' not in text or 'commercial or non-commercial, under Creative Commons Zero (CC0)' not in text:
        raise ValueError('Current museum image policy requires review')
    policy = {'url':POLICY, 'retrieved_at':core.now(), 'sha256':core.sha(policy_bytes), 'open_access_images_cc0':True,
              'basis':'The museum explicitly releases its open-access digital images under CC0. The individual published-image row must independently set openaccess=1.', 'headers':headers}
    core.save_new(run/'image-policy-evidence.json', policy)
    objects = {o['objectid']:o for o in data['objects']}; images = collections.defaultdict(list); relations = collections.defaultdict(list)
    for im in data['nga-published-images']:
        if im['viewtype']=='primary' and im['openaccess']=='1': images[im['depictstmsobjectid']].append(im)
    for rel in data['objects_constituents']:
        if rel['roletype']=='artist': relations[rel['objectid']].append(rel)
    blocked = {r['artwork_id'] for r in json.loads((run.parent/'withdrawn-images.json').read_text())['records']}
    with nga.ro('postgres://localhost/artline') as db:
        scope = ' AND a.id=ANY(%s::uuid[])' if only_ids is not None else ''
        rows = db.execute(nga.QUERY + " AND a.primary_media_id IS NULL"+scope+" ORDER BY popular DESC,(a.work_type='painting') DESC,a.id", (only_ids,) if only_ids is not None else ()).fetchall()
        creator_rows = db.execute("""SELECT aa.artwork_id::text,e.external_id FROM artwork_artists aa
          LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='nga-constituent'
          WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,e.external_id""", ([r['artwork_id'] for r in rows],)).fetchall()
    authorities = collections.defaultdict(list)
    for row in creator_rows: authorities[row['artwork_id']].append(row['external_id'])
    selected = []; held = []
    for c in rows:
        try:
            if c['artwork_id'] in blocked: raise ValueError('Inherited source identity or rights hold')
            oid = c['external_id']; choices = images[oid]
            if len(choices)>1: choices=[im for im in choices if im['sequence']=='0']
            if len(choices)!=1: raise ValueError('No unique source-designated open primary image')
            if not c['artist']: raise ValueError('Creator is not linked')
            o=objects.get(oid,{}); nga.object_match(c,o); image=choices[0]
            credit=c['artist']+'; Courtesy National Gallery of Art, Washington'+('; '+o['creditline'] if o.get('creditline') else '')
            im=dict(c,provider=PROVIDER,page='https://purl.org/nga/collection/artobject/'+oid,
                source_record_url='https://purl.org/nga/collection/artobject/'+oid,source_name='National Gallery of Art',source_object_id=oid,
                source_image_url=image['iiifurl']+'/full/!1000,1000/0/default.jpg',policy_url=CC0,rights_status='cc0',license_label='CC0 1.0',
                artist_authorities=authorities[c['artwork_id']],raw={'nga_object':{k:o.get(k) for k in ('objectid','accessioned','accessionnum','title','displaydate','beginyear','endyear','medium','attribution','creditline','classification','isvirtual')},'published_image':image,'artist_relations':relations[oid],'metadata_captures':captures,'image_policy':policy},
                creator_credit=credit,attribution_text=f"{c['artist']}. {c['title']}. {credit}. CC0 ({CC0}). Full-frame proportional resize and JPEG compression.",
                checked_at=core.now(),rights_verified_at=core.now(),creation_date=c['date_display'],target_ids={'local':c['artwork_id']})
            verify(im); selected.append(im)
        except ValueError as exc: held.append({'artwork_id':c['artwork_id'],'reason':str(exc)})
    valid=[]
    with nga.ro(core.cloud_dsn()) as db:
        remote=db.execute(nga.QUERY+' AND e.external_id=ANY(%s)',([im['external_id'] for im in selected],)).fetchall(); by_id=collections.defaultdict(list)
        for row in remote: by_id[row['external_id']].append(row)
        for im in selected:
            hits=by_id[im['external_id']]
            if len(hits)!=1 or hits[0]['primary_media_id'] or any(hits[0][k]!=im[k] for k in ('title','artist','accession_number','creation_year_start','creation_year_end','work_type')):
                held.append({'artwork_id':im['artwork_id'],'reason':'Production object facts or image state differ'});continue
            im['target_ids']['cloud']=hits[0]['artwork_id'];valid.append(im)
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with nga.ro(dsn) as db:
            before=db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',([im['target_ids'][target] for im in valid],)).fetchall()
            backup=Path.home()/'Library/Application Support/Artline/backups'/run.parent.name/run.name/(target+'-before.json');core.save_new(backup,before)
    for im in valid: core.save_new(run/'selected'/PROVIDER/(im['artwork_id']+'.json'),im)
    core.save_new(path,{'created_at':core.now(),'candidates':valid});core.save_new(run/'held.json',held)
    core.save_new(run/'selection-summary.json',{'at':core.now(),'selected':len(valid),'popular':sum(im['popular'] for im in valid),'types':dict(collections.Counter(im['work_type'] for im in valid)),'held':dict(collections.Counter(im['reason'] for im in held))})
    print((run/'selection-summary.json').read_text(),flush=True);return valid

original_attach=core.attach
def attach(db, im, target):
    verify(im)
    with db.transaction():
        authorities=db.execute("""SELECT e.external_id FROM artwork_artists aa LEFT JOIN external_identifiers e
          ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='nga-constituent'
          WHERE aa.artwork_id=%s ORDER BY e.external_id""",(im['target_ids'][target],)).fetchall()
        if [r['external_id'] for r in authorities]!=im['artist_authorities']:raise ValueError('Target creator authority changed')
        return original_attach(db,im,target)
core.attach=attach

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--select-only',action='store_true');p.add_argument('--metadata-plan',type=Path);p.add_argument('--limit',type=int,default=10000);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True)
    lock=(a.run/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert (a.run.parent/'backups.json').exists()
    only_ids=[r['artwork_id'] for r in json.loads(a.metadata_plan.read_text())['records']] if a.metadata_plan else None
    rows=select(a.run,a.reference,only_ids)
    if a.select_only:return
    done={k for k,v in core.latest_events(a.run).items() if v['outcome'] in ('prepared','complete','failed')}
    pending=[c for c in rows if c['artwork_id'] not in done][:a.limit]
    for start in range(0,len(pending),60):
        if time.time()>=a.deadline:break
        group=pending[start:start+60]
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs=[pool.submit(core.worker,PROVIDER,group[i::3],SimpleNamespace(run=a.run,prepare_only=True),None) for i in range(3) if group[i::3]]
            for job in jobs:job.result()
        print(core.now(),'NGA direct images',dict(core.COUNTS),flush=True)
if __name__=='__main__':main()
