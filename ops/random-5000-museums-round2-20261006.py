#!/usr/bin/env python3
"""Second disjoint random sample and 80% editorial-confidence lead resolution."""
import argparse,collections,gzip,hashlib,importlib.util,json,re,secrets,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('first_task','ops/random-5000-museum-research-20261006.py');r=m.r;d=m.d
OLD=ROOT/'docs/research/random-5000-museums-20261006'
RUN=ROOT/'docs/research/random-5000-museums-round2-20261006'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/random-5000-museums-round2-20261006'
m.RUN=RUN;m.BACKUP=BACKUP;r.RUN=RUN;r.BACKUP=BACKUP;r.PORT=55483;d.ACTOR='random-5000-museums-round2-20261006'
orig_connect=r.connect
def connect(target='production',readonly=True):
    assert target=='production','Production-only task; local catalogue is read-only and outside this task'
    return orig_connect(target,readonly=readonly)
r.connect=connect

def sample():
    assert not(RUN/'sample.json').exists(),'Preserve frozen sample'
    previous=r.load(OLD/'sample.json')['artwork_ids'];priorledger=r.load(OLD/'results-5000.json.gz');followup=[x['artwork_id']for x in priorledger if x['outcome']=='collection_lead_requires_verification'];assert len(followup)==1617
    seed=secrets.token_hex(32);query="""SELECT a.id::text FROM artworks a WHERE a.status<>'archived' AND a.current_institution_id IS NULL AND NOT(a.id=ANY(%s::uuid[])) AND NOT EXISTS(SELECT 1 FROM artwork_location_assertions h WHERE h.artwork_id=a.id AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL) ORDER BY a.id"""
    records={};citations={};supplied=[]
    with r.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');plan=db.execute('EXPLAIN (FORMAT JSON) '+query,(previous,)).fetchone();frame=[x['id']for x in db.execute(query,(previous,))]
        assert len(frame)>=5000;selected=sorted(frame,key=lambda aid:(hashlib.sha256((seed+'/'+aid).encode()).digest(),aid))[:5000];ids=selected+followup;assert len(set(ids))==6617 and not(set(selected)&set(previous))
        for offset in range(0,len(ids),500):
            part=ids[offset:offset+500];records.update(d.snapshots(db,part))
            for row in db.execute("SELECT entity_id::text,array_agg(DISTINCT source_url) urls FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) GROUP BY entity_id",(part,)):citations[row['entity_id']]=row['urls']
            supplied.extend(db.execute("SELECT l.artwork_id::text,r.raw_json FROM research_artwork_links l JOIN research_records r ON(r.snapshot_id,r.source_key,r.record_kind,r.source_record_id)=(l.snapshot_id,l.source_key,l.record_kind,l.research_record_id) WHERE l.artwork_id=ANY(%s::uuid[]) AND r.raw_json #> '{csv,cells}' IS NOT NULL",(part,)).fetchall())
            print('Frozen task records',min(offset+500,len(ids)),'/',len(ids),flush=True)
        artistids=list({c['artist_id']for x in records.values()for c in x['creators']});artists={x['v']['id']:x['v']for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(artistids,))};identifiers=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[])",(artistids,)).fetchall();institutions=[x['v']for x in db.execute("SELECT to_jsonb(i) v FROM institutions i WHERE status<>'archived'")]
    r.save_gz(RUN/'sampling-frame.json.gz',frame);r.save_gz(RUN/'baseline.json.gz',records);r.save_gz(RUN/'citation-urls.json.gz',citations);r.save_gz(RUN/'artists.json.gz',{'artists':artists,'identifiers':identifiers});r.save_gz(RUN/'institutions.json.gz',institutions);r.save_gz(RUN/'supplied-research-links.json.gz',supplied)
    suppliedby=collections.defaultdict(list)
    for x in supplied:suppliedby[x['artwork_id']].append(x['raw_json']['csv']['cells'])
    rows=[{**x,'artists':x['creator_keys'],'supplied':suppliedby.get(aid,[])}for aid,x in records.items()];r.save_gz(RUN/'primary-input-rows.json.gz',rows);r.save_gz(RUN/'missing-locations.json.gz',rows)
    data={'at':r.now(),'target':'production','selected':5000,'eligible_population':len(frame),'excluded_previous_sample':len(previous),'artwork_ids':selected,'followup_lead_ids':followup,'followup_leads':len(followup),'total_task_records':len(records),'seed':seed,'algorithm':'Smallest 5,000 SHA-256(seed + slash + artwork UUID) values over the complete eligible production UUID frame; unweighted selection without replacement, excluding the entire first sample.','eligibility':'Non-archived, no current institution, no active accepted holding assertion, not in the previous 5,000 sample.','sampling_frame_sha256':r.sha((RUN/'sampling-frame.json.gz').read_bytes()),'baseline_sha256':r.sha((RUN/'baseline.json.gz').read_bytes()),'confidence_policy':{'minimum_editorial_confidence':0.8,'user_authorized':True,'calibrated_probability':False,'instruction':'If you are sure at 80%, this is okay; the assistant should verify and decide.'},'local_database_writes':0}
    r.save(RUN/'sample.json',data);r.save(RUN/'sampling-query-plan.json',plan);print(json.dumps({k:v for k,v in data.items()if k not in ['artwork_ids','followup_lead_ids']},ensure_ascii=False),flush=True)

def cached():
    m.cached('-supplement')

def wikidata_cache():
    records=r.load(RUN/'baseline.json.gz');wanted={e['external_id']for x in records.values()for e in x['identifiers']if e['scheme']=='wikidata'};entities={};previous=r.load(OLD/'wikidata-entities.json.gz')
    for q in wanted:
        if q in previous:entities[q]=previous[q]
    base=ROOT/'docs/research/artwork-locations-20261004'
    for path in sorted((base/'wikidata-batches').glob('*.json')):
        data=r.load(path);receipt=data.get('receipt')or data.get('source_receipt');found=data.get('entities',{})
        for q in wanted&found.keys():
            if q not in entities:entities[q]={'entity':found[q],'receipt':receipt,'evidence_path':str(path.relative_to(ROOT))}
    missing=sorted(wanted-entities.keys());r.save_gz(RUN/'wikidata-entities.json.gz',entities);r.save_gz(RUN/'cached-institution-authorities.json.gz',r.load(OLD/'cached-institution-authorities.json.gz'));r.save(RUN/'wikidata-cache-coverage.json',{'at':r.now(),'requested':len(wanted),'captured':len(entities),'missing':missing})
    print('Wikidata exact artwork coverage',len(entities),'/',len(wanted),'missing',len(missing),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['sample','cached','wikidata_cache']);args=ap.parse_args();globals()[args.phase]()
