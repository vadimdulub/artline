#!/usr/bin/env python3
"""Add two independently documented Byzantine fresco fragments, without invented artists."""
import importlib.util,json,re,shutil,uuid
from pathlib import Path
from urllib.parse import urlparse
import psycopg
from psycopg.rows import dict_row
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'docs/research/overnight-images-20260915/met-priority-frescoes'
s=importlib.util.spec_from_file_location('campaign',ROOT/'ops/overnight-image-campaign.py');campaign=importlib.util.module_from_spec(s);s.loader.exec_module(campaign);core=campaign.core
SOURCE='overnight-met-byzantine-frescoes-20260915';IDS=('473058','473161')

def main():
    records=[]
    for oid in IDS:
        o=json.loads((RUN/(oid+'.json')).read_text());assert str(o['objectID'])==oid and o['culture']=='Byzantine' and o['medium']=='Fresco' and o['classification']=='Paintings-Fresco'
        assert o['isPublicDomain'] is True and not o['rightsAndReproduction'] and not o['artistDisplayName'] and not o['artistWikidata_URL']
        assert o['objectDate']=='12th century, modern restoration' and (o['objectBeginDate'],o['objectEndDate'])==(1100,1200)
        assert urlparse(o['primaryImageSmall']).hostname=='images.metmuseum.org' and o['repository']=='Metropolitan Museum of Art, New York, NY'
        aid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/night-selected-met/'+oid));url='https://collectionapi.metmuseum.org/public/collection/v1/objects/'+oid;capture=json.loads((RUN/'metadata'/(core.sha(url.encode())+'.receipt.json')).read_text())
        records.append({'artwork_id':aid,'slug':'night-met-'+oid,'external_id':oid,'scheme':'met-object','provider':'met','title':o['title'],
          'creation_year_start':1100,'creation_year_end':1200,'date_precision':'century','date_display':o['objectDate'],'work_type':'fresco','accession_number':o['accessionNumber'],
          'artist':'Unidentified painter (Byzantine)','popular':False,'priority_tradition':True,'page':o['objectURL'],'target_ids':{'local':aid,'cloud':aid},'object':o,'metadata_capture':capture})
    plan=RUN/'plan.json'
    if not plan.exists():core.save_new(plan,{'records':records,'policy':'Museum dates the original fresco fragments to the twelfth century and explicitly notes modern restoration. Retain that wording and century precision. Anonymous creator labels and Byzantine cultural context are supported without creating a fictional painter or inferring a modern nationality. Records stay in review.'})
    backup=Path.home()/'Library/Application Support/Artline/backups/overnight-images-20260915/met-priority-frescoes';out=[]
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:
        with psycopg.connect(dsn,autocommit=True,row_factory=dict_row) as db:
            iid=db.execute("SELECT id FROM institutions WHERE slug='the-met' AND status<>'archived'").fetchone()['id']
            before=backup/(target+'-before.json')
            if not before.exists():core.save_new(before,db.execute('SELECT to_jsonb(a) artwork FROM artworks a WHERE id=ANY(%s::uuid[])',([c['artwork_id'] for c in records],)).fetchall())
            for c in records:
                o=c['object'];checked=c['metadata_capture']['retrieved_at']
                with db.transaction(),db.pipeline():
                    db.execute('SELECT pg_advisory_xact_lock(559220260915)')
                    old=db.execute('SELECT id,title,status,unlinked_creator_label,cultural_context,work_type FROM artworks WHERE id=%s',(c['artwork_id'],)).fetchone()
                    if old:
                        assert old['title']==c['title'] and old['status']=='review' and old['unlinked_creator_label']=='Unidentified painter' and old['cultural_context']=='Byzantine' and old['work_type']=='fresco';continue
                    assert not db.execute("SELECT 1 FROM external_identifiers WHERE entity_type='artwork' AND ((scheme IN ('met-object','european-met-the-met-object') AND external_id=%s) OR (scheme='wikidata' AND external_id=%s) OR canonical_url=%s)",(c['external_id'],o['objectWikidata_URL'].rsplit('/',1)[-1],c['page'])).fetchone(),'Existing source identity requires reconciliation'
                    assert not db.execute("SELECT 1 FROM artworks WHERE current_institution_id=%s AND (accession_number=%s OR lower(title)=lower(%s))",(iid,c['accession_number'],c['title'])).fetchone(),'Existing museum accession or exact title requires review'
                    db.execute("INSERT INTO sources(slug,name,source_type,base_url,terms_url) VALUES(%s,'Metropolitan Museum: independently documented Byzantine fresco fragments','museum_api','https://collectionapi.metmuseum.org',%s) ON CONFLICT(slug) DO NOTHING",(SOURCE,campaign.CC0));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
                    db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,current_institution_id,accession_number,unlinked_creator_label,cultural_context,status,research_candidate,created_by,updated_by)
                      VALUES(%s,%s,%s,%s,%s,1100,1200,'century','fresco',%s,%s,%s,%s,'Unidentified painter','Byzantine','review',true,%s,%s)""",(c['artwork_id'],c['slug'],c['title'],' '.join(re.findall(r'\w+',c['title'].casefold())),c['date_display'],o['medium'],o['dimensions'],iid,c['accession_number'],core.ACTOR,core.ACTOR))
                    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,'met-object',%s,%s,%s,%s)",(c['artwork_id'],c['external_id'],c['page'],sid,checked))
                    db.execute("INSERT INTO artwork_location_assertions(artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(c['artwork_id'],iid,sid,c['page'],'Official Met repository, museum accession and gift credit establish collection holding; no current display claim.',checked))
                    evidence={'source_fields':{k:o.get(k) for k in ('objectID','objectURL','title','objectDate','objectBeginDate','objectEndDate','culture','classification','medium','dimensions','accessionNumber','repository','creditLine','artistDisplayName')},'metadata_capture':c['metadata_capture'],'metadata_license':campaign.CC0,'editorial_note':'Original twelfth-century creation and modern restoration are distinguished. Creator remains unidentified; Byzantine is cultural context, not inferred modern nationality.'}
                    db.execute("INSERT INTO citations(entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES('artwork',%s,%s,'official_object_identity',%s,%s,%s,%s,%s)",(c['artwork_id'],sid,c['external_id'],c['page'],json.dumps(evidence,ensure_ascii=False),checked,core.ACTOR))
            checked=db.execute("SELECT count(*) n,count(*) FILTER(WHERE status='review' AND published_at IS NULL AND research_candidate AND artline_has_selection_evidence(id)) ok FROM artworks WHERE id=ANY(%s::uuid[])",([c['artwork_id'] for c in records],)).fetchone();assert checked['n']==checked['ok']==2
            out.append({'target':target,'verified_records':2});print(target,'Byzantine fresco metadata verified',flush=True)
    path=RUN/'metadata-verified.json'
    if not path.exists():core.save_new(path,out)
    candidates=[{k:v for k,v in c.items() if k not in ('object','metadata_capture')} for c in records]
    core.save_new(RUN/'candidates.json',{'created_at':records[0]['metadata_capture']['retrieved_at'],'candidates':candidates})
    core.save_new(RUN/'backups.json',(RUN.parent/'backups.json').read_bytes())
    for c in records:
        key=core.sha(('https://collectionapi.metmuseum.org/public/collection/v1/objects/'+c['external_id']).encode())
        for suffix in ('.json','.receipt.json'):core.save_new(RUN/'metadata/met'/(key+suffix),(RUN/'metadata'/(key+suffix)).read_bytes())

if __name__=='__main__':main()
