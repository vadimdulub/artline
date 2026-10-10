#!/usr/bin/env python3
"""Seven selected WikiArt catalogue additions; local, review-only and source-pinned."""
import argparse
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-armenia-checkpoint-20261007.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m=c.m;RUN=c.a.RUN;IID=c.a.IID;SOURCE='armenia-wikiart-001';SID=m.uid('source/'+SOURCE)
SOURCE_SLUG='museum-expansion-20261006-'+SOURCE;SCHEME='wikiart-artwork-page'
PLAN=m.RUN/(SOURCE+'-current-plan.json.gz');IDENTITY=RUN/'wikiart-identity-002.json.gz'
SELECTED={1,3,4,5,6,8,12};reference=c.a.reference;checked_reference=c.a.checked_reference

def body(cap):
    raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());rc=cap['receipt']
    assert rc['status']==200 and hashlib.sha256(raw).hexdigest()==rc['sha256']
    assert rc['url']==rc['final_url'] and urlparse(rc['url']).hostname=='www.wikiart.org'
    return raw

def parse(raw):
    soup=BeautifulSoup(raw,'html.parser');heading=soup.h1;assert heading
    artist=heading.parent.select_one('h2 a');assert artist
    locations=[x for x in soup.select('li.dictionary-values-gallery') if x.select_one('s') and x.select_one('s').get_text(strip=True)=='Location:'];assert len(locations)==1
    fields={}
    for li in locations[0].parent.find_all('li',recursive=False):
        key=li.find('s',recursive=False)
        if key:
            label=key.get_text(' ',strip=True);name=label.rstrip(':')
            if name in ['Original Title','Date','Style','Genre','Media','Location','Dimensions','Series']:
                assert name not in fields;fields[name]=li.get_text(' ',strip=True).removeprefix(label).strip()
    assert fields['Location']=='National Gallery of Armenia, Yerevan, Armenia'
    return dict(title=heading.get_text(' ',strip=True),creator=artist.get_text(' ',strip=True),creator_url='https://www.wikiart.org'+artist['href'],fields=fields,canonical_urls=[x['href'] for x in soup.select('link[rel="canonical"]')],rights_labels=[x.get_text(' ',strip=True) for x in soup.select('a.copyright')])

def creation_date(value):
    literal=(value or '').split(';')[0].strip()
    match=re.fullmatch(r'(c\.\s*)?(\d{4})(?:\s*[-–]\s*(\d{4}))?',literal)
    assert match,'Unreviewed creation statement'
    first=int(match[2]);last=int(match[3] or match[2]);assert 100<=first<=last<=1970
    assert not (match[1] and last>=1970),'Cutoff-adjacent circa date requires review'
    return literal,first,last,('circa' if first==last else 'circa_range') if match[1] else ('exact' if first==last else 'range')

def facts(parsed,url):
    assert parsed['canonical_urls']==[url]
    assert parsed['creator_url']==url.rsplit('/',1)[0]
    date,first,last,precision=creation_date(parsed['fields'].get('Date'))
    medium=parsed['fields'].get('Media');genre=parsed['fields'].get('Genre','')
    kind='painting' if (medium and 'oil' in medium.split()) or 'painting' in genre else 'unknown'
    return dict(title=parsed['title'],creator_label=parsed['creator'],date_display=date,first=first,last=last,date_precision=precision,work_type=kind,medium=medium,dimensions=parsed['fields'].get('Dimensions'),accession=None,source_url=url,holding_basis='Selected user-approved WikiArt object page explicitly labels National Gallery of Armenia, Yerevan, Armenia. Creator, literal title and full creation statement reviewed against existing artist-scoped catalogue records. Editorial museum confidence 0.90 (not a calibrated probability). Collection association only; source label does not establish legal ownership, physical custody or current display.')

def current_identity(db):
    names=sorted({r['creator'] for r in m.load(RUN/'wikiart-object-fields-001.json')['objects']});keys=[m.norm(n) for n in names]
    artists=db.execute('SELECT id::text,display_name,normalized_name,slug FROM artists WHERE normalized_name=ANY(%s) ORDER BY id',(keys,)).fetchall()
    aliases=db.execute('SELECT aa.artist_id::text,aa.alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) ORDER BY aa.artist_id,aa.alias',(keys,)).fetchall()
    ids=sorted({x['id'] for x in artists}|{x['artist_id'] for x in aliases})
    rows=db.execute('''SELECT a.id::text,a.title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.accession_number,a.current_institution_id::text,a.medium_text,a.dimensions_text,a.work_type,a.unlinked_creator_label,
 ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
 ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
 FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) scoped JOIN artworks a ON a.id=scoped.artwork_id ORDER BY a.id''',(ids,)).fetchall()
    unlinked=db.execute('''SELECT id::text,title,alternate_title,date_display,creation_year_start,creation_year_end,date_precision,accession_number,current_institution_id::text,medium_text,dimensions_text,work_type,unlinked_creator_label FROM artworks WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY id''',(['%aivazov%','%айвазов%','%Այվազով%','%sureni%','%сурен%','%Սուրեն%','%vereshch%','%верещ%','%cossiers%','%levitan%','%левитан%','%roerich%','%рерих%'],)).fetchall()
    return dict(artists=artists,aliases=aliases,linked=rows,unlinked=unlinked)

def baseline_unchanged(db):
    baseline=m.load(RUN/(SOURCE+'-before.json'));backup=m.load(Path(baseline['backup_path']));ids=baseline['scoped_ids']
    arts=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
    cites=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
    inst=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(IID,)).fetchone()['row']
    assert arts==backup['artworks'] and cites==backup['citations'] and inst==backup['museum'],'Baseline changed'
    prior,digest=c.a.validate_plan();c.verify_prior_additions(db,prior,digest)
    return dict(existing_artworks_unchanged=len(arts),complete_citations_unchanged=len(cites),institution_unchanged=True)

def records():
    review=m.load(RUN/'wikiart-followup-review-001.json');museum=m.load(RUN/'armenia-001-before.json')['museum'];out=[]
    for row in review['records']:
        if row['number'] not in SELECTED:continue
        obj=row['source'];cap=obj['capture'];parsed=parse(body(cap));assert parsed['title']==obj['title'] and parsed['creator']==obj['creator'] and parsed['fields']==obj['fields']
        assert row['state']=='candidate_pending_final_review'
        oid=urlparse(obj['source_url']).path.removeprefix('/en/');f=facts(parsed,obj['source_url'])
        out.append(dict(source_record_id=oid,museum=museum,facts=f,source_receipt=cap['receipt'],body_path=cap['body_path'],artwork_id=m.uid(SOURCE+'/'+oid),slug='museum-expansion-'+SOURCE+'-'+hashlib.sha256(oid.encode()).hexdigest()[:20],raw_source_record=dict(queue_number=row['number'],parsed=parsed,editorial_note=row['note'],final_decision='approved_review_only_addition',unknown_policy='Unknown accessions, media and dimensions retained. Genre cityscape alone does not establish a physical work type. No painter link inferred from same-name database identities.',rights_policy='Actual page rights labels retained; no image requested. WikiArt accepted under user instruction.')))
    assert len(out)==7 and len({r['source_record_id'] for r in out})==7
    return out

def validate(plan):
    for ref in plan['evidence']:checked_reference(ref)
    assert plan['records']==records();return plan

def validate_plan():return validate(m.load(PLAN)),hashlib.sha256(PLAN.read_bytes()).hexdigest()

def preflight(db,plan):
    checks=baseline_unchanged(db);expected=m.load(checked_reference(plan['identity_snapshot']));actual=current_identity(db)
    for key,rows in actual.items():assert rows==expected[key],'Identity scope changed: '+key
    ids=[r['artwork_id'] for r in plan['records']];urls=[r['facts']['source_url'] for r in plan['records']]
    assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[]) LIMIT 1',(ids,)).fetchone()
    assert not db.execute('SELECT 1 FROM sources WHERE id=%s OR slug=%s',(SID,SOURCE_SLUG)).fetchone()
    assert not db.execute("SELECT 1 FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) LIMIT 1",(urls,)).fetchone()
    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s) LIMIT 1",(urls,)).fetchone()
    keys=sorted({m.norm(t) for r in plan['records'] for t in [r['facts']['title'],r['raw_source_record']['parsed']['fields'].get('Original Title')] if t})
    assert not db.execute('SELECT 1 FROM artworks WHERE normalized_title=ANY(%s) LIMIT 1',(keys,)).fetchone(),'New exact-title lead'
    return dict(**checks,identity_rows={k:len(v) for k,v in actual.items()},eligible_records=7,source_identity_collisions=0)

def prepare():
    assert not PLAN.exists();selected=records()
    with m.connect() as db:
        snapshot=current_identity(db);m.save(IDENTITY,dict(at=m.now(),**snapshot))
        old=m.load(RUN/'wikiart-identity-001.json.gz')
        # Only the known holding reconciliation may have changed this pool.
        assert snapshot['artists']==old['artists'] and snapshot['aliases']==old['aliases'] and snapshot['unlinked']==old['unlinked']
        oldrows={r['id']:r for r in old['linked']};assert set(oldrows)=={r['id'] for r in snapshot['linked']}
        allowed={r['facts']['artwork_id'] for r in c.h.validate_plan()[0]['records']}
        for row in snapshot['linked']:
            ignored={'current_institution_id','source_urls'} if row['id'] in allowed else set()
            assert {k:v for k,v in row.items() if k not in ignored}=={k:v for k,v in oldrows[row['id']].items() if k not in ignored}
        ids=sorted(set(m.load(RUN/'armenia-001-before.json')['scoped_ids'])|{r['artwork_id'] for r in c.a.validate_plan()[0]['records']})
        backup=m.BACKUP/(SOURCE+'-existing-records.json.gz')
        arts=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY id',(ids,)).fetchall()
        cites=db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(ids,)).fetchall()
        museum=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s',(IID,)).fetchone()['row']
        m.save(backup,dict(at=m.now(),artworks=arts,citations=cites,museum=museum))
        m.save(RUN/(SOURCE+'-before.json'),dict(at=m.now(),scoped_ids=ids,backup_path=str(backup)))
        refs=[reference(RUN/f) for f in ['wikiart-object-fields-001.json','wikiart-followup-review-001.json','wikiart-identity-001.json.gz','wikiart-identity-002.json.gz','wikiart-comparison-001.json.gz']]
        plan=dict(at=m.now(),records=selected,held=[r for r in m.load(RUN/'wikiart-followup-review-001.json')['records'] if r['number'] not in SELECTED],evidence=refs,identity_snapshot=reference(IDENTITY),policy='Seven user-approved WikiArt metadata additions in local review. Preserve full literal dates, unknown fields, source original titles and rights labels. No existing metadata, painter links, images, display or publication changes.')
        validate(plan);checks=preflight(db,plan)
    m.save(PLAN,plan);digest=hashlib.sha256(PLAN.read_bytes()).hexdigest();m.save(RUN/(SOURCE+'-preflight.json'),dict(at=m.now(),plan_sha256=digest,**checks))
    print('Pinned seven additions:',digest,flush=True)


FIELDS={'title':'title','normalized_title':None,'date_display':'date_display','creation_year_start':'first','creation_year_end':'last','date_precision':'date_precision','work_type':'work_type','medium_text':'medium','dimensions_text':'dimensions','accession_number':'accession','unlinked_creator_label':'creator_label','object_form':'object_form','cultural_context':'cultural_context'}


def verify(db,plan,digest):
    records=plan['records'];ids=[r['artwork_id'] for r in records]
    actual={r['id']:r for r in db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=ANY(%s::uuid[])',(ids,)) for r in [r['row']]}
    assert len(actual)==len(records)
    citations=db.execute("SELECT entity_id::text,source_id::text,field_name,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
    external=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url,source_id::text FROM external_identifiers WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
    locations=db.execute('SELECT artwork_id::text,claim_type,institution_id::text,context,source_id::text,source_url,evidence_note,review_state,superseded_by FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchall()
    assert len(citations)==len(external)==len(locations)==len(records)
    by_c={r['entity_id']:r for r in citations};by_e={r['entity_id']:r for r in external};by_l={r['artwork_id']:r for r in locations}
    assert len(by_c)==len(by_e)==len(by_l)==len(records)
    for r in records:
        aid=r['artwork_id'];a=actual[aid];f=r['facts'];c=by_c[aid];e=by_e[aid];l=by_l[aid]
        for column,key in FIELDS.items():assert a[column]==(f.get(key) if key else m.norm(f['title'])),(aid,column)
        assert a['slug']==r['slug'] and a['status']=='review' and a['research_candidate'] and a['current_institution_id']==IID
        assert a['primary_media_id'] is None and a['published_at'] is None
        assert c['source_id']==e['source_id']==l['source_id']==SID
        assert c['source_record_id']==e['external_id']==r['source_record_id'] and e['scheme']==SCHEME
        assert c['source_url']==e['canonical_url']==l['source_url']==f['source_url']
        assert c['field_name']=='museum_expansion_wikiart_metadata'
        note=json.loads(c['evidence_note']);assert note['plan_sha256']==digest and note['raw_source_record']==r['raw_source_record'] and note['source_receipt']==r['source_receipt'] and note['body_path']==r['body_path']
        assert l['claim_type']=='holding' and l['institution_id']==IID and l['context']=='collection' and l['review_state']=='accepted' and l['superseded_by'] is None
        assert l['evidence_note']==f['holding_basis']+' Source capture SHA-256 '+r['source_receipt']['sha256']+'.'
    assert db.execute('SELECT count(*) n FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
    assert db.execute('SELECT count(*) n FROM artwork_media WHERE artwork_id=ANY(%s::uuid[])',(ids,)).fetchone()['n']==0
    scope=db.execute("SELECT count(*) n FROM artworks a WHERE id=ANY(%s::uuid[]) AND artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible' AND artline_has_selection_evidence(id)",(ids,)).fetchone()['n'];assert scope==len(records)
    baseline=baseline_unchanged(db)
    counts=db.execute("SELECT count(*) linked,count(*) FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible') eligible FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(IID,)).fetchone()
    return dict(**baseline,verified_new_records=len(records),current_counts=counts,distinct_source_entries=len({r['source_record_id'] for r in records}),source_inventory_count=sum(r['facts']['accession'] is not None for r in records),work_types=dict(collections.Counter(r['facts']['work_type'] for r in records)),new_artist_links=0,new_media_links=0,new_published=0,new_display_claims=0,verified_all_metadata_and_citations=True)


def apply(expected_sha):
    plan,digest=validate_plan();assert digest==expected_sha,'Plan digest changed';records=plan['records'];ids=[r['artwork_id'] for r in records]
    with m.psycopg.connect('postgresql://localhost/artline',autocommit=True,row_factory=m.dict_row,options='-c timezone=UTC -c statement_timeout=180000') as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='5s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        target=db.execute('SELECT current_database() db,host(inet_server_addr()) addr,inet_server_port() port').fetchone()
        assert target['db']=='artline' and target['addr'] in [None,'127.0.0.1','::1'] and target['port'] in [None,5432],'Only the local catalogue is allowed'
        old=db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchall()
        if old:
            assert len(old)==len(records),'Partial batch requires review';result=verify(db,plan,digest)
            print('Unchanged replay:',result['verified_new_records'],'records; zero inserts',flush=True);return
        checks=preflight(db,plan)
        db.execute('SELECT id FROM institutions WHERE id=%s FOR SHARE',(IID,)).fetchone()
        backup=m.BACKUP/(SOURCE+'-preimages.json.gz')
        if backup.exists():assert m.load(backup)['plan_sha256']==digest
        else:m.save(backup,dict(at=m.now(),plan_sha256=digest,new_artwork_ids=ids,existing_new_ids=old,checks=checks,baseline_backup=m.load(RUN/(SOURCE+'-before.json'))['backup_path']))
        m.save(m.BACKUP/(SOURCE+'-reviewed-plan.json.gz'),plan)
        db.execute('INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,%s,%s)',(SID,SOURCE_SLUG,'Museum expansion — reviewed WikiArt National Gallery of Armenia records, 7 October 2026','authority_data','https://www.wikiart.org/'))
        for r in records:
            f=r['facts'];aid=r['artwork_id'];rc=r['source_receipt']
            db.execute('''INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,
              work_type,medium_text,dimensions_text,accession_number,status,research_candidate,unlinked_creator_label,object_form,cultural_context,created_by,updated_by)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s,%s,%s,%s)''',
              (aid,r['slug'],f['title'],m.norm(f['title']),f['date_display'],f['first'],f['last'],f['date_precision'],f['work_type'],f['medium'],f['dimensions'],f['accession'],f['creator_label'],f.get('object_form'),f.get('cultural_context'),m.ACTOR,m.ACTOR))
            db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,SCHEME,r['source_record_id'],f['source_url'],SID,rc['retrieved_at']))
            note=dict(plan_sha256=digest,raw_source_record=r['raw_source_record'],source_receipt=rc,body_path=r['body_path'],policy=plan['policy'])
            db.execute("INSERT INTO citations(entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,'museum_expansion_wikiart_metadata',%s,%s,%s,%s,%s,%s)",(aid,SID,r['source_record_id'],f['source_url'],json.dumps(note,ensure_ascii=False),rc['retrieved_at'],m.ACTOR))
            db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(aid,IID,SID,f['source_url'],f['holding_basis']+' Source capture SHA-256 '+rc['sha256']+'.',rc['retrieved_at']))
        result=verify(db,plan,digest);assert result['current_counts']==dict(linked=184,eligible=183)
    m.save(m.RUN/(SOURCE+'-applied.json'),dict(at=m.now(),plan_sha256=digest,created=len(records),museums=1,local_only=True,images_added=0,published=0,verification=result))
    m.save(RUN/(SOURCE+'-verification.json'),dict(at=m.now(),plan_sha256=digest,**result))
    print('Added',len(records),'review artworks; Armenia now',result['current_counts'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare','apply','verify']);parser.add_argument('--plan-sha');args=parser.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='apply':assert args.plan_sha;apply(args.plan_sha)
    else:
        plan,digest=validate_plan()
        with m.connect() as db:print(json.dumps(verify(db,plan,digest)),flush=True)
