#!/usr/bin/env python3
"""Individually reviewed painting duplicates; retain original catalogue records."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('im',Path(__file__).with_name('million-nga-images-20261010.py'));im=importlib.util.module_from_spec(s);s.loader.exec_module(im)
n=im.n;m=n.m;d=im.d
PAIRS=[('27febc66-2287-5d8f-b287-42f105767162','ebfed71f-664e-5f17-ba32-2b4450eaa613'),('8b19f0ac-c58c-5eb7-a276-57bbae0ac0cc','b0f2bae5-d818-5cb9-9b35-557e4e98357f'),('d2d65d02-58de-5b92-b31b-acbcf0fce5fd','722f3882-cb8d-541d-8f61-93f1380c011b'),('23ac0a98-3566-5867-b568-b8fde2517148','59c6610a-50b4-51e1-a199-f6a25310f52b')]
def reconcile():
    receipt=n.RUN/'duplicate-reconciliation.json'
    if receipt.exists():return
    rows={r['artwork_id']:r for r in m.load(n.RUN/n.PLAN)['new_artworks']};ids=[x for pair in PAIRS for x in pair]
    with m.m.connect() as db:before=d.snapshot(db,ids)
    decision=dict(at=m.now(),pairs=PAIRS,before=before,basis='Individual visual comparison of full NGA and existing reproductions, matching subject, poses, architectural details, native object identities and current WikiArt creator/object pages. Four unique paintings, not separate print impressions, casts or physical copies. Original catalogue dates, creator interpretations, images and status retained. NGA native evidence and museum connection consolidated into original records; four newly introduced duplicates archived with redirects.',confidence='At least 98% editorial confidence, not a calibrated probability')
    m.save(n.RUN/'duplicate-reconciliation-plan.json.gz',decision);m.save(m.BACKUP/'nga/duplicate-reconciliation-before.json.gz',decision)
    with m.m.connect(write=True) as db:
        db.execute("SET LOCAL lock_timeout='120s'");db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(m.ACTOR,));db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(ids,)).fetchall();assert d.snapshot(db,ids)==before
        for newer,older in PAIRS:
            old=before[older]['artwork'];new=before[newer]['artwork'];row=rows[newer];wiki=m.load(n.RUN/'duplicate-pages'/(older+'.json'))
            assert old['current_institution_id'] is None and new['status']=='review' and new['primary_media_id'] is None
            assert not db.execute("SELECT id FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(older,)).fetchall()
            ext=db.execute("SELECT to_jsonb(e) v FROM external_identifiers e WHERE entity_type='artwork' AND entity_id=%s",(newer,)).fetchall()
            for e in ext:
                assert not db.execute("SELECT id FROM external_identifiers WHERE entity_type='artwork' AND entity_id=%s AND scheme=%s",(older,e['v']['scheme'])).fetchall()
            db.execute("UPDATE external_identifiers SET entity_id=%s WHERE entity_type='artwork' AND entity_id=%s",(older,newer))
            n.copy_rows(db,'artwork_location_assertions',[dict(id=m.uid('reconciled-holding/'+newer),artwork_id=older,claim_type='holding',institution_id=n.MID,context='collection',source_id=n.SID,source_url=row['source_url'],evidence_note=json.dumps(dict(native_object=row['raw'],basis=decision['basis'],confidence=decision['confidence']),ensure_ascii=False),checked_at=m.now(),review_state='accepted')])
            n.copy_rows(db,'citations',[dict(id=m.uid('reconciliation/'+newer),entity_type='artwork',entity_id=older,field_name='million_catalogue_identity_reconciliation',source_id=n.SID,source_record_id=row['native_id'],source_url=row['source_url'],evidence_note=json.dumps(dict(archived_duplicate_id=newer,original_record_id=older,native_object=row['raw'],native_creators=row['creators'],wikiart_receipt=wiki['receipt'],basis=decision['basis'],external_identifiers_before=[e['v'] for e in ext]),ensure_ascii=False),retrieved_at=m.now(),created_by=m.ACTOR)])
            db.execute("UPDATE artworks SET status='archived',updated_by=%s,updated_at=now(),revision=revision+1 WHERE id=%s",(m.ACTOR,newer));n.copy_rows(db,'slug_redirects',[dict(id=m.uid('redirect/'+newer),entity_type='artwork',entity_id=older,old_slug=new['slug'])])
        after=d.snapshot(db,ids)
        for newer,older in PAIRS:
            assert after[newer]['artwork']['status']=='archived' and after[older]['artwork']['current_institution_id']==n.MID
            assert {k:v for k,v in before[older]['artwork'].items() if k!='current_institution_id'}=={k:v for k,v in after[older]['artwork'].items() if k!='current_institution_id'}
            assert after[older]['creators']==before[older]['creators'] and after[older]['attachments']==before[older]['attachments']
        db.commit()
    m.save(receipt,dict(at=m.now(),canonical_map=dict(PAIRS),archived_new_duplicates=4,existing_records_connected=4,existing_primary_images_preserved=4,source_dates_and_creators_preserved=True));print('Reconciled four confirmed duplicate paintings',flush=True)
if __name__=='__main__':reconcile()
