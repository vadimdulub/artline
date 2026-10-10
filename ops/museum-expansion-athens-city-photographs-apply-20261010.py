"""Atomic metadata-only delivery of55reviewed photographic works."""
import argparse,hashlib,importlib.util,json
from pathlib import Path
from psycopg import sql
from psycopg.types.json import Jsonb
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-athens-city-photographs-delivery-review-20261010.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
c,m,RUN=r.c,r.m,r.RUN
identity=c.module('identity','museum-expansion-athens-city-photographs-identity-20261010.py');ts=c.module('ts','museum-expansion-ferens-timestamps-20261009.py')
KEY=r.KEY;SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY
PLAN=RUN/(KEY+'-plan-001.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def insert(db,table,row):
    db.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(table),sql.SQL(',').join(map(sql.Identifier,row)),sql.SQL(',').join(sql.Placeholder() for _ in row)),list(row.values()))
def current_art(db,aid):return db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s',(aid,)).fetchone()['row']
def metadata(v):
    f=v['facts'];return dict(id=v['artwork_id'],slug=v['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type='photograph',medium_text=f['medium'],dimensions_text=None,description_md=f['description_md'],accession_number=None,status='review',research_candidate=True,unlinked_creator_label=None,object_form=None,cultural_context=None,created_by=m.ACTOR,updated_by=m.ACTOR)
def evidence(v,digest):return json.dumps(dict(plan_sha256=digest,source_record=v,review_reference=c.ref(REVIEW),policy='Museum digital-collection photographic work. Literal source dates and archive credit preserved; no original-negative/vintage-print ownership, individual-maker or display claim is inferred.'),ensure_ascii=False)
def holding_note(v,digest):return v['identity_basis']+' '+v['limitation']+' Plan SHA-256 '+digest
def records():
    review=m.load(REVIEW)
    for pin in review['dependencies']:c.checked(pin)
    rows,holds=r.build();assert rows==review['records'] and holds==[] and review['images']==[];return rows

def global_identity_unchanged(db):
    observed=m.load(RUN/'production-identity-001.json.gz');state=observed['state'];ids=state['artwork_ids']
    current=db.execute('SELECT '+identity.ARTCOLS+' FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id',(ids,)).fetchall();assert current==state['artworks']
    links=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id,aa.attribution_role',(ids,)).fetchall();assert links==state['creator_links']
    cites=[v['row'] for v in db.execute("SELECT to_jsonb(x) row FROM citations x WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(ids,))];assert cites==m.load(RUN/'production-identity-citations-001.json.gz')['citations']
    assert {v['id'] for v in db.execute('SELECT id::text FROM artworks WHERE normalized_title=ANY(%s)',(observed['params']['titles'],))}<=set(ids)
    rows=m.load(REVIEW)['records'];urls=sorted({u for v in rows for u in v['facts']['source_urls']+v['facts']['native_urls']});sids=[v['facts']['source_id'] for v in rows]
    assert not db.execute("SELECT1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme='searchculture-edm' AND external_id=ANY(%s))) LIMIT1".replace('SELECT1','SELECT 1').replace('LIMIT1','LIMIT 1'),(urls,sids)).fetchone()
    assert not db.execute("SELECT1 FROM citations WHERE entity_type='artwork' AND (source_url=ANY(%s) OR (source_record_id=ANY(%s) AND source_url LIKE 'https://www.searchculture.gr/%%')) LIMIT1".replace('SELECT1','SELECT 1').replace('LIMIT1','LIMIT 1'),(urls,sids)).fetchone()

def preflight(db,p):
    assert db.execute('SELECT current_database() db').fetchone()['db']=='artline';assert c.snapshot(db,p['scoped_ids'])==p['before'];assert c.counts(db)==p['before_counts']=={c.IID:dict(linked=153,eligible=63)};assert c.s.prior_state(db,p['prior_ids'])==p['prior_state'];global_identity_unchanged(db)
    assert len(p['records'])==55 and p['holdings']==[] and p['images']==[]
    assert not db.execute('SELECT1 FROM sources WHERE id=%s OR slug=%s'.replace('SELECT1','SELECT 1'),(SID,SLUG)).fetchone()
    assert not db.execute('SELECT1 FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)'.replace('SELECT1','SELECT 1'),([v['artwork_id'] for v in p['records']],[v['slug'] for v in p['records']])).fetchone()

def prepare():
    assert not PLAN.exists();rows=records();base=m.load(RUN/'baseline-verification-001.json');scope=m.load(RUN/'production-initial-scope-001.json.gz');ids=scope['scoped_ids'];prior_ids=base['prior_production_ids']
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');assert c.snapshot(db,ids)==scope['snapshot'];before=c.snapshot(db,ids);p=dict(at=m.now(),records=rows,holdings=[],images=[],scoped_ids=ids,before=before,before_counts=c.counts(db),prior_ids=prior_ids,prior_state=c.s.prior_state(db,prior_ids),expected_counts=dict(linked=208,eligible=111),baseline_reference=c.ref(c.CP),review_reference=c.ref(REVIEW),policy='55museum-catalogued historical photographic works;48source-dated and7unresolved dates. Digital-only source medium explicit. Allreview, no image/artist/old-record changes. Localcatalogue read-only.');assert p['prior_state']==base['prior_state'];preflight(db,p)
    backup=m.BACKUP/(KEY+'-before-001.json.gz');m.save(backup,dict(at=m.now(),scoped_ids=ids,before=before,prior_ids=prior_ids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=sha(backup))
    paths={c.CP,m.ROOT/'AGENTS.md',m.ROOT/'docs/ARTLINE_IMAGE_USE.md'};paths|={x for x in RUN.rglob('*') if x.is_file()};paths|={x for x in (m.ROOT/'ops').glob('*athens-city-photographs*20261010.py')};paths|={x for x in (m.ROOT/'ops').glob('*athens_city_photographs*20261010.py')}
    paths|={m.ROOT/'ops'/name for name in ['museum-expansion-20261006.py','catalogue-expansion-20261008.py','museum-expansion-kazantzakis-more-common-20261009.py','museum-expansion-ferens-timestamps-20261009.py','museum-expansion-athens-city-delivery-common-20261010.py','museum-expansion-larissa-common-20261010.py','museum-expansion-larissa-common-v2-20261010.py']}
    paths|={m.ROOT/x['path'] for x in m.load(REVIEW)['dependencies']};p['evidence']=[c.ref(x) for x in sorted(paths)];p['external_evidence']=[dict(path=str(x),sha256=sha(x)) for x in sorted(c.PROOF.rglob('*')) if x.is_file()];m.save(PLAN,p)
    print(json.dumps(dict(plan=c.ref(PLAN),new=55,images=0,protected=len(ids),prior=len(prior_ids))),flush=True)

def validate_plan():
    p=m.load(PLAN)
    for pin in p['evidence']:c.checked(pin)
    for pin in p['external_evidence']:assert sha(pin['path'])==pin['sha256']
    assert sha(p['backup_path'])==p['backup_sha256'];assert records()==p['records'] and p['holdings']==[] and p['images']==[];return p,sha(PLAN)

def verify(db,p,digest):
    ids=[v['artwork_id'] for v in p['records']];snap=c.snapshot(db,ids);assert len(snap['artworks'])==55 and not snap['artists'] and not snap['media'] and not snap['media_assets'] and not snap['media_rights_evidence'];by={x['id']:x for x in snap['artworks']}
    for v in p['records']:
        row=by[v['artwork_id']];assert all(row[k]==x for k,x in metadata(v).items());assert row['current_institution_id']==c.IID and row['primary_media_id'] is None and row['alternate_title'] is None and row['published_at'] is None and row['location_checked_at'] is None and row['revision']==1
    assert len(snap['identifiers'])==55 and {(x['entity_id'],x['scheme'],x['external_id'],x['canonical_url'],x['source_id']) for x in snap['identifiers']}=={(v['artwork_id'],'searchculture-edm',v['facts']['source_id'],v['facts']['source_url'],SID) for v in p['records']}
    assert len(snap['citations'])==len(snap['assertions'])==55
    for v in p['records']:
        cs=[x for x in snap['citations'] if x['entity_id']==v['artwork_id']];assert len(cs)==1;cc=cs[0];assert cc['field_name']=='museum_expansion_athens_city_photographs_metadata' and cc['source_id']==SID and cc['evidence_note']==evidence(v,digest) and cc['source_record_id']==v['facts']['source_id'] and cc['source_url']==v['facts']['source_url'] and ts.same_instant(cc['retrieved_at'],v['retrieved_at'])
        h=next(x for x in snap['assertions'] if x['id']==v['holding_id']);assert h['artwork_id']==v['artwork_id'] and h['institution_id']==c.IID and h['claim_type']=='holding' and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_id']==SID and h['source_url']==v['facts']['source_url'] and h['evidence_note']==holding_note(v,digest) and ts.same_instant(h['checked_at'],v['retrieved_at']);assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
    assert c.snapshot(db,p['scoped_ids'])==p['before'],'Existing metadata, primaries, links and sources unchanged';assert c.s.prior_state(db,p['prior_ids'])==p['prior_state'];assert c.counts(db)=={c.IID:dict(linked=208,eligible=111)}
    assert db.execute('SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_has_selection_evidence(id)',(ids,)).fetchone()['n']==55
    audits=db.execute('SELECT entity_type,count(*) n FROM audit_log WHERE request_id=%s GROUP BY entity_type',(KEY,)).fetchall();assert {x['entity_type']:x['n'] for x in audits}==dict(artwork=55)
    return dict(verified_new_records=55,existing_artworks_linked=0,new_images=0,new_artist_links=0,new_published=0,new_display_claims=0,current_counts=c.counts(db),protected_existing_records=153,prior_campaign_records_preserved=len(p['prior_ids']),new_source_identifiers=55,new_citations=55,new_accepted_holdings=55,unknown_date_new_records=7,numeric_date_eligible_new_records=48,existing_primary_images_preserved=45)

def apply(expected_sha):
    p,digest=validate_plan();assert digest==expected_sha;assert m.load(RUN/'cloud-backup-001.json')['status']=='SUCCESSFUL'
    with c.prod.connect(write=True) as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SET LOCAL application_name='artline-athens-city-photographs-apply'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        if db.execute('SELECT1 FROM sources WHERE id=%s'.replace('SELECT1','SELECT 1'),(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(c.IID,));preflight(db,p)
        saved=m.BACKUP/(KEY+'-reviewed-plan-001.json.gz');assert not saved.exists();m.save(saved,p)
        insert(db,'sources',dict(id=SID,slug=SLUG,name='Athens City – selected historical photographic works,10October2026',source_type='collection_page',base_url='https://www.searchculture.gr/aggregator/portal/collections/DigAthensMuseum'))
        for v in p['records']:
            aid=v['artwork_id'];f=v['facts'];insert(db,'artworks',metadata(v));insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme='searchculture-edm',external_id=f['source_id'],canonical_url=f['source_url'],source_id=SID,retrieved_at=v['retrieved_at']))
            insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='museum_expansion_athens_city_photographs_metadata',source_id=SID,source_record_id=f['source_id'],source_url=f['source_url'],evidence_note=evidence(v,digest),retrieved_at=v['retrieved_at'],created_by=m.ACTOR))
            insert(db,'artwork_location_assertions',dict(id=v['holding_id'],artwork_id=aid,claim_type='holding',institution_id=c.IID,context='collection',source_id=SID,source_url=f['source_url'],evidence_note=holding_note(v,digest),checked_at=v['retrieved_at'],review_state='accepted'))
            insert(db,'audit_log',dict(actor_user_id=m.ACTOR,action='insert',entity_type='artwork',entity_id=aid,request_id=KEY,before_json=None,after_json=Jsonb(current_art(db,aid))))
        result=verify(db,p,digest)
    with m.connect() as db:
        local=m.load(RUN/'initial-scope-001.json.gz');assert c.snapshot(db,local['scoped_ids'])==local['snapshot'] and c.counts(db)==local['counts']
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,verification=result,production_only=True,local_unchanged=True,created=55,existing_links=0,images=0));print(json.dumps(result),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','apply']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.command=='prepare':prepare()
    else:assert args.plan_sha;apply(args.plan_sha)
