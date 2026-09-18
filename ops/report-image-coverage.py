#!/usr/bin/env python3
"""Read-only image coverage counts, with explicit scope and review semantics."""
import argparse,importlib.util,json,time
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

s=importlib.util.spec_from_file_location('image_core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
SQL="""
WITH popular_works AS MATERIALIZED (
 SELECT DISTINCT aa.artwork_id FROM artist_discovery_selection d
 JOIN artists ar ON ar.id=d.artist_id AND ar.status<>'archived'
 JOIN artwork_artists aa ON aa.artist_id=d.artist_id WHERE d.is_popular
), supported AS MATERIALIZED (
 SELECT la.artwork_id FROM artwork_location_assertions la
 JOIN sources s ON s.id=la.source_id JOIN institutions i ON i.id=la.institution_id
 WHERE la.claim_type='holding' AND la.review_state='accepted' AND la.superseded_by IS NULL
 AND s.is_active AND i.status<>'archived' AND length(trim(la.evidence_note))>0 AND la.checked_at<=now()
 UNION
 SELECT ci.artwork_id FROM curated_collection_items ci
 JOIN curated_collections cc ON cc.id=ci.collection_id LEFT JOIN sources s ON s.id=ci.source_id
 WHERE cc.status<>'archived' AND length(trim(ci.reason))>0
 AND (cc.curator_kind='owner' OR (s.is_active AND ci.source_url IS NOT NULL AND ci.checked_at<=now()))
), base AS MATERIALIZED (
 SELECT a.id,a.work_type,a.primary_media_id IS NOT NULL attached,
   coalesce(m.verified_at IS NOT NULL AND m.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa','licensed')
     AND nullif(trim(m.alt_text),'') IS NOT NULL AND nullif(m.storage_path,'') IS NOT NULL,false) usable_image,
   p.artwork_id IS NOT NULL popular,
   artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,
   s.artwork_id IS NOT NULL supported
 FROM artworks a LEFT JOIN media_assets m ON m.id=a.primary_media_id
 LEFT JOIN popular_works p ON p.artwork_id=a.id LEFT JOIN supported s ON s.artwork_id=a.id
 WHERE a.status<>'archived'
), groups AS (
 SELECT 'all_artworks' scope,* FROM base
 UNION ALL SELECT 'paintings',* FROM base WHERE work_type='painting'
 UNION ALL SELECT 'popular_painter_artworks',* FROM base WHERE popular
 UNION ALL SELECT 'popular_painter_paintings',* FROM base WHERE popular AND work_type='painting'
 UNION ALL SELECT 'eligible_supported_artworks',* FROM base WHERE date_scope='eligible' AND supported
 UNION ALL SELECT 'eligible_supported_paintings',* FROM base WHERE date_scope='eligible' AND supported AND work_type='painting'
 UNION ALL SELECT 'eligible_supported_popular_artworks',* FROM base WHERE date_scope='eligible' AND supported AND popular
 UNION ALL SELECT 'eligible_supported_popular_paintings',* FROM base WHERE date_scope='eligible' AND supported AND popular AND work_type='painting'
)
SELECT scope,count(*) total,count(*) FILTER(WHERE attached) image_attached,
 count(*) FILTER(WHERE usable_image) usable_image,
 count(*) FILTER(WHERE NOT attached) no_image_attached,
 count(*) FILTER(WHERE NOT usable_image) missing_usable_image,
 count(*) FILTER(WHERE NOT usable_image AND date_scope<>'eligible') date_review_or_out_of_scope,
 count(*) FILTER(WHERE NOT usable_image AND NOT supported) without_selection_evidence
FROM groups GROUP BY scope ORDER BY scope
"""

def snapshot(dsn):
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row,
                         options='-c default_transaction_read_only=on -c statement_timeout=90000') as db:
        rows=db.execute(SQL).fetchall()
        artists=db.execute("""WITH counts AS (
          SELECT ar.id,ar.slug,ar.display_name,coalesce(d.is_popular,false) popular,
          count(DISTINCT a.id) works,count(DISTINCT a.id) FILTER(WHERE a.primary_media_id IS NOT NULL) with_image,
          count(DISTINCT a.id) FILTER(WHERE a.work_type='painting') paintings,
          count(DISTINCT a.id) FILTER(WHERE a.work_type='painting' AND a.primary_media_id IS NULL) paintings_without_image
          FROM artists ar LEFT JOIN artist_discovery_selection d ON d.artist_id=ar.id
          LEFT JOIN artwork_artists aa ON aa.artist_id=ar.id
          LEFT JOIN artworks a ON a.id=aa.artwork_id AND a.status<>'archived'
          WHERE ar.status<>'archived' GROUP BY ar.id,d.is_popular
        ) SELECT slug,display_name,popular,works,with_image,works-with_image missing_images,
          paintings,paintings_without_image FROM counts
          WHERE popular ORDER BY paintings_without_image DESC,works-with_image DESC,display_name""").fetchall()
        types=db.execute("""SELECT work_type,count(*) total,count(primary_media_id) with_image,
          count(*) FILTER(WHERE primary_media_id IS NULL) without_image FROM artworks
          WHERE status<>'archived' GROUP BY work_type ORDER BY count(*) DESC""").fetchall()
        statuses=db.execute('SELECT status,count(*) total,count(primary_media_id) with_image FROM artworks GROUP BY status ORDER BY status').fetchall()
    for row in rows:
        assert row['image_attached']+row['no_image_attached']==row['total']
        assert row['usable_image']+row['missing_usable_image']==row['total']
        row['usable_image_percent']=round(100*row['usable_image']/row['total'],2) if row['total'] else 0
    return {'groups':{x['scope']:x for x in rows},'popular_painters':artists,'by_work_type':types,'by_editorial_status':statuses}

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();started=time.time()
    result={'at':core.now(),'definitions':{
      'universe':'Non-archived artwork records; archived records are listed separately by status.',
      'usable_image':'Matches backend media eligibility: verified media, an allowed rights status, alt text and a storage path. This does not freshly re-audit every historical source or every storage file.',
      'painting':'Existing work_type=painting, not all image attachments or all painted media.',
      'popular':'At least one non-archived linked artist has the existing is_popular selection.',
      'eligible_supported':'Creation scope eligible (through 1970), plus current accepted holding evidence or an existing qualifying curated selection. Unknown dates remain unresolved.',
      'missing':'A coverage gap, not proof that a reusable reproduction exists. Rights, identity or date review may still be required.',
      'artist_counts':'A multi-artist artwork can appear for multiple painters; overall groups count each artwork only once.'},
      'targets':{'local':snapshot('postgres://localhost/artline'),'cloud':snapshot(core.cloud_dsn())},
      'database_writes':False,'elapsed_seconds':round(time.time()-started,2)}
    core.save_new(a.output,result)
    print(json.dumps({t:d['groups'] for t,d in result['targets'].items()},indent=2))

if __name__=='__main__':main()
