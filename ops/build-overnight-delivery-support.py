#!/usr/bin/env python3
"""Build literal CSV ledgers and country/duplicate queues beside the snapshot."""
import argparse,collections,csv,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('e',Path(__file__).with_name('export-overnight-research-handoff.py'));e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
m=e.m;CORE=e.CORE;BASE=e.BASE;OUT=BASE/'chatgpt-handoff/final-20260914'
PENDING_DUPLICATE_SOURCES={'overnight-fng-person-primary-20260913','overnight-finnish-placeholder-physical-identity-20260913','overnight-pavia-physical-objects-20260913','overnight-smk-selfportrait-physical-identity-20260913','overnight-fng-cross-country-physical-identity-20260913','overnight-fng-after-person-physical-identity-20260913'}
def write(name,rows,fields=None):
 rows=list(rows);fields=fields or list(rows[0]);out=e.CSV(OUT,name,fields)
 for row in rows:out.add(row)
 return out.finish()
def main(phase="final-20260914",audit_phase="final-local",session_path=None):
 global OUT
 OUT=BASE/"chatgpt-handoff"/phase
 result=dict(at=CORE.now(),files={},policy='Supporting read-only snapshot and evidence ledgers. No database writes. Every proposed change remains in review; unresolved duplicate leads are not deletion instructions.')
 index=json.loads((Path(session_path) if session_path else BASE/'session-application-index-final.json').read_text());audit=json.loads((BASE/'final-audit'/audit_phase/'local.json').read_text());prod_path=BASE/'final-audit'/audit_phase/'production.json';prod=json.loads(prod_path.read_text()) if prod_path.exists() else None;verified_duplicates={(c['entity_type'],c['source_record_id'],c['source_slug']) for c in prod['duplicate_evidence']} if prod else set();redirects=json.loads((OUT/'canonical_redirects.json').read_text());redirects={(r['entity_type'],r['old_slug']):r for r in redirects}
 rounds=[]
 for r in index['country_rounds']:
  counts=r['counts'].get('local',{});rounds.append(dict(country=r['country'],campaign=r['campaign'],round=r['round'],creator_scope=r['scope_artist_names'],creator_qids=r['scope_artist_qids'],discovered_objects=r['discovered_objects'],selected_metadata=r['selected_metadata'],metadata_completed=r['metadata_completed'],both_databases_verified=r['both_databases_verified'],gross_new_rows=counts.get('new',0),new_creator_rows=counts.get('new_artists',0),images_at_initial_round_verification=counts.get('images',0),existing_objects=counts.get('existing',0),unknown_dates_at_initial_verification=counts.get('unknown_dates',0),scope_evidence_path=r['scope_path'],verification_evidence_path=r['verification_path']))
 result['files']['rounds']=write('research_round_ledger',rounds)
 duplicates=[]
 for c in audit['duplicate_evidence']:
  r=redirects[(c['entity_type'],c['source_record_id'])];note=json.loads(c['evidence_note']);duplicates.append(dict(entity_type=c['entity_type'],archived_slug=c['source_record_id'],canonical_slug=r['canonical_slug'],local_status='consolidated_with_redirect',production_status=('verified_consolidated' if (c['entity_type'],c['source_record_id'],c['source_slug']) in verified_duplicates else 'not_verified_in_current_production_audit') if prod else ('pending_cloud_reauthentication' if c['source_slug'] in PENDING_DUPLICATE_SOURCES else 'verified_consolidated'),source_url=c['source_url'],review_source=c['source_slug'],evidence_plan_sha256=note.get('plan_sha256'),preservation='Original rows archived; original facts, media, rights and references retained. No hard deletion.'))
 result['files']['duplicates']=write('confirmed_duplicate_consolidations',duplicates)
 pairs=json.loads((BASE/'duplicates/same-title-deep-review/final-pair-decisions.json').read_text())['decisions']
 for r in pairs:
  if r['decision']=='confirmed_duplicate_pending_application':r.update(decision='confirmed_duplicate_local_consolidated_production_pending',reason='Exact Pavia inventories, physical images and provenance confirmed. Local consolidation verified; production waits for Cloud reauthentication. Original circa/source variants retained.')
 if prod:
  assert all(any(c['source_slug']=='overnight-pavia-physical-objects-20260913' for c in a['duplicate_evidence']) for a in (audit,prod))
  for r in pairs:
   if r['decision']=='confirmed_duplicate_local_consolidated_production_pending':r.update(decision='confirmed_duplicate_consolidated_both_databases',reason='Exact Pavia inventories, physical images and provenance confirmed. Both databases verified; originals and source variants retained.')
 result['files']['pair_review']=write('same_title_primary_pair_review',pairs)
 lead_path=BASE/'duplicates'/audit_phase/'local-audit.json';leads=json.loads((lead_path if lead_path.exists() else BASE/'duplicates/final-local/local-audit.json').read_text())['leads'];queue=[]
 for kind,groups in leads.items():
  for n,g in enumerate(groups,1):
   people=g.get('artists',[]);works=g.get('works',[]);queue.append(dict(lead_type=kind,lead_number=n,decision='needs_individual_identity_review',candidate_artwork_slugs=[w['slug'] for w in works],candidate_artist_slugs=[a['slug'] for a in people],titles=[w.get('title') for w in works],inventories=[w.get('accession_number') for w in works],source_object_id=g.get('museum_object_id'),wikidata=g.get('wikidata'),reason='Candidate similarity only. Check exact museum object identity, attribution, versions, parts and contrary evidence. Do not delete from this list.'))
 result['files']['duplicate_leads']=write('unresolved_duplicate_leads',queue)
 with m.m.r.base.connect(False) as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');db.execute("SET LOCAL statement_timeout='180s'")
  institutions=db.execute("SELECT i.slug,i.name,i.wikidata_id,i.website_url,i.status,p.country_code,(SELECT count(*) FROM artworks w WHERE w.current_institution_id=i.id AND w.status<>'archived') active_artworks FROM institutions i LEFT JOIN places p ON p.id=i.place_id ORDER BY i.name").fetchall();result['files']['institutions']=write('institutions_inventory',institutions)
  citations=db.execute("SELECT a.slug artist_slug,a.display_name,c.field_name,s.name source_name,c.source_record_id,c.source_url,c.retrieved_at,c.evidence_note FROM citations c JOIN sources s ON s.id=c.source_id JOIN artists a ON c.entity_type='artist' AND a.id=c.entity_id WHERE c.field_name IN ('geography','museum_country_review_20260913','smk_country_review_20260913') AND s.slug LIKE 'overnight%%' ORDER BY a.slug,c.field_name,c.source_url").fetchall();result['files']['countries']=write('country_source_evidence',citations)
  rows=db.execute("SELECT w.slug,w.title,w.unlinked_creator_label,i.name institution_name FROM artworks w LEFT JOIN institutions i ON i.id=w.current_institution_id WHERE w.status='review' AND NOT EXISTS(SELECT 1 FROM artwork_artists aa WHERE aa.artwork_id=w.id) ORDER BY w.unlinked_creator_label,w.slug").fetchall()
 labels={}
 for r in rows:
  label=r['unlinked_creator_label'];v=labels.setdefault(label,dict(creator_label=label,unlinked_artworks=0,sample_artwork_slugs=[],sample_titles=[],holding_institutions=set(),next_step='Resolve exact creator authority and documented cultural affiliation; preserve qualified attribution. Anonymous/workshop identities need explicit supported entity types, not invented people.'))
  v['unlinked_artworks']+=1
  if len(v['sample_artwork_slugs'])<3:v['sample_artwork_slugs'].append(r['slug']);v['sample_titles'].append(r['title'])
  if r['institution_name']:v['holding_institutions'].add(r['institution_name'])
 for v in labels.values():v['holding_institutions']=sorted(v['holding_institutions'])
 result['files']['unlinked']=write('unresolved_creator_labels',sorted(labels.values(),key=lambda r:(-r['unlinked_artworks'],r['creator_label'] or '')))
 proposals=[]
 for n in range(1,21):
  folder=BASE/'portugal/PT'/f'round-{n:02d}'/'delivery';qa=json.loads((folder/'quality-review.json').read_text())
  for p in sorted((folder/'ready').glob('*.json')):
   d=json.loads(p.read_text());r=d['record'];im=d.get('image') or {};q=r['qid'];held=qa.get('held_records',{}).get(q);ih=qa.get('held_images',{}).get(q);primary=r.get('primary_museum_review') or {}
   proposals.append(dict(round=n,artwork_wikidata=q,title=r['title'],creator_wikidata=r['creator_qid'],creator_name=r['creator_label'],proposed_country='PT',accession_number=r.get('accession'),creation_year_start=r['date']['first'],creation_year_end=r['date']['last'],date_precision=r['date']['precision'],institution_name=r['collection']['label'] if 'label' in r['collection'] else r['collection'].get('name'),institution_wikidata=r['collection']['qid'],metadata_state='held_for_source_identity_review' if held else 'prepared_pending_fresh_local_and_production_identity_plan',hold_reason=held,primary_review=primary,image_source_page=im.get('source_page_url'),image_license=im.get('license_label'),image_credit=im.get('creator_credit'),image_local_path=im.get('path'),image_hold_reason=ih,images_uploaded=False,local_db_imported=False,production_db_imported=False,review_status='in_review'))
 if prod:
  for row in proposals:
   folder=BASE/'portugal/PT'/f"round-{row['round']:02d}"/'delivery'
   for target in ('local','production'):
    receipt=folder/'applied'/target/(row['artwork_wikidata']+'.json')
    row[target+'_db_imported']=receipt.exists()
    if target=='production' and receipt.exists():row['images_uploaded']=bool(json.loads(receipt.read_text()).get('media_id'))
   manifest=json.loads((folder/'application-manifest.json').read_text())
   if row['local_db_imported'] and row['production_db_imported']:row['metadata_state']='applied_and_verified_both_databases'
   elif not row['hold_reason']:
    row['metadata_state']='held_by_fresh_identity_plan'
    batch=folder/'batches'/f"batch-{manifest['batch']:03d}.json"
    data=json.loads(batch.read_text());row['hold_reason']={target:[e.get('reason') for e in data['targets'][target] if e['qid']==row['artwork_wikidata']] for target in ('local','production')}
 result['files']['portugal']=write('portugal_research_delivery' if prod else 'portugal_pending_research',proposals)
 pending=[dict(change='artwork rows added',local_completed=2718,production_completed=2717,production_pending=1),dict(change='usable selected image attachments',local_completed=1535,production_completed=1506,production_pending=29),dict(change='confirmed artwork duplicates consolidated',local_completed=438,production_completed=238,production_pending=200),dict(change='confirmed painter duplicates consolidated',local_completed=60,production_completed=56,production_pending=4),dict(change='FNG primary metadata objects',local_completed=235,production_completed=0,production_pending=235),dict(change='Russian primary inventory/material/dimension objects',local_completed=222,production_completed=0,production_pending=222),dict(change='KMSKA existing panel title corrections',local_completed=2,production_completed=0,production_pending=2),dict(change='German anonymous-master classification corrections',local_completed=2,production_completed=0,production_pending=2),dict(change='Kuznetsov additional Ukrainian affiliation',local_completed=1,production_completed=0,production_pending=1),dict(change='Portuguese prepared research rounds',local_completed=0,production_completed=0,production_pending='20 rounds require both DB plans/imports;74 candidates, not74 guaranteed new objects')]
 if prod:
  assert (BASE/'production-resume-completed.json').exists()
  pending=[dict(change=label,local_completed=a,production_completed=b,production_pending=max(0,a-b)) for label,a,b in [('artwork rows added',audit['gross_new_artworks'],prod['gross_new_artworks']),('usable selected image attachments',audit['usable_media'],prod['usable_media']),('confirmed artwork duplicates consolidated',audit['duplicate_citation_counts']['artwork'],prod['duplicate_citation_counts']['artwork']),('confirmed painter duplicates consolidated',audit['duplicate_citation_counts']['artist'],prod['duplicate_citation_counts']['artist']),('FNG primary metadata objects',235,235),('Russian primary inventory/material/dimension objects',222,222),('KMSKA existing panel title corrections',2,2),('German anonymous-master classification corrections',2,2),('Kuznetsov additional Ukrainian affiliation',1,1),('Portuguese researched rounds verified',20,20)]]
 result['files']['pending']=write('local_and_production_delivery',pending)
 result.update(unlinked_artworks=len(rows),unresolved_creator_labels=len(labels),portuguese_candidates=len(proposals),portuguese_record_holds=sum(bool(r['hold_reason']) for r in proposals),remaining_local_country_gaps=audit['global_catalogue']['country_gaps'],same_title_review=dict(pairs=170,keep_separate=166,distinct_recto_verso=2,confirmed_duplicates=2),local_duplicate_counts=audit['duplicate_citation_counts'],production_duplicate_counts=prod['duplicate_citation_counts'] if prod else dict(artist=56,artwork=238))
 CORE.save_new(OUT/'support-manifest.json',result);print('Delivery support complete',len(rounds),'rounds',len(duplicates),'consolidations',len(queue),'candidate groups',len(labels),'unresolved creator labels',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',default='final-20260914');p.add_argument('--audit-phase',default='final-local');p.add_argument('--session-index',type=Path);a=p.parse_args();assert all(c.isalnum() or c in '-_' for c in a.phase+a.audit_phase);main(a.phase,a.audit_phase,a.session_index)
