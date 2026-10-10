#!/usr/bin/env python3
"""Atomic five-museum local review additions with preserved existing catalogue state."""
import argparse,csv,hashlib,importlib.util,json,types
from pathlib import Path
def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
r=module('review','museum-expansion-france-ninth-review-20261008.py')
prior=module('prior','museum-expansion-princeton-apply-20261007.py')
m=r.m;RUN=r.RUN;IIDS=r.identity.IIDS;reference=r.ref;checked=r.checked
KEY='france-ninth-additions-001';SID=m.uid('source/'+KEY);SLUG='museum-expansion-20261006-'+KEY
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'editorial-reviewed-001.json.gz';CHECKPOINT=m.RUN/'native/france-eighth-minimum-20261008/delivery-checkpoint-001.json'
snapshot=r.identity.snapshot;counts=r.identity.counts;expected_art=prior.expected_art
def prior_state(db,ids):return {k:prior.b.prior.digest_rows(v) for k,v in snapshot(db,ids).items()}
def physical_inventory_key(v):
    f=v['facts']
    assert f['inventory'] and f['inventory']!='SN'
    return (v['institution_id'],'inventory',f['inventory'])
def records():
    x=m.load(REVIEW);checked(x['reviewer_reference']);assert x['decisions']==r.build()
    for dep in x['supplement_references']:checked(dep)
    out=[]
    for d in x['decisions']:
        if d['state']=='editorial_hold':continue
        assert d['state']=='approved_review_only_addition' and d['confidence']>=.8 and d['existing_artwork_id'] is None
        f=d['facts'];out.append(dict(institution_id=d['institution_id'],provider='joconde',scheme='joconde-object',facts=f,decision=d,retrieved_at=d['retrieved_at'],artwork_id=m.uid(KEY+'/'+f['source_id']),slug='museum-expansion-'+KEY+'-'+f['source_id']))
    assert len(out)==len({physical_inventory_key(v) for v in out})==len(r.NOTES);return out
def prior_ids():
    ids=[]
    for name in ['added-artworks','reconciled-artworks']:
        with (m.RUN/(name+'-after-wave-63.csv')).open(newline='') as fp:ids += [v['artwork_id'] for v in csv.DictReader(fp)]
    assert len(ids)==len(set(ids))==7703;return sorted(ids)
def verify_baseline():
    assert reference(CHECKPOINT)['sha256']=='0afe2c88230ed4626763ce1360575a6ef660dfca7d3eb0c82a83bef26d1877f1'
    cp=m.load(CHECKPOINT)
    for dep in cp['artifacts']:prior.b.prior.old.h.checked_policy(dep) if dep['path']=='AGENTS.md' and dep['sha256']==prior.b.prior.old.h.OLD else checked(dep)
    for dep in cp['external_artifacts']:assert hashlib.sha256(Path(dep['path']).read_bytes()).hexdigest()==dep['sha256']
    return cp
def fresh_identity(db):
    x=m.load(r.IDENTITY);assert r.identity.queries(db,x['params'])==x['state'],'Identity scope changed'
    c=m.load(r.CITATIONS);actual=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(c['selected_ids'],))];assert actual==c['citations'],'Comparison citations changed'
def preflight(db,p):
    assert snapshot(db,p['scoped_ids'])==p['before'] and counts(db)==p['before_counts']==m.load(RUN/'initial-scope-001.json.gz')['counts']
    assert prior_state(db,p['prior_ids'])==p['prior_state'];fresh_identity(db)
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SLUG)).fetchone()
    assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[])',([v['artwork_id'] for v in p['records']],)).fetchone()
def dependencies():
    paths={Path(__file__).resolve()};seen=set()
    def visit(mod):
        if id(mod) in seen:return
        seen.add(id(mod));file=getattr(mod,'__file__',None)
        if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
        paths.add(Path(file).resolve())
        for v in vars(mod).values():
            if isinstance(v,types.ModuleType):visit(v)
    for mod in [r,prior]:visit(mod)
    return paths
def prepare():
    assert not PLAN.exists();rs=records();verify_baseline();initial=m.load(RUN/'initial-scope-001.json.gz');pids=prior_ids();ds=m.load(REVIEW)['decisions']
    ids=sorted(set(initial['scoped_ids'])|{a['id'] for d in ds for a in d['comparison']['leads']+d['comparison']['exact_title_hits']}|{a['id'] for d in ds for a in d['comparison']['inventory_hits'] if a['relevant']})
    with m.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');assert snapshot(db,initial['scoped_ids'])==initial['snapshot']
        p=dict(at=m.now(),records=rs,scoped_ids=ids,before=snapshot(db,ids),before_counts=counts(db),prior_ids=pids,prior_state=prior_state(db,pids),baseline_reference=reference(CHECKPOINT),policy='Selected local museum additions remain review. All existing catalogue values, images, dates, artist links, holdings and publication unchanged. No images, production updates or current-display assertions.')
        preflight(db,p)
    backup=m.BACKUP/(KEY+'-before.json.gz');assert not backup.exists();m.save(backup,dict(at=m.now(),scoped_ids=ids,before=p['before'],prior_ids=pids,prior_state=p['prior_state']));p.update(backup_path=str(backup),backup_sha256=hashlib.sha256(backup.read_bytes()).hexdigest())
    paths=dependencies()|{CHECKPOINT,m.ROOT/'AGENTS.md',Path(__file__).with_name('test_museum_expansion_france_ninth_20261008.py'),Path(__file__).with_name('test_museum_expansion_france_ninth_context_20261008.py')};paths|={v for v in RUN.rglob('*') if v.is_file() and v.name!='README.md'}
    p['evidence']=[reference(v) for v in sorted(paths)];m.save(PLAN,p);print(json.dumps(dict(new=len(rs),protected_existing=len(ids),protected_prior=len(pids),sha256=reference(PLAN)['sha256'])),flush=True)
def validate_plan():
    p=m.load(PLAN)
    for dep in p['evidence']:checked(dep)
    assert hashlib.sha256(Path(p['backup_path']).read_bytes()).hexdigest()==p['backup_sha256'];assert p['records']==records();return p,reference(PLAN)['sha256']
def citation_note(v,digest):
    d=v['decision'];decision={k:d[k] for k in ['state','confidence','basis','limitation','existing_artwork_id','derived_fields']}
    return json.dumps(dict(plan_sha256=digest,facts=v['facts'],retrieved_at=v['retrieved_at'],native_capture_reference=d['source_reference'],editorial_decision=decision,review_reference=reference(REVIEW),identity_reference=reference(r.IDENTITY),policy='Official API source facts and source-use labels retained verbatim. Museum collection and physical object verified; no current-display or image claim. Existing records unchanged; additions remain review.'),ensure_ascii=False)
def holding_note(v,digest):return v['decision']['basis']+' '+v['decision']['limitation']+' Plan SHA-256 '+digest
def verify(db,p,digest):
    assert snapshot(db,p['scoped_ids'])==p['before'];assert prior_state(db,p['prior_ids'])==p['prior_state'];rs=p['records'];count=len(rs);ids=[v['artwork_id'] for v in rs];snap=snapshot(db,ids)
    assert all(len(snap[k])==count for k in ['artworks','identifiers','citations','assertions']) and not snap['artists'] and not snap['media'] and not snap['media_assets']
    for v in rs:
        f=v['facts'];aid=v['artwork_id'];art=next(x for x in snap['artworks'] if x['id']==aid);assert all(art[k]==value for k,value in expected_art(v).items())
        for k in ['alternate_title','description_md','primary_media_id','published_at','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None
        e=next(x for x in snap['identifiers'] if x['entity_id']==aid);assert(e['scheme'],e['external_id'],e['canonical_url'],e['source_id'])==(v['scheme'],f['source_id'],f['source_url'],SID)
        c=next(x for x in snap['citations'] if x['entity_id']==aid);assert(c['source_id'],c['field_name'],c['source_record_id'],c['source_url'],c['evidence_note'])==(SID,'museum_expansion_reviewed_metadata',f['source_id'],f['source_url'],citation_note(v,digest))
        h=next(x for x in snap['assertions'] if x['artwork_id']==aid);assert h['source_id']==SID and h['claim_type']=='holding' and h['institution_id']==v['institution_id'] and h['context']=='collection' and h['review_state']=='accepted' and h['superseded_by'] is None and h['source_url']==f['source_url'] and h['evidence_note']==holding_note(v,digest)
        assert not any(h.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==count
    assert counts(db)=={iid:{k:value+sum(v['institution_id']==iid for v in rs) for k,value in vals.items()} for iid,vals in p['before_counts'].items()}
    return dict(verified_new_records=count,existing_artworks_linked=0,current_counts=counts(db),protected_existing_records=len(p['scoped_ids']),prior_campaign_records_preserved=len(p['prior_ids']),prior_campaign_table_digests=p['prior_state'],new_media_links=0,new_artist_links=0,new_published=0,new_display_claims=0)
def apply(expected_sha):
    p,digest=validate_plan();assert digest==expected_sha
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
        if db.execute('SELECT 1 FROM sources WHERE id=%s',(SID,)).fetchone():verify(db,p,digest);print('Unchanged replay: zero writes',flush=True);return
        db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(p['scoped_ids'],));db.execute('SELECT id FROM institutions WHERE id=ANY(%s::uuid[]) ORDER BY id FOR SHARE',(IIDS,));preflight(db,p)
        backup=m.BACKUP/(KEY+'-reviewed-plan.json.gz');assert not backup.exists();m.save(backup,p)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SLUG,'Joconde national catalogue: ninth five French museum selections, reviewed 8 October 2026','collection_page','https://pop.culture.gouv.fr'))
        for v in p['records']:
            f=v['facts'];aid=v['artwork_id'];db.execute("INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,created_by,updated_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s)",(aid,v['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions_text'],f['inventory'],f['creator_label'],f['object_form'],m.ACTOR,m.ACTOR))
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,v['scheme'],f['source_id'],f['source_url'],SID,v['retrieved_at']))
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_reviewed_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_id'],f['source_url'],citation_note(v,digest),v['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(m.uid(KEY+'/holding/'+aid),aid,v['institution_id'],SID,f['source_url'],holding_note(v,digest),v['retrieved_at']))
        result=verify(db,p,digest)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=len(p['records']),existing_links=0,local_only=True,verification=result));print(json.dumps(result),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');v=p.parse_args()
    if v.command=='prepare':prepare()
    elif v.command=='apply':assert v.plan_sha;apply(v.plan_sha)
    else:
        p,d=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,p,d)),flush=True)
