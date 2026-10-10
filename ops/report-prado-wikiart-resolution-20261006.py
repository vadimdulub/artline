#!/usr/bin/env python3
"""Write the Prado resolution audit from verified delivery and captured sources."""
import collections, gzip, hashlib, html, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT/'docs/research/prado-wikiart-20261006'
RUN=PREV/'resolution-20261006'
OP='prado-wikiart-resolution-20261006'

def load(p):
    b=p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)

def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2))

def clean(x):return html.unescape(str(x or 'Unknown')).replace('|','\\|').replace('\n',' ')
def link(label,url):return '['+clean(label)+']('+url+')'
def source(url):return load(RUN/'pages'/(hashlib.sha256(url.encode()).hexdigest()+'.json'))

verification=load(RUN/'delivery/complete-verification.json')
assert not verification['errors'] and all(x['verified']for x in verification['live_artwork_api_checks'])
plan=load(RUN/'delivery/production-plan.json.gz')
claims={x['work']['id']:x for x in plan['claims']}
decisions=load(RUN/'identity-decisions.json')
extra=load(RUN/'further-conflict-decisions.json')
baseline=load(RUN/'production-snapshot.json.gz')['records']
backup=load(RUN/'delivery/cloud-sql-backup.json')

additional=[]
existing={x['source_page_url']:x for x in load(RUN/'additional-existing-source-matches.json')['records']}
specific={
 'P000778':'Source omits museum and physical dimensions; distinctive translated title and 1778 support the lead. Check full composition against the accession before import.',
 'P000780':'Source dimensions 295 × 272 cm conflict with museum 259 × 220 cm; identity/version and full frame require visual confirmation.',
 'P000795':'Source image dimensions are nearly square while museum canvas is portrait-format; find a complete source reproduction before attachment.',
 'P000802':'Source dimensions 97 × 160 cm conflict with museum 267 × 160 cm. Existing source-linked record must be reconciled, not duplicated.',
 'P000799':'Source dimensions 293 × 267 cm conflict with museum 269 × 396 cm; check the full source image before attachment.',
 'P007767':'Two WikiArt pages conflict on location and sitter naming. An alternate 1800 page gives exactly 216 × 144 cm but says Private Collection. Retain both and visually resolve the portrait before import.',
 'P007070':'Source says Private Collection; specific named sitter, 1805 and 125 × 207 cm agree with museum 124.7 × 207.7 cm. Prefer accession evidence for the museum association; retain source discrepancy.',
 'P002785':'Museum dataset names Goya; attribution has a history of disagreement. Retain source attribution and require an explicit accepted-creator review before any import.',
 'P000722':'Uncertain sitter remains Leocadia Zorrilla (?). Do not choose a sitter identity from the alternate WikiArt title.',
 'P001176':'Source dimensions retain the older wider format; museum dimensions are narrower. Full-image/version review is required before using this reproduction.',
 'P001177':'Source dimensions retain the older wider format; museum dimensions are narrower. Full-image/version review is required before using this reproduction.',
 'P001168':'Museum dates 1635–1636 versus WikiArt 1641–1644 are retained separately. Existing source-linked record requires reconciliation, not a new duplicate.',
}
for x in load(RUN/'additional-work-queue.json')+load(RUN/'additional-velazquez-queue.json'):
    page=source(x['url']);assert page.get('image_url') and page['public_domain_label']
    m=x['museum'];record=existing.get(x['url'])
    assert x['accession'] not in {a['artwork']['accession_number'] for a in baseline.values()}
    row={**x,'wikiart':page,'outcome':'reconcile_existing_record' if record else 'new_catalogue_candidate',
         'existing_record':record,'review_status':'research candidate; not imported or published',
         'note':specific.get(x['accession'],'Artist and specific artwork title support the accession crosswalk. Preserve both source and museum dates/dimensions; complete visual and attribution review before import or image attachment.'),
         'duplicate_check':'Read-only artist-scoped production title/accession comparison plus exact attached WikiArt source-page comparison. Alternate titles and unlinked creator records can still conceal duplicates.'}
    if x['accession']=='P007767':
        row['alternative_wikiart']=source('https://www.wikiart.org/en/francisco-goya/portrait-of-maria-teresa-of-ballabriga-countess-of-chinchon')
    additional.append(row)
assert len(additional)==53 and sum(x['existing_record'] is not None for x in additional)==7
save(RUN/'additional-artworks.json',{'metadata_only':True,'new_records_created':0,'image_downloads_for_discoveries':0,
    'counts':dict(collections.Counter(x['outcome']for x in additional)),'artworks':additional})

lines=['# Additional Prado works found through WikiArt','',
 '53 accession-level leads outside the 548-work Prado snapshot: **46 candidates for new records and 7 existing records to reconcile**. This is a research list, not an import receipt. All 54 WikiArt pages (including one alternate portrait version) were captured with source image URLs and actual public-domain labels; no images were downloaded for this discovery list.','',
 'Museum identities, dates and dimensions come from the independently preserved [Prado dataset](https://doi.org/10.5281/zenodo.19261880), matched by accession. The raw export and receipt are recorded in `../round-2/museum-crosswalk.json` and `../../artwork-locations-20261004/prado-dataset-receipt-20261005d.json`. Museum URLs below are source references; they are not a claim of a fresh direct museum-page fetch. No current-on-view claim is made.','',
 'Read-only production checks covered 1,168 Goya works and 48 Velázquez works via their artist IDs. Seven exact WikiArt source-page matches identify existing records; the other 46 are candidates rather than a guarantee that no differently attributed or unlinked duplicate exists.','',
 '| Accession / museum record | Artist / title on WikiArt | Museum date / WikiArt date | Outcome | Review note |','|---|---|---|---|---|']
for x in additional:
    p=x['wikiart'];m=x['museum'];existing_label='Reconcile `'+x['existing_record']['id']+'`' if x['existing_record'] else 'New-record candidate'
    lines.append('| '+link(x['accession']+' · '+m['Título'],m['url'])+' | '+clean(m['Autor'])+' · '+link(p['metadata']['title'],x['url'])+' · '+link('image source',p['image_url'])+' | '+clean(m['Fecha'])+' / '+clean(p['metadata']['year'])+' | '+existing_label+' | '+clean(x['note'])+' |')
lines+=['','Full dimensions, source labels, capture receipts, exact image URLs and duplicate matches are preserved in [additional-artworks.json](additional-artworks.json).']
(RUN/'additional-artworks.md').write_text('\n'.join(lines)+'\n')

old=load(PREV/'deep-research-20261006/all-artwork-outcomes.json')['outcomes']
extras=collections.defaultdict(list)
for x in extra:extras[x['artwork_id']].append(x)
rows=[]
for oldrow in old:
    x=dict(oldrow);aid=x['artwork_id']
    if aid in claims:
        c=claims[aid];im=plan['prepared'][aid]
        x.update(outcome='added_after_conflict_resolution',primary_media_id=im['media_id'],source_page_url=c['page']['url'],
            public_image_url='https://artlines.org'+im['path'],reason=c['review_outcome'])
    elif aid in extras:
        x.update(outcome=extras[aid][-1]['outcome'],reason=extras[aid][-1]['reason'])
    x['resolution_decisions']=extras[aid]
    rows.append(x)
assert len(rows)==548 and sum(bool(x['primary_media_id'])for x in rows)==253
save(RUN/'all-artwork-outcomes.json',{'verification':verification,'outcomes':rows})
lines=['# Prado artwork audit after conflict resolution','',
    '548 existing production artworks; **253 with primary images, 295 without**. All retain review status and their existing catalogue metadata. Eleven images were attached in this pass; 70 across the three Prado deliveries. Historical searches are retained in [the previous audit](../deep-research-20261006/all-artworks.md).','',
    '| Artist | Artwork / accession | Primary image | Latest outcome | Source / decision |','|---|---|---|---|---|']
for x in rows:
    artist=', '.join(a['name']for a in x['artists']) or 'Unlinked creator'
    src=link('WikiArt',x['source_page_url'])if x.get('source_page_url')else ''
    detail=clean(x.get('reason',''))if x.get('reason')else ''
    lines.append('| '+clean(artist)+' | '+clean(x['title'])+' · '+clean(x['accession_number'])+' | '+('Yes'if x['primary_media_id']else 'Missing')+' | '+clean(x['outcome'])+' | '+src+' '+detail+' |')
(RUN/'all-artworks.md').write_text('\n'.join(lines)+'\n')

lines=['# Prado: conflict resolution and additional WikiArt research','',
    '**11 further images attached and verified in production. Coverage increased from 242 to 253 of 548 existing Prado artworks; 295 image gaps remain.** This makes 70 verified image additions across the three Prado deliveries.','',
    '**53 additional Prado leads documented: 46 new-record candidates and 7 existing records to reconcile.** See [the new-work list](additional-artworks.md), which includes museum accession numbers, both date statements, WikiArt pages, direct source image URLs and specific review notes. No new artwork rows were created in this image-delivery pass.','',
    'The user explicitly delegated conflict resolution: “resolve conflicts in your own way” and “find more artrorks.” I treated missing catalogue dates and source proportions as evidence to assess individually. I accepted matches supported by specific composition, artist, accession-level museum facts and source metadata; I rejected demonstrably different objects. Catalogue dates, including unknowns, were preserved.','',
    '## Resolved and attached','',
    '| Artist / artwork | Prado accession | WikiArt source | Decision |','|---|---|---|---|']
for x in decisions:
    c=claims[x['artwork_id']];a=c['work']
    lines.append('| '+clean(c['page']['metadata']['artistName'])+' · '+clean(a['title'])+' | '+clean(a['accession_number'])+' | '+link('WikiArt',c['page']['url'])+' · '+link('served image','https://artlines.org'+plan['prepared'][a['id']]['path'])+' | '+clean(x['reason'])+' |')
lines+=['','The Hiepes profile-vase decision uses the Prado’s [botanical description](https://www.museodelprado.es/recurso/un-paseo-botanico-por-el-prado/40d55588-7bb6-a954-9bc4-eb1932600f3e) and [WGA’s description of the sunflower composition](https://www.wga.hu/html_m/h/hiepes/vase1.html). This is an editorial inference from distinctive composition and matching dimensions, not a source accession explicitly printed on WikiArt. Full date and confidence evidence is in [identity-decisions.json](identity-decisions.json); confidence values represent editorial judgment, not calibrated probabilities.','',
    '## Other conflicts decided','',
    '| Candidate | Decision | Corroboration |','|---|---|---|']
for x in extra:
    title=next(y['title']for y in rows if y['artwork_id']==x['artwork_id'])
    lines.append('| '+link(title,x['url'])+' | '+clean(x['reason'])+' | '+', '.join(link('Source '+str(n+1),u)for n,u in enumerate(x['sources']))+' |')
lines+=['','These decisions supersede the corresponding historical holds; earlier evidence remains intact. The other unresolved searches remain documented in the [complete 548-work audit](all-artworks.md). The corrected Hiepes text index contains six entries and no second flower-vase image. Prior login/403 boundaries were respected; indexed museum descriptions supplied corroboration without retrying blocked image endpoints.','',
    '## Verification and recovery','',
    '- All 548 existing Prado records were compared after delivery. All 537 unselected records and attachments were unchanged; selected artwork metadata and creators were unchanged. All 548 remain in review.',
    '- All 11 images, per-object WikiArt rights receipts, identity citations, decoded dimensions and checksums passed. All 11 public image bodies and live artwork API responses matched.',
    '- Derivatives preserve the supplied composition and proportions and are at most '+str(verification['maximum_derivative_bytes'])+' bytes. The source labels are recorded as WikiArt claims, not independently obtained licences.',
    '- Production recovery backup: `'+str(backup['id'])+'` (`SUCCESSFUL`). Pinned plan SHA-256: `'+verification['plan_sha256']+'`.',
    '- Originals, the contact sheet and four additional identity-review images: `~/Library/Application Support/Artline/source-images/'+OP+'/`.',
    '- Preimages, after-images, pinned plan and operation scripts: `~/Library/Application Support/Artline/backups/'+OP+'/`.',
    '- No local database writes, new artwork imports, publication changes, commits or deployments.',
    '',link('Complete verification receipt','delivery/complete-verification.json')+' · '+link('Production application receipt','delivery/production-applied.json')+' · '+link('All outcomes JSON','all-artwork-outcomes.json')]
(RUN/'README.md').write_text('\n'.join(lines)+'\n')

archive=Path.home()/'Library/Application Support/Artline/backups'/OP/'operation-scripts'
archive.mkdir(parents=True,exist_ok=True)
files=['ops/research-prado-wikiart-resolution-20261006.py','ops/deliver-prado-wikiart-resolution-20261006.py',
    'ops/deliver-prado-wikiart-images-20261006.py','ops/deliver-production-wikiart-images-20261006.py',
    'ops/finalize-prado-wikiart-resolution-20261006.py','ops/report-prado-wikiart-resolution-20261006.py']
for path in files:shutil.copy2(ROOT/path,archive/Path(path).name)
manifest={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest()for path in files}
save(RUN/'operation-script-hashes.json',manifest)
print(json.dumps({'added_images':11,'coverage':253,'gaps':295,'additional_leads':len(additional),'new_record_candidates':46,'existing_record_reconciliations':7}))
