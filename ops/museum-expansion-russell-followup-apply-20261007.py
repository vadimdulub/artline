#!/usr/bin/env python3
"""Apply21 reviewed native artworks to reach200 eligible Russell-Cotes records."""
import argparse,copy,hashlib,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('e',Path(__file__).with_name('museum-expansion-russell-followup-review-20261007.py'));e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
n=e.n;prior=e.prior;w=e.w;m=e.m;RUN=e.RUN;IID=w.IID
COUNT=21;KEY='russell-cotes-native-additions-002';SID=m.uid('source/'+KEY);SOURCE_SLUG='museum-expansion-20261006-'+KEY;SCHEME=prior.SCHEME
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'native-editorial-002.json.gz';IDENTITY=RUN/'native-identity-003.json.gz';CANDIDATES=RUN/'native-candidates-003.json.gz'
reference=w.reference;checked_reference=w.checked_reference

def records():
    review=m.load(REVIEW);rows={r['source_id']:r for r in m.load(CANDIDATES)['rows']};comps={r['source_id']:r for r in m.load(RUN/'native-comparisons-003.json.gz')['records']};out=[]
    assert len(review['decisions'])==len({d['source_id'] for d in review['decisions']})==88 and set(rows)=={d['source_id'] for d in review['decisions']}
    disposal=m.load(RUN/'disposal-review-001.json');w.checked_reference(disposal['source_reference']);w.checked_capture(m.load(m.ROOT/disposal['source_reference']['path']))
    for d in review['decisions']:
        if d['state']!='approved_review_only_addition':continue
        row=rows[d['source_id']];page=w.checked_native_page(d['source_reference'])
        assert row['state']=='candidate' and n.source_facts(page)==row['facts'] and page['parsed']==row['parsed']
        assert d['facts']==e.reviewed_facts(row) and d['identity_note']==e.NOTES[d['source_id']] and d['confidence']==.95
        assert d['comparison']==comps[d['source_id']] and not d['comparison']['inventory_hits'] and not d['comparison']['source_hits']
        f=copy.deepcopy(d['facts']);assert f['first']<=f['last']<=1970 and f['creator_label'] and f['inventory']
        assert n.inventory_key(f['inventory']) not in w.compact(disposal['full_extracted_text'])
        out.append(dict(artwork_id=m.uid(KEY+'/'+f['source_id']),slug='museum-expansion-'+KEY+'-'+hashlib.sha256(f['source_id'].encode()).hexdigest()[:16],facts=f,decision=d,native=page))
    assert len(out)==len({n.inventory_key(r['facts']['inventory']) for r in out})==COUNT
    assert {r['facts']['source_id'] for r in out}==set(e.NOTES)==set(review['selected_source_ids'])
    extra=m.load(RUN/'native-exact-source-comparison-003.json.gz')
    assert len(extra['records'])==3
    for r in extra['records']:w.checked_capture(r)
    apsida,vam,wd=extra['records'];assert 'wall - painting' in apsida['parsed'] and '1503' in apsida['parsed']
    assert vam['parsed']['record']['objectType']=='Painting' and vam['parsed']['record']['accessionNumber']=='IS.49-1979'
    assert wd['parsed']['entities']['Q28017814']['claims']['P31'][0]['mainsnak']['datavalue']['value']['id']=='Q3305213'
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
    inventories=db.execute("SELECT id::text,title,normalized_title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE accession_number LIKE 'BORGM%%' OR accession_number LIKE ':BORGM%%' OR accession_number LIKE 'SC%%' OR accession_number LIKE 'Sc%%' OR accession_number LIKE 'RC%%' OR accession_number LIKE ':T%%' OR accession_number LIKE 'T%%' ORDER BY id").fetchall()
    actual=dict(artists=artists,aliases=aliases,linked=linked,unlinked=unlinked,inventory_lookup=inv,exact_title_lookup=exact,source_url_lookup=cites,source_external_lookup=external,museum_inventory=inventories)
    for k,v in actual.items():assert v==x[k],'Identity scope changed: '+k
    return {k:len(v) for k,v in actual.items()}


def baseline_unchanged(db,plan):
    assert w.snapshot(db,plan['scoped_ids'])==plan['before'],'Existing234-record scope changed'
    pp,pd=prior.validate_plan();assert pd==plan['previous_plan_sha256'];return prior.verify(db,pp,pd)

def preflight(db,plan):
    baseline_unchanged(db,plan);identity_state(db)
    assert w.counts(db)==dict(linked=179,eligible=179)
    ids=[r['artwork_id'] for r in plan['records']];urls=[r['facts']['source_url'] for r in plan['records']]
    assert not db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)',(ids,[r['slug'] for r in plan['records']])).fetchall()
    assert not db.execute("SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND (canonical_url=ANY(%s) OR (scheme=%s AND external_id=ANY(%s)))",(urls,SCHEME,[r['facts']['source_id'] for r in plan['records']])).fetchall()
    assert not db.execute('SELECT id FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchall()

def prepare():
    assert not PLAN.exists();rs=records();x=m.load(CANDIDATES);before=m.load(Path(x['backup_path']));before.pop('at')
    pp,pd=prior.validate_plan();assert pd==x['previous_plan_sha256']
    files=[REVIEW,CANDIDATES,IDENTITY,RUN/'native-comparisons-003.json.gz',RUN/'native-identity-context-003.json.gz',RUN/'native-exact-source-comparison-003.json.gz',prior.PLAN,RUN/(prior.KEY+'-applied.json'),RUN/'native-object-queue-002.json',RUN/'native-object-queue-003.json',RUN/'disposal-review-001.json',m.ROOT/'AGENTS.md',Path(__file__),Path(e.__file__),Path(n.__file__),m.ROOT/'ops/museum-expansion-russell-followup-identity-20261007.py']
    files += [m.ROOT/r['source_reference']['path'] for r in x['rows']]
    plan=dict(at=m.now(),key=KEY,count=COUNT,previous_plan_sha256=pd,scoped_ids=x['scoped_ids'],before=before,records=rs,evidence=[reference(p) for p in files],policy='Selected local catalogue additions only. Preserve234 existing records and all source evidence. Review status, unknown metadata and source attribution qualifiers remain; no artist links, images, publication or display claims.')
    with m.connect() as db:preflight(db,plan)
    m.save(PLAN,plan);print(json.dumps(dict(count=COUNT,sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest())))

def validate_plan():
    plan=m.load(PLAN)
    for ref in plan['evidence']:checked_reference(ref)
    assert plan['records']==records() and plan['count']==COUNT and plan['key']==KEY
    return plan,hashlib.sha256(PLAN.read_bytes()).hexdigest()

def citation_note(r,digest):return json.dumps(dict(plan_sha256=digest,source_record=r,policy='Full native caption/narrative/rights retained. Creation is distinct from sitter lives, prototypes, acquisition and biography. Review only; no image or current display claim.'),ensure_ascii=False)
def holding_note(r,digest):return 'Native Russell-Cotes collection object page with exact title, inventoried physical identity and creation statement. Editorial confidence0.95, not calibrated. '+r['decision']['identity_note']+' '+r['decision']['limitation']+' Plan SHA-256 '+digest

def assert_new(art,r):
    f=r['facts'];expected=dict(id=r['artwork_id'],slug=r['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=None,accession_number=f['inventory'],object_form=f['object_form'],cultural_context=f['cultural_context'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],current_institution_id=IID,created_by=m.ACTOR,updated_by=m.ACTOR)
    assert all(art[k]==value for k,value in expected.items()),f['source_id']
    for k in ['alternate_title','description_md','primary_media_id','published_at','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:assert art[k] is None,(f['source_id'],k)

def verify(db,plan,digest):
    ids=[r['artwork_id'] for r in plan['records']];snapshot=w.snapshot(db,ids)
    assert len(snapshot['artworks'])==len(snapshot['identifiers'])==len(snapshot['citations'])==len(snapshot['assertions'])==COUNT
    assert not snapshot['artists'] and not snapshot['media']
    for r in plan['records']:
        aid=r['artwork_id'];f=r['facts'];assert_new(next(a for a in snapshot['artworks'] if a['id']==aid),r)
        ident=next(x for x in snapshot['identifiers'] if x['entity_id']==aid);assert (ident['scheme'],ident['external_id'],ident['canonical_url'],ident['source_id'])==(SCHEME,f['source_id'],f['source_url'],SID)
        c=next(x for x in snapshot['citations'] if x['entity_id']==aid);assert c['source_id']==SID and c['field_name']=='museum_expansion_native_metadata' and c['source_record_id']==f['source_id'] and c['source_url']==f['source_url'] and c['evidence_note']==citation_note(r,digest)
        a=next(x for x in snapshot['assertions'] if x['artwork_id']==aid);assert a['source_id']==SID and a['claim_type']=='holding' and a['institution_id']==IID and a['context']=='collection' and a['review_state']=='accepted' and a['superseded_by'] is None and a['source_url']==f['source_url'] and a['evidence_note']==holding_note(r,digest)
        assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
    assert db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n']==COUNT
    previous=baseline_unchanged(db,plan)
    return dict(verified_new_records=COUNT,source_inventory_count=COUNT,existing_artworks_unchanged=len(plan['before']['artworks']),old_citations_unchanged=len(plan['before']['citations']),previous_native_additions_preserved=previous['verified_new_records'],new_artist_links=0,new_media_links=0,new_published=0,new_display_claims=0,new_identifiers=COUNT,new_citations=COUNT,new_accepted_holdings=COUNT,current_counts=w.counts(db),verified_all_metadata_and_citations=True)

def apply(expected_sha):
    plan,digest=validate_plan();assert digest==expected_sha;ids=[r['artwork_id'] for r in plan['records']]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
        old=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        if old:
            assert len(old)==COUNT;verify(db,plan,digest);print('Unchanged replay:21records;zero inserts',flush=True);return
        preflight(db,plan);db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,)).fetchone();m.save(m.BACKUP/(KEY+'-reviewed-plan.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SOURCE_SLUG,'Russell-Cotes selected native artworks batch2,7 October2026','collection_page','https://russellcotes.com/'))
        for r in plan['records']:
            f=r['facts'];aid=r['artwork_id'];rc=r['native']['capture']['receipt']
            db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,object_form,cultural_context,status,research_candidate,unlinked_creator_label,created_by,updated_by)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s)""",(aid,r['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],None,f['inventory'],f['object_form'],f['cultural_context'],f['creator_label'],m.ACTOR,m.ACTOR))
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,f['source_id'],f['source_url'],SID,rc['retrieved_at']))
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_native_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,f['source_id'],f['source_url'],citation_note(r,digest),rc['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,f['source_url'],holding_note(r,digest),rc['retrieved_at']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=200,eligible=200)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=COUNT,local_only=True,verification=result));print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');args=p.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
