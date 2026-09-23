#!/usr/bin/env python3
"""Continue selected WikiArt coverage without repeating prior source objects."""
import argparse
import collections
import importlib.util
import json
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('coverage',ROOT/'ops/wikiart-artist-coverage.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
PRIOR=c.RUN
EARLIER=c.PREVIOUS
RUN=ROOT/'docs/research/wikiart-artist-followup-20260920'
c.RUN=c.m.RUN=RUN
c.m.BACKUP=Path.home()/'Library/Application Support/Artline/backups/wikiart-artist-followup-20260920'
c.m.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images/wikiart-artist-followup-20260920'
BaseFetcher=c.m.Fetcher


class CachedFetcher(BaseFetcher):
    def get(self,url,limit=5_000_000,image=False):
        key=c.m.core.sha(url.encode())
        for previous in (PRIOR,EARLIER):
            receipt=previous/'captures'/(key+'.json')
            source=(Path.home()/'Library/Application Support/Artline/source-images'/previous.name if image else previous/'captures')/(key+'.body')
            if not source.exists() or not receipt.exists():continue
            raw=source.read_bytes();record=json.loads(receipt.read_bytes())
            if c.m.core.sha(raw)!=record['sha256']:raise ValueError('Previous source checksum changed')
            target=(c.m.ORIGINALS if image else RUN/'captures')/(key+'.body')
            c.m.save_atomic(target,raw);c.m.save_atomic(RUN/'captures'/(key+'.json'),record)
            return raw,record
        return super().get(url,limit,image)


c.SharedFetcher=CachedFetcher


def select():
    inventory=json.loads((PRIOR/'artist-matches.json').read_bytes())
    sources={p['url']:p for p in inventory['unmatched_source_artists']}
    sources.update({p['wikiart']['url']:p['wikiart'] for p in inventory['matches']+inventory['ambiguous']})
    pairs={p['wikiart']['url']:p for p in inventory['matches']}
    for filename in ('extra-artist-matches.json','priority-group-matches.json','supplemental-artist-matches.json'):
        for pair in json.loads((PRIOR/filename).read_bytes())['matches']:
            pairs[pair['wikiart']['url']]=pair
    excluded=set()
    # Delivered image records contain the final reconciled artist identity.
    for previous in (EARLIER,PRIOR):
        for path in (previous/'images').glob('*.json'):
            im=json.loads(path.read_bytes());excluded.add(im['source_id'])
            if previous!=PRIOR:continue
            source_url=im['selection_receipt']['final_url'].replace('/ru/','/en/')
            if source_url in sources:pairs[source_url]={'artist':im['work']['artist'],'wikiart':sources[source_url]}
    with c.m.read_only() as db:
        rows=db.execute("""SELECT to_jsonb(a) record,
            EXISTS(SELECT 1 FROM artist_countries ac WHERE ac.artist_id=a.id AND ac.country_code IN ('RU','GR')) priority
            FROM artists a WHERE a.id=ANY(%s::uuid[]) AND a.status<>'archived'""",
            ([p['artist']['id'] for p in pairs.values() if not p['artist'].get('object_level_creator')],)).fetchall()
        artists={r['record']['id']:{**r['record'],'priority':r['priority']} for r in rows}
        chosen={};held=[]
        for pair in pairs.values():
            artist=pair['artist'];source=pair['wikiart'];slug=urlparse(source['url']).path.rsplit('/',1)[-1]
            if not artist.get('object_level_creator'):
                if artist['id'] not in artists:
                    held.append({'source_url':source['url'],'reason':'Prior candidate artist authority was not created; identity review preserved'});continue
                artist=artists[artist['id']]
            profile=PRIOR/'profiles'/(slug+'.json')
            if not profile.exists():continue
            p=json.loads(profile.read_bytes())
            eligible=sum(bool(c.dated(w.get('year'))) and w['_id'] not in excluded for w in p['featured'])
            if not eligible:continue
            artist={**artist,'selection_limit':3 if artist.get('priority') else 1}
            candidate={'artist':artist,'wikiart':source,'remaining_featured':eligible}
            if artist['id'] in chosen and chosen[artist['id']]['remaining_featured']>=eligible:continue
            chosen[artist['id']]=candidate
        ordered=sorted(chosen.values(),key=lambda p:(not p['artist'].get('priority'),p['artist']['display_name']))
        snapshot={'at':c.m.core.now(),'previous_source_objects_excluded':len(excluded),'pairs':ordered,'held':held,
            'selection':'One further featured work per reconciled artist, up to three for Russian/Greek/Byzantine priority; existing missing images first.'}
        audit=RUN/'artist-inventory.json'
        if not audit.exists():c.m.save_atomic(audit,snapshot)
        else:ordered=json.loads(audit.read_bytes())['pairs']
        for n,pair in enumerate(ordered,1):
            slug=urlparse(pair['wikiart']['url']).path.rsplit('/',1)[-1]
            for suffix in ('.json','.ru.json'):
                profile=PRIOR/'profiles'/(slug+suffix)
                if profile.exists():c.m.save_atomic(RUN/'profiles'/profile.name,profile.read_bytes())
            c.select_one(pair,db,excluded)
            if n%100==0:print('Artist selection progress',n,'of',len(ordered),flush=True)
    matches=c.m.discovered_matches()
    for match in matches:
        if match['wikiart']['source_id'] in excluded:raise ValueError('Repeated source object in follow-up')
    c.m.save_atomic(RUN/'discovered-v2.json',{'at':c.m.core.now(),'matches':matches,'artist_count':len(ordered),
        'new_artworks':sum(bool(x['work'].get('new_record')) for x in matches)})
    print('Follow-up selection complete',len(matches),'images for',len({x['work']['artist']['id'] for x in matches}),'artists/source groups',flush=True)


def deliver_local():
    """Use recoverable local receipts while external sign-in is unavailable."""
    count=0
    with c.m.psycopg.connect('postgres://localhost/artline',autocommit=True,row_factory=c.m.dict_row) as db:
        while not (RUN/'local-delivery-stop.json').exists():
            paths=[p for p in sorted((RUN/'images').glob('*.json')) if not (RUN/'delivery-local'/p.name).exists()]
            for path in paths:
                if (RUN/'local-delivery-stop.json').exists():break
                im=json.loads(path.read_bytes());aid=im['artwork_id']
                data=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
                if len(data)!=im['bytes'] or len(data)>100000 or c.m.core.sha(data)!=im['sha256']:raise ValueError('Local image checksum or size differs')
                backup=c.m.BACKUP/'local-first-preimages'/path.name
                if backup.exists():state=json.loads(backup.read_bytes())
                else:
                    state=c.target_before(db,im);c.m.save_atomic(backup,state)
                applied=RUN/'applied/local'/path.name
                if applied.exists():result=json.loads(applied.read_bytes())
                else:
                    actual=c.target_before(db,im)
                    if state['outcome']!='held' and actual['outcome']=='attach' and actual['record']['primary_media_id']==im['media_id']:
                        result={'outcome':'already_attached','created':state['outcome']=='create','after':actual['record'],
                            'before_attachment':state['record'],'recovered_receipt':True}
                    else:result=c.apply_image(db,im,state)
                    result.update(local_first_backup=str(backup),local_first_backup_sha256=c.m.core.sha(backup.read_bytes()))
                    c.m.save_atomic(applied,result)
                c.m.save_atomic(RUN/'delivery-local'/path.name,{'artwork_id':aid,'at':c.m.core.now(),'path':im['path'],'sha256':im['sha256'],
                    'targets':{'local':result},'cloud_upload':'pending renewed Artline authentication'})
                count+=1
                if count%25==0:print('Local artwork delivery',count,flush=True)
            if not paths and (RUN/'preparation-finished.json').exists():break
            time.sleep(3)
    c.m.save_atomic(RUN/'delivery-local-finished.json',{'at':c.m.core.now(),'receipts':len(list((RUN/'delivery-local').glob('*.json')))})


def sync_local_selection():
    c.sync_selection(targets=('local',),receipt_directory='delivery-local',finished_marker='delivery-local-finished.json',
        output_marker='personal-local-selection-finished.json')


def verify_local():
    receipts=[json.loads(p.read_bytes()) for p in sorted((RUN/'delivery-local').glob('*.json'))]
    images={r['artwork_id']:json.loads((RUN/'images'/(r['artwork_id']+'.json')).read_bytes()) for r in receipts}
    attached=[r for r in receipts if r['targets']['local']['outcome'] in ('attached','already_attached')]
    errors=[]
    with c.m.read_only() as db:
        ids=[r['targets']['local']['after']['id'] for r in attached]
        rows=db.execute('SELECT to_jsonb(a) artwork,to_jsonb(m) media FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.id=ANY(%s::uuid[])',(ids,)).fetchall()
        actual={r['artwork']['id']:r for r in rows}
        for receipt in attached:
            im=images[receipt['artwork_id']];result=receipt['targets']['local'];row=actual.get(result['after']['id'])
            if c.m.core.sha(Path(result['local_first_backup']).read_bytes())!=result['local_first_backup_sha256']:
                errors.append({'artwork_id':im['artwork_id'],'error':'Recovery preimage checksum differs'})
            if not row or row['artwork']!=result['after']:
                errors.append({'artwork_id':im['artwork_id'],'error':'Artwork differs from attachment receipt'});continue
            media=row['media']
            if media['storage_path']!=im['path'] or media['checksum_sha256']!=im['sha256'] or media['byte_size']!=im['bytes'] or media['rights_status']!=im['rights_status'] or media['source_page_url']!=im['page']:
                errors.append({'artwork_id':im['artwork_id'],'error':'Media metadata differs'})
            if im['rights_status'] in ('restricted','unknown') and media['verified_at'] is not None:
                errors.append({'artwork_id':im['artwork_id'],'error':'Unspecified/restricted source label received invented verification'})
        new_ids=[r['targets']['local']['after']['id'] for r in attached if r['targets']['local'].get('created')]
        rows=db.execute("""SELECT a.id::text FROM artworks a WHERE a.id=ANY(%s::uuid[])
            AND a.status='review' AND a.research_candidate AND a.current_institution_id IS NULL
            AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions h WHERE h.artwork_id=a.id)
            AND EXISTS(SELECT 1 FROM curated_collection_items i JOIN curated_collections cc ON cc.id=i.collection_id
                WHERE i.artwork_id=a.id AND cc.institution_id IS NULL AND cc.curator_kind='owner' AND cc.status<>'archived')""",(new_ids,)).fetchall()
        if len(rows)!=len(new_ids):errors.append({'error':'New artwork review, holding or personal selection differs','expected':len(new_ids),'actual':len(rows)})
        sizes=db.execute("SELECT count(*) AS images,max(byte_size) AS maximum_bytes,count(*) FILTER(WHERE byte_size>100000) AS oversize,count(*) FILTER(WHERE byte_size IS NULL) AS unknown_size FROM media_assets WHERE mime_type LIKE 'image/%%' OR mime_type IS NULL").fetchone()
        if sizes['oversize'] or sizes['unknown_size']:errors.append({'error':'Whole catalogue image size audit failed'})
    files=[]
    for im in images.values():
        raw=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
        good=len(raw)==im['bytes']<=100000 and c.m.core.sha(raw)==im['sha256']
        files.append({'artwork_id':im['artwork_id'],'verified':good})
        if not good:errors.append({'artwork_id':im['artwork_id'],'error':'Local file differs'})
    result={'at':c.m.core.now(),'prepared':len(images),'attached':len(attached),'created_artworks':len(new_ids),
        'artists_source_groups':len({im['artist_slug'] for im in images.values()}),'bytes':sum(im['bytes'] for im in images.values()),
        'maximum_bytes':max((im['bytes'] for im in images.values()),default=0),'rights_labels':dict(collections.Counter(im['rights_status'] for im in images.values())),
        'personal_collection_items':len(rows),'whole_catalogue_sizes':sizes,'files':files,'errors':errors}
    output=RUN/('verification-local-'+str(len(receipts))+'-'+str(int(time.time()))+'.json');c.m.save_atomic(output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False),flush=True)
    print('Local verification receipt',output,flush=True)
    if errors:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['select','prepare','deliver_ready','deliver_local','sync_selection','sync_local_selection','verify','verify_local']);args=parser.parse_args()
    if args.phase in ('select','deliver_local','sync_local_selection','verify_local'):globals()[args.phase]()
    else:getattr(c,args.phase)()
