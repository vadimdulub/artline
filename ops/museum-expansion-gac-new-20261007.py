#!/usr/bin/env python3
"""58 selected Government Art Collection paintings; local review-only additions."""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-gac-dates-20261007.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
w=v.w;m=v.m;RUN=v.RUN;IID=v.IID;KEY='gac-native-additions-001';SID=m.uid('source/'+KEY)
SOURCE_SLUG='museum-expansion-20261006-'+KEY;SCHEME='gac-native-object'
PLAN=RUN/(KEY+'-plan.json.gz');REVIEW=RUN/'new-artwork-editorial-003.json.gz';IDENTITY=RUN/'new-artwork-identity-002.json.gz'
reference=w.reference;checked_reference=w.checked_reference


def creators():
    out={}
    for path in sorted((RUN/'new-creators-001').glob('*.gz')):
        row=m.load(path);data=json.loads(v.capture_body(row['capture']))['entities'];assert data==row['entities']
        assert set(row['ids'])==set(data) and not set(data)&set(out);out.update(data)
    assert len(out)==78;return out


def creator_label(literal):
    # Remove only a trailing source lifespan; retain the source name and honorific.
    return re.sub(r'\s*\([^)]*\d{3,4}[^)]*\)$','',literal).strip()


def facts(native,entity,creator,decision):
    parsed=w.parse_native(v.capture_body(native['capture']));assert parsed==native['parsed'];f=parsed['fields']
    assert native['qid']==entity['id']==decision['qid']
    assert decision['state']=='approved_review_only_addition' and decision['confidence']==0.95 and decision['identity_note']
    assert parsed['canonical']==native['url']==native['capture']['receipt']['url']
    assert native['url'].startswith('https://artcollection.dcms.gov.uk/artwork/')
    assert parsed['headings']==[f['Title']] and not parsed['repeated']
    assert f['GAC number']==decision['inventory']==w.val(entity,'P217')
    assert w.qualifier_value(w.one(entity,'P217'),'P195')['id']==w.QID and set(w.one(entity,'P217').get('qualifiers',{}))=={'P195'}
    assert w.val(entity,'P195')['id']==w.QID and not set(w.one(entity,'P195').get('qualifiers',{}))-{'P580'}
    assert w.val(entity,'P31')['id']=='Q3305213' and not w.one(entity,'P31').get('qualifiers')
    assert w.val(entity,'P170')['id']==creator['id'] and not w.one(entity,'P170').get('qualifiers')
    assert not any(w.h.best(entity,p) for p in ['P518','P361','P1877','P527'])
    assert (f['Title'],f['Artist'],f['Date'])==(decision['title'],decision['creator'],decision['source_date'])
    assert not re.search(r'\b(after|circle|attributed|workshop|manner|school|unknown)\b',f['Artist'],re.I)
    label=creator_label(f['Artist']);assert label
    names={m.norm(x['value']) for x in creator.get('labels',{}).values()}|{m.norm(x['value']) for a in creator.get('aliases',{}).values() for x in a}
    assert m.norm(label) in names or m.norm(label.removeprefix('Sir ')) in names or (entity['id']=='Q119305022' and label=='Carolyn Stafford' and creator['labels']['en']['value']=='Cynthia Carolyn Stafford')
    for c in w.h.best(entity,'P18'):
        assert not re.search(r'\b(after|circle|attributed|workshop|manner|school)\b',w.h.value(c).split(' - ')[0],re.I)
    first,last,precision=v.creation(f['Date'])
    assert f.get('Dimensions') and f.get('Medium') and re.search(r'\b(oil|tempera|acrylic)\b',f['Medium'],re.I)
    assert f.get('Acquisition','').startswith(('Purchased','Presented','Commissioned'))
    assert not re.search(r'\b(missing|lost|stolen|deaccessioned)\b',f.get('Location',''),re.I)
    assert not decision['comparison']['same'] and not decision['comparison']['invhits']
    return dict(qid=entity['id'],inventory=f['GAC number'],title=f['Title'],creator_label=label,native_creator=f['Artist'],creator_qid=creator['id'],date_display=f['Date'],first=first,last=last,date_precision=precision,medium=f['Medium'],dimensions=f['Dimensions'],work_type='painting',source_url=native['url'],holding_basis='Native Government Art Collection object page, exact inventory/title/creator and explicit creation date, physical details and acquisition. Editorial holding confidence 0.95 (not calibrated). Collection membership only; no physical custody, legal ownership or current-display inference.')


def records():
    sources=v.source_rows();cs=creators();review=m.load(REVIEW);out=[]
    for ref in review['version_sources']:
        checked_reference(ref);proof=m.load(m.ROOT/ref['path'])
        if 'capture' in proof:v.capture_body(proof['capture'])
    for d in review['decisions']:
        if d['state']!='approved_review_only_addition':continue
        q=d['qid'];native=m.load(RUN/'new-native-objects-002'/(q+'.json.gz'));entity=sources[q]['entity'];creator=cs[w.val(entity,'P170')['id']];f=facts(native,entity,creator,d)
        out.append(dict(artwork_id=m.uid(KEY+'/'+f['inventory']),slug='museum-expansion-'+KEY+'-'+hashlib.sha256(f['inventory'].encode()).hexdigest()[:16],facts=f,decision=d,native=native,wikidata=sources[q],creator_entity=creator))
    assert len(out)==len({r['facts']['inventory'] for r in out})==len({r['facts']['qid'] for r in out})==58
    assert {r['facts']['qid'] for r in out}==set(review['selected_qids'])
    return out


def identity_state(db):
    identity=m.load(IDENTITY);keys=identity['name_keys'];qs=identity['creator_qids']
    authorities=db.execute("SELECT e.entity_id::text,e.external_id,a.display_name,a.normalized_name,a.slug,a.birth_year,a.death_year FROM external_identifiers e JOIN artists a ON a.id=e.entity_id WHERE e.entity_type='artist' AND e.scheme='wikidata' AND e.external_id=ANY(%s) ORDER BY e.entity_id,e.external_id",(qs,)).fetchall()
    artists=db.execute('SELECT id::text,display_name,normalized_name,slug,birth_year,death_year FROM artists WHERE normalized_name=ANY(%s) ORDER BY id',(keys,)).fetchall()
    aliases=db.execute('SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) ORDER BY aa.artist_id,aa.alias',(keys,)).fetchall()
    artistids=sorted({r['entity_id'] for r in authorities}|{r['id'] for r in artists}|{r['artist_id'] for r in aliases});assert artistids==identity['artist_ids']
    linked=db.execute('''SELECT a.id::text,a.title,a.normalized_title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label,
 ARRAY(SELECT aa.artist_id::text FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) artist_ids,
 ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
 ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
 FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) scoped JOIN artworks a ON a.id=scoped.artwork_id ORDER BY a.id''',(artistids,)).fetchall()
    unlinked=db.execute('SELECT id::text,title,normalized_title,alternate_title,date_display,creation_year_start,creation_year_end,date_precision,accession_number,current_institution_id::text,medium_text,dimensions_text,work_type,unlinked_creator_label FROM artworks WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id',(identity['unlinked_patterns'],)).fetchall()
    inv=db.execute('SELECT id::text,title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE accession_number=ANY(%s::text[]) ORDER BY id',(identity['inventories'],)).fetchall()
    exact=db.execute('SELECT id::text,title,normalized_title,unlinked_creator_label,accession_number,current_institution_id::text FROM artworks WHERE normalized_title=ANY(%s::text[]) ORDER BY id',(identity['title_keys'],)).fetchall()
    cites=db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) ORDER BY entity_id,source_url",(identity['source_urls'],)).fetchall()
    external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) ORDER BY entity_id,external_id",(identity['source_urls'],)).fetchall()
    actual=dict(authorities=authorities,artists=artists,aliases=aliases,linked=linked,unlinked=unlinked,inventory_lookup=inv,exact_title_lookup=exact,source_url_lookup=cites,source_external_lookup=external)
    for key,rows in actual.items():assert rows==identity[key],'Identity scope changed: '+key
    return {k:len(rows) for k,rows in actual.items()}


def baseline_unchanged(db,plan):
    assert w.snapshot(db,plan['scoped_ids'])==plan['before'],'Existing collection scope changed'
    return v.verify_prior_holdings(db)


def preflight(db,plan):
    prior=baseline_unchanged(db,plan);identity=identity_state(db);selected=plan['records'];ids=[r['artwork_id'] for r in selected];qs=[r['facts']['qid'] for r in selected];invs=[r['facts']['inventory'] for r in selected]
    assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone()
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND scheme='wikidata' AND external_id=ANY(%s) LIMIT 1",(qs,)).fetchone()
    assert not db.execute('SELECT 1 FROM artworks WHERE accession_number=ANY(%s) LIMIT 1',(invs,)).fetchone(),'New inventory collision'
    return dict(identity_rows=identity,source_identity_collisions=0,prior_holdings=prior['existing_artworks_linked'])


def prepare():
    assert not PLAN.exists();selected=records();dp,dd=v.validate_plan()
    with m.connect() as db:
        before=w.snapshot(db,dp['scoped_ids']);assert w.counts(db)==dict(linked=145,eligible=142)
        backup=m.BACKUP/(KEY+'-existing-records.json.gz');m.save(backup,dict(at=m.now(),**before))
        files=[Path(__file__).resolve(),Path(v.__file__).resolve(),v.PLAN,REVIEW,IDENTITY,RUN/'new-artwork-identity-refresh-001.json',RUN/'new-artwork-editorial-001.json.gz',RUN/'new-artwork-editorial-002.json.gz']
        files+=sorted((RUN/'new-entities-001').glob('*.gz'))+sorted((RUN/'new-creators-001').glob('*.gz'))
        files+=[RUN/'new-native-objects-002'/(r['facts']['qid']+'.json.gz') for r in selected]
        files+=[m.ROOT/ref['path'] for ref in m.load(REVIEW)['version_sources']]
        plan=dict(at=m.now(),records=selected,before=before,scoped_ids=dp['scoped_ids'],backup_path=str(backup),date_enrichment_plan_sha256=dd,evidence=[reference(p) for p in files],policy='58 native-source paintings with documented collection membership and explicit creation dates through1970. All new records remain review/research candidates with native creator labels, original date precision, physical details and source rights retained. No images, artist links, publication or current-display claims. Existing records unchanged.')
        plan['checks']=preflight(db,plan)
    m.save(PLAN,plan);print('Pinned58newpaintings',hashlib.sha256(PLAN.read_bytes()).hexdigest(),flush=True)


def validate_plan():
    plan=m.load(PLAN)
    for ref in plan['evidence']:checked_reference(ref)
    assert plan['records']==records() and v.validate_plan()[1]==plan['date_enrichment_plan_sha256']
    return plan,hashlib.sha256(PLAN.read_bytes()).hexdigest()


def citation_note(r,digest):
    return json.dumps(dict(plan_sha256=digest,source_record=r,policy='Native Date takes precedence for this new record; secondary dates retained. Exact source rights and provenance retained. Review only, no image download, creator link or current-display claim.'),ensure_ascii=False)


def holding_note(r,digest):return r['facts']['holding_basis']+' '+r['decision']['identity_note']+' Plan SHA-256 '+digest


def assert_new(art,r):
    f=r['facts'];expected=dict(id=r['artwork_id'],slug=r['slug'],title=f['title'],normalized_title=m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions'],accession_number=f['inventory'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],current_institution_id=IID,created_by=m.ACTOR,updated_by=m.ACTOR)
    assert all(art[k]==value for k,value in expected.items()),f['qid']
    for k in ['alternate_title','description_md','primary_media_id','published_at','object_form','cultural_context','creation_place_display','creation_place_unknown_reason','current_location_text','current_location_unknown_reason','location_checked_at']:
        assert art[k] is None,(f['qid'],k)


def verify(db,plan,digest):
    selected=plan['records'];ids=[r['artwork_id'] for r in selected];snapshot=w.snapshot(db,ids)
    assert len(snapshot['artworks'])==58 and len(snapshot['identifiers'])==116 and len(snapshot['citations'])==len(snapshot['assertions'])==58
    assert not snapshot['artists'] and not snapshot['media']
    for r in selected:
        aid=r['artwork_id'];f=r['facts'];rc=r['native']['capture']['receipt'];art=next(x for x in snapshot['artworks'] if x['id']==aid);assert_new(art,r)
        ids_for=[x for x in snapshot['identifiers'] if x['entity_id']==aid];assert len(ids_for)==2
        expected={(SCHEME,f['inventory'],f['source_url']),('wikidata',f['qid'],'https://www.wikidata.org/wiki/'+f['qid'])}
        assert {(x['scheme'],x['external_id'],x['canonical_url']) for x in ids_for}==expected and all(x['source_id']==SID for x in ids_for)
        c=next(x for x in snapshot['citations'] if x['entity_id']==aid);assert c['source_id']==SID and c['field_name']=='museum_expansion_native_metadata' and c['source_record_id']==f['inventory'] and c['source_url']==f['source_url'] and c['evidence_note']==citation_note(r,digest)
        a=next(x for x in snapshot['assertions'] if x['artwork_id']==aid);assert a['source_id']==SID and a['claim_type']=='holding' and a['institution_id']==IID and a['context']=='collection' and a['review_state']=='accepted' and a['superseded_by'] is None and a['source_url']==f['source_url'] and a['evidence_note']==holding_note(r,digest)
        assert not any(a.get(k) for k in ['display_state','gallery','venue_id','effective_from','effective_to'])
    scope=db.execute("SELECT count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n'];assert scope==58
    baseline_unchanged(db,plan)
    return dict(verified_new_records=58,source_inventory_count=58,distinct_creator_labels=len({r['facts']['creator_label'] for r in selected}),existing_artworks_unchanged=242,new_artist_links=0,new_media_links=0,new_published=0,new_display_claims=0,new_identifiers=116,new_citations=58,new_accepted_holdings=58,current_counts=w.counts(db),verified_all_metadata_and_citations=True)


def apply(expected_sha):
    plan,digest=validate_plan();assert digest==expected_sha;selected=plan['records'];ids=[r['artwork_id'] for r in selected]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone();assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432]
        old=db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        if old:
            assert len(old)==58;verify(db,plan,digest);print('Unchanged replay:58records;zero inserts',flush=True);return
        preflight(db,plan);db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,)).fetchone()
        m.save(m.BACKUP/(KEY+'-reviewed-plan.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SOURCE_SLUG,'Government Art Collection selected native paintings,7 October2026','collection_page','https://artcollection.dcms.gov.uk/'))
        for r in selected:
            f=r['facts'];aid=r['artwork_id'];rc=r['native']['capture']['receipt']
            db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,created_by,updated_by)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s)''',(aid,r['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions'],f['inventory'],f['creator_label'],m.ACTOR,m.ACTOR))
            for scheme,external,url in [(SCHEME,f['inventory'],f['source_url']),('wikidata',f['qid'],'https://www.wikidata.org/wiki/'+f['qid'])]:
                db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,scheme,external,url,SID,rc['retrieved_at']))
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_native_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,f['inventory'],f['source_url'],citation_note(r,digest),rc['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,f['source_url'],holding_note(r,digest),rc['retrieved_at']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=203,eligible=200)
    m.save(RUN/(KEY+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=58,local_only=True,verification=result));print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','apply','verify']);p.add_argument('--plan-sha');a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='apply':assert a.plan_sha;apply(a.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
