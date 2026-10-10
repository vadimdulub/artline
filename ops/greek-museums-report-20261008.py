#!/usr/bin/env python3
"""Render the verified delivery and a candid national coverage ledger, offline."""
import collections, csv, html, importlib.util, json
from pathlib import Path
spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('greek-museums-verify-20261008.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
d,RUN=v.d,v.RUN


def csvfile(name,rows,fields):
    with (RUN/name).open('w',newline='',encoding='utf-8-sig')as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)


def main():
    result=d.load(RUN/'verification.json');assert not result['errors']
    p=v.plans();facts={f['artwork_id']:f for f in p['records']};images={};after={}
    for name in ['catalogue-applied.json','supplement-catalogue-applied.json','native-catalogue-applied.json']:
        receipt=d.load(RUN/name);after.update({x['artwork']['id']:x['artwork']for x in d.load(Path(receipt['after_path']))})
    quality=d.load(RUN/'quality-corrections-applied.json');after.update({x['artwork']['id']:x['artwork']for x in quality['after']})
    for batch in ['greek','native']:
        images.update({x['image']['artwork_id']:x['image']for x in d.load(RUN/(batch+'-image-plan.json.gz'))['records']})
        after.update({x['id']:x for x in d.load(RUN/(batch+'-images-applied.json'))['after']})
    totals=result['museum_totals'];byid={m['id']:m for m in totals};museum_new=collections.Counter(f['museum']['id']for f in facts.values()if f['action']=='create');museum_images=collections.Counter(im['museum']['id']for im in images.values())
    for m in totals:
        m.update(new_artworks=museum_new[m['id']],new_images=museum_images[m['id']],url='https://artlines.org/museums/'+m['slug'])
    csvfile('museums.csv',totals,['id','name','city','artworks','images','new_artworks','new_images','url'])
    delivery=[];image_gaps=[]
    holds={x['artwork_id']:x['reason']for x in d.load(RUN/'greek-image-candidates-v3.json')['held']}
    for batch in ['greek','native']:
        holds.update({x['artwork_id']:x['reason']for x in d.load(RUN/(batch+'-visual-review.json'))['held']})
    for aid,w in sorted(after.items()):
        f=facts.get(aid);im=images.get(aid);mu=byid[w['current_institution_id']]
        row=dict(artwork_id=aid,title=w['title'],creator=w.get('unlinked_creator_label')or(f['creator_label']if f else im['creator']),date_display=w['date_display'],creation_start=w['creation_year_start'],creation_end=w['creation_year_end'],status=w['status'],action=f['action']if f else'image_only',museum=mu['name'],museum_id=mu['id'],source_url=f['source_url']if f else im['source_url'],source_id=f['source_id']if f else im['source_id'],image_added=bool(im),image_path=im['path']if im else'',image_sha256=im['sha256']if im else'',image_provider=im['provider_name']if im else'',rights_status=im['rights_status']if im else'',rights_label=im['rights_label']if im else'',artwork_url='https://artlines.org/museums/'+mu['slug']+'?work='+aid)
        delivery.append(row)
        if f and f['action']=='create'and not w['primary_media_id']:
            image_gaps.append(dict(artwork_id=aid,title=w['title'],museum=mu['name'],source_url=f['source_url'],reason=holds.get(aid,'Creation date unknown in selected native source; image retained as a research gap.')))
    assert len(delivery)==result['artwork_records_verified']
    csvfile('delivery.csv',delivery,list(delivery[0]));csvfile('image-gaps.csv',image_gaps,['artwork_id','title','museum','source_url','reason'])
    entries=d.load(RUN/'ministry-directory-audit.json')['entries'];nameindex={d.norm(m['name']):m for m in totals};ledger=[]
    for e in entries:
        planned=p['museums'].get('ministry-'+e['key']);mu=byid.get(planned['row']['id'])if planned else nameindex.get(d.norm(e['name']))
        row=dict(directory_id=e['key'],name=e['name'],greek_name=e.get('greek_name'),region=e.get('region'),source_url=e['source_url'],checked_at=e['receipt']['retrieved_at'],directory_content='soft_404'if 'ERROR 404'in e['source_text']else'content_available',coverage='catalogue_items_available'if mu else'object_research_remaining',institution_id=mu['id']if mu else'',artworks=mu['artworks']if mu else 0,images=mu['images']if mu else 0,object_research='Individual source-backed review objects delivered; this is selected coverage, not the complete collection.'if mu else'No individually verified object delivered for this directory identity in this pass; this does not mean the museum has no objects.',native_website='; '.join(a['url']for a in e['outgoing_links']if 'museum' in a['title'].lower()))
        ledger.append(row)
    csvfile('ministry-coverage.csv',ledger,list(ledger[0]))
    selected=d.load(RUN/'collection-selection.json')['keys'];sc_counts=collections.Counter(f.get('raw',{}).get('collection')for f in facts.values()if f['source']=='searchculture');digital=[]
    for e in d.load(RUN/'searchculture-directory.json'):
        digital.append(dict(key=e['key'],title=e['title'],url=e['url'],selected_objects=sc_counts[e['key']],status='selected_objects_delivered'if sc_counts[e['key']]else'collection_screened_no_selected_delivery'if e['key']in selected else'directory_indexed_not_selected',description=e['description']))
    csvfile('digital-collections.csv',digital,list(digital[0]))
    icom=d.load(RUN/'discovery/2f282646d55f6aa8da98f59a77316e32210168c3f2c12b74084e25fe0bf3ce12.json')
    icomlinks=[x for x in icom['links']if x['title']and x['title'].upper()==x['title']and 'icom-greece.gr'not in x['url']]
    icomlinks=list({(x['title'],x['url']):x for x in icomlinks}.values())
    for x in icomlinks:x['status']='Additional directory lead; exact institution and eligible object review required unless already represented in museums.csv.'
    csvfile('icom-directory-leads.csv',icomlinks,['title','url','status'])
    covered=sum(bool(x['institution_id'])for x in ledger);soft=sum(x['directory_content']=='soft_404'for x in ledger)
    summary=dict(at=d.now(),**{k:result[k]for k in ['new_artworks','existing_artworks_linked','new_museums','images','artwork_records_verified']},greek_collections=len(totals),total_artworks=sum(x['artworks']for x in totals),total_images=sum(x['images']for x in totals),directory_entries=len(ledger),directory_entries_with_catalogue=covered,directory_entries_requiring_object_research=len(ledger)-covered,directory_soft_404=soft,new_artworks_without_images=len(image_gaps),digital_collections_indexed=len(digital),icom_directory_leads=len(icomlinks),all_greek_museums_complete=False)
    if (RUN/'delivery-summary.json').exists():summary['at']=d.load(RUN/'delivery-summary.json')['at']
    d.save(RUN/'delivery-summary.json',summary)
    authorization=dict(recorded_at=d.now(),user_instruction="let's cover all greek museums and upload pictures and artworks",date='2026-10-08',scope='Nationwide museum research; selected source-backed production review catalogue additions, supported holding links and authentic image delivery. Real local catalogue queried read-only.',source_policy='Existing Greek museum/artist image continuation dated 20 September 2026; selected works dated by 1955. WikiArt remains an approved source; actual rights labels retained. This is user workflow approval, not a copyright-holder licence.',metadata_policy='Creation by 1970; unknown and qualified dates stay in review. No invented items, date years, biographies or current-display claims. Museums without verified catalogue objects remain research entries.',backup_id='1791471559641')
    if (RUN/'authorization.json').exists():authorization['recorded_at']=d.load(RUN/'authorization.json')['recorded_at']
    d.save(RUN/'authorization.json',authorization)
    lines=f'''# Greek museums — production delivery, 8 October 2026

Delivered **{summary['new_artworks']} new review artworks**, **{summary['images']} new primary images**, and **{summary['existing_artworks_linked']} supported holding link to an existing artwork**. Greek browsing now contains **{summary['greek_collections']} collections, {summary['total_artworks']:,} artworks and {summary['total_images']} illustrated works**. The pass created {summary['new_museums']} institutions with real catalogue items. [Browse Greece](https://artlines.org/museums?country=GR) · [Delivery report](report.html) · [Per-artwork results](delivery.csv) · [Museum totals](museums.csv).

## Coverage and remaining work

The request was “let's cover all greek museums and upload pictures and artworks.” This is a nationwide research and selected-delivery pass, **not complete coverage of every Greek museum**. All {summary['directory_entries']} entries in the [Ministry directory](https://archaeologicalmuseums.culture.gov.gr/en) were checked. {summary['directory_entries_with_catalogue']} have an exact catalogue institution represented in this delivery; {summary['directory_entries_requiring_object_research']} still require individual-object research. The {summary['greek_collections']} collections also include fine-art, folk-art, religious and institutional collections outside this directory. The directory is not a census of all Greek institutions.

The [complete Ministry ledger](ministry-coverage.csv) records every listed identity, source, region, status and native-site lead. HTTP 200 alone was insufficient: {soft} entries returned soft 404 pages (Benaki, Cycladic Art and Historical Museum of Crete); native and museum-supplied catalogues were used where available. A directory description or gallery-room photograph was never imported as an invented object. Empty institutions remain excluded from browsing.

All 163 [SearchCulture collection-directory entries](digital-collections.csv) were indexed; 39 museum/gallery candidates were screened with bounded first-page and oldest-page metadata selections. The Ministry public National Archive catalogue was searched by 45 store-location labels, reconciled to 44 museum/collection identities. Additional native research covered Acropolis, Goulandris, Cycladic Art, Delphi, Olympia and Crete. The [ICOM directory leads](icom-directory-leads.csv) preserve another discovery route. These are overlapping research lists, not additive museum counts. No exhaustive image harvesting was performed.

## Selection and source decisions

- Metadata is supported by exact object identifiers, accession numbers or uniquely named native museum highlights. Works dated after 1970 were not imported; uncertain dates remain explicit review values. Anonymous creators, qualified workshops and fragmentary antiquities are retained without invented biographies or years. Physical print edition dates take precedence over the date of the depicted subject or artist biography.
- All new artwork records remain `review`, unpublished and research candidates. Holding assertions are accepted on documented object-level evidence; no current-display assertions were added. Editorial confidence is a judgment, not a statistically calibrated probability.
- The 62 Goulandris image updates preserve all existing catalogue metadata. All prior primary images were preserved. El Greco’s existing *Mount Sinai* was reused and linked to the Historical Museum of Crete using the native collection and [WikiArt’s explicit holding](https://www.wikiart.org/en/el-greco/mount-sinai-1570); no duplicate was created.
- The early *Baptism of Christ* remains a version-reconciliation lead. The existing WikiArt reproduction is an arched panel; the museum’s text and older caption disagree on 1567/1569. The detailed native resource returned HTTP 500 and its Commons-origin image returned HTTP 403. No guessed merge or new duplicate was delivered.
- Three Ministry records called bronze bracelets in English were corrected to **gold earrings** using their Greek titles, gold material and object descriptions. Original conflicting text remains in source captures and audit history.
- Thirteen Varnavas objects were assigned to the **Interactive Agricultural and Folklore Museum of Varnavas**, which their object-level location identifies, instead of the broad European Bread Museum repository label. Previous holding assertions were superseded and preserved. Three suspicious 1905 calendar strings were cleared to explicit unknown creation dates; their images were withheld. No replacement year was inferred.
- Near-identical Paros icon compositions were checked against distinct inventory numbers, panel construction and signatures. Different physical versions remain separate records.

## Image delivery

All {summary['images']} newly attached images were visually reviewed, uploaded with create-only storage writes, and retrieved through the public site with exact SHA-256 verification. The main batch has 489 images; the native follow-up has 11. Three cropped PLI thumbnails were replaced with complete files from their public file viewers. Delphi’s Charioteer uses the complete surviving statue photograph after excluding a bust, hand detail and reconstruction diagram. The cropped Apollo cylix image remains withheld.

Derivatives preserve the complete selected source frame and original source marks, with proportional resizing and a maximum of 100,000 bytes. Actual rights labels, credits, page/file URLs and source evidence remain separate from user source approval. Restricted labels were not converted into public-domain claims. Originals are archived outside Documents.

There are {len(image_gaps)} [new artwork records without an image](image-gaps.csv), principally because creation dates are unknown or later than the existing 1955 museum-image cutoff. Records remain available for research and museum browsing. Known download failures are preserved in evidence, including the transient Ministry download recovered in the follow-up.

## Verification and recovery

[Verification JSON](verification.json) records {result['artwork_records_verified']} complete artwork-row checks, {len(result['artwork_api_checks'])} museum artwork API samples and all {len(result['public_image_checks'])} public image checksums. Bounded country API pages returned every expected museum with a positive visible-work count. Source identities, selection evidence, accepted holdings, rights evidence, audit coverage and review/publication safeguards passed. Local baseline counts were unchanged: {result['local_baseline_counts_unchanged']}. The local database was queried read-only, with no fixtures or test databases.

The authoritative metadata plans are `delivery-plan-v4.json.gz`, `supplement-delivery-plan.json.gz`, `native-delivery-plan-v2.json.gz` and `quality-correction-plan.json.gz`. Image plans are `greek-image-plan.json.gz` and `native-image-plan.json.gz`; visual reviews bind specific contact-index and image checksums. Earlier plan versions are retained for provenance and must not be reapplied. Applied receipts and transaction after-states distinguish actual delivery from candidates and holds.

Cloud SQL backup **1791471559641** completed before writes. Before/after snapshots are under `/Users/vadimdulub/Library/Application Support/Artline/backups/greek-museums-20261008/`; original images, contact sheets and procedures are under the matching `source-images/greek-museums-20261008/` directory. Accepted application derivatives use `apps/web/public/assets/artworks/imported/greek-museums-20261008/` and matching paths in the production image bucket. No application deployment or commit was performed.
'''
    (RUN/'README.md').write_text(lines,encoding='utf-8')
    esc=lambda value:html.escape(str(value))
    rows=''.join('<tr><td><a href="'+esc(m['url'])+'">'+esc(m['name'])+'</a></td><td>'+esc(m['city'])+'</td><td>'+str(m['artworks'])+'</td><td>'+str(m['images'])+'</td><td>'+str(m['new_artworks'])+'</td><td>'+str(m['new_images'])+'</td></tr>'for m in totals)
    document=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Greek museums — Artline delivery</title><style>body{{max-width:1120px;margin:48px auto;padding:0 24px;color:#1d302c;background:#f8f5ec;font:17px/1.6 Georgia,serif}}h1{{font-size:42px;line-height:1.2}}a{{color:#1d6254}}.numbers{{font:600 26px/1.4 system-ui}}input{{font:inherit;padding:10px;width:min(90%,480px);border:1px solid #a2aba0;background:white}}table{{width:100%;border-collapse:collapse;margin-top:20px;font:14px/1.5 system-ui}}th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid #d2d9cf}}th{{background:#e8ece1}}.table{{overflow:auto}}footer{{font-size:14px;margin:36px 0}}</style><h1>Greek museums</h1><p>Verified production delivery · 8 October 2026</p><p class="numbers">{summary['new_artworks']} new artworks · {summary['images']} new images · {summary['greek_collections']} collections available</p><p>{summary['total_artworks']:,} catalogue artworks across the listed collections. New records remain in review; images and holding evidence are attached.</p><p><strong>Country coverage remains incomplete.</strong> All {len(ledger)} official directory entries were checked; {len(ledger)-covered} still require individual-object research. This list includes additional art and religious collections beyond that directory.</p><p><a href="https://artlines.org/museums?country=GR">Browse Greece</a> · <a href="README.md">Research and verification notes</a> · <a href="delivery.csv">Artwork results</a> · <a href="ministry-coverage.csv">All Ministry entries</a> · <a href="image-gaps.csv">Image gaps</a></p><label for="filter">Find a collection or city</label><br><input id="filter" type="search" placeholder="Type a museum or city"><div class="table"><table><thead><tr><th>Collection</th><th>City</th><th>Artworks</th><th>Images</th><th>New works</th><th>New images</th></tr></thead><tbody>{rows}</tbody></table></div><footer>All {len(images)} new public images passed checksum verification. Original source labels and publication states are preserved. Holdings do not establish current display.</footer><script>document.getElementById('filter').addEventListener('input',function(){{const q=this.value.toLocaleLowerCase();document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.textContent.toLocaleLowerCase().includes(q))}})</script></html>'''
    (RUN/'report.html').write_text(document,encoding='utf-8');print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
