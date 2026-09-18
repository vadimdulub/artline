#!/usr/bin/env python3
"""Import five individually reviewed, source-verified museum paintings in review."""
import argparse,csv,importlib.util,json,re,unicodedata,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('core',ROOT/'ops/enrich-artwork-images.py');core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
RUN=ROOT/'docs/research/overnight-images-20260915/new-primary-works';BACKUP=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/new-primary-works';SOURCE='overnight-selected-primary-20260915'
CC0='https://creativecommons.org/publicdomain/zero/1.0/'
ARTISTS={'573':('Q150679','anthony-van-dyck-q150679'),'41590':('Q8459','giorgione-q8459'),'43721':('Q5599','peter-paul-rubens-q5599'),'71349':('Q5599','peter-paul-rubens-q5599')}
def norm(v):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',v.casefold())))
def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/overnight-verified-primary/'+key))
def plan():
    path=RUN/'plan.json'
    if path.exists():return json.loads(path.read_text())
    prior=json.loads((ROOT/'docs/chat_gpt_out/review-20260915/selected_official_records.json').read_text());receipt=json.loads((RUN.parent/'nga/metadata/objects.receipt.json').read_text())
    with (RUN.parent/'nga/metadata/objects.csv').open() as f:objects={o['objectid']:o for o in csv.DictReader(f) if o['objectid'] in ARTISTS}
    rows=[]
    for oid,(aqid,slug) in ARTISTS.items():
        o=objects[oid];old=next(x for x in prior['objects'] if x['objectid']==oid)
        assert all(o[k]==old[k] for k in ('title','attribution','accessionnum','displaydate','beginyear','endyear','wikidataid'))
        person=next(x for x in prior['constituents'] if x['wikidataid']==aqid)
        assert person['forwarddisplayname']==o['attribution'] and o['accessioned']=='1' and o['isvirtual']=='0' and o['classification']=='Painting'
        lo,hi=int(o['beginyear']),int(o['endyear']);assert 1000<=lo<=hi<=1970
        rows.append({'key':'nga-'+oid,'provider':'nga','scheme':'european-nga-object','object_id':oid,'qid':o['wikidataid'],'artist_qid':aqid,'artist_slug':slug,
          'title':o['title'],'date_display':o['displaydate'],'creation_year_start':lo,'creation_year_end':hi,'date_precision':'circa' if lo==hi else 'circa_range',
          'medium':o['medium'],'dimensions':o['dimensions'],'accession':o['accessionnum'],'institution_slug':'national-gallery-of-art','object_url':'https://purl.org/nga/collection/artobject/'+oid,
          'source_record':o,'metadata_receipt':receipt,'review_note':'Museum-provided normalized indexing bounds retained as approximate, never exact. Original qualified date wording remains unchanged. '+('Initial creation and probable later reworking are explicitly distinct stages in date_display; the broad bounds cover both stages and do not claim continuous execution.' if oid=='71349' else 'The source says probably; this uncertainty remains explicit and the record is not published.')})
    f=core.Fetcher(RUN/'metadata');url='https://collectionapi.metmuseum.org/public/collection/v1/objects/438028';o=f.metadata(url);assert o['objectID']==438028 and o['artistWikidata_URL']=='https://www.wikidata.org/wiki/Q192488' and o['objectWikidata_URL']=='https://www.wikidata.org/wiki/Q19904862' and o['accessionNumber']=='1997.117.9' and o['isPublicDomain'] is True and o['objectDate']=='probably mid-1450s'
    assert (o['objectBeginDate'],o['objectEndDate'])==(1453,1457)
    rows.append({'key':'met-438028','provider':'met','scheme':'met-object','object_id':'438028','qid':'Q19904862','artist_qid':'Q192488','artist_slug':'paolo-uccello-q192488','title':o['title'],
      'date_display':o['objectDate'],'creation_year_start':1453,'creation_year_end':1457,'date_precision':'circa_range','medium':o['medium'],'dimensions':o['dimensions'],'accession':o['accessionNumber'],
      'institution_slug':'the-met','object_url':o['objectURL'],'source_record':o,'metadata_receipt':json.loads((f.cache/(core.sha(url.encode())+'.receipt.json')).read_text()),
      'review_note':'The complete triptych was visually reviewed. Probably mid-1450s stays explicit; approximate 1453–1457 bounds come directly from the museum API, not an inferred exact date. All three panels remain a single museum object.'})
    dsn=core.cloud_dsn();targets={}
    for target,conn in [('local','postgres://localhost/artline'),('cloud',dsn)]:
        with psycopg.connect(conn,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
            details={}
            for c in rows:
                ar=db.execute("SELECT a.id::text,a.slug,a.display_name FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='wikidata' AND e.external_id=%s WHERE a.status='review'",(c['artist_qid'],)).fetchall();assert len(ar)==1 and ar[0]['slug']==c['artist_slug']
                inst=db.execute("SELECT id::text,slug FROM institutions WHERE slug=%s AND status<>'archived'",(c['institution_slug'],)).fetchone();assert inst
                collisions=db.execute("SELECT e.scheme,e.external_id,e.entity_id::text FROM external_identifiers e WHERE e.entity_type='artwork' AND ((e.scheme=ANY(%s) AND e.external_id=%s) OR (e.scheme='wikidata' AND e.external_id=%s))",(['european-nga-object','nga-object'] if c['provider']=='nga' else ['met-object','european-met-the-met-object'],c['object_id'],c['qid'])).fetchall();assert not collisions,(c['key'],'Existing authoritative object')
                peers=db.execute("""SELECT to_jsonb(a) artwork FROM artworks a WHERE (a.current_institution_id=%s AND regexp_replace(coalesce(a.accession_number,''),'\\s+','','g')=%s) OR (a.id IN (SELECT artwork_id FROM artwork_artists WHERE artist_id=%s) AND lower(a.title)=lower(%s))""",(inst['id'],re.sub(r'\s+','',c['accession']),ar[0]['id'],c['title'])).fetchall()
                assert not peers,(c['key'],'Title or accession collision requires object review')
                details[c['key']]={'artist':ar[0],'institution':inst,'artwork_id':uid(c['key'])}
            core.save_new(BACKUP/(target+'-preimages.json'),details);targets[target]=details
    data={'at':core.now(),'records':rows,'targets':targets,'policy':'Source-backed uncertain bounds are approximate; all records remain research candidates in review; no artist facts or current display claims are changed.'}
    core.save_new(path,data);core.save_new(RUN/'manifest.json',{'plan_sha256':core.sha(path.read_bytes()),'new_artworks':len(rows),'status':'review'});return data

def apply(local_only=False):
    data=plan();raw=(RUN/'plan.json').read_bytes();pin=core.sha(raw);assert pin==json.loads((RUN/'manifest.json').read_text())['plan_sha256'];dsn=None if local_only else core.cloud_dsn()
    for target,conn in ([('local','postgres://localhost/artline')] if local_only else [('local','postgres://localhost/artline'),('cloud',dsn)]):
        with psycopg.connect(conn,row_factory=dict_row) as db:
            for c in data['records']:
                t=data['targets'][target][c['key']];aid=t['artwork_id']
                with db.transaction():
                    db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                    if db.execute('SELECT 1 FROM artworks WHERE id=%s',(aid,)).fetchone():continue
                    assert not db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artwork' AND (old_slug=%s OR entity_id=%s)",('night-primary-'+c['key'],aid)).fetchone()
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme=%s AND external_id=%s) OR (scheme='wikidata' AND external_id=%s))",(c['scheme'],c['object_id'],c['qid'])).fetchone()
                    source_slug=SOURCE+'-'+c['provider']
                    source_name='National Gallery of Art: individually reviewed paintings' if c['provider']=='nga' else 'Metropolitan Museum of Art: individually reviewed paintings'
                    base_url='https://www.nga.gov/' if c['provider']=='nga' else 'https://collectionapi.metmuseum.org/'
                    db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,%s,'museum_api',%s,%s) ON CONFLICT(slug) DO NOTHING",(source_slug,source_name,base_url,CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(source_slug,)).fetchone()['id']
                    db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
                      VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'painting',%s,%s,%s,%s,'review',true,%s,%s)""",(aid,'night-primary-'+c['key'],c['title'],norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['medium'],c['dimensions'],t['institution']['id'],c['accession'],core.ACTOR,core.ACTOR))
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Exact primary museum artist attribution and established authority; no biography changes.')",(aid,t['artist']['id']))
                    db.execute("""INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state)
                      VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')""",(aid,t['institution']['id'],sid,c['object_url'],'Physical museum object and inventory '+c['accession']+' verified at the primary source. Holding only; current display not asserted.',c['metadata_receipt']['retrieved_at']))
                    for scheme,value,url in [(c['scheme'],c['object_id'],c['object_url']),('wikidata',c['qid'],'https://www.wikidata.org/wiki/'+c['qid'])]:
                        db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(aid,scheme,value,url,sid,c['metadata_receipt']['retrieved_at']))
                    db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(aid,sid,c['object_id'],c['object_url'],json.dumps({'plan_sha256':pin,'primary_record':c['source_record'],'capture':c['metadata_receipt'],'date_review':c['review_note'],'metadata_license':CC0},ensure_ascii=False),c['metadata_receipt']['retrieved_at'],core.ACTOR))
            with db.transaction():
                db.execute('SET TRANSACTION READ ONLY');out=[]
                for c in data['records']:
                    aid=data['targets'][target][c['key']]['artwork_id'];a=db.execute('SELECT id::text,title,date_display,creation_year_start,creation_year_end,date_precision,status,research_candidate,published_at,artline_has_selection_evidence(id) selected FROM artworks WHERE id=%s',(aid,)).fetchone();assert a['status']=='review' and a['published_at'] is None and a['selected'] and a['research_candidate'];assert all(a[k]==c[k] for k in ('title','date_display','creation_year_start','creation_year_end','date_precision'));out.append(a)
                report_path=RUN/(target+'-metadata-verified.json')
                if not report_path.exists():core.save_new(report_path,{'at':core.now(),'new_artworks':len(out),'records':out})
                print(target,'verified new artworks',len(out),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--local-only',action='store_true');a=p.parse_args();RUN.mkdir(parents=True,exist_ok=True);BACKUP.mkdir(parents=True,exist_ok=True);plan() if a.phase=='plan' else apply(a.local_only)
