#!/usr/bin/env python3
"""Verify and report the fourth batch's 200 named painters and held category."""
import ast,csv,hashlib,html,importlib.util,json
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('x',ROOT/'ops/run-random-200-round4-20261006.py');x=importlib.util.module_from_spec(sp);sp.loader.exec_module(x)
r=x.r;MAIN=x.RUN;SUPP=MAIN.parent/(MAIN.name+'-named-painter-supplement')

def read_csv(path):
 with path.open(newline='') as f:return list(csv.DictReader(f))

def check_run(folder,expected_count,expected_sources):
 proof=r.load(folder/'final-verification.json');summary=r.load(folder/'summary.json');pre=r.load(folder/'production-preflight.json')
 assert proof['painters']==expected_count and proof['all_sampled_painter_outcomes_verified'] and not proof['errors'] and summary['complete']
 assert proof['new_review_records']==pre['new_review_records']==summary['totals']['created']
 assert proof['images_verified']==pre['images']==summary['totals']['images_added']
 assert summary['statuses']=={'production_verified':expected_count}
 for name,digest in proof.get('concurrent_location_review_files',{}).items():assert r.sha((ROOT/name).read_bytes())==digest
 files={n:read_csv(folder/n) for n in ['painters.csv','source-dispositions.csv','new-review-records.csv','uploaded-images.csv','related-artwork-leads.csv','rejected-relationship-leads.csv']}
 assert len(files['painters.csv'])==expected_count
 assert len(files['source-dispositions.csv'])==summary['totals']['source_entries']==expected_sources
 for name,key in [('new-review-records.csv','new_review_records'),('uploaded-images.csv','images_verified')]:
  assert len(files[name])==proof[key] and len({row['artwork_id'] for row in files[name]})==proof[key]
 assert sum(summary['source_dispositions'].values())==expected_sources
 assert len(list((folder/'applied').glob('*.json')))==len(list((folder/'verified').glob('*.json')))==expected_count
 assert len(list((folder/'image-uploads').glob('*.json')))==proof['images_verified']
 parsed=BeautifulSoup((folder/'report.html').read_text(),'html.parser');assert len(parsed.select('tbody tr'))==expected_count
 for a in parsed.select('a[href]'):assert (folder/a['href']).is_file(),a['href']
 r.save(folder/'report-verification.json',{'at':r.now(),'painters':expected_count,'new_review_records':proof['new_review_records'],'images_uploaded_and_verified':proof['images_verified'],'source_entries':expected_sources,'related_work_leads':len(files['related-artwork-leads.csv']),'reviewed_source_notes_verified':proof['reviewed_source_notes_verified'],'checks':['CSV totals and unique artwork IDs','Production preflight, proof and summary agreement','All applied and verified receipts','Public image upload receipts','All HTML artifact links and outcome rows','Complete source-disposition accounting']})
 return summary,proof,files

def main():
 a,ap,af=check_run(MAIN,200,11961);b,bp,bf=check_run(SUPP,1,73)
 entity=r.load(MAIN/'creator-entity-review.json');held_id=entity['artist']['id']
 aztec=next(v for v in a['painters_report'] if v['artist_id']==held_id)
 assert aztec['artist']=='Aztec Art' and aztec['created']==aztec['images_added']==0
 original=r.load(MAIN/'cohort.json');supp=r.load(SUPP/'cohort.json');assert supp['original_rank']==201 and supp['seed']==original['seed']
 frame=r.load(MAIN/'sampling-frame.json')['frame'];ordered=sorted(frame,key=lambda p:hashlib.sha256((original['seed']+'/'+p['artist']['id']).encode()).digest())
 assert ordered[:200]==original['painters'] and ordered[200]==supp['painters'][0]
 named=[v for v in original['painters'] if v['artist']['id']!=held_id]+supp['painters'];assert len(named)==len({v['artist']['id'] for v in named})==len({v['source']['url'] for v in named})==200
 old=[p for folder in x.PRIOR_RUNS for p in r.load(folder/'cohort.json')['painters']]
 assert not {v['artist']['id'] for v in named}&{v['artist']['id'] for v in old}
 assert not {v['source']['url'] for v in named}&({v['source']['url'] for v in old}|{'https://www.wikiart.org/en/otto-dix'})
 rows=[v for v in a['painters_report'] if v['artist_id']!=held_id]+b['painters_report']
 x.csv_file('completed-200-named-painters.csv',rows)
 for name in ['new-review-records.csv','uploaded-images.csv','related-artwork-leads.csv']:
  combined=af[name]+bf[name]
  if name!='related-artwork-leads.csv':assert len(combined)==len({row['artwork_id'] for row in combined})
  x.csv_file('combined-'+name,combined)
 scripts=list((ROOT/'ops').glob('*random-200*round4*.py'))
 for p in scripts:ast.parse(p.read_text())
 summary={'at':r.now(),'complete':True,'named_painters':200,'overlap_with_previous_600_or_otto_dix':0,'seed':original['seed'],
  'new_review_records':ap['new_review_records']+bp['new_review_records'],'images_uploaded_and_verified':ap['images_verified']+bp['images_verified'],
  'matched_existing_records':ap['matched_existing_records']+bp['matched_existing_records'],'related_artwork_leads':len(af['related-artwork-leads.csv'])+len(bf['related-artwork-leads.csv']),
  'concurrent_holding_updates_preserved':ap.get('reviewed_concurrent_holding_updates',0)+bp.get('reviewed_concurrent_holding_updates',0),
  'concurrent_holding_review_files':{**ap.get('concurrent_location_review_files',{}),**bp.get('concurrent_location_review_files',{})},
  'source_entries_researched_including_held_category':11961+73,'source_entries_for_named_painters':11961+73-aztec['source_entries'],
  'source_unavailable_indexes':a['totals']['unavailable_painter_indexes']+b['totals']['unavailable_painter_indexes'],
  'held_category':{'name':'Aztec Art','reason':'Cultural tradition incorrectly typed as a person in the production sampling frame. All changes held; original sample preserved.','record_imports':0,'image_updates':0},
  'eligibility_correction':'Marianne Stokes is rank 201 in the original seeded ordering; this completes 200 named painters without choosing by artwork/image availability.',
  'new_records_remain_review':True,'existing_images_metadata_holdings_publication_preserved':True,'local_database_changed':False,
  'cloud_backup_id':r.load(x.BACKUP/'cloud-backup.json')['id'],'main_report':'report.html','supplement_report':'../'+SUPP.name+'/report.html',
  'main_proof_sha256':r.sha((MAIN/'final-verification.json').read_bytes()),'supplement_proof_sha256':r.sha((SUPP/'final-verification.json').read_bytes()),
  'script_sha256':{str(p.relative_to(ROOT)):r.sha(p.read_bytes()) for p in scripts},'errors':[]}
 assert sum(v['created'] for v in rows)==summary['new_review_records'] and sum(v['images_added'] for v in rows)==summary['images_uploaded_and_verified']
 r.save(MAIN/'combined-summary.json',summary)
 e=html.escape
 links=[('completed-200-named-painters.csv','200 painters'),('combined-new-review-records.csv','New review records'),('combined-uploaded-images.csv','Uploaded images'),('combined-related-artwork-leads.csv','Related-work leads'),('report.html','Main batch evidence'),('../'+SUPP.name+'/report.html','Marianne Stokes supplement'),('creator-entity-review.json','Held category'),('combined-summary.json','Verified totals')]
 page='<!doctype html><meta charset="utf-8"><title>Fourth batch: 200 new painters</title><style>body{font:16px system-ui;max-width:1300px;margin:36px auto;padding:20px;line-height:1.5}table{border-collapse:collapse;width:100%}td,th{padding:8px;border:1px solid #ddd;text-align:left}th{background:#eef2f4}</style><h1>Fourth batch — 200 new painters</h1>'
 page+='<p>'+e(f"{summary['new_review_records']:,} new review records · {summary['images_uploaded_and_verified']:,} images uploaded and verified · {summary['related_artwork_leads']:,} related-work leads")+'</p><p>'+' · '.join('<a href="'+u+'">'+label+'</a>' for u,label in links)+'</p>'
 if summary['concurrent_holding_updates_preserved']:
  page+='<p>'+e(f"{summary['concurrent_holding_updates_preserved']} holding updates made concurrently by separate museum workflows were recorded and preserved. They are not counted as this campaign’s museum assignments.")+'</p>'
 page+='<p>Zero overlap with the previous 600 painters or Otto Dix. All new records remain in review. Existing images, catalogue metadata, holdings, display and publication states were preserved. WikiArt source rights labels remain separate from the user’s source approval.</p><p>'+e(summary['eligibility_correction'])+' The Aztec Art category received no imports or image updates; the original sampling evidence is retained.</p><p>Images follow the pre-1971 creation scope. Unknown dates, unresolved versions and competing makers remain documented review holds. Available source-list coverage and related-work leads are bounded research, not a claim to every artwork worldwide.</p><table><thead><tr><th>Painter</th><th>Source entries</th><th>New review records</th><th>Images added</th><th>Current records</th><th>Current images</th></tr></thead><tbody>'
 page+=''.join('<tr>'+''.join('<td>'+e(str(v[k]))+'</td>' for k in ['artist','source_entries','created','images_added','after_records','after_images'])+'</tr>' for v in rows)+'</tbody></table>'
 path=MAIN/'combined-report.html';r.save(path,page.encode())
 parsed=BeautifulSoup(page,'html.parser');assert len(parsed.select('tbody tr'))==200
 for a in parsed.select('a[href]'):assert (MAIN/a['href']).is_file()
 r.save(MAIN/'combined-report-verification.json',{'at':r.now(),'named_painters':200,'row_totals_match':True,'html_links_checked':True,'source_dispositions_checked':12034,'sha256':r.sha(path.read_bytes()),'errors':[]})
 print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
