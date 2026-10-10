#!/usr/bin/env python3
"""Third Louvre pass: exact authority crosswalks and separately reviewed identities."""
import argparse, collections, concurrent.futures, copy, importlib.util, json, re
from pathlib import Path
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('round2',ROOT/'ops/resolve-louvre-wikiart-round2-20261006.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
PREVIOUS=n.RUN
RUN=ROOT/'docs/research/louvre-wikiart-round3-20261006'
n.RUN=RUN
d=n.d;r=n.r;q=n.q
r.RUN=RUN;d.RUN=RUN/'delivery';d.OP=RUN.name
d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/d.OP
d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/d.OP

def decisions():
    approved={}
    for p in sorted((RUN/'manual-decisions').glob('*.json')):approved.update(r.load(p))
    return approved

def reviewed_decision(record,candidate):
    decision=decisions().get(record['artwork']['id'],{})
    if decision.get('source_id')!=candidate['source_id'] or not decision.get('full_composition_verified'):return None
    comparison=r.load(ROOT/decision['comparison_evidence'])
    assert comparison['artwork_id']==record['artwork']['id']
    assert any(c['source_id']==candidate['source_id']for c in comparison['candidates'])
    assert comparison['museum']['dateCreated']==decision['museum_date_review']
    ref=comparison['primary_object']['reference'];ark=comparison['museum']['arkId'].removeprefix('cl')
    assert any(ref in e['claims']['P347'] and ark in e['claims']['P9394']for e in comparison['object_authorities'])
    return decision

_original_valid_date=d.valid_date
def reviewed_date(record,candidate):
    result=_original_valid_date(record,candidate)
    if result:return result
    # A supplied but unparseable/newer source date must not receive this fallback.
    if d.source_date(candidate) not in (None,'','?'):return None
    decision=reviewed_decision(record,candidate)
    if not decision or not decision.get('catalogue_unknown_dates_preserved_when_wikiart_undated'):return None
    dates=decision['museum_date_review']
    if not dates:return None
    for value in dates:
        start=value.get('startYear');end=value.get('endYear')or start
        if value.get('type')!='Date de création/fabrication' or value.get('doubt'):return None
        if not isinstance(start,int) or not isinstance(end,int) or start>end or end>1970:return None
    # Editorially checked museum creation evidence establishes eligibility only.
    # WikiArt remains authoritative; do not manufacture catalogue year fields.
    return {k:record['artwork'][k]for k in ('creation_year_start','creation_year_end','date_display','date_precision')}

d.valid_date=reviewed_date
_original_safety=d.safety_reason
def reviewed_safety(record,candidate):
    reason=_original_safety(record,candidate)
    if reason=='Full work versus detail/study/copy/component differs':
        decision=reviewed_decision(record,candidate)
        if decision and decision.get('source_title_component_reviewed'):
            if any('Qualified catalogue' in f or 'identifier changed' in f or 'creator differs' in f for f in candidate['review_flags']):return 'Qualified or changed creator/object identity'
            return None
    return reason
d.safety_reason=reviewed_safety

def finalize():
    approved=decisions();held_sources=collections.defaultdict(set)
    for p in sorted((RUN/'manual-holds').glob('*.json')):
        for aid,h in r.load(p).items():held_sources[aid].update(h.get('source_ids',[])+([h['source_id']]if h.get('source_id')else[]))
    approved={aid:x for aid,x in approved.items()if x['source_id']not in held_sources[aid]}
    used_sources={c['source_record_id']for row in n.records()if row['artwork']['primary_media_id']for c in row['citations']if 'wikiart.org'in(c.get('source_url')or'')}
    assert not ({x['source_id']for x in approved.values()}&used_sources),'Existing illustrated source requires explicit duplicate/version reconciliation'
    reviewed={x['artwork_id']:x for x in r.load(Path((RUN/'review-pointer.txt').read_text()))};selected=[]
    for aid,decision in approved.items():
        assert decision['source_id']not in held_sources[aid],('Conflicting manual hold',aid)
        row=copy.deepcopy(reviewed[aid]);matches=[c for c in row['candidates']if c['source_id']==decision['source_id']]
        assert len(matches)==1 and not matches[0]['safety_hold'],(aid,matches)
        row['candidates']=matches;selected.append(row)
    assert len({x['source_id']for x in approved.values()})==len(approved),'Duplicate source work requires separate review'
    path=d.RUN/'reviewed-records'/(r.sha(d.core.encode(selected))+'.json');r.save(path,selected)
    (d.RUN/'reviewed-records-pointer.txt').write_text(str(path))
    path=d.RUN/'object-decision-versions'/(r.sha(d.core.encode(approved))+'.json');r.save(path,approved)
    # Mutable delivery control file; every version remains archived above.
    (d.RUN/'final-object-review.json').write_text(json.dumps(approved,ensure_ascii=False,indent=2)+'\n')
    d.select()
    assert len(d.selection()['selected'])==len(approved)

def seed():
    q.snapshot()
    ids={x['artwork']['id']for x in n.remaining()}
    rows=[x for x in r.load(PREVIOUS/'artist-map-v2.json')['records']if x['artwork_id']in ids]
    r.save(RUN/'artist-map-v2.json',{'records':rows,'previous_evidence':str(PREVIOUS)})
    plan=[x for x in r.load(Path((PREVIOUS/'candidate-pointer.txt').read_text()))if x['artwork_id']in ids]
    p=RUN/'candidate-plans'/(r.sha(d.core.encode(plan))+'.json');r.save(p,plan);(RUN/'candidate-pointer.txt').write_text(str(p))
    reviews=[x for x in r.load(Path((PREVIOUS/'review-pointer.txt').read_text()))if x['artwork_id']in ids]
    p=RUN/'review-passes'/(r.sha(d.core.encode(reviews))+'.json');r.save(p,reviews);(RUN/'review-pointer.txt').write_text(str(p))
    for folder in ['indexes','text-indexes','artwork-pages']:
        for p in (PREVIOUS/folder).glob('*.json'):r.save(RUN/folder/p.name,r.load(p))
    print('Fresh snapshot and prior evidence:',len(rows),'unresolved records',flush=True)

def authorities():
    creators=set();objects=set()
    for x in n.mapping():
        for label in x['label_evidence']:
            if label.get('creator'):creators.add(label['creator'].rsplit('/',1)[-1])
            if label.get('item')and label.get('joconde')==(x.get('primary_object')or{}).get('reference'):objects.add(label['item'].rsplit('/',1)[-1])
    def one(pair):
        kind,ids=pair
        url='https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbgetentities','ids':'|'.join(ids),'props':'claims|labels|aliases','languages':'en|fr|it|nl|de','format':'json'})
        raw,rc=n.capture_once(url,'authority-captures');assert rc['status']==200
        for qid,x in json.loads(raw)['entities'].items():
            claims={p:[v['mainsnak']['datavalue']['value']for v in x.get('claims',{}).get(p,[])if 'datavalue'in v['mainsnak']]for p in ['P6001','P6002','P9394','P347','P217','P170']}
            dest=RUN/(kind+'-authorities')/(qid+'.json')
            if dest.exists():
                assert r.load(dest)['claims']==claims
            else:r.save(dest,{'qid':qid,'claims':claims,'labels':x.get('labels',{}),'aliases':x.get('aliases',{}),'receipt':rc})
        return kind,len(ids)
    jobs=[]
    for kind,ids in [('creator',creators),('object',objects)]:
        ids=sorted(x for x in ids if re.fullmatch(r'Q\d+',x));jobs += [(kind,ids[i:i+40])for i in range(0,len(ids),40)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
        for i,result in enumerate(pool.map(one,jobs),1):print('Authority batch',i,'/',len(jobs),result,flush=True)

def crosswalk_summary():
    for kind,prop in [('creator','P6002')]:
        found=[r.load(p)for p in (RUN/(kind+'-authorities')).glob('*.json')if r.load(p)['claims'][prop]]
        r.save(RUN/(kind+'-wikiart-crosswalks-v2.json'),found)
        print(kind,len(found))
        if kind=='creator':
            unmapped={x['creator'].rsplit('/',1)[-1]for row in n.mapping()if not row['sources']for x in row['label_evidence']if x.get('creator')}
            for x in found:
                if x['qid']in unmapped:print(x['qid'],x['claims'][prop],x['labels'].get('en',{}).get('value'))

def report():
    verified=r.load(d.RUN/'verification.json');plan=d.load_plan()
    assert verified['plan_sha256']==r.sha(d.core.encode(plan))
    attached={x['artwork_id']for x in plan['selected']}
    reviewed=r.load(Path((RUN/'review-pointer.txt').read_text()))
    previous={x['artwork_id']:x for x in r.load(PREVIOUS/'record-outcomes.json')}
    holds=collections.defaultdict(list)
    for p in sorted((RUN/'manual-holds').glob('*.json')):
        for aid,value in r.load(p).items():holds[aid].append(value)
    extra=r.load(RUN/'additional-creator-review.json')
    counts=collections.Counter();outcomes=[]
    for row in reviewed:
        aid=row['artwork_id'];candidates=row['candidates'];prior=previous.get(aid,{}).get('specific_review')
        reviews=holds[aid]+([prior]if prior else[])
        sources=row['sources']
        if aid==extra['artwork_id']:sources=[{'url':extra['source_url'],'authority_evidence':extra['authority_evidence']}]
        if aid in attached:status='Image attached and production verified'
        elif reviews:status='Candidate rejected or held after object, version or image-quality review'
        elif not sources:status='No verified WikiArt creator page found in checked directory and name variants'
        elif not candidates:status='No candidate found in checked artist works and title variants'
        elif all(c['safety_hold']for c in candidates):status='Candidates held for date, rights, creator or component checks'
        else:status='Candidate identity or version remains unverified'
        counts[status]+=1
        outcomes.append({'artwork_id':aid,'title':row['title'],'creator_names':row['names'],'status':status,
          'primary_object':row['primary_object'],'creator_sources':sources,'candidate_urls':[c['url']for c in candidates],
          'specific_reviews':reviews,'additional_creator_review':extra if aid==extra['artwork_id']else None,
          'evidence_review':(RUN/'review-pointer.txt').read_text()})
    assert len(outcomes)==2704 and counts['Image attached and production verified']==verified['artworks_updated']
    assert 2704-len(attached)==verified['remaining_without_images']
    r.save(RUN/'record-outcomes.json',outcomes)
    date_checks=r.load(d.RUN/'editorial-date-checks.json')
    comparisons=[r.load(p)for folder in ['object-comparisons','object-comparisons-03']for p in (RUN/folder).glob('*.json')]
    pages=len({c['url']for row in n.current_plan()for c in row['candidates']})
    def cell(v):return str(v).replace('|','\\|').replace('\n',' ')
    lines=['# Louvre WikiArt reconciliation — third pass, 6 October 2026','',
      f"**{len(attached)} additional production records illustrated. Louvre coverage: {verified['louvre_totals']['with_images']:,} / {verified['louvre_totals']['artworks']:,}. {verified['remaining_without_images']:,} remain unresolved.** Verified {verified['verified_at']}.",'',
      'WikiArt is the user-selected source of truth for securely identified works. Every delivered reproduction comes from its exact artwork page and retains its per-image public-domain assertion. Louvre inventory photos support identity review. All changed records remain in review; existing images, creator attributions, holdings and publication fields were preserved.','',
      f"Reevaluated all 2,704 starting records using prior and new source evidence, with {pages:,} active candidate page URLs. Expanded semantic title/series searches and creator authority checks. Completed {len(comparisons)} inventory-photo comparisons across {len({x['artwork_id']for x in comparisons})} records. Translated titles and similar dimensions alone were not accepted as identity proof.",'',
      f"{verified['date_metadata_updated']} date metadata updates follow explicit WikiArt dates; {verified['year_bounds_updated']} change numeric bounds, including {verified['previously_unknown_years_filled']} previously unknown dates. For {date_checks['unknown_years_preserved']} individually reviewed undated WikiArt matches, exact Louvre inventory creation evidence establishes pre-1971 eligibility while unknown catalogue dates remain unchanged. Both evidence and prior values are retained.",'',
      'Source/version checks excluded mirrored images, details, different portraits, distinct sketches and finished versions. Two nearly identical Valenciennes Two Poplars paintings have separate inventory numbers (RF 2913 and RF 3004); source reuse was held. The Gericault bulldog reproduction matches RF 212, but the Louvre currently describes it as after Gericault; that attribution discrepancy is retained in review, with no creator rewrite.','',
      f"All {verified['audited_records']} database changes have verified audit history. All {verified['public_images_verified']} public JPEGs passed HTTP, SHA-256 and size checks; maximum {verified['largest_image_bytes']:,} bytes. {verified['live_api_records_verified']} live API records were checked. Full-source proportional resizing and JPEG compression only.",'',
      '## Every starting record accounted for','','| Outcome | Records |','| --- | ---: |']
    lines += [f'| {status} | {count:,} |'for status,count in counts.items()]
    lines += ['', 'These outcomes describe checked sources; they do not establish absence from all of WikiArt. Unresolved records need another verified reproduction, stronger object identification, or usable rights evidence. One additional creator authority (Edwin Landseer) was resolved, but the exact artwork was not found in the checked 99-work index. The broader authority lookup stopped on an HTTP 429 after 560 creators; no request bypass was used.','',
      '## Evidence','',
      '[Newly illustrated records with source links](delivery/report.html) · [Production verification](delivery/verification.json) · [All 2,704 outcomes](record-outcomes.json) · [Editorial date checks](delivery/editorial-date-checks.json) · [Final object decisions](delivery/final-object-review.json) · [Previous pass](../louvre-wikiart-round2-20261006/README.md)','',
      f"Production backup: `{verified['backup_directory']}`. Plan SHA-256: `{verified['plan_sha256']}`.",'',
      'Research source captures, review decisions and original helper scripts are preserved here. Source and identity images remain outside Documents under the Artline source-images directory. Disposable contact sheets are under /tmp. No deployment, publication or commit was performed.','',
      '## Remaining records','','| Record | Artwork | Creator | Outcome / reviewed reason |','| --- | --- | --- | --- |']
    for x in outcomes:
        if x['artwork_id']in attached:continue
        reason='; '.join(v.get('reason','')for v in x['specific_reviews'])or x['status']
        lines.append(f"| `{x['artwork_id']}` | {cell(x['title'])} | {cell(x['creator_names'][0]if x['creator_names']else'Unresolved')} | {cell(reason)} |")
    r.save(RUN/'README.md',('\n'.join(lines)+'\n').encode())
    main=ROOT/'docs/louvre-wikiart-reconciliation-20261006.md';old=main.read_text()
    if '## Previous second-pass delivery'not in old:
        intro=['# Louvre: WikiArt image reconciliation — 6 October 2026','',
          f"**{len(attached)} more records now have verified WikiArt images in production.** Louvre coverage is **{verified['louvre_totals']['with_images']:,} of {verified['louvre_totals']['artworks']:,} records**. **{verified['remaining_without_images']:,} remain unresolved.** Verified at {verified['verified_at']}.",'',
          f"All {len(attached)} changes remain in review. WikiArt supplies every image and {verified['date_metadata_updated']} explicit date metadata updates. {date_checks['unknown_years_preserved']} unknown dates remain unchanged after individual Louvre inventory/date review. Existing images, creator attributions, holdings and publication fields were preserved.",'',
          f"Verified database audit history for every change, all {verified['public_images_verified']} public image URLs, and {verified['live_api_records_verified']} live API records. Images retain the full source frame and are at most {verified['largest_image_bytes']:,} bytes. The three deliveries together added images to {442+107+len(attached):,} records, in addition to the original 33 illustrated records.",'',
          '[Full third-pass report and remaining records](research/louvre-wikiart-round3-20261006/README.md) · [All 2,704 starting-record outcomes](research/louvre-wikiart-round3-20261006/record-outcomes.json) · [Production verification](research/louvre-wikiart-round3-20261006/delivery/verification.json)','',
          '## Latest unresolved outcomes','','| Reason | Records |','| --- | ---: |']
        intro += [f'| {status} | {count:,} |'for status,count in counts.items()if status!='Image attached and production verified']
        intro += ['', 'These are checked-source outcomes, not proof that the artworks are absent from all of WikiArt. Specific rejected versions and unresolved identity/rights questions are preserved in the full report.','',
          '## Newly illustrated in the third pass','','| Catalogue artwork | Artist | WikiArt source | Production image |','| --- | --- | --- | --- |']
        for item in plan['selected']:
            im=r.load(d.RUN/'prepared'/(item['candidate']['source_id']+'.json'))
            intro.append(f"| {cell(item['title'])} · `{item['artwork_id']}` | {cell(item['artist'])} | [{cell(im['title'])}]({im['page']}) | [Image](https://artlines.org{im['path']}) |")
        main.write_text('\n'.join(intro)+'\n\n## Previous second-pass delivery\n\n'+old.split('\n',1)[1])
    print(json.dumps({'verified':verified,'outcomes':dict(counts)},ensure_ascii=False),flush=True)

if __name__=='__main__':
    own=['seed','authorities','crosswalk_summary','finalize','report']
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=own+['pages','evaluate','review_list','finalize','select','prepare','sheets','plan','upload','apply','verify_assets','verify']);a=parser.parse_args()
    (globals()[a.command]if a.command in own else getattr(n,a.command)if hasattr(n,a.command)else getattr(d,a.command))()
