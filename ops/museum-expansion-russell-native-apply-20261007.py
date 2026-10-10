#!/usr/bin/env python3
"""Apply 68 individually reviewed native Russell-Cotes artworks to the local catalogue."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
s=importlib.util.spec_from_file_location('editor',Path(__file__).with_name('museum-expansion-russell-native-review-20261007.py'))
e=importlib.util.module_from_spec(s);s.loader.exec_module(e);n=e.n;w=e.w;m=e.m;RUN=e.RUN;IID=w.IID
COUNT=68;KEY='russell-cotes-native-additions-001';SID=m.uid('source/'+KEY);SOURCE_SLUG='museum-expansion-20261006-'+KEY;SCHEME='russell-cotes-native-object'
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'native-editorial-001.json.gz';IDENTITY=RUN/'native-identity-002.json.gz';CANDIDATES=RUN/'native-candidates-002.json.gz'
reference=w.reference;checked_reference=w.checked_reference


def facts(native,row,decision):
    assert decision['state']=='approved_review_only_addition' and decision['confidence']==0.95
    assert row['state']=='candidate' and row['source_id']==decision['source_id']
    assert n.source_facts(native)==row['facts'] and native['parsed']==row['parsed']
    assert decision['facts']==e.reviewed_facts(row) and decision['identity_note'] and decision['limitation']
    f=decision['facts'];assert f['source_url']==native['url'] and f['source_id']==native['url'].rstrip('/').split('/')[-1]
    assert f['first']<=f['last']<=1970 and f['inventory'] and f['creator_label']
    assert not decision['comparison']['inventory_hits']
    return copy.deepcopy(f)


def records():
    review=m.load(REVIEW);rows={r['source_id']:r for r in m.load(CANDIDATES)['rows']};comparisons={r['source_id']:r for r in m.load(RUN/'native-comparisons-002.json.gz')['records']};out=[]
    assert len(review['decisions'])==len({r['source_id'] for r in review['decisions']})==140
    assert set(rows)=={r['source_id'] for r in review['decisions']}
    disposal=m.load(RUN/'disposal-review-001.json');w.checked_reference(disposal['source_reference']);w.checked_capture(m.load(m.ROOT/disposal['source_reference']['path']))
    for d in review['decisions']:
        if d['state']!='approved_review_only_addition':continue
        assert d['comparison']==comparisons[d['source_id']]
        native=w.checked_native_page(d['source_reference']);row=rows[d['source_id']];f=facts(native,row,d)
        assert w.compact(f['inventory']) not in w.compact(disposal['full_extracted_text'])
        out.append(dict(artwork_id=m.uid(KEY+'/'+f['source_id']),slug='museum-expansion-'+KEY+'-'+hashlib.sha256(f['source_id'].encode()).hexdigest()[:16],facts=f,decision=d,native=native))
    assert len(out)==len({r['facts']['source_id'] for r in out})==len({w.compact(r['facts']['inventory']) for r in out})==COUNT
    assert {r['facts']['source_id'] for r in out}==set(review['selected_source_ids'])
    return out


def identity_state(db):
    x=m.load(IDENTITY);keys=x['name_keys'];raw=[v.lower() for v in x['all_names']]
    artists=db.execute('SELECT id::text,display_name,normalized_name,slug,birth_year,death_year FROM artists WHERE normalized_name=ANY(%s) OR lower(display_name)=ANY(%s) ORDER BY id',(keys,raw)).fetchall()
    aliases=db.execute('SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) OR lower(aa.alias)=ANY(%s) ORDER BY aa.artist_id,aa.alias',(keys,raw)).fetchall()
    artistids=sorted({r['id'] for r in artists}|{r['artist_id'] for r in aliases});assert artistids==x['artist_ids']
    linked=db.execute('''SELECT a.id::text,a.title,a.normalized_title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label,
 ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) artist_ids,
 ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
 ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
 FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) scoped JOIN artworks a ON a.id=scoped.artwork_id ORDER BY a.id''',(artistids,)).fetchall()
    unlinked=db.execute('SELECT id::text,title,normalized_title,alternate_title,date_display,creation_year_start,creation_year_end,date_precision,accession_number,current_institution_id::text,medium_text,dimensions_text,work_type,unlinked_creator_label FROM artworks WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id',(x['unlinked_patterns'],)).fetchall()
    inv=db.execute('SELECT id::text,title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s::text[]) ORDER BY id',(x['inventories'],)).fetchall()
    exact=db.execute('SELECT id::text,title,normalized_title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=ANY(%s::text[]) ORDER BY id',(x['title_keys'],)).fetchall()
    cites=db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) ORDER BY entity_id,source_url",(x['source_urls'],)).fetchall()
    external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) ORDER BY entity_id,external_id",(x['source_urls'],)).fetchall()
    inventories=db.execute("SELECT id::text,title,normalized_title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE accession_number LIKE 'BORGM%%' OR accession_number LIKE ':BORGM%%' OR accession_number LIKE 'SC%%' OR accession_number LIKE 'Sc%%' ORDER BY id").fetchall()
    actual=dict(artists=artists,aliases=aliases,linked=linked,unlinked=unlinked,inventory_lookup=inv,exact_title_lookup=exact,source_url_lookup=cites,source_external_lookup=external,museum_inventory=inventories)
    for k,v in actual.items():assert v==x[k],'Identity scope changed: '+k
    context=m.load(RUN/'native-identity-context-001.json.gz')
    old=db.execute('SELECT aa.artwork_id::text,aa.artist_id::text,aa.attribution_role,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[]) ORDER BY aa.artwork_id,aa.artist_id',(context['artwork_ids'],)).fetchall()
    assert old==context['exact_title_creators'],'Exact-title creators changed'
    old=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=ANY(%s::uuid[]) ORDER BY c.entity_id,c.id",(context['citation_artwork_ids'],)).fetchall()
    assert old==context['citations'],'Prior unresolved native-URL evidence changed'
    return {k:len(v) for k,v in actual.items()}


def legacy_url_check(record,before):
    f=record['facts'];hits=record['decision']['comparison']['source_hits']
    if not hits:return
    assert f['source_id'] in ['on-the-cornish-coast','the-bathers','the-bathers-2']
    expected='a93f88f3-7aba-5736-acc7-1188630d6a5c' if f['source_id']=='on-the-cornish-coast' else '26120ee4-ecc2-5b87-9b32-1a3bf7a11cc8'
    assert {r['entity_id'] for r in hits}=={expected}
    old=next(a for a in before['artworks'] if a['id']==expected)
    assert old['accession_number']==('BORGM 01936' if f['source_id']=='on-the-cornish-coast' else 'BORGM 01696') and w.compact(old['accession_number'])!=w.compact(f['inventory'])
    citations=[c for c in before['citations'] if c['entity_id']==expected and c['source_url']==f['source_url']];assert len(citations)==1
    c=citations[0];assert c['field_name']=='museum_location_lead_review'
    evidence=json.loads(c['evidence_note']);assert evidence['source_outcome']=='current_title_creator_inventory_not_reconciled' and evidence['review_state']=='review'
    assert not any(a['source_url']==f['source_url'] and a['review_state']=='accepted' for a in before['assertions'])


def baseline_unchanged(db,plan):
    assert w.snapshot(db,plan['scoped_ids'])==plan['before'],'Existing catalogue scope changed'
    pp,pd=w.validate_plan();assert pd==plan['prior_holding_plan_sha256'];return w.verify(db,pp,pd)


def preflight(db,plan):
    baseline_unchanged(db,plan);checked=identity_state(db)
    ids=[r['artwork_id'] for r in plan['records']];urls=[r['facts']['source_url'] for r in plan['records']];sourceids=[r['facts']['source_id'] for r in plan['records']]
    assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone()
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=%s AND external_id=ANY(%s))) LIMIT 1",(urls,SCHEME,sourceids)).fetchone()
    for r in plan['records']:legacy_url_check(r,plan['before'])
    return checked


def prepare():
    assert not PLAN.exists();selected=records();scope=m.load(CANDIDATES);pp,pd=w.validate_plan()
    with m.connect() as db:
        before=w.snapshot(db,scope['scoped_ids']);old=m.load(Path(scope['backup_path']));assert all(before[k]==old[k] for k in before)
        assert w.counts(db)==dict(linked=111,eligible=111)
        files=[Path(__file__).resolve(),Path(e.__file__).resolve(),Path(n.__file__).resolve(),Path(w.__file__).resolve(),w.PLAN,REVIEW,IDENTITY,CANDIDATES,RUN/'native-comparisons-002.json.gz',RUN/'native-identity-context-001.json.gz',RUN/'disposal-review-001.json',RUN/'native-candidates-001.json.gz',RUN/'native-identity-001.json.gz']
        files += [m.ROOT/r['decision']['source_reference']['path'] for r in selected]
        plan=dict(at=m.now(),records=selected,before=before,scoped_ids=scope['scoped_ids'],backup_path=scope['backup_path'],prior_holding_plan_sha256=pd,evidence=[reference(p) for p in files],policy='68 selected native works created by1970, including separately dated posthumous cast and literal studio/copy/unknown creator labels. Review only. No images, artist links, ownership/current-display claims or existing catalogue edits.')
        plan['identity_checks']=preflight(db,plan)
    m.save(PLAN,plan);print('Pinned68nativeworks',hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)


def validate_plan():
    plan=m.load(PLAN)
    for ref in plan['evidence']:checked_reference(ref)
    assert plan['records']==records()
    return plan,hashlib.sha256(PLAN.read_bytes()).hexdigest()


def citation_note(r,digest):return json.dumps(dict(plan_sha256=digest,source_record=r,policy='Full native caption/narrative/rights retained. Production/casting evidence is distinct from prototypes, depicted events, acquisition and biographies. Review only; no image or current-display claim.'),ensure_ascii=False)
def holding_note(r,digest):return 'Native Russell-Cotes collection object page with exact title, inventoried physical identity and creation statement. Editorial confidence0.95, not calibrated. '+r['decision']['identity_note']+' '+r['decision']['limitation']+' Plan SHA-256 '+digest


def assert_new(art,r):
    f=r['facts'];expected=dict(id=r['artwork_id'],slug=r['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=None,accession_number=f['inventory'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],current_institution_id=IID,created_by=m.ACTOR,updated_by=m.ACTOR)
    assert all(art[k]==value for k,value in expected.items()),f['source_id']
    for k in ['alternate_title','description_md','primary_media_id','published_at','object_form','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None,(f['source_id'],k)


def verify(db,plan,digest):
    selected=plan['records'];ids=[r['artwork_id'] for r in selected];snapshot=w.snapshot(db,ids)
    assert len(snapshot['artworks'])==len(snapshot['identifiers'])==len(snapshot['citations'])==len(snapshot['assertions'])==COUNT
    assert not snapshot['artists'] and not snapshot['media']
    for r in selected:
        aid=r['artwork_id'];f=r['facts'];art=next(x for x in snapshot['artworks'] if x['id']==aid);assert_new(art,r)
        ident=next(x for x in snapshot['identifiers'] if x['entity_id']==aid);assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(SCHEME,f['source_id'],f['source_url'],SID)
        c=next(x for x in snapshot['citations'] if x['entity_id']==aid);assert c['source_id']==SID and c['field_name']=='museum_expansion_native_metadata' and c['source_record_id']==f['source_id'] and c['source_url']==f['source_url'] and c['evidence_note']==citation_note(r,digest)
        a=next(x for x in snapshot['assertions'] if x['artwork_id']==aid);assert a['source_id']==SID and a['claim_type']=='holding' and a['institution_id']==IID and a['context']=='collection' and a['review_state']=='accepted' and a['superseded_by'] is None and a['source_url']==f['source_url'] and a['evidence_note']==holding_note(r,digest)
        assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==COUNT
    prior=baseline_unchanged(db,plan)
    return dict(verified_new_records=COUNT,source_inventory_count=COUNT,distinct_creator_labels=len({r['facts']['creator_label'] for r in selected}),existing_artworks_unchanged=len(plan['before']['artworks']),old_citations_unchanged=len(plan['before']['citations']),prior_holdings_preserved=prior['existing_artworks_linked'],new_artist_links=0,new_media_links=0,new_published=0,new_display_claims=0,new_identifiers=COUNT,new_citations=COUNT,new_accepted_holdings=COUNT,current_counts=w.counts(db),verified_all_metadata_and_citations=True)


def apply(expected_sha):
    plan,digest=validate_plan();assert digest==expected_sha;ids=[r['artwork_id'] for r in plan['records']]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
        old=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        if old:
            assert len(old)==COUNT;verify(db,plan,digest);print('Unchanged replay:68records;zero inserts',flush=True);return
        preflight(db,plan);db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,)).fetchone();m.save(m.BACKUP/(KEY+'-reviewed-plan.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SOURCE_SLUG,'Russell-Cotes selected native artworks,7 October2026','collection_page','https://russellcotes.com/'))
        for r in plan['records']:
            f=r['facts'];aid=r['artwork_id'];rc=r['native']['capture']['receipt']
            db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,created_by,updated_by)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s)''',(aid,r['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],None,f['inventory'],f['creator_label'],m.ACTOR,m.ACTOR))
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,f['source_id'],f['source_url'],SID,rc['retrieved_at']))
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_native_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_id'],f['source_url'],citation_note(r,digest),rc['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,f['source_url'],holding_note(r,digest),rc['retrieved_at']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=179,eligible=179)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=COUNT,local_only=True,verification=result));print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='apply':assert a.plan_sha;apply(a.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
