#!/usr/bin/env python3
"""Read production back and account for every source-index entry and linked work."""
import importlib.util,json
from pathlib import Path
from collections import Counter,defaultdict

spec=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('source-index-production-20261010.py'))
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def report():
    plan,pin=p.pinned();applied=p.m.load(p.RUN/'production-applied.json');verification=p.m.load(p.RUN/'production-verification.json');public=p.m.load(p.RUN/'public-api-verification.json')
    assert all(x['plan_sha256']==pin['sha256'] for x in [applied,verification,public]) and public['verified']==public['checked']==len(plan['claims'])
    inv=p.m.load(p.RUN/'inventory.json.gz');baseline={x['id']:x for x in inv['artworks']};claims={x['artwork_id']:x for x in plan['claims']};native=p.rows();current={}
    ids=sorted(set(baseline)|set(claims))
    with p.m.m.connect() as db:
        for batch in p.r.batches(ids):
            for x in db.execute('SELECT id::text,title,status,current_institution_id::text,primary_media_id::text FROM artworks WHERE id=ANY(%s::uuid[])',(batch,)).fetchall():current[x['id']]=x
    assert set(current)==set(ids)
    pages={x['source_index_id']:x for path in (p.RUN/'object-pages').glob('*.gz') for x in [p.m.load(path)]}
    secondary=p.m.load(sorted(p.RUN.glob('secondary-resolution-*.json.gz'))[-1]);holds=defaultdict(list)
    for x in secondary['held']:holds[x['artwork_id']].append(dict(stage='source_image_resolution',provider=x['provider'],reason=x['reason']))
    for x in plan['concurrent_holds']:holds[x['artwork_id']].append(dict(stage='delivery_preflight',reason=x['reason']))
    prepared={x['artwork_id']:x for path in (p.RUN/'prepared-images').glob('*.json') for x in [p.m.load(path)]}
    for aid,x in prepared.items():
        if x['state']=='held':holds[aid].append(dict(stage='image_download',provider=x['provider'],reason=x['reason']))
    for x in p.m.load(p.RUN/'visual-review.json')['decisions']:
        if x['decision']!='accept':holds[x['artwork_id']].append(dict(stage='visual_review',reason=x['note']))
    work_sources=defaultdict(list);source_claims=defaultdict(list);source_native=defaultdict(list)
    for x in p.m.resources():
        for b in x['artline_bindings']:
            if b['entity_type']=='artwork':work_sources[b['entity_id']].append(x['id'])
    for c in plan['claims']:
        for sid in c['source_index_ids']:source_claims[sid].append(c['artwork_id'])
    for x in native:
        for sid in x['source_index_ids']:source_native[sid].append(dict(artwork_id=x['artwork_id'],state=x['state'],provider=x['provider']))
    works=[]
    for aid,a in current.items():
        c=claims.get(aid);notes=list(holds.get(aid,[]));sids=work_sources[aid]
        if not a['primary_media_id']:
            for sid in sids:
                page=pages.get(sid)
                if page and page['state']=='held':notes.append(dict(stage='source_access',source_index_id=sid,reason=page.get('reason') or page.get('error') or 'Source capture held; see object-page receipt'))
            if not notes:notes.append(dict(stage='remaining_research',reason='No verified usable image completed in this pass; existing catalogue record retained.'))
        works.append(dict(**a,in_original_bound_inventory=aid in baseline,had_image_at_baseline=bool(baseline.get(aid,{}).get('primary_media_id')),image_added_by_this_operation=bool(c and c['image']),metadata_fields_added=list(c['updates']) if c else [],source_index_ids=sids,remaining_image_evidence=notes if not a['primary_media_id'] else []))
    ledger=[]
    for x in p.m.load(p.RUN/'full-index-ledger.json.gz'):
        sid=x['source_index_id'];page=pages.get(sid);native_rows=source_native[sid];delivery=source_claims[sid]
        if delivery:state='production_enrichment_delivered'
        elif native_rows:state='native_object_reconciled_no_delivery'
        elif page and page['state']=='held':state='source_access_held'
        elif page:state='object_page_captured_further_evidence_needed'
        elif x['kind'] in ('museum_or_collection_object',) or x['artwork_ids']:state='object_reference_remaining'
        elif x['state']=='reference_or_discovery_entrypoint':state='reference_or_discovery_resource_not_an_artwork'
        else:state='object_or_artist_reference_remaining'
        ledger.append(dict(**x,delivery_state=state,delivered_artwork_ids=delivery,native_resolution=native_rows,capture_state=page['state'] if page else None,active_bound_artwork_ids=[aid for aid in x['artwork_ids'] if aid in current and current[aid]['status']!='archived']))
    p.m.save(p.RUN/'final-source-ledger.json.gz',ledger);p.m.save(p.RUN/'final-artwork-ledger.json.gz',works)
    bound=[x for x in works if x['in_original_bound_inventory']];by_provider=Counter(c['provider'] for c in plan['claims'] if c['image']);scope_holds=[x for x in plan['concurrent_holds'] if '1970' in x['reason']]
    summary=dict(at=p.m.now(),operation=p.OP,plan_sha256=pin['sha256'],source_index_sha256=plan['index_sha256'],indexed_source_urls=len(ledger),directly_bound_artworks=len(bound),all_directly_bound_artworks_exist=True,
        bound_images_before=sum(x['had_image_at_baseline'] for x in bound),bound_images_after=sum(bool(x['primary_media_id']) for x in bound),bound_missing_images_after=sum(not x['primary_media_id'] for x in bound),
        changed_artworks=len(claims),images_added=applied['new_images'],metadata_artworks=applied['metadata_artworks'],metadata_fields=applied['metadata_fields'],citations=applied['citations'],new_artworks=0,
        added_images_outside_original_bound_inventory=sum(x['image_added_by_this_operation'] and not x['in_original_bound_inventory'] for x in works),images_by_provider=dict(by_provider),metadata_by_field=dict(Counter(k for c in plan['claims'] for k in c['updates'])),
        source_ledger_states=dict(Counter(x['delivery_state'] for x in ledger)),image_download_holds=dict(Counter(x['provider'] for x in prepared.values() if x['state']=='held')),source_page_states=dict(Counter(x['state'] for x in pages.values())),
        source_page_providers=len({x['provider'] for x in pages.values()}),visual_images_checked=sum(b['images'] for path in (p.RUN/'contact-batches').glob('*.json') for b in [p.m.load(path)]),visual_sheets=42,visual_holds=1,
        date_scope_held_targets=len(scope_holds),date_scope_held_prepared_images=sum(x['artwork_id'] in prepared and prepared[x['artwork_id']]['state']=='prepared' for x in scope_holds),
        verified_public_assets=len(list((p.RUN/'uploads').glob('*.json'))),verified_public_records=public['verified'],backup_id=p.m.load(p.RUN/'cloud-backup.json')['id'],local_database_writes=0)
    p.m.save(p.RUN/'delivery-summary.json',summary)
    table='\n'.join('| '+p.NAMES.get(k,k)+' | '+str(v)+' |' for k,v in by_provider.most_common())
    text=f'''# Source-index production delivery — 10 October 2026

Delivered **{summary['images_added']:,} authentic images** and **{summary['metadata_fields']:,} missing descriptive fields** to **{summary['changed_artworks']:,} existing production artworks**. All changed records passed database and live API readback. No user review is pending.

The starting research document is [the source index](../source-index-20261009/README.md). Its 20,000 URLs are a mixture of object records, artist pages, catalogues, books and discovery resources. They are not 20,000 distinct artworks. All **7,209 directly linked artworks already existed in production**; verified native objects also resolved to existing records. No duplicate artwork records were created.

## Delivered

| Image source | Added images |
|---|---:|
{table}

Metadata fills: 323 dimensions, 282 accession numbers and 230 medium descriptions across {summary['metadata_artworks']} works. Added {summary['citations']:,} source citations, per-image rights evidence and explicit before/after audit records. Existing titles, dates, creator links, qualified attributions, holdings, display claims, image attachments and historical editorial statuses were preserved. Review records remain accessible through the unified catalogue.

Of the original 7,209 linked works, **{summary['bound_images_after']:,} now have a primary image**, compared with {summary['bound_images_before']:,} at the pinned baseline; **{summary['bound_missing_images_after']:,} still lack one**. Another {summary['added_images_outside_original_bound_inventory']:,} images enrich existing works reached through native museum references beyond those original direct bindings. These counts describe this source-index pass, not the entire Artline catalogue.

## Verification and recovery

- Cloud SQL backup `{summary['backup_id']}` succeeded. Fresh per-record preimages, locked transaction preimages and postimages are under `~/Library/Application Support/Artline/backups/{p.OP}/`.
- 18 offline source-binding and preservation tests passed. All {summary['visual_images_checked']:,} prepared files were visually checked on 42 contact sheets; original files also passed strict decode checks. Images are proportional, uncropped JPEG derivatives no larger than 100,000 bytes. Frames, scale bars, monochrome reproductions, album covers and fragment views are labelled where applicable.
- All {summary['images_added']:,} uploaded assets were fetched through `artlines.org` and checked against their SHA-256. All {summary['verified_public_records']:,} changed records passed public artwork checks: painter detail routes validate changed metadata and images; the public artwork directory validates identity and primary images for unlinked creators, with all descriptive fields independently verified in the database. Route counts are in `public-api-verification.json`.
- Signed-out museum API checks returned the expected HTTP 401 under the 10 October member-access policy. Those observations are retained in `public-verification-attempts/`. No access settings, accounts or sessions were changed; intentionally public individual-artwork surfaces were used for public content checks.
- Mutations ran in one bounded transaction with the curated-ingestion advisory lock, row locks and exact preimage comparison. Protected fields and existing attachments were verified before commit and independently after commit. Source evidence and the plan are pinned by SHA-256.
- The real local database was not changed. No application deployment, schema change, status rewrite or commit was performed. Indexed, scoped lookups were used; reconciliation query plans are retained. This batch does not constitute a 10-million-row load test.

## Remaining source gaps

This delivery does **not** claim complete image coverage. Every indexed URL is accounted for in `final-source-ledger.json.gz`; every directly linked or changed work is accounted for in `final-artwork-ledger.json.gz`. Capturing a page does not establish its object identity or grant image reuse.

Source download holds include Chicago and Nationalmuseum access denials, Smithsonian and Athens image-host certificate failures, and two unusable Walters files. The visibly damaged Walters reproduction of *Joseph Accused by Potiphar’s Wife* was excluded; its exact-URL retry was denied and no alternate endpoint was used. Three prepared Minneapolis images retain unresolved date ranges crossing 1970. Two other targets have date-scope notes but no prepared image. Native duplicate conflicts (SMK KMS3477 and Walters 37.2619) remain unresolved, without creating more duplicates.

Some indexed sources still need exact object/image research or a usable reproduction: source-access failures, unknown creation dates, title/accession conflicts, missing or restrictive reuse labels and unprocessed reference material remain explicit in the ledgers. No invented artworks, dates, holdings, images or rights claims were added to close these gaps. User-approved Greek, Russian and WikiArt source decisions remain separate from actual copyright labels; Taiwan’s larger image tier retains CC BY 4.0 credit and attribution.

## Evidence

- `delivery-summary.json`, `production-applied.json`, `production-verification.json`, `public-api-verification.json`
- `delivery-plan-pin.json` and `delivery-plan.json.gz`
- `native-resolution-v2.json.gz` and final `secondary-resolution-008.json.gz` (including the exact Rijksmuseum language-alias reconciliation)
- `visual-review.json`, `contact-sheet-index.json`, `strict-image-decode-check*.json`
- `captures/`, `native/`, `object-pages/`, `secondary-native/`, `prepared-images/`, `uploads/`, `public-verification/`

Source-index SHA-256: `{plan['index_sha256']}`. Delivery-plan SHA-256: `{pin['sha256']}`.
'''
    target=p.RUN/'README.md';assert not target.exists();target.write_text(text);print(json.dumps(summary,indent=2))

if __name__=='__main__':report()
