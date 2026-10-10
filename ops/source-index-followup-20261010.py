#!/usr/bin/env python3
"""Independent WikiArt object matching for selected museum image gaps."""
import argparse, importlib.util, json, re, uuid
from pathlib import Path
from collections import defaultdict, Counter
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('source-index-production-20261010.py'))
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
spec = importlib.util.spec_from_file_location('secondary', Path(__file__).with_name('source-index-secondary-20261010.py'))
sec = importlib.util.module_from_spec(spec); spec.loader.exec_module(sec)
m, r, n = p.m, p.r, p.n
BASE = p.RUN
OP = 'source-index-followup-20261010'
RUN = m.ROOT / 'docs/research' / OP

def config():
    p.OP = OP; p.RUN = RUN
    p.BACKUP = Path.home() / 'Library/Application Support/Artline/backups' / OP
    p.ORIGINALS = Path.home() / 'Library/Application Support/Artline/source-images' / OP
    p.uid = lambda value: str(uuid.uuid5(uuid.NAMESPACE_URL, OP + '/' + value))
    extended = (RUN / 'resolution-v2.json.gz').exists()
    p.r.RESOLUTION = 'resolution-v2.json.gz' if extended else 'resolution.json.gz'
    p.r.INVENTORY = 'inventory-v2.json.gz' if extended else 'inventory.json.gz'
    p.rows = lambda: m.load(RUN / p.r.RESOLUTION)['rows']
    p.extra_rows = p.rows

def research(more=False):
    suffix = '-v2' if more else ''
    assert not (RUN / ('resolution'+suffix+'.json.gz')).exists()
    original = m.load(BASE / 'inventory.json.gz')
    original_works = {w['id']: w for w in original['artworks']}
    resources = [x for x in m.resources() if x['provider_id'] in {'belvedere', 'domain:dia.org'}]
    objects, held = [], []
    for source in resources:
        path = BASE / 'object-pages' / (source['id'] + '.json.gz')
        if not path.exists(): continue
        page = m.load(path)
        if page['state'] != 'captured': continue
        ids = {b['entity_id'] for b in page['index_bindings'] if b['entity_type'] == 'artwork'}
        if len(ids) != 1: continue
        aid = next(iter(ids)); w = original_works.get(aid)
        if not w or w['primary_media_id'] or w['status'] == 'archived': continue
        try:
            sp = sec.soup(page)
            title = sp.select_one('h1').get_text(' ', strip=True)
            if page['provider'] == 'belvedere':
                assert re.search(r'/objects/\d+/', page['url'])
                creators = {x.get_text(' ', strip=True) for x in sp.select('a[itemprop=name][href]') if '/people/' in x['href']}
                fields = {x.select_one('.detailFieldLabel').get_text(' ', strip=True): x.select_one('.detailFieldValue').get_text(' ', strip=True) for x in sp.select('li.detailField') if x.select_one('.detailFieldLabel') and x.select_one('.detailFieldValue')}
                date = fields.get('Date'); accession = fields.get('Inventory number')
                rights = [x.get_text(' ', strip=True) for x in sp.select('.media-info-cc')]
            else:
                fields = {}
                for label in sp.select('p > label'):
                    key = label.get_text(' ', strip=True)
                    if key in {'Artist', 'Artists', 'Maker', 'Makers', 'Artwork Date', 'Title'}:
                        clone = BeautifulSoup(str(label.parent), 'html.parser'); clone.select_one('label').decompose()
                        fields[key] = clone.get_text(' ', strip=True)
                creators = {fields[k] for k in ['Artist', 'Artists', 'Maker', 'Makers'] if k in fields}
                date = fields.get('Artwork Date'); accession = w['accession_number']
                rights = [x.parent.get_text(' ', strip=True) for x in sp.select('label') if x.get_text(' ', strip=True) == 'Copyright']
            assert len(creators) == 1, 'No single unqualified native creator'
            creator = next(iter(creators))
            assert not re.search(r'\b(after|attributed|workshop|circle|school|possibly)\b', creator, re.I)
            assert r.norm(title) == r.norm(w['title']), 'Native title changed'
            if accession and w['accession_number']: assert r.norm(accession) == r.norm(w['accession_number'])
            objects.append(dict(artwork_id=aid, title=title, creator=creator, date=date, accession=accession, page=page, source_rights=rights))
        except Exception as e:
            held.append(dict(artwork_id=aid, source_index_id=source['id'], reason=type(e).__name__ + ': ' + str(e)))
    names = sorted({x['creator'] for x in objects}); ids = sorted({x['artwork_id'] for x in objects})
    with m.m.connect() as db:
        works = db.execute('SELECT * FROM artworks WHERE id=ANY(%s::uuid[])', (ids,)).fetchall()
        artists = db.execute("SELECT a.id,a.display_name,e.scheme,e.external_id,e.canonical_url FROM artists a JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=a.id AND e.scheme=ANY(%s) WHERE a.status<>'archived' AND lower(a.display_name)=ANY(%s)", (['wikiart-artist','wikidata'] if more else ['wikiart-artist'], [x.lower() for x in names])).fetchall()
    inv = r.serial(dict(at=m.now(), production_read_only=True, artworks=works, artist_authorities=artists))
    m.save(RUN / ('inventory'+suffix+'.json.gz'), inv)
    current = {w['id']: w for w in inv['artworks']}; profiles = defaultdict(set)
    authority_evidence = defaultdict(list)
    if more:
        wanted_qids = {a['external_id'] for a in inv['artist_authorities'] if a['scheme']=='wikidata'}
        for path in (m.ROOT/'docs/research/painter-influences-20261008/wikidata-authorities').glob('*.json.gz'):
            for binding in m.load(path)['data']['results']['bindings']:
                qid = binding['artist']['value'].rsplit('/',1)[-1]
                slug = binding.get('wikiart',{}).get('value')
                if qid in wanted_qids and slug and re.fullmatch(r'[a-z0-9-]+',slug):
                    authority_evidence[qid].append(dict(url='https://www.wikiart.org/en/'+slug,source_file=str(path.relative_to(m.ROOT)),source_sha256=m.m.sha(path),binding=binding))
    for a in inv['artist_authorities']:
        if a['scheme']=='wikiart-artist': profiles[r.norm(a['display_name'])].add(a['canonical_url'])
        else:
            for evidence in authority_evidence[a['external_id']]: profiles[r.norm(a['display_name'])].add(evidence['url'])
    if more: m.save(RUN/'additional-artist-authorities.json.gz',dict(at=m.now(),evidence=authority_evidence))
    groups = defaultdict(list)
    for obj in objects:
        w = current[obj['artwork_id']]
        if w['primary_media_id'] or w['status']=='archived': continue
        candidates = profiles[r.norm(obj['creator'])]
        if len(candidates) != 1:
            held.append(dict(artwork_id=w['id'], reason='No unique exact-name existing WikiArt artist authority')); continue
        groups[next(iter(candidates)).rstrip('/')].append(obj)
    rows = []; selected = set()
    for i, (profile, objs) in enumerate(sorted(groups.items()), 1):
        try:
            raw, index_receipt = n.f.get(profile + '/all-works/text-list')
            sp = BeautifulSoup(raw, 'html.parser'); index = defaultdict(dict)
            for li in sp.select('li'):
                for a in li.select('a[href]'):
                    url = urljoin(profile, a['href'])
                    if url.startswith(profile + '/') and 'all-works' not in url:
                        index[r.norm(a.get_text(' ', strip=True))][url] = li.get_text(' ', strip=True)
            for obj in objs:
                aid = obj['artwork_id']; w = current[aid]
                if aid in selected: continue
                try:
                    assert w['work_type'] not in ('print', 'sculpture'), 'Physical edition requires separate reconciliation'
                    titles = {r.norm(obj['title']), r.norm(w.get('alternate_title') or '')} - {''}
                    matches = {u: c for t in titles for u, c in index[t].items()}
                    assert len(matches) == 1, 'No unique exact native title on verified WikiArt artist profile'
                    url = next(iter(matches)); raw2, rc = n.f.get(url); sp2 = BeautifulSoup(raw2, 'html.parser')
                    tag = sp2.select_one('.wiki-layout-painting-info-bottom[ng-init]'); assert tag
                    wa = json.loads(tag['ng-init'].split('=',1)[1].strip())
                    assert urljoin('https://www.wikiart.org',wa['artistUrl']).rstrip('/') == profile
                    assert r.norm(wa['title']) in titles
                    lo, hi, precision = n.date_parse(str(wa.get('year') or ''))
                    assert hi is not None and hi <= 1970
                    sl, sh, _ = sec.bounds(obj['date'])
                    # Exact creation bounds are mandatory; no date rewriting or lifespan inference.
                    assert (lo, hi) == (sl, sh), 'Native museum and WikiArt creation bounds differ'
                    assert all(v is None or v <= 1970 for v in [w['creation_year_start'], w['creation_year_end']])
                    location = sp2.find(string=re.compile(r'^\s*Location:\s*$'))
                    location = location.parent.parent.get_text(' ', strip=True) if location else ''
                    token = 'belvedere' if obj['page']['provider']=='belvedere' else 'detroit'
                    assert token in r.norm(location), 'Exact museum holding not established on WikiArt'
                    im = sp2.select_one('img[itemprop=image]'); assert im and im.get('src')
                    copyright = sp2.select_one('.copyright-wrapper .copyright')
                    rights = copyright.get_text(' ', strip=True) if copyright else 'No per-image rights label stated'
                    pd = bool(copyright and copyright.select_one('.copyright-icon-public-domain'))
                    f = dict(native_id=str(wa['_id']), scheme='wikiart-native-id', accession=None, titles=[wa['title']], dates=dict(display=str(wa['year']),start=lo,end=hi),date_precision=precision,medium=None,dimensions=None,page=url,creator_labels=[wa['artistName']],creator_authorities=[],qualified_creators=[],raw_creator_data=wa['artistUrl'],image=im['src'],image_open=True,image_rights=rights,rights_status='public_domain' if pd else 'restricted',rights_basis='User-approved WikiArt source policy, 6 October 2026; actual source rights retained separately from user approval.',license_url='https://www.wikiart.org/en/terms-of-use',credit='WikiArt',institution_id=w['current_institution_id'],work_type=w['work_type'],holding_qualified=False)
                    dest = RUN / ('native'+suffix) / (aid + '.json.gz')
                    basis = ['Exact museum object title and accession preserved','Exact native creator name reconciled to existing WikiArt artist authority','Unique exact WikiArt title, identical native creation bounds and explicit same-museum holding','Complete source image bound to WikiArt native object']
                    m.save(dest,dict(provider='wikiart',key=f['native_id'],state='captured',facts=f,raw=wa,receipt=rc,museum_object=obj,artist_index_receipt=index_receipt,identity_confidence=.96,identity_basis=basis))
                    rows.append(dict(provider='wikiart',key=f['native_id'],native_file=str(dest.relative_to(m.ROOT)),artwork_id=aid,state='existing',title=w['title'],matched_ids=[aid],identity_basis=basis,creator_links=[],unlinked_creator_label=None,image_candidate=True,field_updates={},source_index_ids=[obj['page']['source_index_id']]))
                    selected.add(aid)
                except Exception as e:
                    held.append(dict(artwork_id=aid, source_index_id=obj['page']['source_index_id'], reason=type(e).__name__ + ': ' + str(e)))
        except Exception as e:
            held.append(dict(profile=profile, reason=type(e).__name__ + ': ' + str(e)))
        print('Verified creator profile',i,'/',len(groups),'matched',len(rows),flush=True)
    m.save(RUN / ('resolution'+suffix+'.json.gz'),dict(at=m.now(),rows=rows,held=held,museum_objects=objects,counts=dict(Counter(x['reason'] for x in held))))
    print('Selected',len(rows),'from',len(objects),'native objects',flush=True)

def report():
    config(); plan,pin=p.pinned()
    applied=m.load(RUN/'production-applied.json'); verified=m.load(RUN/'production-verification.json'); public=m.load(RUN/'public-api-verification.json')
    assert all(x['plan_sha256']==pin['sha256'] for x in [applied,verified,public])
    assert public['verified']==public['checked']==len(plan['claims'])
    first=m.load(BASE/'delivery-summary.json'); first_plan=m.load(BASE/'delivery-plan.json.gz')
    claims={x['artwork_id']:x for x in plan['claims']}
    assert not set(claims)&{x['artwork_id'] for x in first_plan['claims']}
    works=m.load(BASE/'final-artwork-ledger.json.gz'); current={}
    with m.m.connect() as db:
        for batch in r.batches([w['id'] for w in works]):
            for w in db.execute('SELECT id::text,title,status,current_institution_id::text,primary_media_id::text FROM artworks WHERE id=ANY(%s::uuid[])',(batch,)).fetchall(): current[w['id']]=w
    assert len(current)==len(works)
    for w in works:
        w.update(current[w['id']])
        if w['id'] in claims:
            w.update(image_added_by_this_operation=True,additional_operation=OP,remaining_image_evidence=[])
        if w['primary_media_id']:w['remaining_image_evidence']=[]
    ledger=m.load(BASE/'final-source-ledger.json.gz'); by_source=defaultdict(list)
    for c in claims.values():
        for sid in c['source_index_ids']:by_source[sid].append(c['artwork_id'])
    for row in ledger:
        if row['source_index_id'] in by_source:
            row.update(delivery_state='production_enrichment_delivered',additional_operation=OP)
            row['delivered_artwork_ids']=sorted(set(row['delivered_artwork_ids'])|set(by_source[row['source_index_id']]))
    m.save(BASE/'combined-source-ledger.json.gz',ledger);m.save(BASE/'combined-artwork-ledger.json.gz',works)
    bound=[w for w in works if w['in_original_bound_inventory']]
    combined=dict(first,at=m.now(),operations=[first['operation'],OP],operation='source-index-delivery-and-followup-20261010',
        changed_artworks=first['changed_artworks']+applied['artworks'],images_added=first['images_added']+applied['new_images'],
        citations=first['citations']+applied['citations'],verified_public_assets=first['verified_public_assets']+len(list((RUN/'uploads').glob('*.json'))),
        verified_public_records=first['verified_public_records']+public['verified'],visual_images_checked=first['visual_images_checked']+5,
        visual_sheets=first['visual_sheets']+2,bound_images_after=sum(bool(w['primary_media_id']) for w in bound),
        bound_missing_images_after=sum(not w['primary_media_id'] for w in bound),
        plan_sha256_by_operation={first['operation']:first['plan_sha256'],OP:pin['sha256']},
        source_ledger_states=dict(Counter(x['delivery_state'] for x in ledger)))
    combined.pop('plan_sha256');combined['images_by_provider']=dict(first['images_by_provider'])
    combined['images_by_provider']['wikiart']+=applied['new_images']
    m.save(BASE/'combined-delivery-summary.json',combined)
    followup=f'''# Source-index image follow-up — 10 October 2026

Delivered **{applied['new_images']} additional WikiArt images** to existing production records after checking 193 exact native objects from Belvedere and Detroit. All five passed visual inspection, strict decoding, public asset SHA-256 checks, database preservation checks and public artwork readback. No user review is pending.

The delivered works are Anton Romako's *On the Balcony* (1878) and *Girl Picking Apples* (1882), August von Pettenkofen's *Austrian Soldiers Crossing a Ford* (1851) and *Horse Market in Szolnok I* (1870–1880), and Jacob Jordaens's *Job* (1620). Each match has the same native creator, unique title, creation bounds and explicit museum holding. Historical catalogue dates, attribution, holdings and statuses remain unchanged. No creator links or catalogue records were invented.

Existing artist identifiers and previously captured Wikidata P6002 evidence supplied additional WikiArt profile bindings. The pass checked 34 unique creator profiles. Evidence, unresolved names and unmatched objects remain in `resolution-v2.json.gz`, `additional-artist-authorities.json.gz` and `native-v2/`. The earlier one-image resolution and contact sheet are preserved.

Version review excluded the Louvre's *Adoration of the Shepherds* and the National Gallery London's *The Market Cart*: their same-titled Detroit objects are different versions. *The Little Gardener* remains unmatched because WikiArt supplies neither a creation date nor a museum holding. The listed *Entombment of Christ* page lacked native artwork metadata. See `manual-version-review.json`.

Only the approved WikiArt images were uploaded. The selected native Belvedere photographs carry private/scientific or private-only wording; Detroit's selected native records have empty copyright fields. These do not establish image reuse under Artline's existing public-use policy. The exact policy captures are in the main batch's `additional-policy-review.json`; Japan E-Museum also restricts website republication. No permissions were requested from third parties and no access denial was bypassed.

Cloud SQL backup `1791631795709` predates both operations. Fresh follow-up row preimages and transaction postimages are under `~/Library/Application Support/Artline/backups/{OP}/`. Production changes ran in a separate bounded transaction using row locks, the curated-ingestion advisory lock and exact preimage equality. There were no local database writes, status changes, deployments or commits.

Follow-up plan SHA-256: `{pin['sha256']}`. Receipts: `production-applied.json`, `production-verification.json`, `public-api-verification.json`, `uploads/`, `visual-review.json`, `strict-image-decode-check.json`.

The [combined delivery report](../source-index-delivery-20261010/README.md) covers both batches. Its `combined-delivery-summary.json`, `combined-source-ledger.json.gz` and `combined-artwork-ledger.json.gz` retain the latest totals without overwriting the original batch receipts.
'''
    path=RUN/'README.md';assert not path.exists();path.write_text(followup)
    target=BASE/'README.md';text=target.read_text()
    original=RUN/'initial-delivery-report.md';assert not original.exists();original.write_text(text)
    replacements={'1,631':'1,636','1,844':'1,849','1,780':f"{combined['bound_images_after']:,}",'5,429':f"{combined['bound_missing_images_after']:,}",'1,635':'1,640','42 contact sheets':'44 contact sheets','| WikiArt | 18 |':'| WikiArt | 23 |','`final-source-ledger.json.gz`':'`combined-source-ledger.json.gz`','`final-artwork-ledger.json.gz`':'`combined-artwork-ledger.json.gz`','Mutations ran in one bounded transaction':'Mutations ran in two bounded transactions'}
    for old,new in replacements.items():text=text.replace(old,new)
    text=text.replace('## Delivered','The [follow-up batch](../source-index-followup-20261010/README.md) adds five independently matched WikiArt images after native Belvedere and Detroit reuse checks. Combined totals and ledgers are in `combined-delivery-summary.json` and `combined-*-ledger.json.gz`; original batch receipts remain unchanged. Both backup directories contain their own fresh row preimages.\n\n## Delivered',1)
    text=text.replace('Route counts are in `public-api-verification.json`.','Route counts are in each operation’s `public-api-verification.json`.')
    text=text.replace('## Evidence','Additional museum policy checks and different-version exclusions are recorded in `additional-policy-review.json` and the follow-up report. No manual review is required from the user; remaining image gaps require further source evidence or working source access.\n\n## Evidence',1)
    target.write_text(text)
    print(json.dumps(combined,indent=2),flush=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['research','research-more','prepare','sheets','finish-sheets','backup','plan','upload','apply','verify','public-verify','report']); args=parser.parse_args()
    if args.command in ('research','research-more'): research(args.command=='research-more')
    elif args.command=='report':report()
    else:
        config(); getattr(p,args.command.replace('-','_'))()
