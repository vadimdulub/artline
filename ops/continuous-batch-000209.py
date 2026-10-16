#!/usr/bin/env python3
import hashlib, importlib.util, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'docs/research/continuous-production-20261011/batches/000209'
R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000209'
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/india-300-delivery-20261011.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
E.mkdir(parents=True,exist_ok=True)
def now(): return datetime.now(timezone.utc).isoformat()
def save(name,obj): h.save(E/name,obj)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

commands=subprocess.check_output(['ps','ax','-o','command='],text=True).splitlines()
target='artline-508319:europe-west1:artline-postgres'
assert any(x.startswith('/tmp/artline-cloud-sql-proxy ') and '--port 55519 ' in x and target in x for x in commands)
with h.connect() as db:
 row=dict(db.execute("select current_database() db,current_setting('transaction_read_only') ro").fetchone())
 ids=['46896','49272','53939','59482','66465']
 rec=[dict(x) for x in db.execute("select ei.external_id,a.id::text artwork_id,a.title,count(am.id) filter(where am.is_primary) primary_media from external_identifiers ei join artworks a on a.id=ei.entity_id left join artwork_media am on am.artwork_id=a.id where ei.entity_type='artwork' and ei.scheme='pma-native-object' and ei.external_id=any(%s) group by 1,2,3 order by 1",(ids,))]
 b107=dict(db.execute("select count(*)::int live_citations from citations where field_name='continuous_wikiart_evidence_b000107'").fetchone())
assert row['db']=='artline' and row['ro'] in ('on',True)
assert len(rec)==5 and all(x['primary_media']==0 for x in rec)
save('production-target-verification.json',{'at':now(),'connection_name':target,'proxy_port':55519,'database':row,'helper':'ops/india-300-delivery-20261011.py','shared_ingestion_lock':'artline-curated-ingestion','writes':0})
save('batch107-live-reconciliation.json',{'at':now(),**b107,'writes':0,'previous_increments_counted':0})
files=[]
for oid in ids:
 p=R/'visual-review'/f'{oid}.jpg';files.append({'native_id':oid,'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'actually_viewed':True})
save('actual-visual-review.json',{'at':now(),'records':files,'finding':'Five authentic full-composition PMA reproductions were viewed individually and matched the official titles/compositions. Visual identity review passed; delivery eligibility did not, because PMA per-object reuse evidence is absent and the registry says never download unless explicitly open.','selected_for_delivery':0})
save('live-gap-reconciliation.json',{'at':now(),'records':rec,'exact_source_identity':True,'existing_primary_images':0,'eligible_for_attachment':0,'hold':'No object-level explicit open image licence. Catalogue availability and public-domain artwork status were not converted into image reuse permission.'})
qpath=ROOT/'docs/research/continuous-production-20261011/source-queue.json';q=json.loads(qpath.read_text());entry=next(x for x in q['sources'] if x['source_id']=='philadelphia_museum_art')
entry.update(status='five_existing_pma_russian_image_gaps_visually_verified_rights_held',checkpoint='docs/research/continuous-production-20261011/batches/000209/CHECKPOINT.json',last_checked_at=now(),access_status='Five exact existing PMA Russian pictorial gaps reviewed against authentic native reproductions; all held because explicit per-object image reuse evidence is absent. No writes.')
entry['resume_cursor'].update({'image_reviewed_native_ids':ids,'image_rights_held_native_ids':ids,'next_page':1,'next_step':'Continue PMA Russian metadata page 1 without repeating page 0, or research a distinct registry museum with explicit open image rights. Do not retry these five images unless rights evidence changes.'})
qbytes=(json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode();qpath.write_bytes(qbytes)
save('source-queue-update-verification.json',{'at':now(),'source_id':'philadelphia_museum_art','queue_sha256':hashlib.sha256(qbytes).hexdigest(),'unrelated_entries_preserved':True,'reviewed_native_ids':ids,'resume_cursor':entry['resume_cursor']})
counts={'new_painters':0,'new_artworks':0,'newly_illustrated':0,'alternate_images':0,'museum_links':0}
next_task='Research an undercovered registry museum with explicit object-level open image rights, prioritizing Greek, Byzantine, post-Byzantine or Russian icons; alternatively continue PMA Russian metadata at page 1 without retrying the five rights-held images.'
save('batch-verification-receipt.json',{'at':now(),'verified_counts':counts,'selected':5,'prepared':5,'imported':0,'verified_production_increments':0,'writes':0,'reason':'All five exact existing production gaps lack permitted object-level image reuse evidence; no prior-campaign rows counted.'})
save('CHECKPOINT.json',{'at':now(),'batch':209,'stage':'complete_no_eligible_candidates','discovered':5,'selected':5,'prepared':5,'imported':0,'verified':0,'verified_counts':counts,'next_task':next_task,'blocker':'','evidence':['docs/research/continuous-production-20261011/batches/000209/production-target-verification.json','docs/research/continuous-production-20261011/batches/000209/live-gap-reconciliation.json','docs/research/continuous-production-20261011/batches/000209/actual-visual-review.json','docs/research/continuous-production-20261011/batches/000209/source-queue-update-verification.json','docs/research/continuous-production-20261011/batches/000209/batch-verification-receipt.json']})
print(json.dumps({'outcome':'no_eligible_candidates','counts':counts,'next_task':next_task}))
