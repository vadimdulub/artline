#!/usr/bin/env python3
"""Batch 117: bounded official-archive review; no unsupported writes."""
import fcntl, json, os, subprocess, sys
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'ops'))
import exhibitions_common as c
E=ROOT/'docs/research/continuous-exhibitions-20261013/batches/000117'
R=Path.home()/'Library/Application Support/Artline/continuous-exhibition-research/batches/000117'
Q=E.parents[1]/'source-queue.json'; OP='continuous-exhibitions-20261013-batch-000117'
URL='https://www.tretyakovgallery.ru/about/history/rekonstruktsiya/'

def save(name,value): c.save(E/name,value)
def main():
 E.mkdir(parents=True,exist_ok=True); R.mkdir(parents=True,exist_ok=True)
 cp=c.load(E.parents[1]/'CHECKPOINT.json'); assert cp['inflight']['batch']==117
 ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True); assert str(cp['supervisor_pid']) in ps
 with c.connect() as db:
  target=dict(db.execute('select current_database() db,inet_server_port() port,current_user usr').fetchone()); assert target['db']=='artline'
  prior=[dict(x) for x in db.execute('select id::text,title from exhibitions where import_batch=%s',(OP,)).fetchall()]
  matches=[dict(x) for x in db.execute("select id::text,title,start_year,end_year,import_batch from exhibitions where start_year between 1986 and 1989 and (lower(title) like any(%s) or lower(coalesce(alternate_titles::text,'')) like any(%s)) order by start_year,title",(['%levits%','%kandinsk%','%malevich%'],['%levits%','%kandinsk%','%malevich%'])).fetchall()]
 assert not prior
 save('production-target-reconciliation.json',dict(at=c.now(),target=target,expected_instance='artline-508319:europe-west1:artline-postgres',proxy_pid=95606,locks=['artline-curated-ingestion',2026101201],prior_attributable_rows=prior,local_catalogue_writes=0,passed=True))
 save('recovery-check.json',dict(at=c.now(),prior_attributable_rows=prior,previous_batch=116,previous_counts_not_recounted=True,danish_job_changes_excluded=True,separate_artwork_programme_untouched=True,passed=True))
 r=requests.get(URL,headers={'User-Agent':'Artline exhibition research; bounded metadata retrieval'},timeout=(15,45)); r.raise_for_status()
 text=' '.join(r.text.split()); assert '1987' in text and '1989' in text
 receipt=dict(url=URL,final_url=r.url,status=r.status_code,retrieved_at=c.now(),sha256=c.sha(r.content),bytes=len(r.content),content_type=r.headers.get('Content-Type'))
 save('source-capture-verification.json',dict(at=c.now(),receipt=receipt,official_assertions=[
  dict(year=1987,label='выставка произведений Д.Г.Левицкого',english='exhibition of works by D. G. Levitsky',organizers='Tretyakov Gallery and Russian Museum',exact_dates=None),
  dict(year=1989,label='В.В.Кандинского',english='works of V. V. Kandinsky',exact_dates=None),
  dict(year=1989,label='К.С.Малевича',english='works of K. S. Malevich',exact_dates=None)],production_candidates=matches,passed=True))
 holds=[
  dict(route='getty_museum',outcome='not_replayed',reason='Batch114 reviewed twenty historical activity routes; unresolved Barocci duplicate identity remains held.'),
  dict(route='fitzwilliam_remaining_pictorial_events',outcome='not_replayed',reason='Batch115 ten-object image route held under CC BY-NC-ND; no changed rights grant.'),
  dict(route='whistler_primary_sources',outcome='not_replayed',reason='Completed Whistler deliveries and current access holds inspected; no unreviewed accession-specific checklist selected.'),
  dict(route='arthive_exhibitions',outcome='hold_reused_without_request',reason='Existing repeated HTTP 429 provider hold remains authoritative; no unchanged retry.',checked_at=c.now()),
  dict(route='tretyakov_reconstruction_history',outcome='research_hold',reason='Official institutional history explicitly supports three single-artist exhibitions and years, but supplies no exact dates and does not identify the venue/stop during the 1986-1995 reconstruction. Production search also requires tour/duplicate reconciliation; no venue stop or participant row forced.')]
 save('candidate-review-verification.json',dict(at=c.now(),discovered=3,prepared=0,imported=0,verified=0,complete_checklists=0,production_matches=matches,holds=holds,decision='No eligible accurately representable production addition in this bounded route.',passed=True))
 save('independent-production-verification.json',dict(at=c.now(),target=target,operation=OP,attributable_rows=[],verified_counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']},other_jobs_excluded=True,passed=True))
 with Q.with_suffix('.lock').open('a+') as lk:
  fcntl.flock(lk,fcntl.LOCK_EX); q=c.load(Q); before=c.sha(Q.read_bytes())
  g=next(x for x in q['sources'] if x['source_id']=='tretyakov_gallery'); a=next(x for x in q['supplemental_sources'] if x['source_id']=='arthive_exhibitions')
  g['research_status']='reconstruction_history_three_year_only_events_held_batch117'; g['last_checked_at']=c.now(); g['cursor']['batch117']=dict(url=URL,capture_sha256=receipt['sha256'],reviewed=['Levitsky 1987','Kandinsky 1989','Malevich 1989'],delivered=0,next='Find original catalogues or annual reports establishing exact venue and tour identity before delivery; do not infer the reconstructed Gallery building as host.')
  g.setdefault('holds',[]).append(dict(at=c.now(),key='reconstruction-era-venue-and-tour-identity',reason=holds[-1]['reason'],evidence='docs/research/continuous-exhibitions-20261013/batches/000117/candidate-review-verification.json'))
  g.setdefault('evidence',[]).extend(['docs/research/continuous-exhibitions-20261013/batches/000117/source-capture-verification.json','docs/research/continuous-exhibitions-20261013/batches/000117/independent-production-verification.json'])
  a['cursor']['batch117']=dict(hold_reused_without_request=True,checked_at=c.now(),next='Await changed HTTP429 state; use accessible official archives meanwhile.'); a['last_checked_at']=c.now()
  temp=Q.with_suffix('.batch117.tmp'); temp.write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n'); os.replace(temp,Q)
 save('queue-update-verification.json',dict(at=c.now(),updated_sources=['tretyakov_gallery','arthive_exhibitions'],unrelated_entries_preserved=True,before_sha256=before,after_sha256=c.sha(Q.read_bytes()),passed=True))
 counts={k:0 for k in ['new_exhibitions','new_venue_stops','new_artists','new_catalogue_artworks','new_documentary_entries','new_artist_participation_links','new_exact_artwork_links','new_images','existing_records_enriched']}
 nxt='Research an accessible official Russian-icon or post-Byzantine archive with original event dates, venue identity and an explicit object checklist; alternatively resolve the Tretyakov 1987/1989 reconstruction-era venue and tour identities from original catalogues. Do not replay Getty/Fitzwilliam/Whistler holds.'
 paths=[f'docs/research/continuous-exhibitions-20261013/batches/000117/{x}' for x in ['production-target-reconciliation.json','recovery-check.json','source-capture-verification.json','candidate-review-verification.json','independent-production-verification.json','queue-update-verification.json','CHECKPOINT.json','final-verification.json']]
 checkpoint=dict(at=c.now(),batch=117,stage='verified_complete_no_eligible_candidates',verified_counts=counts,discovered=3,prepared=0,imported=0,verified=0,next_task=nxt,external_supervisor_owns_continuation=True,evidence_paths=paths); save('CHECKPOINT.json',checkpoint); c.save(R/'batch-checkpoint.json',checkpoint)
 result=dict(outcome='no_eligible_candidates',summary='Reviewed the remaining Getty, Fitzwilliam and Whistler routes without replaying completed or held work, and captured an official Tretyakov reconstruction-history route supporting Levitsky (1987), Kandinsky (1989) and Malevich (1989) exhibitions. The source does not establish exact dates or a safe venue/stop identity during reconstruction, so no event, stop or participation record was forced. The existing Arthive HTTP 429 hold was recorded without an unchanged retry.',next_task=nxt,blocker='',verified_counts=counts,evidence_paths=paths)
 save('final-verification.json',dict(**result,at=c.now(),passed=True)); save('worker-result.json',result); print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': main()
