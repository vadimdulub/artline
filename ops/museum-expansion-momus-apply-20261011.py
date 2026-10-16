"""Atomic selected199artwork/38image delivery; source-backed review objects only."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-momus-review-20261011.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c,m,RUN,KEY=r.c,r.m,r.RUN,r.KEY
ts=c.module('ts','museum-expansion-ferens-timestamps-20261009.py')
identity=c.module('identity','museum-expansion-momus-identity-v2-20261011.py')
PLAN=RUN/(KEY+'-plan-001.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz'
SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY;BUCKET='artline-508319-images'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def insert(db,table,row):
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder() for _ in row)),list(row.values()))
def current_art(db,aid):return db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row']
def audit(db,kind,aid,before,after):insert(db,'audit_log',dict(actor_user_id=m.ACTOR,action='update' if before is not None else 'insert',entity_type=kind,entity_id=aid,request_id=KEY,before_json=Jsonb(before) if before is not None else None,after_json=Jsonb(after)))
def metadata(v):
    f=v['facts'];return dict(id=v['artwork_id'],slug=v['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions_text'],description_md=f['description_md'],accession_number=f['inventory'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],object_form=None,cultural_context=None,alternate_title=f['alternate_title'],created_by=m.ACTOR,updated_by=m.ACTOR)
def metadata_note(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,review_reference=c.ref(REVIEW),policy='Literal maker, date and physical-unit evidence retained. Multiple source IDs may document opposite sides or an ensemble component. Holding is not current display.'),ensure_ascii=False)
def holding_note(v,digest):return v['identity_basis']+' '+v['limitation']+' Plan SHA-256 '+digest
def image_note(im,digest):return json.dumps(dict(plan_sha256=digest,number=im['number'],source_id=im['source_id'],source_image_url=im['verified_https_source_image_url'],identity_basis=im['identity_basis'],confidence=im['image_identity_confidence_editorial'],view_label=im['view_label'],policy=im['user_approved_source_policy']),ensure_ascii=False)
def media_row(im):
    return dict(id=im['media_id'],storage_kind='local',storage_path=im['storage_path'],source_page_url=im['source_url'],provider_name=im['image_source'],mime_type=im['mime_type'],width=im['width'],height=im['height'],byte_size=im['bytes'],checksum_sha256=im['sha256'],alt_text=im['source_title']+' — '+im['view_label'],rights_status=im['rights_status'],license_label=im['rights_label'],license_url=im['rights_url'],creator_credit=im['credit'],attribution_text=im['credit']+' '+im['changes'],retrieved_at=im['image_retrieved_at'],verified_at=None,verified_by=None)
def constraints(db):return db.execute("SELECT conname,pg_get_constraintdef(oid) definition FROM pg_constraint WHERE conrelid='artworks'::regclass AND contype='c' ORDER BY conname").fetchall()

def validate_plan():
    p=m.load(PLAN);digest=sha(PLAN);assert p['review_reference']==c.ref(REVIEW)
    for pin in p['evidence']:c.checked(pin)
    for pin in p['external_evidence']:assert sha(pin['path'])==pin['sha256'],pin['path']
    records,holdings=r.build();review=m.load(REVIEW);assert records==p['records']==review['records'] and not holdings
    assert len(records)==199 and len(p['images'])==38 and len(p['prior_ids'])==2938
    assert len({v['artwork_id'] for v in records})==len({v['facts']['inventory'] for v in records})==199
    assert sum(v['facts']['last']>1970 for v in records)==2 and all(v['facts']['first'] is not None for v in records)
    for im in p['images']:
        assert im['last']<=1955 and im['date_policy_passed'] and im['bytes']<=100000
        assert sha(im['prepared_path'])==im['sha256'] and sha(im['original_reference']['path'])==im['original_reference']['sha256']
        assert im['rights_status']=='unknown' and im['rights_url'] is None
    return p,digest

def preflight(db,p):
    assert db.execute('SELECT current_database() db').fetchone()['db']=='artline'
    assert constraints(db)==p['constraints']
    assert c.snapshot(db,p['scoped_ids'])==p['before'] and c.counts(db)==p['before_counts']=={c.IID:dict(linked=11,eligible=7)}
    assert c.s.prior_state(db,p['prior_ids'])==p['prior_state']
    assert c.snapshot(db,p['counterpart_ids'])==p['counterpart_state']
    sids=[v['facts']['source_id'] for v in p['records']];urls=[v['facts']['source_url'] for v in p['records']];scids=['momus/000179-'+str(v['facts']['number']) for v in p['records']]
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='momus-native' AND external_id=ANY(%s)) OR (scheme='searchculture-edm' AND external_id=ANY(%s))) LIMIT 1",(urls,sids,scids)).fetchone()
    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND (source_url=ANY(%s) OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.momus.gr/%%') OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%')) LIMIT 1",(urls,sids,scids)).fetchone()
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
    assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s) OR accession_number=ANY(%s) LIMIT 1',([v['artwork_id'] for v in p['records']],[v['slug'] for v in p['records']],[v['facts']['inventory'] for v in p['records']])).fetchone()
    assert not db.execute('SELECT 1 FROM media_assets WHERE id=ANY(%s::uuid[]) OR storage_path=ANY(%s) OR checksum_sha256=ANY(%s) LIMIT 1',([x['media_id'] for x in p['images']],[x['storage_path'] for x in p['images']],p['all_image_hashes'])).fetchone()

def prepare():
    assert not PLAN.exists();review=m.load(REVIEW);records,holdings=r.build();assert review['records']==records and not holdings
    base=m.load(RUN/'baseline-verification-001.json');old=m.load(RUN/'production-initial-scope-001.json.gz');identity0=m.load(RUN/'production-identity-001.json.gz');images=[]
    for src in review['images']:
        im=dict(src);im['media_id']=m.uid(KEY+'/image/'+im['artwork_id']+'/'+im['sha256']);im['storage_path']='/assets/artworks/imported/museum-expansion-momus-20261011/'+im['artwork_id']+'-'+str(im['number'])+'-'+im['sha256'][:16]+'.jpg';im['sort_order']=0;im['set_primary']=True;images.append(im)
    p=dict(at=m.now(),records=records,images=images,scoped_ids=old['scoped_ids'],before=old['snapshot'],before_counts=old['counts'],prior_ids=base['prior_production_ids'],prior_state=base['prior_state'],expected_counts=dict(linked=210,eligible=204),review_reference=c.ref(REVIEW),baseline_reference=c.ref(c.CP),counterpart_ids=identity0['state']['artwork_ids'],all_image_hashes=sorted({x['sha256'] for x in images}|{x['sha256'] for x in m.load(RUN/'visual-references-001.json')['rows']}),policy='199selected native review objects,197numericeligible,2broad1967–1974ranges;38authenticpreviewsby1955. Explicit museum holding field, unique native inventory and reviewed physical units. Preserve11old/2938prior/counterpart records. Localdatabase read-only.')
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');p['constraints']=constraints(db);p['counterpart_state']=c.snapshot(db,p['counterpart_ids']);preflight(db,p)
        values=','.join(['(%s,%s,%s)']*len(records));params=[z for v in records for z in [v['facts']['first'],v['facts']['last'],v['facts']['date_precision']]]
        result=db.execute('SELECT artline_creation_scope(v.first,v.last,v.precision) scope,count(*) n FROM (VALUES '+values+') v(first,last,precision) GROUP BY scope',params).fetchall();p['backend_date_classification']={x['scope']:x['n'] for x in result};assert p['backend_date_classification']==dict(eligible=197,review=2)
    evidence={x for x in RUN.rglob('*') if x.is_file()}|set((m.ROOT/'ops').glob('museum-expansion-momus-*.py'))|{m.ROOT/'AGENTS.md',m.ROOT/'docs/ARTLINE_IMAGE_USE.md',m.ROOT/'ops/museum-expansion-jewish-delivery-review-20261010.py'}
    p['evidence']=[c.ref(x) for x in sorted(evidence)];p['external_evidence']=[dict(path=str(x),sha256=sha(x)) for x in sorted(c.PROOF.rglob('*')) if x.is_file()]
    m.save(PLAN,p);validate_plan();print(json.dumps(dict(plan=c.ref(PLAN),records=199,images=38)),flush=True)

def verify(db,p,digest):
    assert c.snapshot(db,p['counterpart_ids'])==p['counterpart_state']
    assert c.snapshot(db,p['scoped_ids'])==p['before'] and c.s.prior_state(db,p['prior_ids'])==p['prior_state']
    ids=[v['artwork_id'] for v in p['records']];snap=c.snapshot(db,ids);by={x['id']:x for x in snap['artworks']};assert len(by)==199 and not snap['artists']
    images={x['artwork_id']:x for x in p['images']}
    for v in p['records']:
        art=by[v['artwork_id']];expected=metadata(v);assert all(art[k]==val for k,val in expected.items())
        assert art['current_institution_id']==c.IID and art['primary_media_id']==(images[art['id']]['media_id'] if art['id'] in images else None)
        assert art['revision']==(2 if art['id'] in images else 1) and art['alternate_title']==v['facts']['alternate_title'] and art['published_at'] is None and art['location_checked_at'] is None
    assert len(snap['identifiers'])==199
    for v in p['records']:
        f=v['facts'];ident=next(x for x in snap['identifiers'] if x['entity_id']==v['artwork_id']);assert ident['scheme']=='momus-native' and ident['external_id']==f['source_id'] and ident['canonical_url']==f['source_url'] and ident['source_id']==SID
    cites=[x for x in snap['citations'] if x['source_id']==SID];holds=[x for x in snap['assertions'] if x['source_id']==SID];assert len(cites)==237 and len(holds)==199
    for v in p['records']:
        h=next(x for x in holds if x['id']==v['holding_id']);assert h['artwork_id']==v['artwork_id'] and h['institution_id']==c.IID and h['claim_type']=='holding' and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==v['facts']['source_url'] and h['evidence_note']==holding_note(v,digest)
        assert ts.same_instant(h['checked_at'],v['retrieved_at']) and not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
        for sid,url in zip(v['facts']['source_ids'],v['facts']['source_urls']):
            cs=[x for x in cites if x['entity_id']==v['artwork_id'] and x['field_name']=='museum_expansion_momus_metadata' and x['source_record_id']==sid];assert len(cs)==1 and cs[0]['source_url']==url and cs[0]['evidence_note']==metadata_note(v,digest) and ts.same_instant(cs[0]['retrieved_at'],v['retrieved_at'])
    media={x['id']:x for x in snap['media_assets']};rights={x['media_id']:x for x in snap['media_rights_evidence']};links={(x['artwork_id'],x['media_id']):x for x in snap['media']};assert len(media)==len(rights)==len(links)==38
    for im in p['images']:
        expected=media_row(im);row=media[im['media_id']];assert all(ts.same_instant(row[k],v) if k=='retrieved_at' else row[k]==v for k,v in expected.items())
        rr=rights[im['media_id']];assert rr['source_id']==SID and rr['source_record_id']==im['source_id'] and rr['source_image_url']==im['verified_https_source_image_url'] and rr['source_checksum']==im['source_receipt']['sha256'] and rr['evidence_json']==im and rr['rights_basis']==im['user_approved_source_policy'] and rr['adapter_version']==KEY and rr['policy_url']==im['source_url'] and ts.same_instant(rr['checked_at'],im['source_receipt']['retrieved_at'])
        link=links[(im['artwork_id'],im['media_id'])];assert link['sort_order']==0 and link['view_label']==im['view_label']
        cs=[x for x in cites if x['field_name']=='museum_expansion_momus_image' and x['entity_id']==im['artwork_id']];assert len(cs)==1 and cs[0]['source_record_id']==im['source_id'] and cs[0]['evidence_note']==image_note(im,digest)
    assert c.counts(db)=={c.IID:dict(linked=210,eligible=204)}
    assert db.execute('SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_has_selection_evidence(id)',(ids,)).fetchone()['n']==199
    audits=db.execute('SELECT entity_type,count(*) n FROM audit_log WHERE request_id=%s GROUP BY entity_type',(KEY,)).fetchall();assert {x['entity_type']:x['n'] for x in audits}==dict(artwork=237,media_asset=38,artwork_media=38)
    return dict(verified_new_records=199,new_images=38,new_primary_images=38,new_source_identifiers=199,source_records_preserved=199,new_citations=237,new_accepted_holdings=199,new_artist_links=0,new_published=0,new_display_claims=0,unknown_date_new_records=0,crossing_date_new_records=2,numeric_date_eligible_new_records=197,protected_existing_records=11,prior_campaign_records_preserved=2938,current_counts=c.counts(db))
def apply(expected_sha):
    p,digest=validate_plan();assert expected_sha==digest
    backup=m.load(RUN/'cloud-backup-001.json');assert backup['status']=='SUCCESSFUL'
    upload=m.load(RUN/'storage-upload-001.json');assert upload['plan_sha256']==digest and len(upload['checks'])==38
    for im,check in zip(p['images'],upload['checks']):assert check['media_id']==im['media_id'] and check['sha256']==im['sha256'] and check['path']==im['storage_path']
    with c.prod.connect(write=True) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL application_name='artline-momus-selected-apply'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(c.IID,));preflight(db,p)
        saved=m.BACKUP/(KEY+'-reviewed-plan-001.json.gz');assert not saved.exists();m.save(saved,p)
        insert(db,'sources',dict(id=SID,slug=SLUG,name='MOMus – Museum of Contemporary Art – selected native objects and authentic previews,11October2026',source_type='collection_page',base_url='https://www.momus.gr/en/collections'))
        for v in p['records']:
            insert(db,'artworks',metadata(v));audit(db,'artwork',v['artwork_id'],None,current_art(db,v['artwork_id']))
            f=v['facts'];insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=v['artwork_id'],scheme='momus-native',external_id=f['source_id'],canonical_url=f['source_url'],source_id=SID,retrieved_at=v['retrieved_at']))
            for sid,url in zip(f['source_ids'],f['source_urls']):insert(db,'citations',dict(entity_type='artwork',entity_id=v['artwork_id'],field_name='museum_expansion_momus_metadata',source_id=SID,source_record_id=sid,source_url=url,evidence_note=metadata_note(v,digest),retrieved_at=v['retrieved_at'],created_by=m.ACTOR))
            insert(db,'artwork_location_assertions',dict(id=v['holding_id'],artwork_id=v['artwork_id'],claim_type='holding',institution_id=c.IID,context='collection',source_id=SID,source_url=f['source_url'],evidence_note=holding_note(v,digest),checked_at=v['retrieved_at'],review_state='accepted'))
        for im in p['images']:
            row=media_row(im);insert(db,'media_assets',row);audit(db,'media_asset',im['media_id'],None,row)
            insert(db,'media_rights_evidence',dict(media_id=im['media_id'],source_id=SID,source_record_id=im['source_id'],source_checksum=im['source_receipt']['sha256'],source_image_url=im['verified_https_source_image_url'],policy_url=im['source_url'],rights_basis=im['user_approved_source_policy'],adapter_version=KEY,checked_at=im['source_receipt']['retrieved_at'],evidence_json=Jsonb(im)))
            link=dict(artwork_id=im['artwork_id'],media_id=im['media_id'],sort_order=0,view_label=im['view_label']);insert(db,'artwork_media',link);audit(db,'artwork_media',im['artwork_id'],None,link)
            insert(db,'citations',dict(entity_type='artwork',entity_id=im['artwork_id'],field_name='museum_expansion_momus_image',source_id=SID,source_record_id=im['source_id'],source_url=im['source_url'],evidence_note=image_note(im,digest),retrieved_at=im['source_receipt']['retrieved_at'],created_by=m.ACTOR))
            before=current_art(db,im['artwork_id']);assert before['primary_media_id'] is None
            db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],m.ACTOR,im['artwork_id']));audit(db,'artwork',im['artwork_id'],before,current_art(db,im['artwork_id']))
        verified=verify(db,p,digest)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,verification=verified,backup_reference=c.ref(RUN/'cloud-backup-001.json'),storage_reference=c.ref(RUN/'storage-upload-001.json')))
    print(json.dumps(verified),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','apply']);parser.add_argument('--expected-sha');args=parser.parse_args()
    prepare() if args.command=='prepare' else apply(args.expected_sha)
