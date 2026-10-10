#!/usr/bin/env python3
"""Read-only production reconciliation and honest island-wide coverage report."""
import collections,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('island',Path(__file__).with_name('cyprus-island-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
h,n,d,R=x.h,x.n,x.d,x.R
def run():
    institution_dirs=[R,*sorted((R/'waves').glob('cyprus-island-institutions-*'))]
    art_dirs=sorted(p.parent for p in (R/'waves').glob('*/artworks-applied.json'))
    ir=[h.load(p/'institutions-applied.json')for p in institution_dirs]
    ar=[h.load(p/'artworks-applied.json')for p in art_dirs]
    plans=[h.load(p/'artwork-plan.json.gz')for p in art_dirs]
    for path,receipt in zip(art_dirs,ar):
        assert h.sha((path/'artwork-plan.json.gz').read_bytes())==receipt['plan_sha256']
        assert h.load(path/'production-verification.json')['verified']
    for path,receipt in zip(institution_dirs,ir):
        assert h.sha((path/'institution-plan.json.gz').read_bytes())==receipt['plan_sha256']
        assert h.load(path/'institution-verification.json')['verified']
    new_ids=[row['artwork_id']for p in plans for row in p['records']if row['action']=='create']
    expected={row['artwork_id']:row['museum']['id']for p in plans for row in p['records']}
    assert len(new_ids)==len(set(new_ids))==sum(v['new_artworks']for v in ar)
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        assert db.execute('SELECT current_database()name').fetchone()['name']=='artline'
        museums=db.execute("SELECT i.id::text,i.name,i.slug,i.status,p.name place FROM institutions i JOIN places p ON p.id=i.place_id WHERE p.country_code='CY' ORDER BY p.name,i.name").fetchall()
        mids=[r['id']for r in museums]
        query="""SELECT current_institution_id::text institution_id,count(*)artworks,
          count(*)FILTER(WHERE artline_creation_scope(creation_year_start,creation_year_end,date_precision)='eligible')eligible,
          count(*)FILTER(WHERE status='published')published,count(*)FILTER(WHERE primary_media_id IS NOT NULL)with_images
          FROM artworks WHERE current_institution_id=ANY(%s::uuid[])AND status<>'archived'GROUP BY current_institution_id"""
        count_plan=db.execute('EXPLAIN(FORMAT JSON) '+query,(mids,)).fetchone()
        counts={r['institution_id']:r for r in db.execute(query,(mids,))}
        current=db.execute("SELECT id::text,current_institution_id::text,status,published_at,primary_media_id,artline_creation_scope(creation_year_start,creation_year_end,date_precision)scope FROM artworks WHERE id=ANY(%s::uuid[])",(list(expected),)).fetchall()
        assert len(current)==len(expected)
        new=set(new_ids)
        for row in current:
            assert row['current_institution_id']==expected[row['id']]
            if row['id']in new:assert row['status']=='review'and row['published_at']is None and row['primary_media_id']is None
        holdings=db.execute("SELECT artwork_id::text,institution_id::text FROM artwork_location_assertions WHERE artwork_id=ANY(%s::uuid[])AND claim_type='holding'AND review_state='accepted'AND superseded_by IS NULL",(list(expected),)).fetchall()
        assert len(holdings)==len(expected)and {r['artwork_id']:r['institution_id']for r in holdings}==expected
        qualification=h.load(R/'pomos-citation-qualification.json')
        note=db.execute('SELECT evidence_note FROM citations WHERE id=%s',(qualification['citation_id'],)).fetchone();assert json.loads(note['evidence_note'])['editorial_confidence']==.88
    before={r['id']:r for r in h.load(R/'production-baseline.json.gz')['cyprus_counts']}
    for row in museums:
        row.update({k:counts.get(row['id'],{}).get(k,0)for k in ['artworks','eligible','published','with_images']})
        row['before_artworks']=before.get(row['id'],{}).get('artworks',0)
        row['remaining_to_500']=max(0,500-row['artworks'])
        row['target_status']='500_to_1000_reached'if 500<=row['artworks']<=1000 else'above_1000'if row['artworks']>1000 else'below_500'
    summary=dict(at=h.now(),target='production',verified=True,new_institutions=sum(v['new_institutions']for v in ir),new_places=sum(v['new_places']for v in ir),geography_enrichments=sum(v['geography_enrichments']for v in ir),new_artworks=len(new),new_links=sum(v['new_links']for v in ar),painter_links=sum(v['painter_links']for v in ar),tracked_cyprus_institutions=len(museums),total_artworks=sum(r['artworks']for r in museums),institutions_at_least_500=sum(r['artworks']>=500 for r in museums),institutions_below_500=sum(r['artworks']<500 for r in museums),institutions_without_artworks=sum(r['artworks']==0 for r in museums),new_creation_scopes=dict(collections.Counter(r['scope']for r in current if r['id']in new)),new_publications=0,new_display_claims=0,image_changes=0,local_database_writes=0)
    gaps=[
      dict(source='https://www.visitcyprus.com/discover-cyprus/culture/museums-galleries/the-archibishop-kyprianos-museum/',constraint='Official directory states 138 total exhibits. A 500-object target exceeds the documented collection, even before eligibility filtering.'),
      dict(source='https://musan.com.cy/',constraint='Museum states 93 sculptures created in 2021. Institution added; works are outside the <=1970 creation scope.'),
      dict(source='https://larnakaregion.com/directory/product/museum-christian-art-christoforou-collection',constraint='Collection described as 300+ works. Twenty individually identified tour records delivered; no evidence establishes 500 eligible works.'),
      dict(source='https://www.kyreniaship.com/objects',constraint='573 selected craft/art-object leads indexed. Sampled research histories include missing objects, fragments, duplicate aliases, overseas analysis locations and paginated events. No accepted production holding added from these unresolved leads.'),
      dict(source='https://dioptra.cyi.ac.cy/',constraint='Certificate error prevented retrieval. No TLS bypass; digitisation totals are not object records or verified holdings.'),
      dict(source='https://hambismuseum.cy/category/artworks/',constraint='Shared collection spans Nicosia and Platanisteia branches. Branch-specific object custody remains unresolved; do not duplicate shared works into both museums.'),
      dict(source='https://leventisgallery.org/wp-json/wp/v2/artworks?per_page=100&page=4',constraint='Official API reports no fourth page. Existing native and Cypriot-artist sources do not establish 500 eligible, distinct museum records in this pass.'),
      dict(source='https://www.pomos.org.cy/',constraint='Municipal website returned certificate-origin error. Museum identity retained in review from local reporting, with explicit historical-identity uncertainty and 0.88 editorial confidence.'),
    ]
    h.save(R/'final-production-coverage.json',dict(summary=summary,institutions=museums,source_gaps=gaps,institution_receipts=ir,artwork_receipts=ar))
    h.save(R/'final-count-query-plan.json',count_plan)
    changed=[r for r in museums if r['artworks']>r['before_artworks']]
    text=f'''# Cyprus island expansion — 7 October 2026

Production verified at {summary['at']}.

Added **{summary['new_institutions']} institution records**, **{summary['new_artworks']:,} artwork records**, **{summary['new_links']} links to existing artworks**, and **{summary['painter_links']} links to existing painter identities**. Added {summary['new_places']} places and filled Kykkos Museum's missing geography. All new institutions and artworks remain in review. Existing metadata, images and publication states were preserved. No new images, publication changes, display assertions, local catalogue writes, commits or deployments.

The tracked Cyprus scope is now **{len(museums)} institutions and {summary['total_artworks']:,} artworks**. This is a researched registry, not a certification that every museum on the island has been found. **Only {summary['institutions_at_least_500']} institutions meet the requested minimum of 500; {summary['institutions_below_500']} remain below it, including {summary['institutions_without_artworks']} with no artwork records. The requested per-museum target is not complete.** Some documented collections contain fewer than 500 total objects; others lack sufficient verified object-level evidence or predominantly contain works outside the creation cutoff.

## Collections enriched in this pass

| Museum | Before | Production artworks | Dated eligible |
| --- | ---: | ---: | ---: |
'''
    text+='\n'.join(f"| {r['name']} | {r['before_artworks']} | {r['artworks']} | {r['eligible']} |"for r in sorted(changed,key=lambda r:-r['artworks']))
    text+='''

“Dated eligible” is the backend creation-scope classification; it does not mean published. Unknown dates remain unknown. Seven source dates stated as circa 1970 correctly remain in editorial review. Artist life dates, print-design dates, acquisition dates and excavation dates were not substituted for object creation dates.

## Evidence and verification

The national Visit Cyprus directory, Department of Antiquities, municipal/regional directories, northern departmental and tourism sources, and museum-owned websites supplied institutional evidence. Additional rural collections and separate branches were reconciled before insertion. Actual source URLs, native identifiers, literal metadata, source body hashes and retrieval timestamps are preserved in research captures and production citations.

The main artwork batch used selected CVAR and Makarios object pages. The regional batch used the Department of Antiquities' official *Ancient Cyprus: Cultures in Dialogue* (2012) catalogue, Kykkos Monastery's hosted museum guide, and the officially linked Aradippou Christian Art Museum virtual tour. Historical catalogue holdings are explicitly distinguished from current display. Detail images and duplicate native objects were not counted as extra artworks. Seventeen native identity candidates remain held; source exclusions are recorded separately.

Each production transaction used an acknowledged full-instance backup, transaction-specific preimages, source hash checks, object/version checks, duplicate checks, the curated-ingestion lock and an atomic transaction. Independent read-only checks verified all delivered artwork holdings, source citations, review/publication states and retained metadata. The final country-scoped count and plan are saved. No application query or 10-million-row load-performance claim is made.

Two attempts rolled back entirely on schema validation before successful retries: blank creator labels now map to NULL; absent date-display text maps to “Unknown” while numeric years remain NULL. Literal source fields remain in citations. A later audited correction explicitly identifies the Pomos evidence as local reporting and lowers its historical-identity confidence to 0.88.

Backups and preimages are under `/Users/vadimdulub/Library/Application Support/Artline/backups/cyprus-island-expansion-20261007/`.

## Outstanding source work

'''
    text+='\n'.join(f"- [{g['source']}]({g['source']}): {g['constraint']}"for g in gaps)
    text+='''

All remaining institution counts and numeric gaps are below and in [final-production-coverage.json](final-production-coverage.json). A missing artwork count is not an assertion that the museum has no real collection. It identifies unfilled Artline coverage requiring individual object research.

## All tracked institutions

| Institution | Place | Artworks | Dated eligible | Gap to 500 |
| --- | --- | ---: | ---: | ---: |
'''
    text+='\n'.join(f"| {r['name']} | {r['place']} | {r['artworks']} | {r['eligible']} | {r['remaining_to_500']} |"for r in museums)+'\n'
    dest=R/'README.md';assert not dest.exists();dest.write_text(text)
    h.save(R/'delivery-manifest.json',dict(at=h.now(),files=[dict(path=str(p.relative_to(n.REPO)),sha256=h.sha(p.read_bytes()))for p in [*sorted((n.REPO/'ops').glob('cyprus-island-*-20261007.py')),R/'README.md',R/'final-production-coverage.json',*sorted(R.glob('*verification.json')),*sorted((R/'waves').glob('*/*applied.json')),*sorted((R/'waves').glob('*/*verification.json'))]]))
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':run()
