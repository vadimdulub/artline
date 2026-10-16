#!/usr/bin/env python3
"""Reconcile the single visually verified collision from a concurrent Met import.

Keep the original delivery receipts immutable. Archive only this run's duplicate,
retain its evidence, and enrich the museum-backed canonical object reversibly.
"""
import importlib.util,json,shutil
from pathlib import Path
import requests
from psycopg.types.json import Jsonb

sp=importlib.util.spec_from_file_location('delivery','ops/random-ten-twenty-batches-delivery-20261010.py')
d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
r=d.r;m=d.m;RUN=d.RUN
OLD='8fcf768d-d27a-53e9-82e6-987eef8e7e8a'
NEW='3ca0cd37-37ad-5ec4-afc6-54b4731aa9da'
AID='b760025f-c83f-4a54-a0a7-1d403fd10ff3'
MEDIA='f1b45386-437a-53a9-8cd5-e97e0cb2a18f'
MARKER=m.uid('post-delivery-reconciliation/'+OLD)

def snapshot(db):
    result={'records':d.s.snapshots(db,[OLD,NEW])}
    for key,sql in {
      'identifiers':"SELECT to_jsonb(t) value FROM external_identifiers t WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",
      'citations':"SELECT to_jsonb(t) value FROM citations t WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY id",
      'selections':"SELECT to_jsonb(t) value FROM curated_collection_items t WHERE artwork_id=ANY(%s::uuid[]) ORDER BY id",
    }.items():result[key]=[x['value'] for x in db.execute(sql,([OLD,NEW],)).fetchall()]
    result['media']=db.execute('SELECT to_jsonb(t) value FROM media_assets t WHERE id=%s',(MEDIA,)).fetchone()['value']
    result['rights']=[x['value'] for x in db.execute('SELECT to_jsonb(t) value FROM media_rights_evidence t WHERE media_id=%s',(MEDIA,)).fetchall()]
    return result

def main():
    receipt=RUN/'post-delivery-reconciliations.json'
    if not receipt.exists():
        proof=d.ORIGINALS/'reconciliation'/'sentimental-music-met-public-page.png';proof.parent.mkdir(parents=True,exist_ok=True)
        if not proof.exists():shutil.copyfile('/tmp/artline-dove-met-reference.png',proof)
        decision=dict(artist_id=AID,artist='Arthur Dove',batch=6,title='Sentimental Music',archived_artwork_id=OLD,canonical_artwork_id=NEW,media_id=MEDIA,
          confidence=.99,confidence_note='Editorial assessment, not a calibrated probability.',
          basis='Manually compared the approved WikiArt reproduction with the normally displayed Met object-page recto. The distinctive abstract composition, forms, shading and orientation match. Creator, title and 1913/circa 1913 date agree. Met accession 49.70.77a, b records recto and verso; this image depicts the recto, not a separate object or the verso.',
          source_urls=['https://www.metmuseum.org/art/collection/search/488524','https://www.wikiart.org/en/arthur-dove/sentimental-music-1913'],
          visual_evidence_path=str(proof),visual_evidence_sha256=r.sha(proof.read_bytes()),
          source_policy='The Met page was viewed normally for identity evidence. Its restricted reproduction is not used for delivery. The existing approved WikiArt media and actual rights evidence are unchanged.',
          scope='Archive only the duplicate newly created by this operation; keep the existing museum object and all its metadata, holding evidence and review state. Preserve original receipts and archived record evidence; move the WikiArt identifier and personal selection to the canonical object, copy citations, and attach the already verified WikiArt recto image.')
        plan=RUN/'post-delivery-reconciliation-plan.json'
        if not plan.exists():r.save(plan,{'at':r.now(),'decision':decision})
        else:assert r.load(plan)['decision']==decision
        with r.connect('production',readonly=False) as db:
            with db.transaction():
                db.execute("SET LOCAL lock_timeout='120s'")
                db.execute('SELECT pg_advisory_xact_lock(2026100607)')
                db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',([OLD,NEW],)).fetchall()
                db.execute('SELECT id FROM curated_collections WHERE id=%s FOR UPDATE',(m.COLLECTION,)).fetchone()
                existing=db.execute('SELECT after_json FROM audit_log WHERE id=%s',(MARKER,)).fetchone()
                if existing:result=existing['after_json']['receipt']
                else:
                    before=snapshot(db);old=before['records'][OLD];new=before['records'][NEW]
                    assert old['artwork']['status']=='review' and old['artwork']['primary_media_id']==MEDIA
                    assert new['artwork']['status']=='review' and new['artwork']['primary_media_id'] is None
                    assert new['artwork']['accession_number']=='49.70.77a, b'
                    assert new['artwork']['title']==old['artwork']['title']=='Sentimental Music'
                    assert {x['artist_id'] for x in old['creators']}=={x['artist_id'] for x in new['creators']}=={AID}
                    assert not any(x['entity_id']==NEW and x['scheme']=='wikiart-artwork' for x in before['identifiers'])
                    assert len(before['selections'])==1 and before['selections'][0]['artwork_id']==OLD
                    baseline=d.BACKUP/'post-delivery-reconciliation-before.json.gz'
                    if not baseline.exists():r.save_gz(baseline,before)
                    else:assert r.load(baseline)==before
                    assert db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s AND scheme='wikiart-artwork' AND external_id='5772838eedc2cb3880fb29ae'",(NEW,OLD)).rowcount==1
                    for citation in [x for x in before['citations'] if x['entity_id']==OLD]:
                        db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,page_or_locator,evidence_note,retrieved_at,created_by)
                          SELECT %s,entity_type,%s,field_name,source_id,source_record_id,source_url,page_or_locator,evidence_note,retrieved_at,created_by FROM citations WHERE id=%s''',
                          (m.uid('reconciled-citation/'+citation['id']),NEW,citation['id']))
                    db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(NEW,MEDIA,'Recto — WikiArt reproduction'))
                    assert db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(MEDIA,d.ACTOR,NEW)).rowcount==1
                    assert db.execute("UPDATE artworks SET status='archived',revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND status='review'",(d.ACTOR,OLD)).rowcount==1
                    assert db.execute('UPDATE curated_collection_items SET artwork_id=%s WHERE id=%s AND artwork_id=%s',(NEW,before['selections'][0]['id'],OLD)).rowcount==1
                    db.execute('UPDATE curated_collections SET revision=revision+1,updated_at=now() WHERE id=%s',(m.COLLECTION,))
                    for wid in [OLD,NEW]:
                        db.execute('''INSERT INTO citations(id,entity_type,entity_id,field_name,source_id,source_record_id,source_url,evidence_note,retrieved_at,created_by)
                          VALUES(%s,'artwork',%s,'object_identity_reconciliation',%s,'5772838eedc2cb3880fb29ae',%s,%s,now(),%s)''',
                          (m.uid('reconciliation-note/'+wid),wid,m.uid('source/wikiart'),decision['source_urls'][1],json.dumps(decision,ensure_ascii=False),d.ACTOR))
                    after=snapshot(db)
                    for wid,allowed in [(OLD,{'status','revision','updated_at','updated_by'}),(NEW,{'primary_media_id','revision','updated_at','updated_by'})]:
                        assert {k:v for k,v in before['records'][wid]['artwork'].items() if k not in allowed}=={k:v for k,v in after['records'][wid]['artwork'].items() if k not in allowed}
                        for key in ['creators','locations']:assert before['records'][wid][key]==after['records'][wid][key]
                    assert before['media']==after['media'] and before['rights']==after['rights']
                    assert all(x in after['citations'] for x in before['citations'])
                    result=dict(at=r.now(),operation=d.OP,reconciliations=[decision],gross_created=2798,archived_new_duplicates=1,net_new_active_artworks=2797,pictures_added=2818,local_database_changed=False,errors=[])
                    for wid,marker in [(OLD,MARKER),(NEW,m.uid('canonical-reconciliation/'+NEW))]:
                        db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,request_id,before_json,after_json) VALUES(%s,%s,'artist_expansion_duplicate_reconciliation','artwork',%s,%s,%s,%s)",
                          (marker,d.ACTOR,wid,d.OP,Jsonb(before),Jsonb({'receipt':result,'snapshot':after})))
            r.save_gz(d.BACKUP/'post-delivery-reconciliation-after.json.gz',snapshot(db))
        r.save(receipt,result)
    result=r.load(receipt)
    with r.connect('production') as db:
        after=snapshot(db)
        assert after['records'][OLD]['artwork']['status']=='archived'
        assert after['records'][NEW]['artwork']['status']=='review'
        assert after['records'][NEW]['artwork']['primary_media_id']==MEDIA
        assert any(x['entity_id']==NEW and x['scheme']=='wikiart-artwork' for x in after['identifiers'])
        assert any(x['artwork_id']==NEW for x in after['selections'])
        artist=db.execute('SELECT slug FROM artists WHERE id=%s',(AID,)).fetchone()['slug']
    items={};pages=[];params={'limit':50,'image_only':'true'}
    while True:
        response=requests.get('https://artlines.org/api/backend/v1/artists/'+artist+'/works',params=params,timeout=(15,60));response.raise_for_status();body=response.json()
        pages.append(dict(url=response.url,body=body,status=response.status_code))
        items.update({x['id']:x for x in body['items']})
        if not body.get('next_cursor'):break
        assert len(pages)<20
        params['cursor']=body['next_cursor']
    assert OLD not in items and NEW in items
    assert items[NEW]['media_url']==after['media']['storage_path']
    assert items[NEW]['rights_status']==after['media']['rights_status']
    r.save_gz(RUN/'reconciliation-api-verification.json.gz',dict(at=r.now(),pages=pages,canonical_artwork_id=NEW,archived_artwork_id=OLD,errors=[]))
    r.save(RUN/'final-completion-verification.json',dict(at=r.now(),artists=200,batches=20,new_review_records=2797,gross_created_records=2798,archived_duplicate_records=1,pictures_added=2818,original_verification='completion-verification.json',supplemental_verification='reconciliation-api-verification.json.gz',local_database_changed=False,errors=[]))
    print(json.dumps(result))

if __name__=='__main__':main()
