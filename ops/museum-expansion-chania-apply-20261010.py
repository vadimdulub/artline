"""Chania delivery using one canonical external ID per physical artwork/source.
All component/pair source IDs remain in source facts, metadata citations and image evidence.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-chania-delivery-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c,m,RUN=r.c,r.m,r.RUN
identity=c.module('identity','museum-expansion-chania-identity-20261010.py')
ts=c.module('ts','museum-expansion-ferens-timestamps-20261009.py')
KEY=r.KEY;SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY
PLAN=RUN/(KEY+'-plan-001.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz'
BUCKET='artline-508319-images'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def insert(db,table,row):
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder() for _ in row)),list(row.values()))
def audit(db,kind,aid,before,after,action):
    insert(db,'audit_log',dict(actor_user_id=m.ACTOR,action=action,entity_type=kind,entity_id=aid,request_id=KEY,before_json=Jsonb(before) if before is not None else None,after_json=Jsonb(after)))
def current_art(db,aid):return db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row']

def records():
    review=m.load(REVIEW)
    for pin in review['dependencies']:c.checked(pin)
    records,holdings=r.build();assert review['records']==records and review['holdings']==holdings
    return records,holdings

def metadata(v):
    f=v['facts']
    return dict(id=v['artwork_id'],slug=v['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],
        work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions_text'],description_md=f['description_md'],accession_number=f['inventory'],status='review',research_candidate=True,
        unlinked_creator_label=f['creator_label'],object_form=None,created_by=m.ACTOR,updated_by=m.ACTOR)

def identifier_values(v):
    # The schema permits one identifier per source scheme and physical artwork.
    # Component and pair sequences stay intact in facts and complete citations.
    f=v['facts'];assert f['source_ids'] and len(f['source_ids'])==len(f['source_urls'])
    return [(f['source_ids'][0],f['source_urls'][0])]

def evidence(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,review_reference=c.ref(REVIEW),policy='Literal museum object evidence and physical/version comparison. Existing titles, dates, artist links, images and publication state are preserved; holding is not current display.'),ensure_ascii=False)
def holding_note(v,digest):return v['identity_basis']+' '+v['limitation']+' Plan SHA-256 '+digest
def image_note(im,digest):return json.dumps(dict(plan_sha256=digest,number=im['number'],source_id=im['source_id'],identity_basis=im['identity_basis'],confidence=im['image_identity_confidence_editorial'],source_image_url=im['verified_https_source_image_url'],view_label=im['view_label'],policy=im['user_approved_source_policy']),ensure_ascii=False)

def image_records(before):
    arts={x['id']:x for x in before['artworks']};nextsort={};primary={aid:a['primary_media_id'] for aid,a in arts.items()};out=[]
    for link in before['media']:nextsort[link['artwork_id']]=max(nextsort.get(link['artwork_id'],0),link['sort_order']+1)
    for src in m.load(REVIEW)['images']:
        im=dict(src);aid=im['artwork_id'];mid=m.uid(KEY+'/image/'+aid+'/'+im['sha256']);im['media_id']=mid
        im['storage_path']='/assets/artworks/imported/museum-expansion-chania-20261010/'+aid+'-'+str(im['number']).zfill(3)+'-'+im['sha256'][:16]+'.jpg'
        im['sort_order']=nextsort.get(aid,0);nextsort[aid]=im['sort_order']+1
        im['set_primary']=not primary.get(aid)
        if im['set_primary']:primary[aid]=mid
        out.append(im)
    assert len(out)==188 and sum(x['set_primary'] for x in out)==183 and sum(not x['set_primary'] for x in out)==5
    return out

def media_row(im):
    return dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=im['source_url'],provider_name=im['image_source'],mime_type=im['mime_type'],width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],
        alt_text=im['source_title']+' — '+im['view_label'],rights_status='restricted',license_label=im['rights_label'],license_url=im['rights_url'],creator_credit=im['credit'],attribution_text=im['credit']+' '+im['changes'],retrieved_at=im['image_retrieved_at'],verified_at=None,verified_by=None)

def global_identity_unchanged(db):
    observed=m.load(RUN/'production-identity-001.json.gz');state=observed['state'];ids=state['artwork_ids']
    current=db.execute('SELECT '+identity.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,)).fetchall();assert current==state['artworks'],'Comparison artwork metadata changed'
    links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id,aa.attribution_role',(ids,)).fetchall();assert links==state['creator_links']
    cites=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,))];assert cites==m.load(RUN/'production-identity-citations-001.json.gz')['citations']
    titles=observed['params']['titles'];current_ids={v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE normalized_title=ANY(%s)',(titles,))};assert current_ids<=set(ids),'Unreviewed exact-title candidate appeared'
    accession_ids={v['id'] for v in db.execute("SELECT id::text FROM artworks WHERE regexp_replace(upper(coalesce(accession_number,'')),'[^A-ZΑ-Ω0-9]','','g')=ANY(%s)",(observed['params']['accession_keys'],))};assert accession_ids<=set(ids),'Unreviewed accession candidate appeared'
    review=m.load(REVIEW);units=review['records']+review['holdings'];urls=sorted({u for v in units for u in v['facts']['source_urls']+v['facts']['native_urls']});sids=sorted({x for v in units for x in v['facts']['source_ids']})
    urls=sorted(set(urls)|{u+'/' for u in urls if u.startswith('https://amch.gr/') and not u.endswith('/')})
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='searchculture-edm' AND external_id=ANY(%s))) LIMIT 1",(urls,sids)).fetchone()
    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND (source_url=ANY(%s) OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%')) LIMIT 1",(urls,sids)).fetchone()

def preflight(db,p):
    assert db.execute('SELECT current_database() db').fetchone()['db']=='artline'
    assert c.snapshot(db,p['scoped_ids'])==p['before'] and c.counts(db)==p['before_counts']=={c.IID:dict(linked=18,eligible=0)}
    assert c.s.prior_state(db,p['prior_ids'])==p['prior_state'];global_identity_unchanged(db)
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
    assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)',([v['artwork_id'] for v in p['records']],[v['slug'] for v in p['records']])).fetchone()
    assert not db.execute('SELECT 1 FROM media_assets WHERE id=ANY(%s::uuid[]) OR storage_path=ANY(%s) OR checksum_sha256=ANY(%s) LIMIT 1',([x['media_id'] for x in p['images']],[x['storage_path'] for x in p['images']],[x['sha256'] for x in p['images']])).fetchone()
    for im in p['images']:
        assert im['verified_https_source_image_url'].startswith('https://') and im['source_url'].startswith('https://') and im['bytes']<=100000
    originals=sorted({im['original_reference']['sha256'] for im in p['images']});assert not db.execute('SELECT1 FROM media_assets WHERE checksum_sha256=ANY(%s) LIMIT1'.replace('SELECT1','SELECT 1').replace('LIMIT1','LIMIT 1'),(originals,)).fetchone()
    assert len(p['records'])==174 and len(p['holdings'])==0 and len(p['images'])==188
    assert not set(p['prior_ids'])&{v['artwork_id'] for v in p['holdings']}

def prepare():
    assert not PLAN.exists();records0,holdings=records();scope=m.load(RUN/'production-initial-scope-001.json.gz');focus=m.load(RUN/'focused-comparators-001.json.gz');base=m.load(RUN/'baseline-verification-001.json')
    ids=sorted(set(scope['scoped_ids'])|set(focus['ids']));prior_ids=base['prior_production_ids']
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');assert c.snapshot(db,scope['scoped_ids'])==scope['snapshot'];assert c.snapshot(db,focus['ids'])==focus['snapshot']
        before=c.snapshot(db,ids);p=dict(at=m.now(),records=records0,holdings=holdings,images=image_records(before),scoped_ids=ids,before=before,before_counts=c.counts(db),prior_ids=prior_ids,prior_state=c.s.prior_state(db,prior_ids),
            expected_counts=dict(linked=192,eligible=117),baseline_reference=c.ref(c.CP),review_reference=c.ref(REVIEW),policy='174selected review additions and188authentic source images; one physical unit per reconciled accession grouping. Preserve all existing metadata/primaries/statuses, actual rights labels and unknown dates. Real local catalogue read-only.')
        assert p['prior_state']==base['prior_state'];preflight(db,p)
    backup=m.BACKUP/(KEY+'-before-001.json.gz');m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=prior_ids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=sha(backup))
    paths={c.CP,c.RESEARCH_CP,m.ROOT/'AGENTS.md',m.ROOT/'docs/ARTLINE_IMAGE_USE.md',m.ROOT/'ops/museum-expansion-20261006.py',m.ROOT/'ops/catalogue-expansion-20261008.py',m.ROOT/'ops/museum-expansion-kazantzakis-more-common-20261009.py',m.ROOT/'ops/museum-expansion-ferens-timestamps-20261009.py'}
    paths|={x for x in RUN.rglob('*') if x.is_file()};paths|={x for x in c.RESEARCH.rglob('*') if x.is_file()};paths|={x for x in (m.ROOT/'ops').glob('*chania*20261010.py')}
    paths|={m.ROOT/'ops'/name for name in ['museum-expansion-larissa-common-20261010.py','museum-expansion-larissa-common-v2-20261010.py']}
    paths|={m.ROOT/v['path'] for v in m.load(REVIEW)['dependencies']}
    p['evidence']=[c.ref(x) for x in sorted(paths)]
    proofs=[Path.home()/'Library/Application Support/Artline/research-proofs'/x for x in ['chania-20261010','chania-delivery-20261010']]
    p['external_evidence']=[dict(path=str(x),sha256=sha(x)) for root in proofs for x in sorted(root.rglob('*')) if x.is_file()]
    m.save(PLAN,p);print(json.dumps(dict(plan=c.ref(PLAN),new=174,links=0,images=188,protected=len(ids),prior=len(prior_ids))),flush=True)

def validate_plan():
    p=m.load(PLAN)
    for pin in p['evidence']:c.checked(pin)
    for pin in p['external_evidence']:assert sha(pin['path'])==pin['sha256'],pin['path']
    assert sha(p['backup_path'])==p['backup_sha256'];news,holds=records();assert news==p['records'] and holds==p['holdings'] and p['images']==image_records(p['before'])
    return p,sha(PLAN)

def verify_existing(before,after,p,digest):
    old={x['id']:x for x in before['artworks']};new={x['id']:x for x in after['artworks']};assert old.keys()==new.keys()
    linked={x['artwork_id'] for x in p['holdings']};new_primary={x['artwork_id']:x['media_id'] for x in p['images'] if x['set_primary']}
    for aid,a in old.items():
        allowed={'updated_at'} if aid in linked else set()
        if aid in linked:allowed.add('current_institution_id');assert a['current_institution_id'] is None and new[aid]['current_institution_id']==c.IID
        if aid in new_primary:
            allowed|={'primary_media_id','revision','updated_at','updated_by'};assert a['primary_media_id'] is None and new[aid]['primary_media_id']==new_primary[aid] and new[aid]['revision']==a['revision']+1
        assert {k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in new[aid].items() if k not in allowed},aid
        if a['primary_media_id']:assert new[aid]['primary_media_id']==a['primary_media_id']
    newm={x['media_id'] for x in p['images']}
    assert before['artists']==after['artists'] and before['museums']==after['museums']
    assert before['identifiers']==after['identifiers'],'Existing artwork identifiers are preserved'
    for key in ['citations','assertions']:assert before[key]==[x for x in after[key] if x['source_id']!=SID]
    for key in ['media','media_rights_evidence']:assert before[key]==[x for x in after[key] if x['media_id']not in newm]
    assert before['media_assets']==[x for x in after['media_assets'] if x['id']not in newm]

def verify(db,p,digest):
    ids=[v['artwork_id'] for v in p['records']];snap=c.snapshot(db,ids);assert len(snap['artworks'])==174 and not snap['artists']
    newby={x['id']:x for x in snap['artworks']};newprimary={im['artwork_id']:im['media_id'] for im in p['images'] if im['set_primary']}
    for v in p['records']:
        a=newby[v['artwork_id']];assert all(a[k]==x for k,x in metadata(v).items());assert a['current_institution_id']==c.IID and a['primary_media_id']==newprimary.get(a['id'])
        assert a['alternate_title'] is None and a['published_at'] is None and a['location_checked_at'] is None
        assert a['revision']==(2 if a['id'] in newprimary else 1)
    expected_identifiers={(v['artwork_id'],sid,url) for v in p['records'] for sid,url in identifier_values(v)}
    assert {(x['entity_id'],x['external_id'],x['canonical_url']) for x in snap['identifiers']}==expected_identifiers and len(snap['identifiers'])==174
    for x in snap['identifiers']:assert x['scheme']=='searchculture-edm' and x['source_id']==SID
    after=c.snapshot(db,p['scoped_ids']);verify_existing(p['before'],after,p,digest);assert c.s.prior_state(db,p['prior_ids'])==p['prior_state']
    allids=sorted(set(ids)|{x['artwork_id'] for x in p['holdings']}|{x['artwork_id'] for x in p['images']});allstate=c.snapshot(db,allids)
    cites=[x for x in allstate['citations'] if x['source_id']==SID];holds=[x for x in allstate['assertions'] if x['source_id']==SID]
    assert len(holds)==174 and len(cites)==174+188
    for v in p['records']+p['holdings']:
        h=next(x for x in holds if x['id']==v['holding_id']);assert h['artwork_id']==v['artwork_id'] and h['institution_id']==c.IID and h['claim_type']=='holding' and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['facts']['source_url'] and h['evidence_note']==holding_note(v,digest)
        assert ts.same_instant(h['checked_at'],v['retrieved_at']);assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
        cs=[x for x in cites if x['entity_id']==v['artwork_id'] and x['field_name']=='museum_expansion_chania_metadata'];assert len(cs)==1;cc=cs[0];assert cc['evidence_note']==evidence(v,digest) and cc['source_record_id']==v['facts']['source_id'] and cc['source_url']==v['facts']['source_url'] and ts.same_instant(cc['retrieved_at'],v['retrieved_at'])
    media={x['id']:x for x in allstate['media_assets']};rights={x['media_id']:x for x in allstate['media_rights_evidence']};links={(x['artwork_id'],x['media_id']):x for x in allstate['media']}
    for im in p['images']:
        row=media[im['media_id']];expected=media_row(im)
        assert all(ts.same_instant(row[k],val) if k=='retrieved_at' else row[k]==val for k,val in expected.items())
        rr=rights[im['media_id']];assert rr['source_id']==SID and rr['source_record_id']==im['source_id'] and rr['source_image_url']==im['verified_https_source_image_url'] and rr['source_checksum']==im['source_receipt']['sha256'] and rr['evidence_json']==im and rr['rights_basis']==im['user_approved_source_policy']
        assert rr['policy_url']==im['source_url'] and rr['adapter_version']==KEY and ts.same_instant(rr['checked_at'],im['source_receipt']['retrieved_at'])
        link=links[(im['artwork_id'],im['media_id'])];assert link['sort_order']==im['sort_order'] and link['view_label']==im['view_label']
        cs=[x for x in cites if x['field_name']=='museum_expansion_chania_image' and x['entity_id']==im['artwork_id'] and x['source_record_id']==im['source_id']];assert len(cs)==1 and cs[0]['evidence_note']==image_note(im,digest)
    assert len([x for x in rights.values() if x['source_id']==SID])==188
    assert c.counts(db)=={c.IID:dict(linked=192,eligible=117)}
    assert db.execute('SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_has_selection_evidence(id)',(ids+[x['artwork_id'] for x in p['holdings']],)).fetchone()['n']==174
    audits=db.execute('SELECT entity_type,count(*) n FROM audit_log WHERE request_id=%s GROUP BY entity_type',(KEY,)).fetchall();assert {x['entity_type']:x['n'] for x in audits}==dict(artwork=174+0+183,media_asset=188,artwork_media=188)
    return dict(verified_new_records=174,existing_artworks_linked=0,new_images=188,new_primary_images=183,alternate_images=5,protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),current_counts=c.counts(db),new_source_identifiers=174,source_records_preserved=180,new_citations=362,new_accepted_holdings=174,new_artist_links=0,new_published=0,new_display_claims=0,unknown_date_new_records=57,numeric_date_eligible_new_records=117,existing_unknown_dates_preserved=18)

def apply(expected_sha):
    p,digest=validate_plan();assert expected_sha==digest
    backup=m.load(RUN/'cloud-backup-001.json');assert backup['status']=='SUCCESSFUL'
    upload=m.load(RUN/'storage-upload-001.json');assert upload['plan_sha256']==digest and len(upload['checks'])==188
    for im,check in zip(p['images'],upload['checks']):assert check['media_id']==im['media_id'] and check['sha256']==im['sha256'] and check['path']==im['storage_path']
    with c.prod.connect(write=True) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL application_name='artline-chania-selected-apply'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(c.IID,));preflight(db,p)
        saved=m.BACKUP/(KEY+'-reviewed-plan-001.json.gz');assert not saved.exists();m.save(saved,p)
        insert(db,'sources',dict(id=SID,slug=SLUG,name='Chania – selected museum artworks and authentic source images, 10 October2026',source_type='collection_page',base_url='https://www.searchculture.gr/aggregator/portal/collections/AMusChania'))
        for v in p['records']:
            insert(db,'artworks',metadata(v));audit(db,'artwork',v['artwork_id'],None,current_art(db,v['artwork_id']),'insert')
            for sid,url in identifier_values(v):insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=v['artwork_id'],scheme='searchculture-edm',external_id=sid,canonical_url=url,source_id=SID,retrieved_at=v['retrieved_at']))
        for v in p['records']+p['holdings']:
            before=current_art(db,v['artwork_id']) if v in p['holdings'] else None
            insert(db,'citations',dict(entity_type='artwork',entity_id=v['artwork_id'],field_name='museum_expansion_chania_metadata',source_id=SID,source_record_id=v['facts']['source_id'],source_url=v['facts']['source_url'],evidence_note=evidence(v,digest),retrieved_at=v['retrieved_at'],created_by=m.ACTOR))
            insert(db,'artwork_location_assertions',dict(id=v['holding_id'],artwork_id=v['artwork_id'],claim_type='holding',institution_id=c.IID,context='collection',source_id=SID,source_url=v['facts']['source_url'],evidence_note=holding_note(v,digest),checked_at=v['retrieved_at'],review_state='accepted'))
            if before:audit(db,'artwork',v['artwork_id'],before,current_art(db,v['artwork_id']),'update')
        for im in p['images']:
            row=media_row(im);insert(db,'media_assets',row);audit(db,'media_asset',im['media_id'],None,row,'insert')
            insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=SID,source_record_id=im['source_id'],source_checksum=im['source_receipt']['sha256'],source_image_url=im['verified_https_source_image_url'],policy_url=im['source_url'],rights_basis=im['user_approved_source_policy'],adapter_version=KEY,checked_at=im['source_receipt']['retrieved_at'],evidence_json=Jsonb(im)))
            link=dict(artwork_id=im['artwork_id'],media_id=im['media_id'],sort_order=im['sort_order'],view_label=im['view_label']);insert(db,'artwork_media',link);audit(db,'artwork_media',im['artwork_id'],None,link,'insert')
            insert(db,'citations',dict(entity_type='artwork',entity_id=im['artwork_id'],field_name='museum_expansion_chania_image',source_id=SID,source_record_id=im['source_id'],source_url=im['source_url'],evidence_note=image_note(im,digest),retrieved_at=im['source_receipt']['retrieved_at'],created_by=m.ACTOR))
            if im['set_primary']:
                before=current_art(db,im['artwork_id']);assert before['primary_media_id'] is None
                db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],m.ACTOR,im['artwork_id']));audit(db,'artwork',im['artwork_id'],before,current_art(db,im['artwork_id']),'update')
        result=verify(db,p,digest)
    with m.connect() as db:
        local=m.load(RUN/'initial-scope-001.json.gz');assert c.snapshot(db,local['scoped_ids'])==local['snapshot'] and c.counts(db)==local['counts']
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,verification=result,production_only=True,local_unchanged=True,created=174,existing_links=0,images=188))
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','apply']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.command=='prepare':prepare()
    else:assert args.plan_sha;apply(args.plan_sha)
