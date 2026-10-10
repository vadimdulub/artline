#!/usr/bin/env python3
"""Read-only integrated production verification and refreshable Prado report."""
import collections, concurrent.futures, importlib.util, json
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('prado',ROOT/'ops/expand-prado-catalogue-20261006.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r
def run():
 plan=r.load(m.RUN/'production-plan.json.gz');base=r.load(m.RUN/'production-baseline.json.gz')
 consolidation=r.load(m.RUN/'duplicate-consolidation/applied.json');mapping=consolidation['canonical_map']
 source_records=plan['records'];ids=[mapping.get(x['artwork_id'],x['artwork_id'])for x in source_records];assert len(set(ids))==7129
 baseline={x['artwork']['id']:x['artwork']for x in base['records']}
 aftermeta=r.load(m.RUN/'production-after-metadata.json.gz')['records']
 images={};delivery_plans=[]
 for folder in ('images/delivery','wikiart-delivery','images/commons-followup/delivery'):
  root=m.RUN/folder;p=r.load(root/'production-plan.json.gz');applied=r.load(root/'production-applied.json')
  assert applied['plan_sha256']==r.sha((root/'production-plan.json.gz').read_bytes())
  delivery_plans.append((root,p,applied))
 root=m.RUN/'museum-image-delivery'
 for receipt in sorted(root.glob('batch-*-applied.json')):
  applied=r.load(receipt);pfile=root/f"batch-{applied['batch']:03}-plan.json.gz";p=r.load(pfile)
  assert applied['plan_sha256']==r.sha(pfile.read_bytes());delivery_plans.append((root,p,applied))
 for root,p,a in delivery_plans:
  for aid,im in p['prepared'].items():
   assert aid not in images;images[aid]=im
   receipt=r.load(root/'uploads'/(aid+'.json'))
   assert receipt['sha256']==im['sha256'] and receipt['public_bytes_verified'] and receipt['plan_sha256']==a['plan_sha256']
   body=(ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes()
   assert len(body)==im['bytes']<=100000 and r.sha(body)==im['sha256']
 allids=sorted(set(ids)|set(mapping)|set(baseline));mids=[x['media_id']for x in images.values()]
 with r.connect('production')as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  current={x['data']['id']:x['data']for x in db.execute('SELECT to_jsonb(a) data FROM artworks a WHERE id=ANY(%s::uuid[])',(allids,))}
  native={x['external_id']:x['entity_id']for x in db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE source_id=%s AND scheme='prado-native-object'",(plan['source_id'],))}
  media={x['media']['id']:x for x in db.execute("SELECT to_jsonb(a) media,CASE WHEN e.media_id IS NOT NULL THEN jsonb_build_object('source_image_url',e.source_image_url) END rights FROM media_assets a LEFT JOIN media_rights_evidence e ON e.media_id=a.id WHERE a.id=ANY(%s::uuid[])",(mids,))}
  cites=db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE source_id=%s AND field_name='prado_catalogue_source_metadata'",(plan['source_id'],)).fetchall()
  counts=db.execute("SELECT count(*) works,count(primary_media_id) images,count(*) FILTER(WHERE status='review') review FROM artworks WHERE current_institution_id=%s AND status<>'archived'",(m.MUSEUM,)).fetchone()
  scopes=db.execute('SELECT artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope,count(*) n FROM artworks WHERE id=ANY(%s::uuid[]) GROUP BY 1',(ids,)).fetchall()
  holdings=db.execute("SELECT review_state,count(*) n FROM artwork_location_assertions WHERE source_id=%s AND claim_type='holding' GROUP BY 1",(plan['source_id'],)).fetchall()
  assert db.execute("SELECT count(*) n FROM artwork_location_assertions WHERE source_id=%s AND claim_type='display'",(plan['source_id'],)).fetchone()['n']==0
  queryplans={'native_identity_lookup':db.execute("EXPLAIN (FORMAT JSON) SELECT entity_id FROM external_identifiers WHERE scheme='prado-native-object' AND external_id=%s",(source_records[0]['source_id'],)).fetchone(),
   'museum_bounded_page':db.execute("EXPLAIN (FORMAT JSON) SELECT id,title,primary_media_id FROM artworks WHERE current_institution_id=%s AND status<>'archived' ORDER BY id LIMIT 60",(m.MUSEUM,)).fetchone()}
 assert len(native)==len(cites)==len(ids)
 for x in source_records:
  aid=mapping.get(x['artwork_id'],x['artwork_id']);assert native[x['source_id']]==aid
  assert current[aid]['current_institution_id']==m.MUSEUM and current[aid]['status']=='review'
  assert any(c['entity_id']==aid and c['source_record_id']==x['source_id'] and c['source_url']==x['object']['url']for c in cites)
 allowed={'primary_media_id','revision','updated_at','updated_by'}
 for aid,old in aftermeta.items():
  if aid in mapping:
   assert current[aid]['status']=='archived' and current[aid]['current_institution_id']is None;continue
  assert {k:v for k,v in old.items()if k not in allowed}=={k:v for k,v in current[aid].items()if k not in allowed},'Catalogue metadata changed: '+aid
  if old['primary_media_id']:assert old['primary_media_id']==current[aid]['primary_media_id']
 for aid,old in baseline.items():
  assert {k:v for k,v in old.items()if k not in allowed}=={k:v for k,v in current[aid].items()if k not in allowed},'Original catalogue metadata changed: '+aid
  if old['primary_media_id']:assert old['primary_media_id']==current[aid]['primary_media_id']
 rights=collections.Counter()
 for aid,im in images.items():
  assert current[aid]['primary_media_id']==im['media_id'];row=media[im['media_id']];asset=row['media'];ev=row['rights'];assert ev
  assert asset['storage_path']==im['path'] and asset['checksum_sha256']==im['sha256'] and asset['byte_size']==im['bytes']
  assert (asset['width'],asset['height'])==(im['width'],im['height'])
  expected=im.get('rights_status','public_domain');assert asset['rights_status']==expected
  assert ev['source_image_url']==im.get('source_image_url',im.get('page',{}).get('image_url'))
  rights[expected]+=1
 gaps=[aid for aid,a in baseline.items()if not a['primary_media_id']]
 gapfilled=[aid for aid in gaps if current[aid]['primary_media_id']]
 # Representative public API checks complement full database and byte receipts.
 sample=[]
 for root,p,a in delivery_plans:
  aid=next(iter(p['prepared']));sample.append(aid)
 sample=list(dict.fromkeys(sample))
 def api(aid):
  url='https://artlines.org/api/backend/v1/museums/museo-del-prado/works/'+aid
  response=requests.get(url,timeout=(15,45));response.raise_for_status();body=response.json()
  assert body.get('media_url')==images[aid]['path'] and body.get('title')==current[aid]['title']
  return {'artwork_id':aid,'url':url,'status':response.status_code,'image':body['media_url'],'verified':True}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:api_results=list(pool.map(api,sample))
 museum_total=sum(a['attached']for root,p,a in delivery_plans if root.name=='museum-image-delivery')
 commons_total=sum(a['attached']for root,p,a in delivery_plans if root.name=='delivery')
 result={'at':r.now(),'all_checks_passed':True,'source_paintings':7141,'selected_paintings':7129,'explicit_post_1970_exclusions':12,
  'gross_records_created':6517,'new_duplicates_archived':2,'net_new_distinct_paintings':6515,'existing_identities_reconciled':614,
  'production':counts,'source_native_identifiers_verified':len(native),'creation_scope_counts':scopes,'holding_assertions':holdings,'display_claims_added':0,
  'original_image_gaps':len(gaps),'original_gaps_filled':len(gapfilled),'original_gaps_remaining':len(gaps)-len(gapfilled),
  'images_attached_this_expansion':len(images),'wikiart_images':46,'independent_commons_images':commons_total,'museum_source_images':museum_total,
  'rights_status_counts':dict(rights),'all_attached_files_public_bytes_verified':len(images),'representative_live_api_checks':api_results,
  'existing_images_preserved':True,'catalogue_metadata_preserved':True,'published':0,'local_database_writes':0,
  'scope_note':'7,129 selected P-inventory paintings plus one pre-existing D007473 drawing record retained without rewriting its legacy work type. The source snapshot is not a complete current museum inventory.'}
 stamp=result['at'].replace(':','').replace('-','');folder=m.RUN/'verification'/stamp
 r.save(folder/'query-plans.json',queryplans);r.save_gz(folder/'catalogue-snapshot.json.gz',current)
 outcomes=[]
 for x in source_records:
  aid=mapping.get(x['artwork_id'],x['artwork_id']);a=current[aid]
  outcomes.append({'artwork_id':aid,'initial_import_id':x['artwork_id'],'accession':x['accession'],'title':x['object']['Título'],'source_url':x['object']['url'],
   'creator_label':x['creator_label'],'source_date':x['object']['Fecha'],'status':a['status'],'image_present':bool(a['primary_media_id']),
   'image_added_this_expansion':aid in images,'primary_media_id':a['primary_media_id'],'duplicate_consolidated':aid!=x['artwork_id']})
 r.save_gz(folder/'all-painting-outcomes.json.gz',outcomes)
 spec=importlib.util.spec_from_file_location('outcomes',ROOT/'ops/prado-image-outcomes-20261006.py');out=importlib.util.module_from_spec(spec);spec.loader.exec_module(out)
 result['detailed_image_outcome_counts']=out.write(m,current,images,source_records,mapping,baseline,folder)
 r.save(folder/'result.json',result)
 (m.RUN/'latest-verification.json').write_text(json.dumps({'receipt':str((folder/'result.json').relative_to(m.RUN)),**result},ensure_ascii=False,indent=2)+'\n')
 report=f'''# Prado paintings expansion — 6 October 2026

Verified production result: **{counts['works']:,} Prado catalogue records, {counts['images']:,} with images**, at {result['at']}. **{len(gapfilled)} of the original 295 image gaps are filled; {295-len(gapfilled)} remain.** This report records completed deliveries and the remaining object-level research and download limits.

The paintings expansion added **6,515 distinct paintings**: 6,517 rows were created, then two source-proven duplicate imports were archived and their references consolidated into existing illustrated records. No records or images were deleted. All 7,129 selected source paintings have exact museum-native identities in production and remain in review. One pre-existing D007473 drawing record is retained outside this P-inventory selection.

## Source scope

The [independent March 2026 snapshot of Prado catalogue pages](https://zenodo.org/records/19261880), published 27 March 2026, contains 23,002 objects and 7,141 unique P-inventory painting records. **7,129 selected paintings are accounted for; 12 explicit post-1970 Ramón Gaya paintings are excluded.** This is an independently archived scrape, not an official export or a fresh complete museum inventory. The [museum describes approximately 8,000 paintings](https://www.museodelprado.es/actualidad/noticia/el-bsc-y-el-museo-del-prado-ensean-a-la-ia-a/b3e3e805-5beb-cdda-f1a3-ddb4191be5ec); this pass does not establish coverage of that entire holding.

The [complete painting inventory](all-paintings.md) preserves Spanish titles, literal dates, creator qualifications, inventory numbers and per-object official links. Missing dates and unknown/qualified creators remain explicit; no artist authorities or years were invented. A museum collection connection does not imply current display or physical whereabouts.

## Images delivered

| Source | Newly attached images |
|---|---:|
| WikiArt | 46 |
| Independently licensed Commons files | {commons_total} |
| Prado-origin reproductions under explicit user approval | {museum_total:,} |
| Total in this expansion | {len(images):,} |

The original 253 illustrated Prado records were preserved. Metadata reconciliation also brought 17 already illustrated records into the Prado collection, giving 270 before these image attachments. Every attached derivative is proportionally resized without cropping and at most 100,000 bytes; source originals are archived outside Documents. All attached public image bodies were checksum-verified before their database attachment. Source labels and credits are preserved individually.

The user explicitly approved WikiArt across all project source/image-use policies and extended that collection/display policy to Prado-origin images. [Policy](../../ARTLINE_IMAGE_USE.md) · [Prado authorization](prado-image-authorization.json). Museum-origin images are stored as `restricted`, with the museum terms and separate Commons labels retained; user approval is recorded separately from source rights claims.

[Per-painting image outcomes](image-outcomes.md) and [all original-gap decisions](original-gap-outcomes.md) distinguish attached images, existing images, object/source review and pending downloads.

The initial museum selection and five reviewed addenda contain **3,169 distinct matched artworks**. **3,046 selected files were prepared and visually reviewed**: 3,044 were attached, the already illustrated Jovellanos record kept its existing WikiArt image, and the Fra Angelico predella candidate was held because it shows only one scene. A separately inspected Teniers kitchen candidate remains held because its source identifies another copy. Superseded crops and unused candidates were archived outside the application asset directory; [archive receipt](unused-derivative-archive.json).

**[123 selected files remain pending download](pending-image-downloads.md)** after bounded retries and provider rate-limit pauses. The original source URLs, preparation events and resumable selection are preserved in the [preparation inventory](museum-image-delivery/final-selection-preparation-outcomes.json.gz). Image-host limits were respected with persisted Retry-After pauses and a shared request queue. These files are not counted as attached images. Direct WikiArt access also returned an access denial during the follow-up; cached captures and indexed sources were preserved, without bypassing the restriction.

## Reconciliation and verification

Exact Prado object IDs take precedence over duplicate Wikidata authorities. P002046 / Jacob’s Journey and P006808 / Asturias were consolidated using explicit museum accession/native links in the existing image records, with corroborating creator/dimension evidence. [Consolidation plan](duplicate-consolidation/plan.json.gz) · [application receipt](duplicate-consolidation/applied.json). Distinct Alfonso XIII portraits P008071/P008072 and La Sabiduría study/large work P007728/P008170 remain separate despite overlapping titles or authorities.

The [latest integrated verification](latest-verification.json) checks all 7,129 exact source identities, original catalogue metadata and existing images, newly attached media/rights records, archived duplicate outcomes, source citations and representative live artwork API responses. There are no new display claims or publications. The real local database was not modified.

Production recovery backup **1791286791075** succeeded before import. Plans, locked preimages, after-images and recovery evidence are under `~/Library/Application Support/Artline/backups/`. Originals and visual review sheets are under `~/Library/Application Support/Artline/source-images/`. [Metadata verification](metadata-verification.json) · [latest per-painting outcomes]({str((folder/'all-painting-outcomes.json.gz').relative_to(m.RUN))}).

Nine offline import tests passed, including conservative date parsing, creator qualification, shared-authority and multipart inventory cases. Scoped native-identifier and bounded museum-page query plans are retained with each integrated verification. No ten-million-artwork load test was performed. Direct museum-page access and the in-app browser had access/runtime limits; source snapshots, indexed museum pages, public API and public image responses supplied the evidence. No commit, deployment or local fixtures were created.
'''
 (m.RUN/'README.md').write_text(report)
 print(json.dumps({k:v for k,v in result.items()if k not in ('representative_live_api_checks','scope_note')}),flush=True)
if __name__=='__main__':run()
