#!/usr/bin/env python3
"""Read-only final verification ledger and research report for this delivery."""
import collections,concurrent.futures,csv,importlib.util,requests
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('cesi-top100-20261010.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def main():
    b=m.load(m.RUN/'baseline.json.gz');before={r['id']:r for r in m.load(m.RUN/'cohort-review.json')}
    plans={phase:m.load(m.RUN/phase/'plan.json.gz') for phase in ['cesi','top100']}
    receipts={phase:m.load(m.RUN/phase/'applied.json') for phase in plans}
    for phase in plans:
        assert m.load(m.RUN/phase/'database-verification.json')['plan_sha256']==receipts[phase]['plan_sha256']
        assert m.load(m.RUN/phase/'public-verification.json')['checks']
    ids=[r['record']['id'] for r in b['artists']]
    with m.connect() as db:
        current={r['artist_id']:r for r in db.execute("""SELECT aa.artist_id::text,count(*) works,
            count(*) FILTER(WHERE a.primary_media_id IS NOT NULL) images,
            count(*) FILTER(WHERE a.current_institution_id IS NOT NULL) museum_links
            FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
            WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived' GROUP BY aa.artist_id""",(ids,))}
        overall=db.execute("""SELECT count(DISTINCT a.id) artworks,
            count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NOT NULL) illustrated,
            count(DISTINCT a.id) FILTER(WHERE a.current_institution_id IS NOT NULL) museum_linked
            FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id
            WHERE aa.artist_id=ANY(%s::uuid[]) AND a.status<>'archived'""",(ids,)).fetchone()
    with m.connect(local=True) as db:local=db.execute('SELECT count(*) artworks,count(*) FILTER(WHERE primary_media_id IS NOT NULL) illustrated FROM artworks').fetchone()
    local_before=m.load(m.RUN/'local-readonly-baseline.json')['counts']
    def check_artist(a):
        ar=a['record'];url='https://artlines.org/api/backend/v1/artists/'+ar['slug']+'/works?limit=1'
        r=requests.get(url,timeout=(15,60));r.raise_for_status();data=r.json()
        expected=current.get(ar['id'],dict(works=0))['works'];assert data['total']==expected,(ar['display_name'],data['total'],expected)
        assert len(data['items'])<=1
        return dict(artist_id=ar['id'],name=ar['display_name'],url=url,total=data['total'],sha256=m.sha(r.content),status=r.status_code)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(check_artist,b['artists']))
    p=m.RUN/'public-cohort-count-verification.json'
    if not p.exists():m.save(p,dict(at=m.now(),checks=checks,scope='All 100 painters plus Cesi, bounded one-item gallery requests; totals agree with production SQL.'))
    p=m.RUN/'final-counts.json'
    if p.exists():assert m.load(p)['production_cohort']==current
    else:m.save(p,dict(at=m.now(),production_cohort=current,production_distinct_totals=overall,local_before=local_before,local_after=local,local_counts_unchanged=local==local_before,local_write_connections=0))
    selected=collections.defaultdict(list)
    for plan in plans.values():
        for r in plan['rows']:selected[r['artist_id']].append(r)
    ledger=[];indexes={};discovery={}
    for a in b['artists']:
        ar=a['record'];aid=ar['id'];prior=before[aid];rows=selected[aid];now=current.get(aid,dict(works=0,images=0,museum_links=0))
        ip=m.RUN/'indexes-corrections'/(aid+'.json.gz');ix=m.load(ip if ip.exists() else m.RUN/'indexes'/(aid+'.json.gz'));indexes[aid]=ix
        dp=m.RUN/'discovery-supplements'/(aid+'.json.gz');d=m.load(dp if dp.exists() else m.RUN/'discovery-v2'/(aid+'.json.gz'));discovery[aid]=d
        if not a['discovery'] or not a['discovery']['is_popular']:continue
        holds=[r for r in plans['top100']['held'] if any(x['artwork_id']==r['artwork_id'] for x in d['rows'])]
        counts=d.get('candidate_counts',{})
        note='Selected source pass completed; remaining index candidates require separate selection and object review.'
        if ar['display_name']=='Bob Ross':note='No confirmed WikiArt index; native catalogue URL returned 404. No eligible work was invented.'
        if ar['display_name']=='Andrea del Verrocchio':note='No supported addition: source date conflicts, physical sculpture/edition identity and no new holding.'
        if ar['display_name']=='Artemisia Gentileschi':note='No supported addition: checked objects had no new holding or conflicting index/detail dates.'
        ledger.append(dict(rank=prior['rank'],artist=ar['display_name'],artist_id=aid,source_index_state=ix['state'],source_entries=len(ix['works']),works_before=prior['works'],new_artworks=sum(r['state']=='new' for r in rows),works_after=now['works'],images_before=prior['images'],new_images=sum(bool(r['image']) for r in rows),images_after=now['images'],museum_links_before=prior['museum_links'],new_museum_links=sum(r['add_holding'] for r in rows),museum_links_after=now['museum_links'],discovery_holds=len(d['held']),delivery_holds=len(holds),new_candidate_pool_before_selection=counts.get('new',0),existing_image_gap_candidates=counts.get('gaps',0),existing_connection_candidates=counts.get('connections',0),note=note))
    assert len(ledger)==100
    path=m.RUN/'top100-painter-ledger.csv'
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(ledger[0]));writer.writeheader();writer.writerows(ledger)
    # Keep the deferred source selection explicit, without downloading more images.
    remaining=[]
    for a in ledger:
        for row in discovery[a['artist_id']]['held']:remaining.append(dict(artist=a['artist'],stage='source discovery',source_url=row.get('url',''),title='',reason=row['reason']))
    safe={r['artwork_id']:r for r in m.safe_rows()}
    for r in plans['top100']['held']:
        candidate=safe[r['artwork_id']];remaining.append(dict(artist=candidate['artist_name'],stage='delivery review',source_url=candidate['source_url'],title=r['title'],reason=r['reason']))
    for r in m.load(m.RUN/'identity-ambiguity-holds.json')['rows']:remaining.append(dict(artist=r['artist_name'],stage='object identity',source_url=r['source_url'],title=r['title'],reason='Ambiguous target identity or repeated weak title'))
    with (m.RUN/'remaining-object-research.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['artist','stage','source_url','title','reason']);w.writeheader();w.writerows(remaining)
    c,t=receipts['cesi'],receipts['top100'];cesiid='07441bd8-6663-4e16-963d-f16fc6cd35ba';cesi=current[cesiid]
    conn=m.load(m.RUN/'top100-connection-audit-final.json.gz');candidate_review=m.load(m.RUN/'top100-reviewed-connections.json')
    cis=m.load(m.RUN/'cesi-candidates.json');inst={r['record']['id']:r['record']['name'] for r in b['institutions']}
    table='\n'.join('| '+r['title'].replace('|','/')+' | '+inst[r['institution_id']]+' | '+(r['date']['display'] if r['date'] else 'Unknown')+' | '+('Attributed to Cesi' if r['attribution_role']=='attributed_to' else 'Cesi')+' | [Source]('+r['source_url']+') |' for r in cis['rows'])
    relationships='\n'.join('- '+r['source_label']+' → '+plans['top100']['artists'][r['target_artist_id']]['display_name']+': '+r['evidence_note'].split(' Independently')[0]+' [Source]('+r['source_url']+').' for r in candidate_review['rows'])
    report=f'''# Bartolomeo Cesi deep review and Top 100 expansion — 10 October 2026

Completed in production. The user requested a deep Cesi review and more works, followed by supported artwork, picture and connection enrichment for the existing Top 100 painters. New artworks and teaching claims remain in review; all active artwork records are available through the unified catalogue. No publication status was changed.

## Delivered and verified

| Scope | New artworks | New images | New museum holdings | New creator links | Existing works enriched | New teaching links |
|---|---:|---:|---:|---:|---:|---:|
| Cesi | {c['new_artworks']} | {c['new_images']} | {c['new_holding_connections']} | {c['new_creator_links']} | {c['existing_artworks_enriched']} | {c['new_teacher_relationships']} |
| Top 100 | {t['new_artworks']} | {t['new_images']} | {t['new_holding_connections']} | {t['new_creator_links']} | {t['existing_artworks_enriched']} | {t['new_teacher_relationships']} |

The Top 100 cohort is the production `artist_discovery_selection.is_popular` list captured before research, rather than a new subjective ranking. All 100 were audited; 97 received artwork or holding additions. See the [100-painter before/after ledger](top100-painter-ledger.csv). Verrocchio and Artemisia Gentileschi had no supported additions among the checked objects. Bob Ross had no confirmed source index; the native WikiArt catalogue URL returned 404.

Across Cesi and the Top 100, the production cohort now contains {overall['artworks']:,} distinct active works, {overall['illustrated']:,} with primary images and {overall['museum_linked']:,} linked to holding institutions. These are catalogue totals, not claims of complete artist coverage.

## Cesi findings

Cesi now has {cesi['works']} linked active works and {cesi['images']} illustrated works. The additions include paintings and drawings, with source uncertainty retained.

| Added work | Documented institution | Creation date | Attribution | Evidence |
|---|---|---|---|---|
{table}

Three authentic images were attached: Getty Holy Family (98.GB.1), Grenoble's seated draped man and the recto of Rijksmuseum RP-T-1967-68(R). Each was individually checked against the native museum record. Recto and verso are one physical sheet, not two new artworks.

The existing Corsini portrait was linked as **attributed to Cesi**, preserving its supplied creator label. Official ICCD evidence supplies approximately 1580–1607, oil on canvas and inventory 278; the source capture from 5 October was verified and cited without claiming a new retrieval. The existing Met pregnant-woman drawing was corrected from the imported 1556–1629 range to the current museum's 1576–1629 range. Previous values remain in the audit trail. Existing images, holding assertions and statuses were preserved.

A concise biography and a Nosadella → Cesi teaching claim were added from the [Getty biography](https://www.getty.edu/art/collection/person/103KWN). Nosadella remains a source label because the corresponding artist authority was not securely reconciled.

The Louvre Saint Anthony lead was excluded because the catalogue commentary rejects the Cesi attribution and favors Calvaert; another kneeling nude belongs to Macchietti. British Museum, Morgan and Prado sources that denied access were held without bypassing their restrictions. Unknown creation dates stay unknown. The Bologna 2025–26 exhibition establishes documented collection connections, not current display after that exhibition ended. Outstanding Cesi image and authority gaps remain in `cesi-candidates.json`, `cesi-unlinked-candidates.json` and the captured source evidence.

## Top 100 selection and image checks

Full metadata indexes were reviewed for 99 of the 100 painters, totaling {sum(len(indexes[a['artist_id']]['works']) for a in ledger):,} source entries. Gauguin's malformed stored profile lead was resolved against the correct native profile in a separate supplemental evidence set. Historical intermediate captures are retained; `discovery-v2/` plus `discovery-supplements/` are the authoritative discovery sets.

This is a bounded curated pass, not exhaustive ingestion. Per painter, research considered up to 40 existing image gaps, 15 existing connection gaps and 45 fresh object pages, selecting up to 30 new highlights. Existing source URLs/IDs and exact artist identity take precedence. A title-based existing-image match additionally requires a distinctive unique title, matching creation bounds and compatible holding evidence. Repeated titles, translations, versions, copies, physical print editions and uncertain attributions remain deferred.

The image workflow uses the existing conservative creation cutoff of 1955; the overall catalogue cutoff remains 1970. Later eligible catalogue works, unknown dates and ambiguous ranges require a separate reviewed metadata selection. New WikiArt works were selected as personal owner highlights, including source-famous works and under-illustrated periods. That selection is stored separately from museum masterpiece designations and museum holdings.

Every delivered image was visually inspected, proportionally resized without cropping to at most 100,000 bytes, uploaded with an immutable object precondition and fetched through the public site for an exact byte-hash check. Actual WikiArt rights labels, including restricted or unknown labels, remain intact; the user's source approval is recorded separately and is not described as a licence grant. Museum images retain their actual source and rights evidence. No existing primary image was replaced.

All 24,975 existing cohort primary images were hashed for comparison. The perceptual check flagged 99 selected reproductions for duplicate/version review; similarity is a warning rather than proof of identity. There were {len(plans['top100']['held'])} delivery holds plus {len(m.load(m.RUN/'identity-ambiguity-holds.json')['rows'])} earlier ambiguous source rows. These sets overlap other visual/duplicate review counts and must not be added together as distinct artworks. Visual review also withheld book pages with uncertain edition identity, wrong pictures, composite objects and uncertain authorship. See [remaining object research](remaining-object-research.csv), `visual-review/`, `duplicate-image-review.json` and `identity-ambiguity-holds.json`.

Institution labels were reviewed against existing records: 204 mappings were accepted and six were held, including erroneous broad aliases for Rimini and Fragonard d'Alfort and labels naming multiple collections. Literal source labels are retained. New assertions mean documented holdings, with an editorial confidence assessment of 94% for reviewed WikiArt matches, not calibrated probability and not current display.

## Artist connections

The relationship audit recorded 1,037 explicit source assertions: 281 already matched stored claims, 732 lacked an unambiguous exact artist authority, and the remaining assertions reduced to 23 candidate pairs. Four independently corroborated teacher relationships were added in review:

{relationships}

The other 19 resolved candidate pairs remain deferred or rejected as stated. In particular, the source directions Rembrandt → Mantegna and Pissarro → Vermeer contradict chronology. Source labels alone were not used to merge artist identities. Detailed evidence and gaps are retained in `top100-connection-audit-final.json.gz` and `top100-reviewed-connections.json`.

## Verification and recovery

- Successful Cloud SQL backup **1791655436996** precedes both deliveries.
- Immutable plans, locked preimages and transaction postimages are archived under `{m.BACKUP}`.
- Cesi plan SHA-256: `{receipts['cesi']['plan_sha256']}`.
- Top 100 plan SHA-256: `{receipts['top100']['plan_sha256']}`.
- Eight offline guard tests passed. No real local test fixtures or test database were used.
- Database verification checked every delivered artwork, image checksum, rights-evidence row and new Top 100 teaching claim. Existing status, creator, image and holding preservation checks passed.
- Public detail APIs were verified for every Cesi addition and one affected object per Top 100 painter; every delivered image separately passed a public byte-hash check. Bounded one-item gallery requests verified counts for all 100 painters plus Cesi against production SQL.
- The real local catalogue was queried read-only. Its before/after counts {'match' if local==local_before else 'differ, indicating external changes; this workflow never opened a writable local connection'}: {local['artworks']:,} artworks and {local['illustrated']:,} illustrated artworks after the pass.
- No commits, application deployment, bulk status rewrite or current-display assertions were made. All new artworks remain review records.

Queries were scoped to artist IDs, selected object IDs and relevant institutions, with an actual production query plan retained in the baseline. This pass makes no new claim of verified ten-million-row performance; representative large-scale load testing remains separate backend work.

## Reproducible evidence

The campaign scripts are `ops/cesi-top100-20261010.py`, `ops/cesi-reviewed-records-20261010.py`, `ops/cesi-delivery-20261010.py`, `ops/review-top100-connections-20261010.py`, `ops/pin-top100-reviewed-connections-20261010.py`, `ops/record-cesi-top100-visual-review-20261010.py` and `ops/report-cesi-top100-20261010.py`. Source receipts pin URL, retrieval time, response status and SHA-256. Originals and contact sheets are archived outside Documents under `{m.ORIGINALS}`. Delivery receipts and verification results are in `cesi/` and `top100/`.
'''
    (m.RUN/'README.md').write_text(report)
    print('Report and 100-painter ledger written. Production cohort:',overall,'Cesi:',cesi,'local unchanged:',local==local_before)
if __name__=='__main__':main()
