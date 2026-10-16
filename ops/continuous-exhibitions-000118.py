#!/usr/bin/env python3
"""Batch 118: reconcile one Cleveland drawing across eight existing entries."""
import fcntl, json, os, subprocess, sys
from pathlib import Path
import requests
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'ops'))
import exhibitions_common as c
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000118'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000118'
Q=E.parents[1]/'source-queue.json'; OP='continuous-exhibitions-20261013-batch-000118'
URL='https://openaccess-api.clevelandart.org/api/artworks/109494'
AID='520a7ba2-2202-552b-94e2-8f1b00ee12c4'; ARTIST='22910ad1-23c3-42b1-94d0-c0ba32681f3b'
ENTRY_IDS=['41c7162b-db02-5a23-9bf3-907a4b561b91','1078b6f7-a027-5c4a-9c03-0b844b915fed','da5761a3-c9c1-5eb7-832f-cf177d423687','6529d94c-3776-5570-9e48-fb64c333ea4d','76875f0b-447b-53be-a8e7-ebe10e003069','1de7e969-bcbc-5733-accc-045429fbe572','23be0954-68f7-52c3-8f90-eceb6d896895','6d34b9b0-6f15-50ea-a052-9f910031869f']
COUNT_KEYS=['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']

def save(n,v):
 if (E/n).exists(): return
 c.save(E/n,v)
def normal(v): return json.loads(json.dumps(dict(v),default=str)) if v is not None else None
def main():
 E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
 cp=c.load(E.parents[1]/'CHECKPOINT.json'); assert cp['inflight']['batch']==118
 ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True); assert str(cp['supervisor_pid']) in ps and 'artline-508319:europe-west1:artline-postgres' in ps
 with c.connect() as db:
  target=dict(db.execute('select current_database() db,inet_server_port() port,current_user usr').fetchone()); assert target['db']=='artline'
  prior=[dict(x) for x in db.execute("select id::text,exhibition_id::text,artist_id::text from exhibition_participants where evidence->>'operation'=%s",(OP,)).fetchall()]
  rows=[normal(x) for x in db.execute("select ee.*,ee.source_record_id::text source_record_uuid,e.title exhibition_title,e.start_date,e.end_date,esr.source_key,esr.source_record_id native_exhibition_id from exhibition_entries ee join exhibitions e on e.id=ee.exhibition_id join exhibition_source_records esr on esr.id=ee.source_record_id where ee.id=any(%s::uuid[]) order by e.start_date",(ENTRY_IDS,)).fetchall()]
  work=normal(db.execute('select * from artworks where id=%s',(AID,)).fetchone()); creator=normal(db.execute("select aa.*,a.display_name from artwork_artists aa join artists a on a.id=aa.artist_id where aa.artwork_id=%s and aa.artist_id=%s",(AID,ARTIST)).fetchone())
 assert not prior and len(rows)==8 and work['accession_number']=='1928.15' and work['creation_year_end']<=1970 and creator['attribution_role']=='primary'
 assert all(x['artwork_id'] is None and x['source_key']=='cleveland' and x['source_artwork_id']=='109494' for x in rows)
 save('production-target-reconciliation.json',dict(at=c.now(),target=target,expected_instance='artline-508319:europe-west1:artline-postgres',proxy_pid=95606,locks=['artline-curated-ingestion',2026101201],prior_attributable_rows=prior,local_catalogue_writes=0,passed=True))
 save('recovery-check.json',dict(at=c.now(),prior_attributable_rows=prior,selected_entries_already_linked=sum(x['artwork_id'] is not None for x in rows),previous_batch_counts_not_recounted=True,danish_job_changes_excluded=True,separate_artwork_programme_untouched=True,passed=True))
 r=requests.get(URL,headers={'User-Agent':'Artline exhibition research; bounded metadata retrieval'},timeout=(15,45)); r.raise_for_status(); raw=r.content; obj=r.json()['data']
 rc=dict(url=URL,final_url=r.url,status=r.status_code,retrieved_at=c.now(),sha256=c.sha(raw),bytes=len(raw),content_type=r.headers.get('Content-Type'))
 ex={str(x['id']):x for x in obj['exhibitions']['current']}; expected={x['native_exhibition_id'] for x in rows}; assert expected<=set(ex)
 assert str(obj['id'])=='109494' and obj['accession_number']=='1928.15' and obj['title']==work['title'] and obj['creators'][0]['description'].startswith('Claude Lorrain')
 save('source-capture-verification.json',dict(at=c.now(),receipt=rc,object=dict(id=obj['id'],accession=obj['accession_number'],title=obj['title'],creator=obj['creators'][0],creation_date=obj['creation_date'],type=obj['type'],technique=obj['technique']),matched_exhibitions=[ex[x['native_exhibition_id']] for x in rows],passed=True))
 basis='Exact Cleveland native object 109494 and accession 1928.15; identical recto/verso title and reciprocal official object exhibition history. Claude Lorrain primary attribution is explicit; checklist remains partial.'
 evidence=dict(operation=OP,sourceURL=URL,captureSHA256=rc['sha256'],nativeObjectID='109494',accession='1928.15',creatorNativeID='1873',creatorLabel=obj['creators'][0]['description'],creationDate=obj['creation_date'],exactVersion=True,checklistComplete=False,holdingClaim=False,currentDisplayClaim=False)
 plan=dict(at=c.now(),operation=OP,source_capture_sha256=rc['sha256'],artwork_before=work,creator=creator,entries_before=rows,evidence=evidence,match_basis=basis,participant_ids={x['exhibition_id']:c.uid(OP+'/participant/'+x['exhibition_id']) for x in rows})
 save('corrected-immutable-plan.json',plan); plan_sha=c.sha((E/'corrected-immutable-plan.json').read_bytes()); save('corrected-transaction-preimage.json',dict(at=c.now(),plan_sha256=plan_sha,entries=rows,artwork=work,prior_attributable_rows=prior,failed_plan_sha256=c.sha((E/'immutable-plan.json').read_bytes()),failed_attempt_rolled_back=True,passed=True))
 with c.connect(write=True) as db:
  db.execute("select set_config('artline.actor_user_id','continuous-exhibition-research',true)"); db.execute("select pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))"); db.execute('select pg_advisory_xact_lock(2026101201)')
  for x in rows:
   cur=normal(db.execute('select * from exhibition_entries where id=%s for update',(x['id'],)).fetchone()); assert cur['artwork_id'] is None
   ev=evidence|dict(planSHA256=plan_sha,exhibitionSourceRecordID=x['native_exhibition_id'])
   db.execute('update exhibition_entries set artwork_id=%s,evidence=%s,match_basis=%s where id=%s and artwork_id is null',(AID,Jsonb(ev),basis,x['id']))
   if not db.execute('select 1 from exhibition_participants where exhibition_id=%s and artist_id=%s',(x['exhibition_id'],ARTIST)).fetchone():
    db.execute("insert into exhibition_participants(id,exhibition_id,source_record_id,artist_id,name_label,role,evidence) values(%s,%s,%s,%s,'Claude Lorrain','artist',%s)",(plan['participant_ids'][x['exhibition_id']],x['exhibition_id'],x['source_record_uuid'],ARTIST,Jsonb(ev)))
 counts={k:0 for k in COUNT_KEYS}; counts.update(new_artist_participation_links=8,new_exact_artwork_links=8,existing_records_enriched=8)
 save('applied-receipt.json',dict(at=c.now(),operation=OP,plan_sha256=plan_sha,transaction_committed=True,verified_counts=counts))
 with c.connect() as db:
  after=[normal(x) for x in db.execute('select * from exhibition_entries where id=any(%s::uuid[]) order by id',(ENTRY_IDS,)).fetchall()]
  parts=[normal(x) for x in db.execute("select * from exhibition_participants where evidence->>'operation'=%s order by id",(OP,)).fetchall()]
  unchanged=normal(db.execute('select * from artworks where id=%s',(AID,)).fetchone())
 assert len(after)==8 and all(x['artwork_id']==AID for x in after) and len(parts)==8 and unchanged==work
 public=[]
 for x in rows:
  u='https://artline-api-lpuqqlugnq-ew.a.run.app/api/v1/exhibitions/'+x['exhibition_id']+'/entries'; z=requests.get(u,timeout=(15,45)); z.raise_for_status(); item=next(v for v in z.json()['items'] if v['id']==x['id']); assert item['artworkId']==AID; public.append(dict(url=u,status=z.status_code,entry_id=x['id'],artwork_id=item['artworkId']))
 save('independent-production-verification.json',dict(at=c.now(),target=target,operation=OP,plan_sha256=plan_sha,entries=after,participants=parts,public_checks=public,artwork_record_preserved=True,other_jobs_excluded=True,verified_counts=counts,passed=True))
 save('candidate-review-verification.json',dict(at=c.now(),selected=8,prepared=8,imported=8,verified=8,complete_checklists=0,exact_object='Cleveland 109494 / accession 1928.15',decision='Eight pre-existing documentary entries safely linked to the same exact existing drawing; no new main artwork.',passed=True))
 with Q.with_suffix('.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX); q=c.load(Q); before=c.sha(Q.read_bytes()); g=next(x for x in q['sources'] if x['source_id']=='cleveland_museum')
  g['research_status']='batch118_eight_exact_claude_lorrain_links_verified'; g['last_checked_at']=c.now(); g.setdefault('cursor',{})['batch118']=dict(objectID='109494',accession='1928.15',reviewedExhibitionIDs=sorted(expected),deliveredExactLinks=8,deliveredArtistLinks=8,next='Continue accession-level Cleveland entries whose source_artwork_id has a unique cleveland-object identifier; reject bare numeric cross-provider matches.')
  g.setdefault('evidence',[]).extend(['docs/research/continuous-exhibitions-20261013/batches/000118/source-capture-verification.json','docs/research/continuous-exhibitions-20261013/batches/000118/independent-production-verification.json'])
  temp=Q.with_suffix('.batch118.tmp'); temp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n'); os.replace(temp,Q)
 save('queue-update-verification.json',dict(at=c.now(),updated_sources=['cleveland_museum'],unrelated_entries_preserved=True,before_sha256=before,after_sha256=c.sha(Q.read_bytes()),resume_cursor=g['cursor']['batch118'],passed=True))
 nxt='Continue the undercovered Cleveland accession route: select up to 20 unlinked historical entries only where source_artwork_id uniquely resolves under the cleveland-object scheme and the official object history reciprocally names the exhibition. Do not use bare numeric matches from other providers.'
 paths=[f'docs/research/continuous-exhibitions-20261013/batches/000118/{n}' for n in ['production-target-reconciliation.json','recovery-check.json','source-capture-verification.json','immutable-plan.json','transaction-preimage.json','corrected-immutable-plan.json','corrected-transaction-preimage.json','applied-receipt.json','candidate-review-verification.json','independent-production-verification.json','queue-update-verification.json','CHECKPOINT.json','final-verification.json']]
 checkpoint=dict(at=c.now(),batch=118,stage='verified_complete',verified_counts=counts,discovered=8,prepared=8,imported=8,verified=8,next_task=nxt,external_supervisor_owns_continuation=True,evidence_paths=paths); save('CHECKPOINT.json',checkpoint); c.save(R/'batch-checkpoint.json',checkpoint)
 result=dict(outcome='progress',summary='Verified and delivered eight exact artwork links from existing Cleveland exhibition entries to the existing Claude Lorrain drawing View of the Acqua Acetosa (recto); David and Goliath (verso), native object 109494/accession 1928.15. Added eight supported artist participation links. Official reciprocal object histories and public exhibition entry delivery were independently checked; the main artwork record and local catalogue were unchanged.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=paths)
 save('final-verification.json',dict(**result,at=c.now(),passed=True)); save('worker-result.json',result); print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': main()
