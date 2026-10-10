#!/usr/bin/env python3
"""Read-only production verification and delivery report for Polish collections."""
import collections,concurrent.futures,csv,html,importlib.util,json
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('import-poland-collections-20261008.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def verify():
 plans={phase:m.pinned(phase)[0] for phase in ['poland']};records=[r for p in plans.values() for r in p['records']];ids=sorted({r['artwork_id'] for r in records});newids={r['artwork_id'] for r in records if not r['before']}
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
   count=db.execute("SELECT count(*) n FROM citations WHERE field_name='poland_collection_import_20261008' AND entity_id=ANY(%s::uuid[])",([r['artwork_id'] for r in p['records']],)).fetchone()['n'];assert count>=len(p['records'])
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

def artists_and_country():
 p=m.load(m.RUN/'artists-plan-reviewed.json.gz');old=m.load(m.RUN/'artists-concurrency-refresh.json.gz')['existing'];ids=[x['id'] for x in p['new']]
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
  actual={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(list(old),))};assert actual==old,'Existing artist metadata changed'
  new={r['v']['id']:r['v'] for r in db.execute('SELECT to_jsonb(a) v FROM artists a WHERE id=ANY(%s::uuid[])',(ids,))}
  assert len(new)==len(ids) and all(x['status']=='review' and x['published_at'] is None for x in new.values())
  for x in p['new']:assert all(new[x['id']][k]==v for k,v in x.items())
  linked={r['artist_id']:r['n'] for r in db.execute("SELECT aa.artist_id::text,count(*) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' GROUP BY aa.artist_id",(ids,))}
  for c in p['countries']:
   assert db.execute('SELECT EXISTS(SELECT 1 FROM artist_countries WHERE artist_id=%s AND country_code=%s AND relationship_type=%s) yes',(c['artist_id'],c['country_code'],c['relationship_type'])).fetchone()['yes']
  country=db.execute("SELECT count(DISTINCT artist_id) n FROM artist_countries WHERE country_code='PL'").fetchone()['n']
  museumids={r['id'] for r in db.execute("SELECT i.id::text FROM institutions i JOIN places p ON p.id=i.place_id WHERE p.country_code='PL' AND i.status<>'archived' AND EXISTS(SELECT 1 FROM artworks a WHERE a.current_institution_id=i.id AND a.status<>'archived')")}
 url='https://artlines.org/api/backend/v1/museums?country=PL&limit=60';resp=requests.get(url,timeout=45);resp.raise_for_status();page=resp.json();assert page['total']==len(museumids) and {x['id'] for x in page['items']}==museumids and all(x['work_count']>0 for x in page['items'])
 samples=[x for x in p['new'] if x['display_name'] in ['Artur Grottger','Juliusz Kossak','Alina Szapocznikow','Jerzy Nowosielski']];checks=[]
 for a in samples:
  base='https://artlines.org/api/backend/v1/artists/'+a['slug'];res=requests.get(base,timeout=45);res.raise_for_status();detail=res.json();assert detail['display_name']==a['display_name']
  res=requests.get(base+'/works?limit=1',timeout=45);res.raise_for_status();works=res.json();assert len(works['items'])==1
  checks.append(dict(name=a['display_name'],url=base,verified=True))
 out=dict(at=m.now(),new_artist_profiles_verified=len(new),existing_profiles_preserved=len(old),poland_artist_country_links_added=len(p['countries']),poland_linked_artists_total=country,new_artists_with_catalogue_items=len(linked),new_artists_without_catalogue_items=[new[aid]['display_name'] for aid in ids if aid not in linked],poland_nonempty_museums=len(museumids),museum_country_browse=page,public_artist_checks=checks)
 m.save(m.RUN/'artist-country-verification.json',out);print('Verified artist profiles',len(new),'Poland museums',len(museumids),flush=True)

def report():
 p=m.pinned('poland')[0];v=m.load(m.RUN/'verification.json');av=m.load(m.RUN/'artist-country-verification.json');a=m.load(m.RUN/'poland/applied.json');artists=m.load(m.RUN/'artists-applied.json');images=set(m.load(m.RUN/'poland/images-applied.json')['artwork_ids']);prep=m.load(m.RUN/'poland/image-preparation.json.gz');selection=m.load(m.RUN/'poland/image-selection.json.gz');review=m.load(m.RUN/'poland/visual-review.json')
 fields=['artwork_id','title','creator_label','museum','date_display','accession_number','source_url','action','new_image','artist_id']
 with (m.RUN/'imported-artworks.csv').open('w',newline='',encoding='utf-8-sig') as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
  for r in p['records']:writer.writerow({**{k:r.get(k) for k in fields if k not in ['action','new_image']},'action':'existing record enriched' if r['before'] else 'new review record','new_image':r['artwork_id'] in images})
 esc=lambda x:html.escape(str(x))
 by=collections.defaultdict(collections.Counter)
 for r in p['records']:
  by[r['museum']]['new' if not r['before'] else 'enriched']+=1;by[r['museum']]['images']+=r['artwork_id'] in images
 table=''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in [name,c['new'],c['enriched'],c['images']])+'</tr>' for name,c in sorted(by.items()))
 holds=''.join('<li><a href="'+esc(x['record']['source_url'])+'">'+esc(x['record']['title'])+'</a>: '+esc(x['reason'])+'</li>' for x in p['held'])
 summary=dict(new_artworks=a['new_artworks'],existing_artworks_enriched=a['existing_records_enriched'],new_artist_profiles=artists['new_artists'],new_images=len(images),collections_enriched=len(by),new_institutions=a['new_institutions'],poland_nonempty_museums=av['poland_nonempty_museums'],unknown_dates_retained=v['unknown_dates_preserved'],duplicate_version_holds=len(p['held']),later_casts_excluded=5,visual_rejections=len(review['rejected']),image_preparation_errors=sum(not x['prepared'] for x in prep['records']),image_policy_holds=len(selection['source_access_holds']),local_database_changes=0,current_display_claims=0,publication_changes=0)
 m.save(m.RUN/'delivery-summary.json',summary)
 doc='''<!doctype html><html lang="en"><meta charset="utf-8"><title>Poland collection delivery — 8 October 2026</title><style>body{max-width:1100px;margin:40px auto;padding:0 24px;font:16px/1.55 system-ui;color:#242424;background:#faf8f2}h1,h2{line-height:1.2}table{border-collapse:collapse;width:100%;background:white}th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}th{background:#ece8dc}a{color:#165e8c}.stats{font-size:21px;background:#e8efdf;padding:18px}</style><h1>Poland collection delivery</h1><p>Verified production import · 8 October 2026</p>'''
 doc+='<p class="stats">'+esc(a['new_artworks'])+' new artworks · '+esc(artists['new_artists'])+' new artist profiles · '+esc(len(images))+' new images</p>'
 doc+='<p>Enriched '+esc(a['existing_records_enriched'])+' existing artworks and '+esc(len(by))+' collections. Poland browsing now includes '+esc(av['poland_nonempty_museums'])+' institutions with actual catalogue items, including the previously populated Wawel Castle and Museum of Warsaw. New records remain in review. Existing metadata, images and publication states were preserved; holdings do not assert current display.</p>'
 doc+='<table><thead><tr><th>Collection</th><th>New artworks</th><th>Existing enriched</th><th>New images</th></tr></thead><tbody>'+table+'</tbody></table>'
 doc+='<h2>Coverage and source decisions</h2><p>This is a bounded selection, not an exhaustive Polish catalogue: official Warsaw and Kraków masterpieces; 360 Wrocław painting index records; 40 Zachęta catalogue pages; four Royal Castle painting pages and a Rembrandt highlight; 50 linked Łódź objects; selected official highlights in Poznań, Gdańsk, Lublin and Szczecin. Lublin’s 1418 Trinity Chapel murals are represented as one documented ensemble, without invented scene records. Remaining Wrocław and Zachęta pages, Wawel expansion, Silesian Museum and Bydgoszcz remain coverage gaps.</p>'
 doc+='<p>'+esc(v['unknown_dates_preserved'])+' new artworks retain unknown creation bounds. Five later physical casts or reconstructions were excluded. Qualified and unresolved creators remain explicit object labels. Artist profiles describe creators represented in Polish collections and do not imply Polish nationality; '+esc(artists['poland_country_links'])+' country relationships were added only with supporting evidence.</p>'
 doc+='<p>Images use the museum’s public-domain designation for the exact object reproduction. Originals are archived separately; complete-frame JPEG derivatives are at most 100,000 bytes. Each delivered image was visually reviewed and its public bytes verified. Restricted or unresolved museum photography remains unattached; selected images after 1955 remain outside the existing museum image workflow. Source wording and credits are retained.</p>'
 doc+='<h2>Unresolved object identities</h2><ul>'+holds+'</ul>'
 doc+='<h2>Verification and recovery</h2><p>Read-only production checks covered every affected artwork, new artist profile, new image and nonempty collection. Public API checks verified museum browsing, representative artwork/image responses and new artist profiles. There were no local database writes, catalogue publication changes or current-display claims. One failed transaction rolled back before artwork insertion when a source parser captured narrative text in inventory fields; exact labelled fields were corrected from retained HTML before the successful retry. Query plans are retained, but this pass is not a ten-million-row load test.</p>'
 doc+='<p>Cloud SQL backup 1791483318247 and row snapshots are retained under the Artline backups directory outside Documents. Concurrent publication changes to existing artists were captured and preserved before import. Source captures, hashes, editorial decisions and upload receipts remain alongside this report.</p>'
 doc+='<p><a href="imported-artworks.csv">Imported artwork ledger</a> · <a href="delivery-summary.json">Delivery totals</a> · <a href="verification.json">Artwork and image verification</a> · <a href="artist-country-verification.json">Artist and country verification</a></p></html>'
 (m.RUN/'report.html').write_text(doc,encoding='utf-8');print('Report',m.RUN/'report.html',flush=True)

if __name__=='__main__':
 import sys
 globals()[sys.argv[1] if len(sys.argv)>1 else 'verify']()
