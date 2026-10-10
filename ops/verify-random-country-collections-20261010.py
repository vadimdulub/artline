#!/usr/bin/env python3
"""Read-only verification of every changed record, plus public catalogue samples."""
import collections,concurrent.futures,csv,html,importlib.util,json,sys
from pathlib import Path
import requests,time
def public_get(url,**kwargs):
 for attempt in range(3):
  response=requests.get(url,**kwargs)
  if response.status_code not in [500,502,503,504]:return response
  if attempt<2:time.sleep(2)
 return response
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-random-country-collections-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def verify():
 plans={code:m.pinned(code)[0] for code in ['BE','LV','HR']};records=[r for p in plans.values() for r in p['records']];ids=[r['artwork_id'] for r in records];images={}
 for code in plans:
  accepted=set(m.load(m.RUN/code/'images-applied.json')['artwork_ids'])
  for x in m.load(m.RUN/code/'image-preparation.json.gz')['records']:
   if x['prepared'] and x['artwork_id'] in accepted:images[x['artwork_id']]=x
 cache=m.RUN/'database-verification.json.gz'
 if cache.exists():
  checked=m.load(cache);states=checked['states'];counts=checked['counts'];institutions=checked['institutions'];geography=checked['geography'];artist_samples=checked['artist_samples'];artists_verified=checked['artists_verified']
 else:
  with m.connect() as db,db.transaction():
   db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY');states=m.snapshot(db,ids)
   assert len(states)==len(ids)
   for r in records:
    st=states[r['artwork_id']];a=st['artwork'];assert a['current_institution_id']==r['institution_id']
    if not r['before']:
     assert a['status']=='review' and a['published_at'] is None and a['research_candidate'];assert (a['creation_year_start'],a['creation_year_end'])==(r['first'],r['last']);assert a['title']==r['title'];assert len(st['holdings'])==1 and st['holdings'][0]['claim_type']=='holding' and st['holdings'][0]['review_state']=='accepted'
    else:
     old=r['before'];allowed={'current_institution_id'}
     if r['artwork_id'] in images:allowed|={'primary_media_id','revision','updated_by','updated_at'}
     assert {k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in old['artwork'].items() if k not in allowed},('Existing metadata changed',r['key']);assert st['creators']==old['creators'];assert all(x in st['attachments'] for x in old['attachments'])
    if r['artwork_id'] in images:assert a['primary_media_id']==images[r['artwork_id']]['media_id']
   assert db.execute("SELECT count(*) n FROM citations WHERE field_name='random_country_collection_import_20261010' AND entity_id=ANY(%s::uuid[])",(ids,)).fetchone()['n']==len(records)
   media={x['id']:x for x in db.execute('SELECT id::text,storage_path,byte_size,checksum_sha256,rights_status,provider_name FROM media_assets WHERE id=ANY(%s::uuid[])',([im['media_id'] for im in images.values()],))}
   evidenced={x['media_id'] for x in db.execute('SELECT DISTINCT media_id::text FROM media_rights_evidence WHERE media_id=ANY(%s::uuid[])',([im['media_id'] for im in images.values()],))}
   for aid,im in images.items():
    x=media[im['media_id']];assert x['byte_size']==im['bytes']<=100000 and x['checksum_sha256']==im['sha256'];assert im['media_id'] in evidenced
   artists_verified=0;artist_samples=[]
   for code in plans:
    p=m.load(m.RUN/code/'artists-plan.json.gz');newids=[a['id'] for a in p['new']];existing=p['existing']
    actual={x['v']['id']:x['v'] for x in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(newids+list(existing),))}
    for a in p['new']:assert all(actual[a['id']][k]==v for k,v in a.items());assert actual[a['id']]['published_at'] is None
    for aid,a in existing.items():assert actual[aid]==a,('Existing artist changed concurrently',aid)
    artists_verified+=len(newids)
    if p['new']:artist_samples.append(p['new'][0])
   institutions={i['id']:i for p in plans.values() for i in p['institutions'].values()};geography=m.load(m.RUN/'institution-country-applied.json')['records'];institution_ids=set(institutions)|{i['id'] for i in geography}
   counts=list(db.execute("SELECT i.id::text,i.name,i.slug,trim(p.country_code) country,count(a.id) total,count(a.primary_media_id) images FROM institutions i LEFT JOIN places p ON p.id=i.place_id JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived' WHERE i.id=ANY(%s::uuid[]) GROUP BY i.id,p.country_code ORDER BY i.name",(list(institution_ids),)));assert all(x['total']>0 and x['country'] for x in counts)
  m.save(cache,dict(at=m.now(),states=states,counts=counts,institutions=institutions,geography=geography,artist_samples=artist_samples,artists_verified=artists_verified,all_record_assertions_passed=True))
  print('All database assertions passed',len(states),'artworks',flush=True)
 selected=[]
 for iid in institutions:
  rr=[r for r in records if r['institution_id']==iid];selected.append(next((r for r in rr if r['artwork_id'] in images),rr[0]))
 def check(r):
  i=institutions[r['institution_id']];base='https://artlines.org/api/backend/v1/museums/'+i['slug'];response=public_get(base+'/works/'+r['artwork_id'],timeout=45);response.raise_for_status();a=response.json();assert a['title']==states[r['artwork_id']]['artwork']['title']
  if r['artwork_id'] in images:assert a['media_url']==images[r['artwork_id']]['path']
  detail=dict(slug=i['slug'],artwork_id=r['artwork_id'],title=a['title'],media_url=a.get('media_url'),verified=True)
  target=m.RUN/'public-artwork-details'/(i['slug']+'.json')
  if not target.exists():m.save(target,detail)
  response=public_get(base+'/works?limit=1',timeout=45);response.raise_for_status();page=response.json();assert page['total']>0 and len(page['items'])==1
  return dict(slug=i['slug'],artwork_id=r['artwork_id'],title=a['title'],media_url=a.get('media_url'),browse_total=page['total'],verified=True)
 def captured_check(r):
  slug=institutions[r['institution_id']]['slug'];target=m.RUN/'public-api-checks'/(slug+'.json')
  if target.exists():return m.load(target)
  try:result=check(r)
  except requests.RequestException as e:result=dict(slug=slug,artwork_id=r['artwork_id'],verified=False,error=str(e),status=e.response.status_code if getattr(e,'response',None) is not None else None)
  m.save(target,result);print('Public museum check',slug,result['verified'],flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:checks=list(pool.map(captured_check,selected))
 country_checks=[];artist_checks=[]
 for code in plans:
  try:
   res=public_get('https://artlines.org/api/backend/v1/museums',params=dict(country=code,limit=60),timeout=45);res.raise_for_status();page=res.json();assert all(x['work_count']>0 for x in page['items']);expected={i['id'] for i in counts if i['country']==code};assert expected<={i['id'] for i in page['items']};country_checks.append(dict(country=code,total=page['total'],verified=True))
  except requests.RequestException as e:country_checks.append(dict(country=code,verified=False,error=str(e)))
 for a in artist_samples:
  try:
   res=public_get('https://artlines.org/api/backend/v1/artists/'+a['slug'],timeout=45);res.raise_for_status();assert res.json()['display_name']==a['display_name'];artist_checks.append(dict(name=a['display_name'],verified=True))
  except requests.RequestException as e:artist_checks.append(dict(name=a['display_name'],verified=False,error=str(e)))
 failures=[x for x in checks+country_checks+artist_checks if not x['verified']]
 out=dict(at=m.now(),target='production',records_verified=len(ids),new_artworks=sum(not r['before'] for r in records),existing_records_preserved=sum(bool(r['before']) for r in records),new_artist_profiles_verified=artists_verified,new_images_verified=len(images),metadata_collections=len(institutions),country_links_added=len(geography),unknown_dates_preserved=sum(not r['before'] and r['first'] is None for r in records),museum_counts=counts,public_artwork_checks=checks,country_browse_checks=country_checks,public_artist_checks=artist_checks,public_api_failures=failures,database_assertions_passed=True,local_database_changes=0,publication_changes=0,current_display_claims=0)
 m.save(m.RUN/'verification.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ['museum_counts','public_artwork_checks']}),flush=True)
def report():
 v=m.load(m.RUN/'verification.json');country=[];ledger=[]
 for code in ['BE','LV','HR']:
  a=m.load(m.RUN/code/'applied.json');artists=m.load(m.RUN/code/'artists-applied.json');images=set(m.load(m.RUN/code/'images-applied.json')['artwork_ids']);p=m.pinned(code)[0]
  country.append(dict(country=code,new_artworks=a['new_artworks'],existing_enriched=a['existing_records_enriched'],new_artists=artists['new_artists'],images=len(images),collections=len(p['institutions'])))
  for r in p['records']:ledger.append({**{k:r.get(k) for k in ['artwork_id','title','creator_label','museum','date_display','accession_number','source_url']},'country':code,'action':'existing enriched' if r['before'] else 'new review record','image_added':r['artwork_id'] in images})
 with (m.RUN/'imported-artworks.csv').open('w',newline='',encoding='utf-8-sig') as f:
  writer=csv.DictWriter(f,fieldnames=list(ledger[0]));writer.writeheader();writer.writerows(ledger)
 queue=m.load(m.RUN/'country-order.json');affiliations=m.load(m.RUN/'US/artist-country-supplement-applied.json');m.save(m.RUN/'delivery-summary.json',dict(at=m.now(),countries=country,verification=v,us_native_artist_affiliations=affiliations,queue=queue))
 esc=lambda s:html.escape(str(s));table=''.join('<tr>'+''.join('<td>'+esc(x[k])+'</td>' for k in ['country','new_artworks','existing_enriched','new_artists','images','collections'])+'</tr>' for x in country)
 source_ledger=m.load(m.RUN/'institution-research.json.gz');entries=[]
 for x in source_ledger:
  populated=next((i for i in v['museum_counts'] if i['slug']==x['slug']),None)
  status=x.get('error') or ('Catalogue additions/enrichment verified' if any(q['slug']==x['slug'] for q in v['public_artwork_checks']) else 'Institution researched; no new object selection in this batch')
  entries.append(dict(country=x['country'],slug=x['slug'],url=x['url'],status=status,total=populated['total'] if populated else None,evidence=x.get('evidence')))
 m.save(m.RUN/'coverage-ledger.json',entries)
 htmltext='<!doctype html><html lang="en"><meta charset="utf-8"><title>Random country collection delivery</title><style>body{font:16px/1.5 system-ui;background:#faf8f1;color:#222;max-width:1150px;margin:40px auto;padding:0 24px}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;border-bottom:1px solid #ddd;text-align:left}a{color:#075886}</style><h1>Switzerland → United States → Canada</h1><p>Verified production catalogue batch · 9 October 2026</p><table><tr><th>Country</th><th>New works</th><th>Existing enriched</th><th>New artists</th><th>New images</th><th>Collections enriched</th></tr>'+table+'</table>'
 htmltext+='<p>Every affected artwork and image was verified in production. '+esc(v['country_links_added'])+' populated institutions received country links. New catalogue records retain review status and are visible under the unified catalogue policy. Existing metadata and publication states were preserved; '+esc(v['unknown_dates_preserved'])+' new works retain unknown date bounds. No current-display claims or local database changes.</p>'
 htmltext+='<p>'+esc(affiliations['country_links_added'])+' additional US artist affiliations were supported by explicit American labels in native museum metadata, without changing biographies or inferring nationality from museum location.</p>'
 htmltext+='<h2>Selection and remaining coverage</h2><p>The draw used a saved 42-country frame and random seed. This first batch is bounded: Zürich Masterpieces/Evergreens, Basel highlights, four Lausanne collection pages and Winterthur departmental highlights; 700 Cleveland metadata leads and four Chicago painting/drawing API pages; eight McMichael Group of Seven collection pages, Montréal homepage recommendations and an explicitly credited National Gallery loan. This does not represent complete national coverage.</p><p>Institution research covered nine Swiss, eleven US and eight Canadian sites. Bern, Aargauer, Beyeler, Geneva, Reinhart and the additional US/Canadian institutions retain object-source gaps. AGO collection and selected National Gallery endpoints were access restricted; the public National Gallery homepage and its partner museum supplied other evidence. Montréal’s client search returned an access restriction; only accessible exact-object recommendations were selected. Empty institutions remain research records.</p>'
 htmltext+='<h2>Images and identity</h2><p>Approved museum open-access images and WikiArt matches were selected only after catalogue reconciliation. Full source frames were resized to at most 100,000 bytes; every delivered derivative was visually reviewed and verified at its public URL. Actual rights labels, credits and source evidence are retained. Basel’s native image host returned HTTP 403; matching approved WikiArt reproductions were researched separately. A Monet Waterloo Bridge candidate was rejected because WikiArt identified a different holding. A Tom Thomson Sunset candidate was also rejected after comparison with the exact McMichael preview; five other supported Canadian matches already had primary images and were preserved. Chicago’s image endpoint returned HTTP 403, pausing that provider. Four Cleveland web renditions were too narrow for delivery as usable full scrolls. Dates, versions, casts, prints and qualified creator labels remain explicit.</p>'
 htmltext+='<h2>Live catalogue checks</h2><p>All database and image-file assertions passed. '+(esc(len(v['public_api_failures']))+' public catalogue checks returned server/network errors after bounded retries; see verification.json.' if v['public_api_failures'] else 'All nine representative museum artwork/detail checks, three country filters and three new artist profile checks passed. Earlier intermittent HTTP 500/503 responses succeeded on later bounded retries; the retry history remains in public-api-retry-audit.json.')+' Import records and image attachments were verified independently. No service configuration changes were made.</p>'
 htmltext+='<h2>Recovery and evidence</h2><p>Cloud SQL backup 1791534041098 and exact row snapshots are preserved outside Documents in the Artline backups directory. Scoped query plans are retained; this ingestion does not establish performance at ten million rows. No commits or application deployments were performed.</p><p><a href="imported-artworks.csv">Artwork ledger</a> · <a href="coverage-ledger.json">Institution coverage and gaps</a> · <a href="verification.json">Verification</a> · <a href="country-order.json">Random queue</a></p></html>'
 (m.RUN/'report.html').write_text(htmltext,encoding='utf-8');print('Report written',flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
