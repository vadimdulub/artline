"""Persist bounded batch results and merge only researched registry routes."""
import importlib.util,json,gzip,datetime,fcntl,shutil
from pathlib import Path
s=importlib.util.spec_from_file_location('b',Path(__file__).with_name('continuous-basel-images-000115.py'));b=importlib.util.module_from_spec(s);s.loader.exec_module(b);h=b.h;E=b.E

def main():
 receipt=h.load(E/'batch-verification-receipt.json');counts=receipt['verified_counts'];assert counts['newly_illustrated']==1
 assert h.load(E/'independent-resume-verification.json')['unchanged_snapshot']
 sample=h.load(E/'reserve-visual-sample-selection.json');assert h.sha(Path(sample['path']).read_bytes())==sample['sha256']
 holds=[dict(artwork_id='0438b88b-1f50-5dcf-a069-4c2043883005',title='Green April',outcome='rights_deferred',evidence='gilliam-source-receipt.json',reason='Foundation names Basel and Lee Thompson photograph, courtesy David Kordansky Gallery. No explicit reusable image licence established. WikiArt/Commons search found no exact approved image. No image requested.'),dict(artwork_id='004a664d-3f35-55f3-8448-728e8d6816cb',title='Blick in den Kreuzgang des Münsters zu Basel',outcome='different_version_and_access_hold',evidence='neustuck-source-receipt.json',reason='Indexed Staatsarchiv SMM Inv.1968.19 differs from Basel792. Separate1819 joint watercolour also differs from1865 painting. Direct Staatsarchiv returned403; no retry or image download.'),dict(artwork_id='025431a1-bab4-5c8f-b476-4532434c991c',title='Das Jüngste Gericht',outcome='no_exact_image_found_in_bounded_search'),dict(artwork_id='00cd37e9-ea91-51ee-bccd-7d54c5772860',title='Studienblatt mit Figurenstudien',outcome='no_exact_image_found_in_bounded_search'),dict(artwork_id='02c75e0c-bdf5-5b91-b942-ca431a37b150',title='Mädchen mit Kuh in einem Stall',outcome='no_exact_image_found_in_bounded_search')]
 b.save('research-holds.json',dict(at=h.now(),records=holds,scope='Five unresolved Basel objects in this bounded pass; not exhaustive source coverage',selected_and_delivered=['02b69f34-6844-5c4f-a883-f7fff4b0e391']))
 b.save('source-access-holds.json',dict(at=h.now(),inherited_basel='docs/research/continuous-production-20261011/batches/000104/source-access-holds.json',unchanged_held_surfaces=['sammlung.kunstmuseumbasel.ch/multimedia/*','commons.wikimedia.org/w/api.php'],new_holds=[dict(url='https://dls.staatsarchiv.bs.ch/records/940136',status=403,attempts=1,retry_allowed=False,receipt='neustuck-source-receipt.json')],held_surface_retries=0))
 queries=['site.commons.wikimedia.org Basel "Schaffner" "Gericht"','site.wikiart.org "Sam Gilliam" "Green April"','site.commons.wikimedia.org "Neustück" "Kreuzgang"','"Neustück" "Kreuzgang" Basel painting','"Schaffner" "Jüngste Gericht" Basel Commons','"Franz Adam" "Ulanen" Basel','"Senave" "Kuh" "Basel"','site.wikiart.org "Schaffner" "Judgment"','site.commons.wikimedia.org "Senave" "Basel"','site.commons.wikimedia.org "Millet" "1961.15"','site.wikiart.org "Franz Adam" "1863"']
 b.save('discovery-search-log.json',dict(at=h.now(),tool='web.run',queries=queries,query_results_are_leads_only=True,primary_urls=['https://samgilliamfoundation.org/artwork/artwork-b-new-name/','https://dls.staatsarchiv.bs.ch/records/940136','https://commons.wikimedia.org/wiki/Category:Franz_Adam','https://commons.wikimedia.org/wiki/File:Ulanen_jagen_Honved-Husaren_eine_Pferdeherde_ab,_1863.jpg'],findings='Adam exact file found by category navigation after title search missed it; verified against current museum object3096. Other records held per research-holds. No claimed exhaustive absence.'))
 next_task='Rotate to Museum Data Service UK cached icon page3 offset10; select eligible paintings/icons using object-level rights and date evidence. French188 reserve exhausted; do not replay. Basel17 unprocessed pending IDs remain for a future alternate-source pass.'
 refs=[str(p.relative_to(b.ROOT)) for p in sorted(E.glob('*.json')) if p.name not in ['source-queue-before.json','CHECKPOINT.json']]
 qp=E.parents[1]/'source-queue.json'
 with qp.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);before=h.load(qp);q=json.loads(json.dumps(before));changed=['yale_lux','kunstmuseum_basel','wikimedia_commons'];at=h.now()
  for r in q['sources']:
   if r['source_id'] not in changed:continue
   r.setdefault('research_history',[]).append(dict(batch=115,at=at,evidence=refs,verified_counts=counts if r['source_id']!='yale_lux' else {k:0 for k in counts}))
   r['last_checked_at']=at;r['checkpoint']=str((E/'CHECKPOINT.json').relative_to(b.ROOT));r['last_batch']=115
   if r['source_id']=='yale_lux':
    r['status']='french_reserve_exhausted_live_verified_188_already_delivered';r['resume_cursor']=dict(remaining_prepared_french_reserve=0,recheck_only_on_new_reserve_or_production_change=True,next_step='Choose another registry route; all188 belong to historical reserve plan, zero new increments')
   else:
    r['status']='one_Basel_Adam_primary_image_verified_via_exact_public_domain_Commons_museum_source'
    if r['source_id']=='kunstmuseum_basel':
     c=r['resume_cursor'];done=receipt['production_ids'];reviewed=[x['artwork_id'] for x in holds]+done
     c['researched_artwork_ids']=sorted(set(c['researched_artwork_ids']+reviewed));c['delivered_artwork_ids']=sorted(set(c['delivered_artwork_ids']+done));c['held_artwork_ids']=sorted(set(c['held_artwork_ids']+[x['artwork_id'] for x in holds]));c['pending_artwork_ids']=[aid for aid in c['pending_artwork_ids'] if aid not in reviewed];c['next_step']='Rotate to MDS UK; later process remaining pending IDs without repeating held searches.'
     r['remaining_gaps']=[str(len(c['pending_artwork_ids']))+' unprocessed pending IDs in frozen cursor','Six held records including prior Degas; no provider hold bypass','All remaining records still lack primary images; no full museum coverage claim']
    else:r.setdefault('resume_cursor',{})['basel_batch115']=dict(delivered=receipt['production_ids'],native_id='3096',other_candidates='See batch115 research-holds.json',next_step='Rotate sources; Commons API hold unchanged')
  assert all(a==z for a,z in zip(before['sources'],q['sources']) if a['source_id'] not in changed)
  b.save('source-queue-preupdate.json',before);tmp=qp.with_suffix('.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');tmp.replace(qp)
  reread=h.load(qp);assert reread==q
  b.save('independent-queue-verification.json',dict(at=at,changed_source_ids=changed,unrelated_entries_preserved=True,registry_entries=len(q['sources']),before_sha256=h.sha((E/'source-queue-preupdate.json').read_bytes()),after_sha256=h.sha(qp.read_bytes())))
 b.save('source-register.json',dict(at=h.now(),routes=[r for r in q['sources'] if r['source_id'] in changed],policy='Original111-source registry plus newer source-specific approvals; actual Commons PD-Art/PDM and museum public-domain statement preserved',directory_coverage_added=0,object_research_count=6))
 start=h.load(E/'started.json')['at'];end=h.now();elapsed=(datetime.datetime.fromisoformat(end)-datetime.datetime.fromisoformat(start)).total_seconds()
 cp=dict(batch=115,status='complete',outcome='progress',started_at=start,finished_at=end,measured_runtime_seconds=elapsed,verified_counts=counts,production_ids=receipt['production_ids'],stage_counts=dict(french_reserve_inspected=188,french_reserve_unimported=0,basel_objects_researched=6,selected=1,prepared=1,imported=1,verified=1),next_task=next_task,evidence_paths=refs,local_catalogue_connections=0,supervisor_unmodified=True,delivery_complete_do_not_recount=True)
 b.save('CHECKPOINT.json',cp);h.save(b.R/'CHECKPOINT.json',cp)
 b.save('batch-report.json',dict(at=end,measured_runtime_seconds=elapsed,verified_counts=counts,scope='One bounded batch; programme cumulative counts owned by external supervisor',failures=['System python lacks psycopg; established venv used','Staatsarchiv403 held; no retry'],unresolved=holds,next_task=next_task))
 print(json.dumps(dict(outcome='progress',verified_counts=counts,next_task=next_task)))
if __name__=='__main__':main()
