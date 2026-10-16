#!/usr/bin/env python3
"""Reconcile all fifty completed batches and produce source-linked local reports."""
import importlib.util,json,html,collections,shutil,csv
from pathlib import Path
sp=importlib.util.spec_from_file_location('delivery','ops/wikiart-500-painters-delivery-20261011.py');d=importlib.util.module_from_spec(sp);sp.loader.exec_module(d)
r=d.r;b=d.b;RUN=d.RUN

def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.partial');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)

def write_csv(path,rows,fields):
 with path.open('w',encoding='utf-8-sig',newline='') as out:
  writer=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');writer.writeheader()
  for row in rows:writer.writerow({key:json.dumps(row[key],ensure_ascii=False) if isinstance(row.get(key),(dict,list)) else row.get(key) for key in fields})

def main():
 pairs=b.cohort();artists={x['artist']['id']:x['artist'] for x in pairs};batch_of={x['artist']['id']:x['batch'] for x in pairs};catalog=[];source_rows=[];stats=[]
 correction_path=RUN/'post-delivery-reconciliations.json';corrections=r.load(correction_path) if correction_path.exists() else {'reconciliations':[]}
 reconciled={x['archived_artwork_id']:x for x in corrections['reconciliations']}
 archived_by_artist=collections.Counter(x['artist_id'] for x in reconciled.values())
 duplicate_references={}
 for path in (RUN/'duplicate-review-decisions').glob('*.json'):
  for pair in r.load(path)['pairs']:
   canonical=pair.get('canonical_artwork_id')
   if canonical:
    for candidate in pair['artwork_ids']:
     if candidate!=canonical:duplicate_references[candidate]=dict(canonical_artwork_id=canonical,reason=pair['reason'])
 # Scope every query to a single artist. This is an offline research artifact, not a production API.
 with r.connect('production') as db:
  for aid in artists:
   catalog.extend(db.execute("""SELECT a.id::text,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.status,a.primary_media_id::text,
    aa.artist_id::text,ma.storage_path media_path,ma.delivery_url,ma.source_page_url image_source_page,ma.rights_status,ma.license_label,ma.checksum_sha256,i.name institution,
    coalesce((SELECT jsonb_agg(jsonb_build_object('url',e.canonical_url,'scheme',e.scheme)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.canonical_url IS NOT NULL),'[]'::jsonb) sources
    FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id LEFT JOIN media_assets ma ON ma.id=a.primary_media_id LEFT JOIN institutions i ON i.id=a.current_institution_id
    WHERE aa.artist_id=%s AND a.status<>'archived' ORDER BY a.normalized_title,a.id""",(aid,)).fetchall())
 current={x['id']:x for x in catalog}
 for x in catalog:
  x.update(artist=artists[x['artist_id']]['display_name'],batch=batch_of[x['artist_id']],artwork_url='https://artlines.org/artists/'+artists[x['artist_id']]['slug']+'/works/'+x['id'],picture_url=x['delivery_url'] or (('https://artlines.org'+x['media_path']) if x['media_path'] and x['media_path'].startswith('/') else x['media_path']),source_picture_urls=[])
 unlinked=r.load(RUN/'unlinked-index-entries.json.gz')
 for pair in pairs:
  a=pair['artist'];aid=a['id'];idx=r.load(RUN/'indexes'/(aid+'.json.gz'));sel=r.load(RUN/'selections'/(aid+'.json.gz'));delivery=r.load(RUN/'delivery-plans'/(aid+'.json.gz'));applied=r.load(RUN/'applied'/(aid+'.json'));verified=r.load(RUN/'verified'/(aid+'.json'));assert not verified['errors']
  selected={x.get('source_url',x.get('record',{}).get('index',{}).get('url')):x for x in sel['rows'] if x.get('source_scheme')!='wikiart-legacy-content-id'}
  delivered={x['source_id']:x for x in delivery['rows']};images={x['artwork_id']:x for x in delivery['images']};api=r.load(RUN/'translations'/(aid+'-en.json.gz'))['items'];entries=[]
  for item in idx['items']:entries.append((item,selected.get(item['url'],{}),'linked_artwork_page'))
  for item in [v for v in unlinked if v['artist_id']==aid]:
   row=next((v for v in sel['rows'] if v.get('index_entry')==item),{})
   entries.append((dict(title=item['title'],source_date=item['source_date'],date=item.get('date'),url=pair['source']['url']+'/all-works/text-list'),row,'index_entry_without_artwork_page'))
  if not idx['items'] and not any(v['artist_id']==aid for v in unlinked):
   for v in api:entries.append((dict(title=v['title'],source_date=str(v.get('yearAsString') or ''),date=None,url=pair['source']['url']),{},'artist_api_only_index_unavailable'))
  start=len(source_rows)
  for item,row,kind in entries:
   page=row.get('page') or row.get('record',{}).get('page') or {};wid=row.get('artwork_id');picture=page.get('metadata',{}).get('image') or page.get('image_url');sid=row.get('source_id');date=item.get('source_date') or 'Unknown date'
   if not picture:
    matches=[v for v in api if b.q.norm(v['title'])==b.q.norm(item['title']) and str(v.get('yearAsString') or '')==str(item.get('source_date') or '')]
    if len(matches)==1:picture=matches[0].get('image')
   action=row.get('action');reason=row.get('reason') or row.get('image_hold') or ''
   if sid in delivered:
    wid=delivered[sid]['artwork_id'];action='created_review' if delivered[sid]['action']=='create' else 'existing_enriched';reason=delivery.get('manual_image_holds',{}).get(wid) or delivery['image_scope_holds'].get(wid) or delivered[sid].get('reviewed_source_discrepancy',{}).get('reason') or delivered[sid].get('reviewed_existing_match',{}).get('reason') or reason
   elif wid in delivery['held']:action='identity_hold';reason=delivery['held'][wid]
   elif action=='hold':action='identity_hold'
   elif action=='excluded':action='excluded_after_1970'
   elif not action:
    if kind=='linked_artwork_page':action='excluded_after_1970';reason='Explicit source-index creation date after the 1970 cutoff.'
    elif kind=='artist_api_only_index_unavailable':action='source_identity_hold';reason='The artist index is unavailable; no individual artwork-page identity was guessed from an artist API entry.'
    elif item.get('date') and item['date']['creation_year_start']>1970:action='excluded_after_1970';reason='Explicit source-index creation after 1970; no artwork-page link.'
    else:action='source_identity_hold';reason='Index listing lacks an individual artwork-page link; exact object identity is not resolved.'
   original_wid=wid
   if wid in reconciled:
    reason=reconciled[wid]['basis'];wid=reconciled[wid]['canonical_artwork_id'];action='existing_reconciled'
   elif wid in duplicate_references and duplicate_references[wid]['canonical_artwork_id'] in current:
    reason=duplicate_references[wid]['reason'];wid=duplicate_references[wid]['canonical_artwork_id'];action='duplicate_reference'
   present=current.get(wid,{})
   out=dict(batch=pair['batch'],artist=a['display_name'],artist_id=aid,title=item['title'],source_date=date,source_url=item['url'],source_kind=kind,source_picture_url=picture,source_rights_label=page.get('rights_label'),action=action,reason=reason,artwork_id=wid if present else None,artwork_url=present.get('artwork_url'),catalogue_picture_url=present.get('picture_url'),image_added=original_wid in images)
   if original_wid in reconciled:out['archived_duplicate_artwork_id']=original_wid
   source_rows.append(out)
   if present and picture:present['source_picture_urls'].append(picture)
   if present and reason:present['research_note']=reason
  matching=[x for x in catalog if x['artist_id']==aid];rows=source_rows[start:]
  stats.append(dict(batch=pair['batch'],batch_rank=pair['batch_rank'],artist=a['display_name'],artist_id=aid,artist_url='https://artlines.org/artists/'+a['slug'],wikiart_url=pair['source']['url'],source_entries=len(rows),index_status=idx.get('outcome',idx.get('status')),new_works=applied['created']-archived_by_artist[aid],gross_created=applied['created'],archived_duplicates=archived_by_artist[aid],images_added=applied['attached'],before_works=sel['baseline_counts']['works'],before_images=sel['baseline_counts']['images'],after_works=len(matching),after_images=sum(bool(x['primary_media_id']) for x in matching),date_scope_image_holds=len(delivery['image_scope_holds']),manual_image_holds=len(delivery.get('manual_image_holds',{})),identity_holds=sum('hold' in x['action'] for x in rows),verified=True))
 for x in catalog:x['source_picture_urls']=list(dict.fromkeys(x['source_picture_urls']))
 keys=['source_entries','new_works','gross_created','archived_duplicates','images_added','before_works','before_images','after_works','after_images','identity_holds','date_scope_image_holds','manual_image_holds']
 batches=[]
 for n in range(1,51):
  subset=[x for x in stats if x['batch']==n];assert len(subset)==10
  batches.append(dict(batch=n,artists=subset,totals={k:sum(x[k] for x in subset) for k in keys},verified=True))
 summary=dict(at=r.now(),operation=b.OP,artists=stats,batches=batches,totals={k:sum(x[k] for x in stats) for k in keys},artists_researched=500,batches_completed=50,source_records=len(source_rows),source_records_with_picture_links=sum(bool(x['source_picture_url']) for x in source_rows),source_outcomes=dict(collections.Counter(x['action'] for x in source_rows)),scope='Complete accessible WikiArt-index research pass for 500 existing artist profiles (including collective and non-painter profiles already present in Artline) prioritized by estimated catalogue gaps in 50 batches. An unavailable index and unlinked listings remain explicit. This does not establish a complete lifetime oeuvre for any artist.',new_records_status='review',local_database_connected=False,verification_errors=[])
 summary['post_delivery_reconciliation']=corrections
 summary['report_browser_limitation']=r.load(RUN/'report-browser-limitation.json') if (RUN/'report-browser-limitation.json').exists() else None
 summary['quality_review']=r.load(RUN/'quality-final-review.json')
 summary['component_review']=r.load(RUN/'component-final-review.json')
 summary['production_preflight']=r.load(RUN/'production-preflight.json')
 summary['catalogue_count_note']='Current catalogue totals may include concurrent additions by other operations. This operation’s additions are counted only from its own committed receipts and documented reconciliations.'
 summary['distinct_current_catalogue_artworks']=len(current)
 summary['distinct_current_catalogue_images']=sum(bool(row['primary_media_id']) for row in current.values())
 summary['count_grouping_note']='Per-artist and batch totals count artwork associations; an artwork shared by creators can occur in more than one artist total. Distinct catalogue counts are supplied separately.'
 for name,value in [('summary.json',summary),('all-source-artworks.json',source_rows),('catalogue-artworks.json',catalog)]:write_json(RUN/name,value)
 write_csv(RUN/'artist-results.csv',stats,['batch','artist','artist_id','artist_url','wikiart_url','source_entries','new_works','images_added','before_works','before_images','after_works','after_images','identity_holds','date_scope_image_holds','manual_image_holds','verified'])
 write_csv(RUN/'source-artworks.csv',source_rows,['batch','artist','title','source_date','source_url','source_picture_url','source_rights_label','action','reason','artwork_id','artwork_url','catalogue_picture_url','image_added'])
 write_csv(RUN/'added-artworks.csv',[row for row in source_rows if row['action']=='created_review'],['batch','artist','title','source_date','source_url','source_picture_url','artwork_id','artwork_url','catalogue_picture_url','image_added','reason'])
 write_csv(RUN/'added-pictures.csv',[row for row in source_rows if row['image_added']],['batch','artist','title','source_date','artwork_id','artwork_url','catalogue_picture_url','source_url','source_picture_url','source_rights_label'])
 for n in range(1,51):
  part=batches[n-1];folder=RUN/'batches'/f'{n:02d}';sc=[x for x in source_rows if x['batch']==n];cc=[x for x in catalog if x['batch']==n]
  for name,value in [('summary.json',part),('source-artworks.json',sc),('catalogue-artworks.json',cc)]:write_json(folder/name,value)
  render_batch(folder,part,sc,cc)
  supersede_preview(folder,'source-research.html',dict(part,production_delivery_completed=True),sc)
 approved={im['path'] for plan,pin in d.pinned_deliveries() for im in plan['images']};relocations=[]
 for p in (RUN/'prepared-images').glob('*.json'):
  x=r.load(p)
  if x.get('outcome')!='prepared' or x['path'] in approved:continue
  old=Path(x['visual_path']);new=d.ORIGINALS/'reference-derivatives'/old.name;new.parent.mkdir(parents=True,exist_ok=True)
  if old.exists():
   assert r.sha(old.read_bytes())==x['sha256']
   if new.exists():assert r.sha(new.read_bytes())==x['sha256'];old.unlink()
   else:shutil.move(old,new)
  assert r.sha(new.read_bytes())==x['sha256'];relocations.append(dict(artwork_id=x['artwork_id'],old_path=str(old),research_path=str(new),sha256=x['sha256']))
 write_json(RUN/'research-image-relocations.json',relocations)
 render_index(summary)
 supersede_preview(RUN,'source-research-report.html',dict(summary,production_delivery_completed=True,blocker=None),source_rows)
 print(json.dumps({'totals':summary['totals'],'source_records':len(source_rows),'picture_links':summary['source_records_with_picture_links'],'archived_research_derivatives':len(relocations)}))

STYLE='body{font:16px/1.5 system-ui;color:#26372f;background:#f7f5ef;margin:0}main{max-width:1300px;margin:auto;padding:32px 22px}h1{font:42px/1.2 Georgia,serif}a{color:#205c4c}table{border-collapse:collapse;width:100%;background:white}th,td{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid #ddd}th{background:#e7ece4}small{display:block;color:#58645e}.filters,nav{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}input,select,button{font:inherit;padding:10px;border:1px solid #9ba79d;background:white}input{flex:1}td img{width:100px;height:110px;object-fit:contain}.scroll{overflow-x:auto}.count{font-size:22px}p{max-width:1050px}@media(max-width:600px){h1{font-size:32px}main{padding:20px 10px}td,th{padding:7px}td img{width:70px;height:90px}}'
def supersede_preview(folder,filename,summary,sources):
 for name in [filename,'source-research-summary.json','source-research-artworks.json']:
  old=folder/name;archived=RUN/'progress-history'/old.relative_to(RUN)
  if old.exists() and not archived.exists():
   archived.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(old,archived)
 (folder/filename).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=report.html"><title>Completed artwork research</title><p>Production delivery is complete. <a href="report.html">Open the completed artwork and picture report.</a></p></html>')
 write_json(folder/'source-research-summary.json',summary);write_json(folder/'source-research-artworks.json',sources)
def shell(title,body):return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style><main>'+body+'</main></html>'
def render_index(s):
 t=s['totals'];frame=r.load(RUN/'sampling-frame.json.gz');gaps=r.load(RUN/'source-index-gaps.json');unlinked=r.load(RUN/'unlinked-index-entries.json.gz')
 rows=''.join(f'<tr><td><a href="batches/{x["batch"]:02d}/report.html">Batch {x["batch"]:02d}</a></td><td>'+html.escape(', '.join(a['artist'] for a in x['artists']))+f'</td><td>{x["totals"]["source_entries"]:,}</td><td>{x["totals"]["new_works"]:,}</td><td>{x["totals"]["images_added"]:,}</td></tr>' for x in s['batches'])
 intro=f'Completed and production-verified: 500 existing artist profiles in 50 batches, {t["new_works"]:,} net new review records and {t["images_added"]:,} added pictures.'
 sampling=f'This review selects 500 distinct artists by estimated catalogue gaps from {len(frame["frame"]):,} matched identities, excluding {len(frame["excluded_artist_ids"]):,} artist IDs in the recorded earlier cohorts. The selection ranking and complete sampling-frame evidence are preserved; fresh production identity validation preceded delivery.'
 scope=f'{s["source_records"]:,} source listings and {s["source_records_with_picture_links"]:,} direct source-picture links are recorded. Accessible indexes were checked in full; this does not establish a complete lifetime catalogue. There are {len(gaps["painters"])} unavailable indexes and {len(unlinked)} entries without individual source artwork links.'
 correction=f'{t["gross_created"]:,} records were created; {t["archived_duplicates"]} new duplicates were subsequently archived through documented reconciliation.' if t['archived_duplicates'] else 'Duplicate and conflicting source identities were screened before insertion; this campaign did not archive any existing artwork.'
 body=f'<h1>WikiArt review · 500 artist profiles</h1><p class="count">{t["new_works"]:,} new artworks · {t["images_added"]:,} pictures added</p><p>'+html.escape(intro)+'</p><p>'+html.escape(sampling)+'</p><p>'+html.escape(scope)+'</p><p>Active new records remain in review. Explicit creation dates after 1970 were excluded; unknown dates and attribution or version questions remain explicit. Existing pictures, holdings and publication state were preserved.</p><p>'+html.escape(correction+' '+s['catalogue_count_note'])+f'</p><div class="scroll"><table><thead><tr><th>Batch</th><th>Artists</th><th>Source listings</th><th>New works</th><th>Pictures added</th></tr></thead><tbody>{rows}</tbody></table></div><p><a href="artist-results.csv">500 artist results (CSV)</a> · <a href="added-artworks.csv">Added artworks (CSV)</a> · <a href="added-pictures.csv">Added pictures (CSV)</a> · <a href="README.md">Research notes</a> · <a href="summary.json">All artist results</a> · <a href="all-source-artworks.json">Source records</a> · <a href="catalogue-artworks.json">Catalogue records</a></p>'
 (RUN/'report.html').write_text(shell('WikiArt review — 500 artist profiles',body))
 lines=['# WikiArt review of 500 artist profiles','',intro,'','[Browse artworks and pictures](report.html). Each batch has ten artist results and a searchable, paginated artwork table.','',sampling,'',scope,'','## Results','','| Batch | New works | Pictures added | Artists |','|---|---:|---:|---|']
 for x in s['batches']:lines.append(f'| [{x["batch"]:02d}](batches/{x["batch"]:02d}/report.html) | {x["totals"]["new_works"]} | {x["totals"]["images_added"]} | '+', '.join(a['artist'] for a in x['artists'])+' |')
 lines+=['','## Source and identity review','','- WikiArt is the approved image reference. Actual source rights labels, credits, retrieval receipts, source images and checksums are preserved separately from user approval.','- Known dates after 1970 are excluded. New images retain the existing 1955 creation cutoff; later and unknown dates keep their source links. Unknown or conflicting creation dates remain explicit in review. Version, attribution, translation and duplicate questions are recorded; source listings need not represent distinct physical objects.','- Existing images, catalogue metadata and holding assertions are preserved. Personal selections do not assert museum designation or current display.','',correction,'',s['catalogue_count_note'],'','## Verification','','- Fresh production identity validation, a successful Cloud SQL backup, immutable plans, and per-artist application and verification receipts support the results. Image uploads use create-only object generations and public byte verification. Bounded public artist APIs confirm every delivered record, including unillustrated review works, and every delivered attachment.','- Every selected image receives decoding, dimensions, proportions, byte-budget, checksum and duplicate checks. Visual sampling covers each artist and all flagged identity, low-resolution and placeholder cases. It does not imply manual viewing of every image.','- Backups, originals, review sheets and held derivatives live under Artline Application Support outside Documents. The real local database is unchanged. No commits, application deployment or publication were performed.','','## Data','','- [All 500 artist results](summary.json)', '- [Artist results CSV](artist-results.csv)', '- [Added artworks CSV](added-artworks.csv)', '- [Added pictures CSV](added-pictures.csv)', '- [Complete source decision CSV](source-artworks.csv)','- [All source listings and picture URLs](all-source-artworks.json)','- [Current catalogue artwork records](catalogue-artworks.json)','- [Frozen sample](cohort.json)','']
 (RUN/'README.md').write_text('\n'.join(lines))
 with (RUN/'README.md').open('a') as out:
  qa=s['quality_review'];pf=s['production_preflight']
  out.write(f'\n## Individual review evidence\n\n{qa["source_notes"]} source notes, {qa["visual_sheets_reviewed"]} ordinary contact sheets and {qa["additional_quality_sheets_reviewed"]} extra quality sheets were reviewed. The component scan covered {s["component_review"]["reviewed"]} title flags. Full and component views of the same altarpiece are reconciled explicitly; cropped details and mixed copy/original identities remain held.\n\n')
  if s.get('report_browser_limitation'):out.write('Browser visual/interaction checking was unavailable because the browser connection failed before execution. The report is checked structurally; production database, public API and public image-byte verification are independent. See [browser limitation](report-browser-limitation.json).\n\n')
  out.write('- [Individual source decisions](reviewed-source-discrepancies.json)\n- [Component and alternate-view review](component-final-review.json)\n- [Existing-image comparison](additional-image-reference-audit.json)\n- [Cross-creator comparison](cross-creator-image-audit.json)\n- [Production preflight](production-preflight.json)\n- [Pipelined precheck validation](pipelined-precheck-validation.json)\n- [Bounded write-window lifecycle validation](cooperative-write-window-validation.json)\n\n')
  out.write(f'Personal-selection membership uses {pf["position_groups_needed"]} append-only display ranks shared by each transaction group. The schema permits equal positions; no existing positions or schema were changed. The indexed single-artist query was checked on production; this does not establish ten-million-row performance. See [query and schema evidence](indexed-query-and-position-evidence.json).\n')

def render_batch(folder,part,sources,catalogue):
 n=part['batch'];t=part['totals'];data=json.dumps(dict(summary=part,sources=sources,catalogue=catalogue),ensure_ascii=False).replace('<','\\u003c')
 body=f'<p><a href="../../report.html">All 50 batches</a></p><h1>Batch {n:02d} · ten artists</h1><p class="count">{t["new_works"]:,} new works · {t["images_added"]:,} pictures added</p><p>Source listings include excluded dates and unresolved identities. Only attached catalogue pictures load inline; source reproductions are linked individually. Holdings do not establish current display.</p><details><summary>Artist results</summary><div class="scroll"><table id="artists"><thead><tr><th>Artist</th><th>Source listings</th><th>New works</th><th>Pictures added</th><th>Catalogue works</th><th>Catalogue pictures</th></tr></thead><tbody></tbody></table></div></details><div class="filters"><label>View <select id="view"><option value="catalogue">Catalogue works</option><option value="sources">Source listings and decisions</option></select></label><label>Artist <select id="artist"></select></label><input id="search" type="search" aria-label="Search titles" placeholder="Search artwork titles"></div><p id="count"></p><div class="scroll"><table><thead><tr><th>Picture</th><th>Artwork</th><th>Artist</th><th>Date</th><th>Sources and decision</th></tr></thead><tbody id="works"></tbody></table></div><nav><button id="prev">Previous</button><span id="page"></span><button id="next">Next</button></nav><p><a href="summary.json">Artist results</a> · <a href="source-artworks.json">Source records</a> · <a href="catalogue-artworks.json">Catalogue records</a></p><script id="data" type="application/json">'+data+'</script>'
 # Reuse the already visually checked, bounded 40-row report interaction.
 previous=(d.ROOT/'ops/vyzantios-random-ten-report-20261010.py').read_text();js=previous.split('<script>const D=')[1].split('</script>')[0]
 body+='<script>const D='+js+'</script>'
 (folder/'report.html').write_text(shell(f'Batch {n:02d} — artwork research',body))
if __name__=='__main__':main()
