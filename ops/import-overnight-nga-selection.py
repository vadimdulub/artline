#!/usr/bin/env python3
"""Import reviewed NGA source objects for established artists; both targets stay in review."""
import argparse,collections,importlib.util,json,re,uuid
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('nga',ROOT/'ops/overnight-nga-commons.py');nga=importlib.util.module_from_spec(s);s.loader.exec_module(nga);core=nga.core
RUN=ROOT/'docs/research/overnight-images-20260915/nga-new';BACKUP=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/nga-new';SOURCE='overnight-nga-selected-primary-20260915';REFERENCE_METADATA=None
def uid(oid):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-nga/'+str(oid)))
def norm(v):return nga.norm(v or '')
def source_fields(o):return {k:o.get(k) for k in ('objectid','accessioned','accessionnum','title','displaydate','beginyear','endyear','medium','dimensions','attribution','creditline','classification','isvirtual','wikidataid','parentid','portfolio','series','volume')}
def build(native_ids_only=False):
    if (RUN/'plan.json').exists():return json.loads((RUN/'plan.json').read_text())
    rows=json.loads((RUN/'after-duplicate-review.json').read_text());out=[];held=[];receipts={name:json.loads(((REFERENCE_METADATA or RUN.parent/'nga/metadata')/(name+'.receipt.json')).read_text()) for name in ('objects','constituents','objects_constituents','nga-published-images')}
    with nga.ro('postgres://localhost/artline') as db:
        inst=db.execute("SELECT id::text FROM institutions WHERE slug='national-gallery-of-art' AND status<>'archived'").fetchall();assert len(inst)==1;iid=inst[0]['id']
        prior=db.execute("""SELECT a.id::text,a.accession_number FROM artworks a WHERE a.current_institution_id=%s OR a.id IN
          (SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s) OR a.id IN
          (SELECT entity_id FROM external_identifiers WHERE entity_type='artwork' AND scheme IN ('nga-object','european-nga-object'))""",(iid,iid)).fetchall()
        core.save_new(BACKUP/'local-institution-preimages.json',prior);accessions={norm(x['accession_number']) for x in prior if x['accession_number']};seen=set()
        for row in rows:
            o=row['object'];oid=o['objectid'];acc=norm(o['accessionnum'])
            if not acc or acc in accessions or acc in seen:held.append({'object_id':oid,'reason':'Institution accession collides'});continue
            # Reverse/recto and parent-part works need an object relationship review before creating new top-level catalogue rows.
            if o.get('parentid') or re.search(r'\[(?:reverse|verso|recto)\]',o['title'],re.I):held.append({'object_id':oid,'reason':'Painted side or multipart identity requires relationship review'});continue
            c={'artwork_id':uid(oid),'slug':'night-nga-'+oid,'title':o['title'],'date_display':o['displaydate'],'creation_year_start':row['creation_year_start'],'creation_year_end':row['creation_year_end'],
               'date_precision':row['date_precision'],'work_type':o['classification'].lower(),'accession_number':o['accessionnum'],'external_id':oid,'artist':row['artist']['display_name'],'artist_slug':row['artist']['slug'],
               'artist_authority':row['artist']['external_id'],'artist_qid':row['creator']['wikidataid'],'qid':o['wikidataid'],'popular':row['artist']['popular'],'scheme':'european-nga-object','provider':'night-nga-commons',
               'nga_object':source_fields(o),'creator_record':row['creator'],'creator_relation':row['creator_relation'],'nga_metadata_capture':receipts['objects'],'commons_file':row['commons_file'],'target_ids':{'local':uid(oid)},'primary_media_id':None}
            if native_ids_only:c['qid']=None
            nga.object_match(c,c['nga_object']);out.append(c);seen.add(acc)
    data={'at':core.now(),'records':out,'source_captures':receipts,'held':held,'production_metadata_pending':True,'policy':'Museum object and constituent IDs, current source dates and type, holding, accessions and CC0 donation leads checked. New records remain research candidates in review. No artist biography/country changes.'}
    core.save_new(RUN/'plan.json',data);core.save_new(RUN/'plan-manifest.json',{'sha256':core.sha((RUN/'plan.json').read_bytes()),'count':len(out)});print('NGA final plan',len(out),'popular',sum(c['popular'] for c in out),'types',dict(collections.Counter(c['work_type'] for c in out)),'held',len(held),flush=True);return data

def apply(target,limit):
    data=build();assert core.sha((RUN/'plan.json').read_bytes())==json.loads((RUN/'plan-manifest.json').read_text())['sha256'];records=data['records'][:limit] if limit else data['records'];dsn='postgres://localhost/artline' if target=='local' else core.cloud_dsn();out=[]
    if (RUN/'identity-amendment.json').exists():amendment=json.loads((RUN/'identity-amendment.json').read_text());assert amendment['plan_sha256']==core.sha((RUN/'plan.json').read_bytes())
    else:
        assert all(not c.get('qid') for c in data['records']),'Physical-object cross-references require explicit review'
        amendment={'records':[]}
    shared_qids={r['shared_source_qid'] for r in amendment['records']}
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
        inst=db.execute("SELECT id::text FROM institutions WHERE slug='national-gallery-of-art' AND status<>'archived'").fetchall();assert len(inst)==1;iid=inst[0]['id'];sid=None
        known={r['id']:r for r in db.execute('SELECT id::text,title,status,accession_number,creation_year_start,creation_year_end,date_precision,work_type FROM artworks WHERE id=ANY(%s::uuid[])',([c['artwork_id'] for c in records],)).fetchall()}
        for c in records:
            o=c['nga_object'];nga.object_match(c,o);page='https://purl.org/nga/collection/artobject/'+c['external_id'];public_qid=c['qid'] if c['qid'] not in shared_qids else None
            if c['artwork_id'] in known:
                old=known[c['artwork_id']];assert old['status']=='review' and all(old[k]==c[k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_precision','work_type'))
                out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
            with db.transaction(),db.pipeline():
                db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                artist=db.execute("SELECT a.id::text,a.slug FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme='nga-constituent' AND e.external_id=%s WHERE a.status<>'archived'",(c['artist_authority'],)).fetchall();assert len(artist)==1 and artist[0]['slug']==c['artist_slug']
                old=db.execute('SELECT id::text,title,status,accession_number FROM artworks WHERE id=%s',(c['artwork_id'],)).fetchone()
                if old:
                    assert old['title']==c['title'] and old['status']=='review' and old['accession_number']==c['accession_number'];out.append({'artwork_id':c['artwork_id'],'outcome':'already_present'});continue
                assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme IN ('european-nga-object','nga-object') AND external_id=%s) OR (scheme='wikidata' AND external_id=%s) OR canonical_url=%s)",(c['external_id'],public_qid or None,page)).fetchone(),'Existing authoritative artwork; reconcile first'
                assert not db.execute("SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number=%s",(iid,c['accession_number'])).fetchone(),'Existing museum accession'
                assert not db.execute("SELECT 1 FROM artworks a JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE aa.artist_id=%s AND lower(a.title)=lower(%s) AND NOT EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='european-nga-object')",(artist[0]['id'],c['title'])).fetchone(),'Unresolved same-artist title'
                assert not db.execute("SELECT 1 FROM slug_redirects WHERE entity_type='artwork' AND (old_slug=%s OR entity_id=%s)",(c['slug'],c['artwork_id'])).fetchone()
                if sid is None:
                    db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'National Gallery of Art: selected independently verified works','museum_api','https://github.com/NationalGalleryOfArt/opendata',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,nga.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
                db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,current_institution_id,accession_number,status,research_candidate,created_by,updated_by)
                  VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",(c['artwork_id'],c['slug'],c['title'],norm(c['title']),c['date_display'],c['creation_year_start'],c['creation_year_end'],c['date_precision'],c['work_type'],o['medium'],o['dimensions'],iid,c['accession_number'],core.ACTOR,core.ACTOR))
                db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary','Exact unqualified museum constituent-to-object artist relation; existing artist authority confirmed.')",(c['artwork_id'],artist[0]['id']))
                for scheme,value,url in [('european-nga-object',c['external_id'],page)]+([('wikidata',public_qid,'https://www.wikidata.org/wiki/'+public_qid)] if public_qid else []):
                    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(c['artwork_id'],scheme,value,url,sid,c['nga_metadata_capture']['retrieved_at']))
                db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(c['artwork_id'],iid,sid,page,'Official source identifies an accessioned physical museum object, accession '+c['accession_number']+'. Holding only; no current display claim.',c['nga_metadata_capture']['retrieved_at']))
                evidence={'primary_record':o,'creator_relation':c['creator_relation'],'creator_authority_id':c['artist_authority'],'source_captures':data['source_captures'],'metadata_license':nga.CC0,'date_review':'Original date wording and explicit circa/probably qualifiers retained. Normalized bounds reflect those stated years, not an invented exact year.','object_identity_review':'Separate accessioned physical objects are retained. Shared design/series Wikidata IDs are not used as physical-object identifiers.'}
                db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(c['artwork_id'],sid,c['external_id'],page,json.dumps(evidence,ensure_ascii=False),c['nga_metadata_capture']['retrieved_at'],core.ACTOR));out.append({'artwork_id':c['artwork_id'],'outcome':'inserted'})
            if len(out)%100==0:print(target,len(out),'of',len(records),flush=True)
        verified=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone();assert verified['n']==verified['ok']==len(records)
        path=RUN/(target+'-metadata-verified'+('-canary' if limit else '')+'.json')
        if not path.exists():core.save_new(path,{'at':core.now(),'counts':verified,'records':out})
        print(target,'verified',verified,flush=True)
    if target=='local' and not limit:
        p=RUN/'candidates.json'
        if not p.exists():core.save_new(p,{'created_at':data['at'],'candidates':data['records'],'production_metadata_pending':True})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','apply']);p.add_argument('--target',choices=['local','cloud'],default='local');p.add_argument('--limit',type=int,default=0);p.add_argument('--run',type=Path);p.add_argument('--native-ids-only',action='store_true');p.add_argument('--reference-metadata-dir',type=Path);p.add_argument('--backup-root',type=Path);p.add_argument('--source-slug');a=p.parse_args()
    if a.run:RUN=a.run.resolve();BACKUP=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915'/RUN.name
    if a.reference_metadata_dir:REFERENCE_METADATA=a.reference_metadata_dir.resolve()
    if a.backup_root:
        BACKUP=a.backup_root.resolve()/RUN.name
        assert BACKUP.is_relative_to(Path.home()/'Library/Application Support/Artline/backups'),'Backup root must use the designated recovery directory'
    if a.source_slug:
        assert re.fullmatch(r'[a-z0-9-]+',a.source_slug);SOURCE=a.source_slug
    RUN.mkdir(exist_ok=True);BACKUP.mkdir(parents=True,exist_ok=True);build(a.native_ids_only) if a.phase=='plan' else apply(a.target,a.limit)
