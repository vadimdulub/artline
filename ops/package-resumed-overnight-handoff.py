#!/usr/bin/env python3
"""Finish a newly named handoff from current, verified delivery audits."""
import argparse, collections, csv, importlib.util, json, re, shutil, zipfile
from pathlib import Path

s=importlib.util.spec_from_file_location('e',Path(__file__).with_name('export-overnight-research-handoff.py'))
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
CORE=e.CORE;BASE=e.BASE

def main(phase,index_path):
    root=BASE/'chatgpt-handoff'/phase;prior=BASE/'chatgpt-handoff/final-20260914'
    archive=root.parent/('artline-research-'+phase+'-chatgpt.zip');assert not archive.exists()
    audit_root=BASE/'final-audit'/phase
    audits={t:json.loads((audit_root/(t+'.json')).read_text()) for t in ('local','production')}
    parity=json.loads((audit_root/'semantic-parity.json').read_text());assert parity['matched']
    index=json.loads(index_path.read_text());support=json.loads((root/'support-manifest.json').read_text())
    assert all(r['both_databases_verified'] for r in index['country_rounds'])
    snapshots={t:json.loads((audit_root/(t+'-semantic-snapshot.json')).read_text()) for t in audits}
    csv.field_size_limit(20000000)
    def rows(name):
        with (root/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    def write(name,data,fields=None):
        data=list(data);out=e.CSV(root,name,fields or list(data[0]))
        for row in data:out.add(row)
        return out.finish()
    def textfile(name,text):
        p=root/name;assert not p.exists();p.write_text(text)
    active=[r for r in rows('artworks_added_this_session') if r['status']=='review']
    write('artworks_added_active',active)
    country_exceptions=[r['artwork_slug'] for r in active if not r['artist_country_codes']]
    assert sorted(country_exceptions)==['wikimedia-artwork-q26997957','wikimedia-artwork-q27000045']
    assert all(r['production_artwork_id'] for r in active)
    for r in active:
        if not r['artist_country_codes']:assert all(c['role']=='formerly_attributed_to' for c in json.loads(r['creator_roles']))
    pictures=[]
    for path,im in snapshots['local']['images'].items():
        if not im['verified'] or im['rights_status'] not in ('public_domain','cc0','cc_by','cc_by_sa','licensed'):continue
        assert snapshots['production']['images'][path]==im
        pictures.append(dict(**im,local_image_path=str(e.m.x.ROOT/'apps/web/public'/path.lstrip('/')),production_image_url=e.m.SITE+path,production_upload_verified=True))
    write('verified_selected_images',pictures)
    write('unresolved_creators_top_500',rows('unresolved_creator_labels')[:500])
    historical={r['artwork_slug']:r for r in csv.DictReader((prior/'new_row_identity_review.csv').open(encoding='utf-8-sig',newline=''))}
    fields=list(next(iter(historical.values())))
    identity=[]
    for r in rows('artworks_added_this_session'):
        if r['artwork_slug'] in historical:identity.append(historical[r['artwork_slug']])
        else:
            identity.append(dict(artwork_slug=r['artwork_slug'],title=r['title'],local_id=r['local_artwork_id'],status=r['status'],canonical_local_id=r['local_artwork_id'],canonical_slug=r['artwork_slug'],identity_review='active_new_row_no_prior_identity_found_in_fresh_two_database_plan',earlier_or_other_import_identity_slugs=[],caveat='Fresh Portuguese object/creator identity preflight found no earlier identity. This is not a guarantee of exhaustive uniqueness.'))
    write('new_row_identity_review',identity,fields)
    for target in audits:CORE.save_new(root/(target.upper()+'_AUDIT_SUMMARY.json'),audits[target])
    CORE.save_new(root/'SEMANTIC_PARITY.json',parity)
    CORE.save_new(root/'QUALIFIED_CREATOR_COUNTRY_AUDIT.json',dict(at=CORE.now(),active_additions=len(active),qualified_creator_country=len(active)-len(country_exceptions),historical_attribution_exceptions=country_exceptions,basis='Rijksmuseum rejects the historical Walraven attribution; the two works do not inherit his Dutch cultural affiliation.'))
    shutil.copyfile(BASE/'production-resume-completed.json',root/'PRODUCTION_RESUME_COMPLETED.json')
    shutil.copyfile(audit_root/'public-delivery.json',root/'PUBLIC_DELIVERY_VERIFICATION.json')
    public_checks=json.loads((audit_root/'public-delivery.json').read_text())
    if (audit_root/'recovery-backups.json').exists():shutil.copyfile(audit_root/'recovery-backups.json',root/'RECOVERY_BACKUPS.json')
    prompt=(prior/'RESEARCH_PROMPT.md').read_text().replace('and Finland, with a Portuguese research queue awaiting import','Finland and Portugal, with unresolved Portuguese identity holds retained for further research').replace('The CSV is a dated local snapshot; some later local changes are pending production authentication.','The CSV is a dated local snapshot with a fresh production database ID crosswalk. This session’s delivered records, countries, duplicate redirects and image metadata were compared in both databases; this does not assert equality of every unrelated catalogue record.')
    prompt=prompt.replace('Belgium Finland and Portugal','Belgium, Finland and Portugal')
    prompt+='\nPortuguese follow-up priorities: the three eighteenth-century works Q23701003, Q23737770 and Q23758703 were held because their candidate creator is Francisco Smith (1881–1961). Resolve the exact maker and cultural affiliation from primary museum evidence before proposing a creator link; do not assign Portuguese affiliation automatically from this conflicting candidate. For Simão Álvares (Q61993985, Q62018125 and Q62018150 are the artworks), find primary identity and activity-period evidence while preserving unknown artwork creation dates. The remaining Portuguese holds and their exact reasons are in portugal_research_delivery.csv.\n'
    textfile('RESEARCH_PROMPT.md',prompt)
    local=audits['local'];prod=audits['production'];pt=rows('portugal_research_delivery')
    pt_applied=sum(r['local_db_imported']=='true' and r['production_db_imported']=='true' for r in pt)
    pt_images=sum(r['images_uploaded']=='true' for r in pt)
    holds=len(pt)-pt_applied
    counts=[('Gross added artwork rows','gross_new_artworks'),('Gross added creator profiles','gross_new_artists'),('Verified selected image assets','usable_media')]
    table='| Result | Local | Production |\n|---|---:|---:|\n'+''.join(f"| {label} | {local[k]:,} | {prod[k]:,} |\n" for label,k in counts)
    table+=f"| Active primary images | {parity['active_primary_images']['local']:,} | {parity['active_primary_images']['production']:,} |\n"
    table+=''.join(f"| {kind.title()} duplicates consolidated | {local['duplicate_citation_counts'][kind]:,} | {prod['duplicate_citation_counts'][kind]:,} |\n" for kind in ('artwork','artist'))
    report=f"""# Artline research: production delivery completed

Snapshot: {CORE.now()}. The Google Cloud sign-in issue was resolved and the queued deliveries completed. Twenty country research rounds each for the Netherlands, Greece, Russia, France, Italy, Spain, Germany, Austria, Belgium, Finland and Portugal now have verification receipts in both databases. The ledger also includes 20 additional Greek historical scopes: {len(index['country_rounds'])} country scopes in total. Earlier primary-museum and selected-image follow-ups remain part of the research evidence.

{table}

All {len(active):,} active added works remain **In review**, as do all added creator profiles. Gross inserted rows include replacements of earlier placeholders and rows subsequently archived; they are not a count of newly discovered physical objects. See [row-level identity notes](new_row_identity_review.csv).

## Completed production catch-up

The previously queued one Antwerp panel and 29 selected Finnish/Antwerp images were delivered. Production also received 200 artwork consolidations, four painter consolidations, 235 Finnish primary metadata updates, 222 Russian Museum inventory/material/dimension updates, two Antwerp title corrections, two anonymous-master type corrections and Kuznetsov’s added Ukrainian affiliation. These categories overlap and are not additive counts of distinct objects. Each mutation used the reviewed source evidence and target-specific preimages; changes stopped on conflicting identities or relationships.

Portuguese research prepared {len(pt)} candidates across 20 scopes. Fresh plans applied {pt_applied} records in both databases and delivered {pt_images} selected images; {holds} candidates remain held. The [Portuguese delivery ledger](portugal_research_delivery.csv) records the actual outcomes and reasons, including any additional holds found by the fresh identity checks. Held source facts and images were preserved; no invented creator or museum identity was imported.

Fresh checks added six holds to the eight earlier holds: three eighteenth-century works conflict with the candidate creator Francisco Smith’s 1881–1961 lifespan, and three undated Simão Álvares works lack usable creator chronology in the prepared import. The latter are retained as metadata proposals for primary identity/activity research; no birth, death or creation dates were invented. These are distinct limitations, not a claim that every held record is a proven duplicate or has the wrong creator.

## Country and review status

All {local['gross_new_artists']:,} added creator profiles have cultural-affiliation records. {len(active)-2:,} active added works have qualified creator-country links. Two works retain only a rejected historical attribution to Isaac Walraven and intentionally have no inherited artwork country. The Rijksmuseum object authorities are [SK-A-5036](https://id.rijksmuseum.nl/200653393) and [SK-A-5035](https://id.rijksmuseum.nl/200653392). Painter country, birthplace, imperial citizenship and museum location remain distinct.

The catalogue-wide queue still has {local['global_catalogue']['country_gaps']['missing_cultural']:,} active profiles without documented cultural affiliation. [Country evidence](country_source_evidence.csv) includes source wording and authority links; a review citation is not publication approval. Kuznetsov’s additional affiliation is supported by the [Simferopol Art Museum biography](https://simhm.ru/collection/picture/1199-ko-dnyu-rozhdeniya-nd-kuznecova.html), not inferred from birthplace. Artwork dates remain uncertain where no reliable creation date was available; no current-display claims were invented.

## Duplicate and image evidence

Confirmed duplicate rows were archived with canonical redirects, preserving sources, artwork relationships, images, rights and alternative assertions. Similar titles, shared acquisition registers, recto/verso depictions and whole-work/panel images were not automatically merged. The 170 individually reviewed same-title pairs include 166 distinct-object decisions, two distinct recto/verso decisions and two confirmed Pavia duplicates. See [the decisions](same_title_primary_pair_review.csv) and [consolidation ledger](confirmed_duplicate_consolidations.csv).

Finnish identity checks used exact object IDs, inventories and maker records from the [Finnish National Gallery metadata export](https://kokoelma.kansallisgalleria.fi/api/v1/objects). Numeric artwork IDs were not confused with legacy artist identifiers. Russian Museum inventories distinguished 222 objects in 111 same-title pairs. Later primary metadata enrichment preserved source wording and uncertain dates.

The image CSV retains per-file rights, source pages, credits, SHA-256, dimensions and delivery paths. Reproductions were selected individually, and served derivatives are no larger than 100,000 bytes. Retained duplicate-record assets explain the difference between image-asset and active-primary-image counts. Metadata licensing alone did not authorize image delivery.

## Verification and remaining research

Fresh read-only audits checked this session’s receipt membership, publication state, country coverage, creator links, selection evidence, creation eligibility, validated foreign keys and image-file integrity. [Semantic parity](SEMANTIC_PARITY.json) compared stable catalogue fields, creator roles, country relationships, authorities, redirects and selected image metadata between separately captured local and production snapshots. This is scoped delivery verification, not a claim that every unrelated database row is identical or that every possible duplicate has been found.

Public delivery checks fetched all {len(public_checks['images'])} newly delivered image assets since the earlier handoff and matched their SHA-256 values to the reviewed derivatives. Dutch and Portuguese timelines, plus sampled artwork pages and their data endpoints, returned successful responses. [Public verification receipt](PUBLIC_DELIVERY_VERIFICATION.json)

{support['unlinked_artworks']:,} older review works still lack creator links across {support['unresolved_creator_labels']:,} labels. Country gaps, Portuguese holds and remaining duplicate candidates are research queues. The [ChatGPT prompt](RESEARCH_PROMPT.md) requests sourced proposals, preserves uncertainty and forbids direct database mutation. The earlier pre-reauthentication archive remains unchanged as dated evidence. No application deployment or publication was needed for these data updates.
"""
    textfile('REPORT.md',report)
    textfile('README.md',f"""# Artline: verified research handoff

Start with [REPORT.md](REPORT.md), then paste [RESEARCH_PROMPT.md](RESEARCH_PROMPT.md) into ChatGPT and attach the relevant CSVs. The archive contains metadata and image-source links; artwork binaries and database backups remain in their dedicated local/GCS locations.

- `artworks_added_active.csv`: {len(active):,} active additions, including reconciled replacement identities.
- `artworks_added_this_session.csv`: gross inserted rows, including later archived duplicates.
- `artwork_identity_index_*.csv`: complete local catalogue identity baseline, split into bounded files.
- `artworks_NL_*.csv` and other country files: country-focused research; multiple affiliations can overlap.
- `painters_country_inventory.csv`, `painters_country_gaps.csv`, `country_source_evidence.csv`: creator identities and documented cultural affiliations.
- `verified_selected_images.csv`: selected authentic reproductions, rights, credits, local paths and production URLs.
- `confirmed_duplicate_consolidations.csv`, `same_title_primary_pair_review.csv`, `unresolved_duplicate_leads.csv`: confirmed decisions versus unresolved research leads.
- `portugal_research_delivery.csv`: actual import/image outcomes and retained holds.
- `unresolved_creators_top_500.csv`: manageable starting queue for creator reconciliation.
- `research_round_ledger.csv`, `local_and_production_delivery.csv`, audit JSONs: completion evidence.

CSV files use UTF-8 with BOM, RFC4180 quoting and JSON for multivalue cells. Formula-leading literal text is prefixed with an apostrophe; that escape is not part of the source wording. Match by stable slug and exact source identity, not a cross-environment UUID. Use canonical redirects before proposing duplicates. The two Walraven historical-attribution works intentionally do not inherit his country. All active additions remain In review.
""")
    checks={};ids=set();slugs=set()
    for path in sorted(root.glob('*.csv')):
        n=0
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);assert reader.fieldnames and len(reader.fieldnames)==len(set(reader.fieldnames))
            for row in reader:
                assert None not in row and all(v is not None for v in row.values())
                assert all(not v.lstrip().startswith(('=','+','-','@')) and not v.startswith(('\t','\r','\n')) for v in row.values())
                if path.name.startswith('artwork_identity_index_'):
                    assert row['local_artwork_id'] not in ids and row['artwork_slug'] not in slugs;ids.add(row['local_artwork_id']);slugs.add(row['artwork_slug'])
                n+=1
        checks[path.name]=dict(rows=n,sha256=CORE.sha(path.read_bytes()))
    expected=sum(r['n'] for r in local['global_catalogue']['artwork_status']);assert len(ids)==expected
    assert len(pictures)==local['usable_media']==prod['usable_media']
    for path in root.glob('*.json'):json.loads(path.read_text())
    for path in root.glob('*.md'):
        for ref in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            if not re.match(r'^[a-z]+://',ref) and not ref.startswith('#'):assert (path.parent/ref.split('#')[0]).exists(),(path,ref)
    CORE.save_new(root/'PACKAGE_VALIDATION.json',dict(at=CORE.now(),csv_files=len(checks),csv_checks=checks,unique_artwork_identities=len(ids),active_additions=len(active),selected_images=len(pictures),production_pending_deliveries=0,country_exceptions=country_exceptions,json_parsed=True,local_markdown_links_resolve=True,semantic_parity_verified=True))
    files=[dict(name=p.name,bytes=p.stat().st_size,sha256=CORE.sha(p.read_bytes())) for p in sorted(root.iterdir())]
    CORE.save_new(root/'PACKAGE_MANIFEST.json',dict(at=CORE.now(),files=files,scope='Current CSV snapshot plus source and delivery evidence; no image binaries, credentials or database dumps.',local={k:local[k] for _,k in counts},production={k:prod[k] for _,k in counts},portugal=dict(candidates=len(pt),applied_both=pt_applied,selected_images=pt_images,held=holds),all_rounds_verified_both=True))
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for path in sorted(root.iterdir()):assert path.is_file() and path.suffix in ('.json','.csv','.md');z.write(path,path.name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for item in files:assert CORE.sha(z.read(item['name']))==item['sha256']
    receipt=dict(at=CORE.now(),archive=str(archive),bytes=archive.stat().st_size,sha256=CORE.sha(archive.read_bytes()),files=len(files)+1,csv_files=len(checks),zip_crc_verified=True,manifest_entries_verified=True)
    CORE.save_new(archive.with_suffix('.receipt.json'),receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',required=True);p.add_argument('--session-index',type=Path,required=True);a=p.parse_args();assert all(c.isalnum() or c in '-_' for c in a.phase);main(a.phase,a.session_index)
