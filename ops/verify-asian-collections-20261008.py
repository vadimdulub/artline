#!/usr/bin/env python3
"""Read-only production verification and delivery report for the Asian collection pass."""
import collections,concurrent.futures,csv,html,importlib.util,json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-asian-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def verify():
 plans={phase:m.pinned(phase)[0] for phase in ['china','japan','manila']};records=[r for p in plans.values() for r in p['records']];ids=sorted({r['artwork_id'] for r in records});newids={r['artwork_id'] for r in records if not r['before']}
 image_records={x['artwork_id']:x for phase in plans for x in m.load(m.RUN/phase/'image-preparation.json.gz')['records'] if x['prepared'] and x['artwork_id'] in set(m.load(m.RUN/phase/'images-applied.json')['artwork_ids'])}
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');states=m.snapshot(db,ids)
  assert len(states)==len(ids)
  for phase,p in plans.items():
   for r in p['records']:
    st=states[r['artwork_id']];a=st['artwork'];assert a['current_institution_id']==r['institution_id']
    if not r['before']:
     assert a['status']=='review' and a['published_at'] is None and a['research_candidate']
     assert (a['creation_year_start'],a['creation_year_end'])==(r['first'],r['last'])
     assert a['title']==r['title']
    else:
     old=r['before'];allowed={'current_institution_id'}
     if r['artwork_id'] in image_records:allowed|={'primary_media_id','revision','updated_by','updated_at'}
     assert {k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in old['artwork'].items() if k not in allowed},('Existing metadata changed',r['key'])
     assert st['creators']==old['creators']
     assert all(x in st['attachments'] for x in old['attachments'])
    if r['artwork_id'] in image_records:assert a['primary_media_id']==image_records[r['artwork_id']]['media_id']
    if not r['before']:
     assert len(st['holdings'])==1 and st['holdings'][0]['claim_type']=='holding'
     assert st['holdings'][0]['review_state']=='accepted'
   count=db.execute("SELECT count(*) n FROM citations WHERE field_name='asian_collection_import_20261008' AND entity_id=ANY(%s::uuid[])",([r['artwork_id'] for r in p['records']],)).fetchone()['n'];assert count>=len(p['records'])
  media={x['id']:x for x in db.execute('SELECT id::text,storage_path,byte_size,checksum_sha256,rights_status,provider_name,source_page_url FROM media_assets WHERE id=ANY(%s::uuid[])',([st['artwork']['primary_media_id'] for st in states.values() if st['artwork']['primary_media_id']],))}
  evidenced={x['media_id'] for x in db.execute('SELECT DISTINCT media_id::text FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im in image_records.values()],))}
  for aid,im in image_records.items():
   ma=media[im['media_id']];assert ma['storage_path']==im['path'] and ma['byte_size']==im['bytes']<=100000 and ma['checksum_sha256']==im['sha256']
   assert im['media_id'] in evidenced
  institutions={i['id']:i for p in plans.values() for i in p['institutions'].values()}
  counts={str(x['id']):x for x in db.execute("SELECT i.id,i.name,i.slug,trim(p.country_code) country,count(a.id) total,count(a.primary_media_id) images FROM institutions i LEFT JOIN places p ON p.id=i.place_id JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id,p.country_code ORDER BY i.name",(list(institutions),))};assert len(counts)==len(institutions)
  assert all(x['total']>0 for x in counts.values())
  newinst={i['id'] for p in plans.values() for i in p['new_institutions']};assert all(counts[i]['country'] for i in newinst)
 selected=[]
 for iid in institutions:
  candidates=[r for r in records if r['institution_id']==iid];r=next((r for r in candidates if r['artwork_id'] in image_records),candidates[0]);selected.append(r)
 def api_check(r):
  museum=counts[r['institution_id']];base='https://artlines.org/api/backend/v1/museums/'+museum['slug'];u=base+'/works/'+r['artwork_id'];response=requests.get(u,timeout=(10,45));response.raise_for_status();body=response.json();expected=states[r['artwork_id']]['artwork'];mid=expected['primary_media_id'];assert body['title']==expected['title'];assert body.get('media_url')==(media[mid]['storage_path'] if mid else None)
  response2=requests.get(base+'/works?limit=1',timeout=(10,45));response2.raise_for_status();page=response2.json();assert page['total']>0 and len(page['items'])==1
  return dict(institution_id=r['institution_id'],museum=museum['name'],slug=museum['slug'],url=u,artwork_id=r['artwork_id'],title=body['title'],status=response.status_code,media_url=body.get('media_url'),browse_total=page['total'],browse_images=page.get('image_count'),verified=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(api_check,selected))
 out=dict(at=m.now(),target='production',records_verified=len(ids),new_records_in_review=len(newids),existing_records_preserved=len(ids)-len(newids),new_images_verified=len(image_records),museums_with_items=len(institutions),new_museums_with_country_links=len(newinst),metadata_and_publication_preserved=True,local_database_changes=0,public_api_checks=checks,museum_counts=list(counts.values()),unknown_dates_preserved=sum(states[aid]['artwork']['creation_year_start'] is None for aid in newids))
 m.save(m.RUN/'verification.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ['public_api_checks','museum_counts']}),flush=True)

def report():
 verification=m.load(m.RUN/'verification.json');phases=['china','japan','manila'];receipts={k:m.load(m.RUN/k/'applied.json') for k in phases};images={k:m.load(m.RUN/k/'images-applied.json')['images_attached'] for k in phases};plans={k:m.pinned(k)[0] for k in phases}
 with (m.RUN/'imported-artworks.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['phase','artwork_id','museum','title','creator','source_date','creation_year_start','creation_year_end','action','new_image','source_url']);writer.writeheader()
  for phase,p in plans.items():
   attached=set(m.load(m.RUN/phase/'images-applied.json')['artwork_ids'])
   for r in p['records']:writer.writerow(dict(phase=phase,artwork_id=r['artwork_id'],museum=r['museum'],title=r['title'],creator=r.get('creator_label'),source_date=r.get('date_display'),creation_year_start=r['first'],creation_year_end=r['last'],action='new review artwork' if not r['before'] else 'existing record enriched',new_image=r['artwork_id'] in attached,source_url=r['source_url']))
 intro='Imported 5,393 new review artworks, enriched 1,721 previously existing records and attached 1,062 images in production. The pass covers 30 museums, galleries and mural sites; 22 newly added institutions have country-level browsing links. No publication or current-display claims were added.'
 summary='\n'.join(f"| {k.title()} | {receipts[k]['new_artworks']:,} | {receipts[k]['existing_records_enriched']:,} | {images[k]:,} | {len(receipts[k]['by_museum'])} |" for k in phases)
 gaps=[
 'Coverage is substantial but incomplete. China has 17 represented collections/sites and Japan 10, with four institutions shared. Manila means Metro Manila and covers seven collections. The phase table counts records at the start of each phase: one Tokyo work added during China was enriched again during Japan, so the 1,722 phase enrichments cover 1,721 records that existed before this overall operation.',
 'China includes paintings, prints, calligraphy, mural fragments and nine named Dunhuang scenes. Nine source records remain held for blank titles, accession/component reconciliation or conflicting existing identities. Source inventory units include albums and leaves; counts are catalogue records, not necessarily independent compositions.',
 'Japan includes Cleveland, Chicago, Minneapolis, Tokyo/Kyoto/Nara/Kyushu national museums, Ōta, Adachi and the National Museum of Modern Art Kyoto. Two source records remain held. Tokyo modern-art access returned 403; no collection coverage is claimed for it.',
 'Manila: Lopez 61, Ayala 78, National Museum of Fine Arts 18, Vargas 44, BSP 38, UST 3 and Ateneo 1. Two duplicate title variants were reconciled into retained records; 53 explicitly later source entries were excluded. Six jewellery entries remain in research outside this pictorial/sculptural pass. Ayala loan/private-owner records were not assigned as museum-owned works.',
 'Ateneo’s collection URLs returned 404 and its homepage returned unrelated gambling content during retrieval. No data from that content was used. Its single addition is supported by the government NCCA inventory. Metropolitan Museum Manila and other collections without eligible object evidence remain coverage gaps.',
 'Chinese image downloads: 486 accepted and attached; three prepared images rejected as a closed album, blank backing and distant installation view. Chicago and Minneapolis denied selected image requests with HTTP 403 and further requests were stopped. Twenty-four narrow scroll previews failed the minimum-size filter. Japan: 575 attached; eight files failed preparation. Full preparation and access receipts are retained.',
 'Manila: WikiArt’s Spoliarium image was visually matched and attached with its actual Public domain label. WikiArt’s Amorsolo El Ciego and Bombing of the Intendencia images were held as different/private versions. Most Manila photographs still lack an established reusable source; metadata records remain available without invented images.',
 'Unknown creation dates, disputed source values and qualified maker labels remain explicit. Lopez pages showing an unlabelled current-year 2026 for historical works were recorded as unknown dates. No artist lifespan, excavation date or exhibition date became an artwork creation year.',
 'Country links identify only country-level geography; no city, coordinates, street address or current display was invented. Historical collection catalogues support holdings, not live display.',
 'Image originals are archived outside Documents. Application derivatives are complete source frames, resized proportionally, at most 100,000 bytes, with original source/rights labels and checksums. The production /assets/ route was used; obsolete pre-correction /media/ uploads remain unreferenced.',
 'All 7,114 distinct affected records were verified using scoped read-only production queries, with publication/metadata preservation checks. Museum browsing and one artwork detail per represented institution passed public API checks. Every newly attached image passed a public file checksum check. No application code, deployment or local database writes were required.',
 'The scoped museum query plan is retained in each plan. A separate limited exact-title check used a sequential scan; no broad title-only enrichment was performed. This catalogue operation is not a 10-million-row load test.'
 ]
 readme='# Chinese, Japanese and Manila production import — 8 October 2026\n\n'+intro+'\n\n| Pass | New records | Existing enriched | New images | Collections |\n|---|---:|---:|---:|---:|\n'+summary+'\n\n## Evidence and verification\n\n- [Delivery report](report.html)\n- [Imported artwork register](imported-artworks.csv)\n- [Production verification](verification.json)\n- [Institution country links](institution-country-applied.json)\n- Phase folders retain pinned plans, source captures, exclusions, preparation, visual review, upload receipts and applied receipts.\n\n## Decisions and remaining gaps\n\n'+'\n\n'.join('- '+g for g in gaps)+'\n\n## Recovery and operation\n\nProduction backup: `1791478316451` (successful before imports). Row preimages and after-state evidence are under `/Users/vadimdulub/Library/Application Support/Artline/backups/asian-collections-import-20261008/`. Original images are under the corresponding `source-images` directory. Preserve both; no unrelated files or databases were removed.\n\nScripts: `ops/import-asian-collections-20261008.py`, `ops/images-asian-collections-20261008.py`, `ops/research-japan-import-20261008.py`, `ops/research-manila-import-20261008.py`, and `ops/verify-asian-collections-20261008.py`. The earlier [Chinese research](../chinese-art-20261008/README.md) remains a historical pre-import record.\n'
 (m.RUN/'README.md').write_text(readme)
 esc=html.escape
 table=''.join('<tr><td>'+esc(k.title())+'</td><td>'+f"{receipts[k]['new_artworks']:,}"+'</td><td>'+f"{receipts[k]['existing_records_enriched']:,}"+'</td><td>'+f"{images[k]:,}"+'</td></tr>' for k in phases)
 detail=''
 for phase in phases:
  detail+='<h2>'+phase.title()+'</h2><table><tr><th>Collection</th><th>Records in this pass</th></tr>'
  for name,n in receipts[phase]['by_museum'].items():
   inst=plans[phase]['institutions'][name];detail+='<tr><td><a href="https://artlines.org/museums/'+esc(inst['slug'])+'">'+esc(name)+'</a></td><td>'+str(n)+'</td></tr>'
  detail+='</table>'
 page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Artline — Asian collections import</title><style>body{font:17px/1.6 system-ui,sans-serif;margin:3rem auto;max-width:1000px;padding:0 24px;color:#182b2a;background:#faf8f2}h1{font-family:Georgia,serif;font-size:2.6rem;line-height:1.15}h2{margin-top:2.4rem}table{border-collapse:collapse;width:100%;background:white}td,th{text-align:left;padding:10px 15px;border-bottom:1px solid #d7ded8}a{color:#176954}li{margin:.8rem 0}.meta{color:#536960}</style><p class="meta">ARTLINE · PRODUCTION DELIVERY · 8 OCTOBER 2026</p><h1>Chinese, Japanese and Manila art</h1><p>'+esc(intro)+'</p><table><tr><th>Pass</th><th>New records</th><th>Existing enriched</th><th>New images</th></tr>'+table+'</table><p><a href="imported-artworks.csv">Download the complete imported-artwork register</a> · <a href="verification.json">Verification evidence</a></p>'+detail+'<h2>Decisions and remaining gaps</h2><ul>'+''.join('<li>'+esc(g)+'</li>' for g in gaps)+'</ul><p class="meta">All additions remain in review. Production backup 1791478316451. Source captures and per-image receipts are retained alongside this report.</p></html>'
 (m.RUN/'report.html').write_text(page);print('Report and artwork register saved',flush=True)

if __name__=='__main__':
 import sys
 globals()[sys.argv[1]]()
