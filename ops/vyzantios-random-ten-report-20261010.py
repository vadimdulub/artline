#!/usr/bin/env python3
"""Read-only final catalogue reconciliation and a bounded local research report."""
import importlib.util, json, html, collections, shutil
from pathlib import Path
sp=importlib.util.spec_from_file_location('delivery','ops/vyzantios-random-ten-delivery-20261010.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
b=d.b;r=d.r;RUN=b.RUN
def derived_json(path,value):
 """Refresh generated views, never the immutable plans or source evidence."""
 temp=path.with_name(path.name+'.partial');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');temp.replace(path)
pairs=b.cohort();artists={x['artist']['id']:x['artist'] for x in pairs};source_rows=[];stats=[]
with r.connect('production') as db:
 catalog=db.execute("""SELECT a.id::text,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.status,
   aa.artist_id::text,ma.storage_path media_path,ma.source_page_url image_source_page,ma.rights_status,
   ma.license_label,ma.checksum_sha256,i.name institution,
   coalesce((SELECT jsonb_agg(jsonb_build_object('url',e.canonical_url,'scheme',e.scheme)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.canonical_url IS NOT NULL),'[]'::jsonb) sources
   FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
   LEFT JOIN media_assets ma ON ma.id=a.primary_media_id LEFT JOIN institutions i ON i.id=a.current_institution_id
   WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' ORDER BY aa.artist_id,a.normalized_title,a.id""",(list(artists),)).fetchall()
current={x['id']:x for x in catalog};assert len(catalog)==len(current)
for x in catalog:
 x['artist']=artists[x['artist_id']]['display_name'];x['artwork_url']='https://artlines.org/artists/'+artists[x['artist_id']]['slug']+'/works/'+x['id'];x['picture_url']=('https://artlines.org'+x['media_path']) if x['media_path'] and x['media_path'].startswith('/') else x['media_path'];x['source_picture_urls']=[]
for pair in pairs:
 a=pair['artist'];aid=a['id'];idx=r.load(RUN/'indexes'/(aid+'.json.gz'));sel=r.load(RUN/'selections'/(aid+'.json.gz'));delivery=r.load(RUN/'delivery-plans'/(aid+'.json.gz'));applied=r.load(RUN/'applied'/(aid+'.json'));verified=r.load(RUN/'verified'/(aid+'.json'));assert not verified['errors']
 selection={x.get('source_url',x.get('record',{}).get('index',{}).get('url')):x for x in sel['rows']};delivered={x['source_url']:x for x in delivery['rows']};images={x['artwork_id']:x for x in delivery['images']};api=r.load(RUN/'translations'/(aid+'-en.json.gz'))['items']
 for item in idx['items']:
  row=selection.get(item['url'],{});page=row.get('page') or row.get('record',{}).get('page') or {};workid=row.get('artwork_id');picture=page.get('image_url')
  if not picture:
   matches=[x for x in api if b.q.norm(x['title'])==b.q.norm(item['title']) and (str(x.get('yearAsString') or '')==str(item.get('source_date') or ''))]
   if len(matches)==1:picture=matches[0].get('image')
  action=row.get('action','excluded_after_1970');reason=row.get('reason') or row.get('image_hold') or ''
  if item['url'] in delivered:
   action='created_review' if row['action']=='create' else 'existing_enriched'
   reason=delivery['image_scope_holds'].get(workid,reason)
  elif workid in delivery['held']:action='identity_hold';reason=delivery['held'][workid]
  elif action=='hold':action='identity_hold'
  if action=='excluded_after_1970':reason='Explicit creation after the 1970 catalogue cutoff; source link retained only.'
  present=current.get(workid,{})
  out=dict(artist=a['display_name'],artist_id=aid,title=item['title'],source_date=item.get('source_date') or 'Unknown date',source_url=item['url'],source_picture_url=picture,source_rights_label=page.get('rights_label'),action=action,reason=reason,artwork_id=workid if present else None,artwork_url=present.get('artwork_url'),catalogue_picture_url=present.get('picture_url'),image_added=workid in images)
  source_rows.append(out)
  if present and picture:present['source_picture_urls'].append(picture)
  if present and not present.get('research_note'):present['research_note']=reason
 matching=[x for x in catalog if x['artist_id']==aid]
 stats.append(dict(artist=a['display_name'],artist_id=aid,artist_url='https://artlines.org/artists/'+a['slug'],wikiart_url=pair['source']['url'],source_entries=len(idx['items']),new_works=applied['created'],images_added=applied['attached'],before_works=sel['baseline_counts']['works'],before_images=sel['baseline_counts']['images'],after_works=len(matching),after_images=sum(bool(x['media_path']) for x in matching),unknown_date_image_holds=len(delivery['image_scope_holds']),identity_holds=sum(x['action']=='identity_hold' for x in source_rows if x['artist_id']==aid)))
assert len(source_rows)==800
native=r.load(RUN/'native-additions/plan.json.gz');native_images={x['artwork_id'] for x in r.load(RUN/'native-additions/images.json')};native_source=r.load(RUN/'vyzantios-native-sources.json.gz');aid=pairs[0]['artist']['id']
for x in native['rows']:
 present=current[x['id']];present['source_picture_urls'].append(x['source_image_url']);reason='' if x['id'] in native_images else 'Source picture linked; creation date unknown or outside the existing pre-1956 Greek museum image workflow.'
 present['research_note']=reason
 source_rows.append(dict(artist=artists[aid]['display_name'],artist_id=aid,title=x['title'],source_date=present['date_display'],source_url=x['url'],source_picture_url=x['source_image_url'],source_rights_label=x['rights_label'],action='created_review',reason=reason,artwork_id=x['id'],artwork_url=present['artwork_url'],catalogue_picture_url=present['picture_url'],image_added=x['id'] in native_images))
# Four native museum pages depict existing WikiArt objects; source overlap remains explicit.
overlap={'aurelie':'orel-1914','figures-3':'figures','interior-or-the-artists-room-in-paris':'interior-1913','self-portrait-7920':'self-portrait-1926'}
for x in native_source['objects']:
 key=x['url'].rstrip('/').rsplit('/',1)[1]
 if key not in overlap:continue
 match=next(y for y in source_rows if y['artist_id']==aid and y['source_url'].endswith('/'+overlap[key]));pic=next(y['src'] for y in x['images'] if 'Vyzantios' in (y.get('alt') or ''))
 source_rows.append(dict(match,source_url=x['url'],source_picture_url=pic,action='museum_source_overlap',reason='Same object visually reconciled; no duplicate artwork created.',image_added=False))
 current[match['artwork_id']]['source_picture_urls'].append(pic)
rhodes=r.load(RUN/'rhodes-creator-link-applied.json');x=current[rhodes['artwork_id']];source_rows.append(dict(artist=x['artist'],artist_id=aid,title=x['title'],source_date=x['date_display'],source_url=x['sources'][0]['url'] if x['sources'] else r.load(RUN/'rhodes-creator-link-plan.json')['citations'][0]['c']['source_url'],source_picture_url=None,source_rights_label='CC0 source record',action='existing_creator_link',reason='Original Greek creator label retained; linked to the verified artist. No image attached in this pass.',artwork_id=x['id'],artwork_url=x['artwork_url'],catalogue_picture_url=x['picture_url'],image_added=False))
stats[0]['new_works']+=7;stats[0]['images_added']+=2;stats[0]['existing_creator_links']=1
for x in catalog:x['source_picture_urls']=list(dict.fromkeys(x['source_picture_urls']))
summary=dict(at=r.now(),operation=b.OP,artists=stats,totals={k:sum(x.get(k,0) for x in stats) for k in ['source_entries','new_works','images_added','before_works','before_images','after_works','after_images','identity_holds','unknown_date_image_holds','existing_creator_links']},source_records=len(source_rows),source_records_with_picture_links=sum(bool(x['source_picture_url']) for x in source_rows),scope='Complete accessible WikiArt index pass for Periklis Vyzantios and ten reproducibly sampled artists, plus selected official Vyzantios museum object research. This is not a verified complete lifetime oeuvre for any artist.',new_records_status='review',local_database_connected=False,verification_errors=[])
assert summary['totals']['new_works']==424 and summary['totals']['images_added']==242
assert summary['totals']['after_works']==784 and summary['totals']['after_images']==369
assert stats[0]['after_works']==42 and stats[0]['after_images']==15
derived_json(RUN/'summary.json',summary);derived_json(RUN/'all-source-artworks.json',source_rows);derived_json(RUN/'catalogue-artworks.json',catalog)
# Archive research-only derivatives outside the deployable public folder, retaining the old manifests and a relocation map.
approved={x['path'] for p in (RUN/'delivery-plans').glob('*.json.gz') for x in r.load(p)['images']};approved.update(x['path'] for x in r.load(RUN/'native-additions/images.json'))
relocations=[]
for p in (RUN/'prepared-images').glob('*.json'):
 x=r.load(p)
 if x['path'] in approved:continue
 old=Path(x['visual_path']);new=b.ORIGINALS/'reference-derivatives'/old.name;new.parent.mkdir(parents=True,exist_ok=True)
 if old.exists():
  assert r.sha(old.read_bytes())==x['sha256']
  if new.exists():assert r.sha(new.read_bytes())==x['sha256'];old.unlink()
  else:shutil.move(old,new)
 assert new.exists() and r.sha(new.read_bytes())==x['sha256']
 relocations.append(dict(artwork_id=x['artwork_id'],old_path=str(old),research_path=str(new),sha256=x['sha256'],reason='Research reference only; not approved for production attachment.'))
r.save(RUN/'research-image-relocations.json',relocations)
if not (RUN/'native-additions/visual-review-annotation.json').exists():
 r.save(RUN/'native-additions/visual-review-annotation.json',dict(at=r.now(),original_review_sha256=r.sha((RUN/'native-additions/visual-review.json').read_bytes()),correction='Hammam depicts the exterior domed bathhouse, including the complete decorative frame. The word interior in the original review note was a transcription error; the approved image and object identity are unchanged.'))
# A compact, searchable offline gallery with 40 rows per page. Only public catalogue images load inline.
data=json.dumps(dict(summary=summary,catalogue=catalog,sources=source_rows),ensure_ascii=False).replace('<','\\u003c')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vyzantios and ten artists — artwork research</title><style>body{font:16px/1.5 system-ui,sans-serif;color:#24312e;background:#f7f5ef;margin:0}main{max-width:1280px;margin:auto;padding:36px 24px}h1{font:44px/1.15 Georgia,serif;max-width:800px}a{color:#215d54}p{max-width:1000px}.filters{display:flex;gap:12px;flex-wrap:wrap;margin:26px 0}input,select,button{font:inherit;padding:10px;background:white;border:1px solid #a6b0a9;border-radius:4px}input{flex:1;min-width:220px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #dde1dc;text-align:left;vertical-align:top}th{background:#e8ece5}td img{width:100px;height:110px;object-fit:contain;background:#f8f7f4}small{display:block;color:#55645c}.scroll{overflow-x:auto}nav{display:flex;gap:18px;align-items:center;margin:18px 0}.count{font-size:20px}.foot{font-size:14px;margin:32px 0}summary{cursor:pointer;font-weight:600}@media(max-width:600px){h1{font-size:32px}main{padding:20px 12px}th,td{padding:8px}td img{width:70px;height:85px}}</style><main><h1>Vyzantios and ten artists</h1><p class="count">424 new artwork records · 242 pictures added · 11 artists</p><p>Periklis Vyzantios now has <strong>42 catalogue works and 15 pictures</strong>. This pass records all 800 accessible WikiArt listings and 12 official museum object references. Source listings can represent the same work or different versions. Complete lifetime coverage is not established.</p><p>Works created after 1970 are excluded from new catalogue additions. Unknown dates stay explicit in review. Source picture links remain available when a picture could not be attached. Holdings do not establish current display.</p><details><summary>Results by artist</summary><div class="scroll"><table id="artists"><thead><tr><th>Artist</th><th>WikiArt entries</th><th>New works</th><th>Pictures added</th><th>Catalogue works</th><th>Catalogue pictures</th></tr></thead><tbody></tbody></table></div></details><div class="filters"><label>View <select id="view"><option value="catalogue">Catalogue works</option><option value="sources">All source listings and decisions</option></select></label><label>Artist <select id="artist"></select></label><input id="search" type="search" aria-label="Search titles" placeholder="Search artwork titles"></div><p id="count"></p><div class="scroll"><table><thead><tr><th>Picture</th><th>Artwork</th><th>Artist</th><th>Date</th><th>Sources and decision</th></tr></thead><tbody id="works"></tbody></table></div><nav><button id="prev">Previous</button><span id="page"></span><button id="next">Next</button></nav><p class="foot">Verified 10 October 2026. <a href="README.md">Research notes and remaining gaps</a> · <a href="summary.json">Summary data</a> · <a href="all-source-artworks.json">All source records</a> · <a href="catalogue-artworks.json">Catalogue records</a>. New records remain in review. Existing metadata, pictures and publication states were preserved.</p></main><script id="data" type="application/json">'''+data+'''</script><script>const D=JSON.parse(document.getElementById('data').textContent);const E=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const link=(u,t)=>u?`<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>`:'';let offset=0,rows=[];E('artist').innerHTML='<option value="">All artists</option>'+D.summary.artists.map(a=>`<option value="${a.artist_id}">${esc(a.artist)}</option>`).join('');E('artist').value=D.summary.artists[0].artist_id;E('artists').querySelector('tbody').innerHTML=D.summary.artists.map(a=>`<tr><td>${link(a.artist_url,a.artist)}</td>${['source_entries','new_works','images_added','after_works','after_images'].map(k=>`<td>${a[k]}</td>`).join('')}</tr>`).join('');function render(reset){if(reset)offset=0;const mode=E('view').value,q=E('search').value.toLowerCase(),artist=E('artist').value;rows=D[mode].filter(x=>(!artist||x.artist_id===artist)&&(!q||x.title.toLowerCase().includes(q)));E('count').textContent=`${rows.length} ${mode==='sources'?'source listings':'catalogue works'} match`;E('works').innerHTML=rows.slice(offset,offset+40).map(x=>{const pic=x.picture_url||x.catalogue_picture_url;const sourceLinks=mode==='sources'?[link(x.source_url,'Object source'),link(x.source_picture_url,'Source picture')]:[...(x.sources||[]).slice(0,3).map(s=>link(s.url,'Object source')),...(x.source_picture_urls||[]).slice(0,2).map(s=>link(s,'Source picture'))];return `<tr><td>${pic?`<a href="${esc(pic)}" target="_blank"><img loading="lazy" src="${esc(pic)}" alt="${esc(x.title)}"></a>`:'No attached picture'}</td><td>${link(x.artwork_url,x.title)||esc(x.title)}${x.institution?`<small>${esc(x.institution)} · holding</small>`:''}</td><td>${esc(x.artist)}</td><td>${esc(x.date_display||x.source_date||'Unknown date')}</td><td>${sourceLinks.filter(Boolean).join(' · ')}<small>${esc(x.action||x.status)}</small><small>${esc(x.reason||x.research_note||'')}</small></td></tr>`}).join('');E('page').textContent=rows.length?`${offset+1}–${Math.min(offset+40,rows.length)} of ${rows.length}`:'0';E('prev').disabled=offset===0;E('next').disabled=offset+40>=rows.length;}['view','artist','search'].forEach(id=>E(id).addEventListener(id==='search'?'input':'change',()=>render(true)));E('prev').onclick=()=>{offset=Math.max(0,offset-40);render(false)};E('next').onclick=()=>{offset+=40;render(false)};render(true);</script></html>'''
(RUN/'report.html').write_text(page)
print(json.dumps(summary['totals']));print('source rows',len(source_rows),'direct picture links',summary['source_records_with_picture_links'],'reference derivatives archived',len(relocations))
