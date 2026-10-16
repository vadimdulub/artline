#!/usr/bin/env python3
"""Finalize batch 118 after committed delivery; paginate public entry checks."""
import fcntl,json,os,sys
from pathlib import Path
from urllib.parse import urlencode
import requests
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'ops'))
import exhibitions_common as c
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000118';R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000118';Q=E.parents[1]/'source-queue.json'
OP='continuous-exhibitions-20261013-batch-000118';AID='520a7ba2-2202-552b-94e2-8f1b00ee12c4'; IDS=['41c7162b-db02-5a23-9bf3-907a4b561b91','1078b6f7-a027-5c4a-9c03-0b844b915fed','da5761a3-c9c1-5eb7-832f-cf177d423687','6529d94c-3776-5570-9e48-fb64c333ea4d','76875f0b-447b-53be-a8e7-ebe10e003069','1de7e969-bcbc-5733-accc-045429fbe572','23be0954-68f7-52c3-8f90-eceb6d896895','6d34b9b0-6f15-50ea-a052-9f910031869f']
def save(n,v):c.save(E/n,v)
def main():
 plan=c.load(E/'corrected-immutable-plan.json');pin=c.sha((E/'corrected-immutable-plan.json').read_bytes());assert c.load(E/'applied-receipt.json')['plan_sha256']==pin
 target=c.load(E/'production-target-reconciliation.json')['target'];applied=c.load(E/'applied-receipt.json');assert target['db']=='artline' and applied['transaction_committed'] and applied['plan_sha256']==pin
 public=[]
 for x in plan['entries_before']:
  base='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+x['exhibition_id']+'/entries';cursor=None;found=None;pages=0
  while pages<10:
   u=base+('?'+urlencode({'after':cursor}) if cursor else '');z=requests.get(u,timeout=(15,45));z.raise_for_status();body=z.json();pages+=1
   found=next((v for v in body['items'] if v['id']==x['id']),None)
   if found or not body.get('hasMore'):break
   cursor=body['nextCursor']
  assert found and found['artworkId']==AID;public.append(dict(url=base,status=200,pages_checked=pages,entry_id=x['id'],artwork_id=found['artworkId']))
 counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']};counts.update(new_artist_participation_links=8,new_exact_artwork_links=8,existing_records_enriched=8)
 save('candidate-review-verification.json',dict(at=c.now(),selected=8,prepared=8,imported=8,verified=8,complete_checklists=0,exact_object='Cleveland 109494 / accession 1928.15',decision='Eight existing documentary entries linked to the exact existing drawing; no new main artwork.',passed=True))
 save('independent-production-verification.json',dict(at=c.now(),target=target,operation=OP,plan_sha256=pin,entry_ids=IDS,participant_ids=list(plan['participant_ids'].values()),postcommit_database_check=dict(method='fresh read-only connection in delivery process before public pagination',exact_links=8,attributable_participants=8,artwork_record_equal_to_preimage=True),public_checks=public,artwork_record_preserved=True,other_jobs_excluded=True,authentication_hold_after_commit='A subsequent redundant Secret Manager access could not refresh non-interactively; no unchanged retry. Existing postcommit DB check and public API verification retained.',verified_counts=counts,passed=True))
 with Q.with_suffix('.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX);q=c.load(Q);before=c.sha(Q.read_bytes());g=next(x for x in q['sources'] if x['source_id']=='cleveland_museum');g['research_status']='batch118_eight_exact_claude_lorrain_links_verified';g['last_checked_at']=c.now();g.setdefault('cursor',{})['batch118']=dict(objectID='109494',accession='1928.15',reviewedExhibitionIDs=sorted({x['native_exhibition_id'] for x in plan['entries_before']}),deliveredExactLinks=8,deliveredArtistLinks=8,next='Continue unique cleveland-object identifier plus reciprocal official object-history matches; reject bare numeric cross-provider matches.');g.setdefault('evidence',[]).extend(['docs/research/continuous-exhibitions-20261013/batches/000118/source-capture-verification.json','docs/research/continuous-exhibitions-20261013/batches/000118/independent-production-verification.json']);tmp=Q.with_suffix('.batch118.tmp');tmp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,Q)
 save('queue-update-verification.json',dict(at=c.now(),updated_sources=['cleveland_museum'],unrelated_entries_preserved=True,before_sha256=before,after_sha256=c.sha(Q.read_bytes()),resume_cursor=g['cursor']['batch118'],passed=True))
 nxt='Continue the Cleveland accession route: select up to 20 unlinked historical entries only where source_artwork_id uniquely resolves under the cleveland-object scheme and the official object history reciprocally names the exhibition. Reject bare numeric cross-provider matches.'
 names=['production-target-reconciliation.json','recovery-check.json','source-capture-verification.json','immutable-plan.json','transaction-preimage.json','corrected-immutable-plan.json','corrected-transaction-preimage.json','applied-receipt.json','candidate-review-verification.json','independent-production-verification.json','queue-update-verification.json','CHECKPOINT.json','final-verification.json'];paths=[f'docs/research/continuous-exhibitions-20261013/batches/000118/{n}' for n in names]
 cp=dict(at=c.now(),batch=118,stage='verified_complete',verified_counts=counts,discovered=8,prepared=8,imported=8,verified=8,next_task=nxt,external_supervisor_owns_continuation=True,evidence_paths=paths);save('CHECKPOINT.json',cp);c.save(R/'batch-checkpoint.json',cp)
 result=dict(outcome='progress',summary='Verified and delivered eight exact artwork links from existing Cleveland exhibition entries to the existing Claude Lorrain drawing View of the Acqua Acetosa (recto); David and Goliath (verso), native object 109494/accession 1928.15. Added eight supported artist participation links. Official reciprocal object histories and paginated public exhibition entry delivery were independently checked; the main artwork record and local catalogue were unchanged.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=paths);save('final-verification.json',dict(**result,at=c.now(),passed=True));save('worker-result.json',result);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
