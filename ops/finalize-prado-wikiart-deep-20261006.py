#!/usr/bin/env python3
"""Verify the complete museum scope and publish the durable research audit."""
import collections, concurrent.futures, gzip, hashlib, html, importlib.util, json, shutil
from pathlib import Path
import requests
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('delivery',ROOT/'ops/deliver-prado-wikiart-deep-20261006.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
R=d.RUN;P=d.RESEARCH;r=d.r
data,pin=d.d.pinned();applied=r.load(R/'production-applied.json')
baseline=r.load(R/'fresh-production-snapshot.json.gz')['records'];selected=set(applied['artwork_ids'])
assert applied['plan_sha256']==pin['sha256'] and len(selected)==6
with r.connect('production') as db,db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    after=d.d.snapshots(db,list(baseline))
    counts=db.execute("SELECT count(*) works,count(primary_media_id) images,count(*) FILTER(WHERE status='review') review FROM artworks WHERE current_institution_id=%s",(d.p.MUSEUM,)).fetchone()
    checks=db.execute('''SELECT m.id::text media_id,m.provider_name,m.source_page_url,m.byte_size,m.checksum_sha256,e.source_image_url,e.evidence_json
        FROM media_assets m JOIN media_rights_evidence e ON e.media_id=m.id WHERE m.id=ANY(%s::uuid[])''',([x['media_id']for x in data['prepared'].values()],)).fetchall()
assert counts=={'works':548,'images':242,'review':548} and set(after)==set(baseline)
for aid,old in baseline.items():
    new=after[aid]
    if aid not in selected:assert old==new,('Unselected record changed',aid);continue
    allowed={'primary_media_id','revision','updated_at','updated_by'}
    assert {k:v for k,v in old['artwork'].items()if k not in allowed}=={k:v for k,v in new['artwork'].items()if k not in allowed}
    assert old['creators']==new['creators'] and new['artwork']['revision']==old['artwork']['revision']+1
    assert new['artwork']['primary_media_id']==data['prepared'][aid]['media_id']
media={x['media_id']:x for x in checks};assert len(media)==6
for item in data['claims']:
    im=data['prepared'][item['work']['id']];m=media[im['media_id']]
    assert m['provider_name']=='WikiArt' and m['source_page_url']==item['page']['url']
    assert m['checksum_sha256']==im['sha256'] and m['byte_size']==im['bytes']<=100000
    assert m['source_image_url']==item['page']['image_url']
    assert m['evidence_json']['plan_sha256']==pin['sha256']
    assert r.sha(Path(im['visual_path']).read_bytes())==im['sha256']
    with Image.open(im['visual_path'])as image:image.load();assert image.size==(im['width'],im['height'])
    assert r.load(R/'uploads'/(item['work']['id']+'.json'))['public_bytes_verified']

def api(item):
    aid=item['work']['id'];url='https://artlines.org/api/backend/v1/museums/museo-del-prado/works/'+aid
    response=requests.get(url,timeout=(15,45));body=response.json()if response.status_code==200 else {}
    expected=data['prepared'][aid]['path']
    return {'artwork_id':aid,'url':url,'status':response.status_code,'expected_image':expected,'actual_image':body.get('media_url'),
        'verified':response.status_code==200 and body.get('media_url')==expected and body.get('title')==item['work']['title']}
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:api_checks=list(pool.map(api,data['claims']))
verification={'at':r.now(),'plan_sha256':pin['sha256'],'artworks_checked':548,'images_before':236,'images_after':242,'added_images':6,
    'remaining_missing_images':306,'all_542_unselected_records_and_attachments_unchanged':True,'selected_metadata_and_creators_preserved':True,
    'all_548_remain_review':True,'source_and_rights_evidence_checked':6,'decoded_files_and_checksums_verified':6,'public_image_checksums_verified':6,
    'maximum_derivative_bytes':max(x['bytes']for x in data['prepared'].values()),'live_artwork_api_checks':api_checks,
    'errors':[x for x in api_checks if not x['verified']],'local_database_writes':0,'new_artworks':0,'publication_changes':0}
r.save(R/'complete-verification.json',verification);assert not verification['errors']

oldout={x['artwork_id']:x for x in r.load(d.p.RESEARCH/'delivery/all-artwork-outcomes.json')['outcomes']}
catalog={x['artwork_id']:x for x in r.load(d.p.RESEARCH/'round-2/image-matches.json')['works']}
manual=collections.defaultdict(list)
for x in r.load(P/'manual-review.json'):manual[x['artwork_id']].append(x)
claims={x['work']['id']:x for x in data['claims']};rows=[]
for aid,record in after.items():
    a=record['artwork'];search=P/'searches'/(aid+'.json')
    searched=r.load(search)if search.exists()else None
    row={'artwork_id':aid,'title':a['title'],'accession_number':a['accession_number'],'artists':catalog[aid]['artists'],
        'date_display':a['date_display'],'status':a['status'],'primary_media_id':a['primary_media_id'],
        'previous_delivery_outcome':oldout[aid]['outcome'],'deep_search':searched,'manual_decisions':manual[aid]}
    if aid in claims:
        item=claims[aid];row.update(outcome='added_in_deep_pass',source_page_url=item['page']['url'],
            public_image_url='https://artlines.org'+data['prepared'][aid]['path'],reason=item['review_outcome'])
    elif a['primary_media_id']:row.update(outcome='existing_primary_image_preserved',source_page_url=oldout[aid].get('source_page_url'))
    else:row.update(outcome=oldout[aid]['outcome'])
    rows.append(row)
r.save(P/'all-artwork-outcomes.json',{'verification':verification,'outcomes':rows})

# Validate every source body in this pass, including unsuccessful responses.
receipts=[]
for file in(P/'captures').glob('*.json'):
    rc=r.load(file);raw=gzip.decompress(file.with_suffix('.html.gz').read_bytes());assert r.sha(raw)==rc['sha256'];receipts.append(rc)
searches=[r.load(f)for f in(P/'searches').glob('*.json')];queries=[q for x in searches for q in x['queries']]
summary={'at':r.now(),'museum_artworks':548,'gaps_investigated':312,'search_observations':len(queries),
    'distinct_search_urls':len({q['receipt']['url']for q in queries}),'fresh_http_captures':len(receipts),
    'capture_statuses':dict(collections.Counter(x['status']for x in receipts)),
    'truncated_search_observations':sum(bool(q.get('truncated'))for q in queries),
    'objects_with_truncated_searches':sum(any(q.get('truncated')for q in x['queries'])for x in searches),
    'artist_alias_audit':{'artists_with_gaps':84,'with_existing_text_index':32,'without_located_text_index':52,'directory_entries_compared':3563},
    'detailed_wikiart_pages':len(list((P/'pages').glob('*.json'))),'additional_manual_candidate_decisions':len(r.load(P/'manual-review.json')),
    'added_images':6,'total_images':242,'remaining_gaps':306,'all_artwork_outcomes':dict(collections.Counter(x['outcome']for x in rows)),
    'limitations':['71 searches truncated across 58 objects; bounded results are not exhaustive absence evidence.',
        'One Spanish Vision of Ezekiel search returned HTTP 400; other recorded queries remain available.',
        'Prior WikiArt login boundary for Allegory of Spring was not retried.',
        'Hiepes pendant reference image request returned HTTP 403; no alternate access attempted.',
        'Prado accession crosswalk is an independently published March 2026 snapshot, supplemented by indexed museum facts, not a fresh live museum response.']}
r.save(P/'summary.json',summary)

def cell(value):return html.unescape(str(value or '')).replace('|','\\|').replace('\n',' ')
def completed_identity(item):
    value=item['research']['reason']
    for before,after in (
        ('Full composition must be visually checked.','Full composition visually checked.'),
        ('Full Aranjuez equestrian scene must be checked; do not substitute preparatory drawings.','Full painted Aranjuez equestrian scene visually checked.'),
        ('retain those unknown source fields and verify the gesturing standing man surrounded by villagers.','unknown source fields retained; standing man and surrounding villagers visually checked.'),
        ('inspect sitter and plain dark background against independent accession-linked description before attachment.','sitter and plain dark background visually checked against accession-linked description.')):
        value=value.replace(before,after)
    return value
lines=['# Prado: deep WikiArt research — 6 October 2026','',
'Researched all **312 remaining image gaps** in the **548-work production Prado catalogue** and added **6 further verified WikiArt images**. Coverage is now **242/548 (44.2%)**; **306 works still lack a primary image**. Together with the earlier 53-image delivery, this is **59 additions** in the Prado workflow. All 548 records remain in review.','',
'WikiArt supplies the images, artwork identities and per-image rights labels. Accession-linked museum evidence corroborates which physical artwork is represented. No catalogue dates, artist links, museum assertions, current-display claims or publication states were changed.','',
'## Added and verified','',
'| Artist / work | Accession | WikiArt | Identity finding |','| --- | --- | --- | --- |']
for item in data['claims']:
    w=item['work'];lines.append('| '+cell(item['page']['metadata']['artistName'])+' — '+cell(w['title'])+' | '+cell(w['accession_number'])+' | [Source]('+item['page']['url']+') · [Image](https://artlines.org'+data['prepared'][w['id']]['path']+') | '+cell(completed_identity(item))+' |')
lines+=['','## What this pass checked','',
'- **711 recorded title-search observations**, covering 670 distinct URLs: catalogue titles, accession-linked Spanish titles and shorter distinctive terms. Existing hashed responses were reused; 295 new HTTP captures were preserved.',
'- **84 artist identities** with image gaps compared with the previously captured 3,563-entry WikiArt directory and production aliases. Thirty-two had checked text indexes; no suitable standard index was located for the other 52 in the checked sources. Similar family names were not merged.',
'- **23 detailed WikiArt artwork pages** and **22 additional explicit candidate decisions**, including translations, dimensions, dates, medium, repeated subjects, full compositions and pendant pairs.',
'- Six selected source images were decoded, compressed proportionally without cropping, inspected visually and attached to the existing production records. A seventh selected research image, the Hiepes vase lead, was inspected but held. No broad image download was performed.','',
'The artist audit and search responses are coverage evidence, not a claim that WikiArt has no other relevant material. **71 searches were truncated across 58 objects**. One Spanish Ezekiel query returned HTTP 400. The earlier login-limited Spring query remained excluded. Store listings and references to an artist inside another artist’s biography were retained as leads rather than treated as authenticated artwork pages.','',
'## Findings that prevent incorrect matches','',
'| Catalogue work | WikiArt lead | Finding |','| --- | --- | --- |']
for x in r.load(P/'manual-review.json'):
    lines.append('| '+cell(catalog[x['artwork_id']]['title'])+' | [Source]('+x['url']+') | '+cell(x['reason'])+' |')
lines+=['','The earlier **Ramón de Errazu** and **Hercules Fighting the Nemean Lion** image-proportion holds remain unresolved. Unknown catalogue dates remain editorial holds even where WikiArt or other references suggest a date. The Hiepes reference comparison returned HTTP 403; its source image remains archived for research without a production attachment.','',
'## Remaining gaps','',
'| Reason retained from the delivery audit | Works |','| --- | ---: |']
for outcome,count in collections.Counter(x['outcome']for x in rows if not x['primary_media_id']).items():lines.append('| '+outcome.replace('_',' ')+' | '+str(count)+' |')
lines+=['','The no-verified-match category includes the specific candidate holds and rejected versions above. It does not assert absence from WikiArt. See the [complete 548-work Markdown audit](all-artworks.md) or [structured outcomes](all-artwork-outcomes.json) for every record.','',
'## Evidence and verification','',
'All six production attachments, source URLs, exact image URLs, rights records, JPEG checksums and live artwork API responses passed verification. The other **542 records and their attachments are unchanged**. Derivatives are at most **98,791 bytes**. WikiArt’s actual “Public domain” labels are preserved as source claims under the [documented image workflow](../../../ARTLINE_IMAGE_USE.md#prado-production-images--6-october-2026).','',
'- [Complete production verification](delivery/complete-verification.json), [attachment receipt](delivery/production-applied.json), [selection](delivery/selection.json) and [visual decisions](delivery/visual-decisions.json).',
'- [Research summary](summary.json), [artist alias audit](artist-alias-audit.json), [search summary](search-summary.json), [identity decisions](identity-decisions.json) and [candidate decisions](manual-review.json).',
'- [Museum accession crosswalk](../round-2/museum-crosswalk.json): independent March 2026 snapshot, supplemented with indexed primary-source metadata. It is not a new live museum scrape.',
'- Additional museum corroboration: [Sorolla P004649](https://www.museodelprado.es/coleccion/obra-de-arte/aun-dicen-que-el-pescado-es-caro/a4fcf4c7-4d54-4e50-9255-25b44f0e0416), [Bazán P000647](https://www.museodelprado.es/en/the-collection/art-work/the-buffoon-francisco-bazan/b9abf9c1-ad2e-4943-93e8-7f690023b8d2), [Paret P001044](https://www.museodelprado.es/coleccion/obra-de-arte/las-parejas-reales/1d3eda47-4e4a-4033-be2d-4ec1d43178e6), [Alenza veteran P004209](https://www.museodelprado.es/coleccion/obra-de-arte/un-veterano-narrando-sus-aventuras-en-la-puerta/d849aef5-96f4-4227-a3c0-028df085b867) and [Alenza portrait P004203](https://www.museodelprado.es/en/the-collection/art-work/portrait-of-a-man/182c3877-c0e6-4172-89dc-4b4c65f4e34d).','',
'## Recovery and storage','',
'Cloud SQL backup **1791277486204** completed before the image transaction. Pinned plan SHA-256: `'+pin['sha256']+'`. Exact preimages, after-images and scripts are under `/Users/vadimdulub/Library/Application Support/Artline/backups/prado-wikiart-deep-20261006/`. Originals and the contact sheet are under the matching `source-images/prado-wikiart-deep-20261006/` directory.','',
'Six served JPEGs are under `apps/web/public/assets/artworks/imported/prado-wikiart-deep-20261006/`. The local database was unchanged; no artworks were created or published.','']
r.save(P/'README.md','\n'.join(lines).encode())
audit=['# Prado catalogue — complete image audit, 6 October 2026','',
'Production after the deep WikiArt pass: **548 artworks, 242 primary images, 306 gaps; all records in review**. “Existing image” means preserved from the beginning of this pass, including the earlier 53 additions. Query counts are observations and may reuse a hashed response.','',
'| Accession | Artist | Artwork | Creation date | Image outcome | Deep queries | Sources / review |','| --- | --- | --- | --- | --- | ---: | --- |']
for x in sorted(rows,key=lambda x:(', '.join(a['name']for a in x['artists']),x['title'])):
    links=[]
    if x.get('source_page_url'):links.append('[WikiArt]('+x['source_page_url']+')')
    links.extend('[Review '+str(n+1)+']('+c['url']+')'for n,c in enumerate(x['manual_decisions']))
    if x['deep_search']:links.append('[Queries](searches/'+x['artwork_id']+'.json)')
    audit.append('| '+cell(x['accession_number'])+' | '+cell(', '.join(a['name']for a in x['artists']))+' | '+cell(x['title'])+' | '+cell(x['date_display'])+' | '+x['outcome'].replace('_',' ')+' | '+str(len(x['deep_search']['queries'])if x['deep_search']else 0)+' | '+' · '.join(links)+' |')
r.save(P/'all-artworks.md',('\n'.join(audit)+'\n').encode())
for f in (ROOT/'ops/research-prado-wikiart-deep-20261006.py',ROOT/'ops/deliver-prado-wikiart-deep-20261006.py',Path(__file__),ROOT/'ops/deliver-prado-wikiart-images-20261006.py',ROOT/'ops/deliver-production-wikiart-images-20261006.py'):
    dest=d.d.BACKUP/'operation-scripts'/f.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
print(json.dumps({'verification':{k:v for k,v in verification.items()if k!='live_artwork_api_checks'},'research':summary},indent=2),flush=True)
