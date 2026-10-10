#!/usr/bin/env python3
"""Read-only cross-catalogue museum coverage audit, with no fixtures."""
import argparse,collections,importlib.util,json,time
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-artwork-locations-20261004.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);r.PORT=55445
r.RUN=r.ROOT/'docs/research/museum-gaps-20261005'

def baseline(target):
 with r.connect(target)as db:
  stats=db.execute('''SELECT count(*) works,count(primary_media_id) with_media,count(current_institution_id) with_museum,
   count(*) FILTER(WHERE status='review') review,count(*)FILTER(WHERE status='published') published,
   count(*)FILTER(WHERE creation_year_start>creation_year_end) reversed_dates
   FROM artworks WHERE status<>'archived' ''').fetchone()
  museums=db.execute('''SELECT i.id::text id,i.slug,i.name,i.status,count(*) works,
   count(*)FILTER(WHERE m.storage_path ~ '^/assets/[a-zA-Z0-9/_-]+\\.(jpg|jpeg|png|webp|avif)$') images,
   count(*)FILTER(WHERE a.primary_media_id IS NOT NULL AND (m.storage_path IS NULL OR m.storage_path !~ '^/assets/[a-zA-Z0-9/_-]+\\.(jpg|jpeg|png|webp|avif)$')) invalid_image_paths,
   count(*)FILTER(WHERE m.byte_size>100000) oversized_images,
   count(*)FILTER(WHERE a.creation_year_start IS NULL OR a.creation_year_end IS NULL) unknown_dates,
   count(*)FILTER(WHERE a.creation_year_start<=1970 AND a.creation_year_end<=1970) eligible_dates
   FROM institutions i JOIN artworks a ON a.current_institution_id=i.id AND a.status<>'archived'
   LEFT JOIN media_assets m ON m.id=a.primary_media_id WHERE i.status<>'archived'
   GROUP BY i.id ORDER BY count(*) DESC,i.slug''').fetchall()
  lead_counts=db.execute('''SELECT c.evidence_note::jsonb->>'reported_location' location,count(DISTINCT a.id) illustrated_works
    FROM citations c JOIN artworks a ON a.id=c.entity_id WHERE c.entity_type='artwork'
    AND c.field_name='museum_location_lead_review' AND a.primary_media_id IS NOT NULL
    AND a.current_institution_id IS NULL AND a.status<>'archived' GROUP BY 1 ORDER BY 2 DESC,1 LIMIT 100''').fetchall()
  media=db.execute('''SELECT count(*) attached,count(*)FILTER(WHERE m.byte_size>100000) oversized,
    count(*)FILTER(WHERE m.rights_status IN ('unknown','restricted')) rights_unclear,
    count(*)FILTER(WHERE m.checksum_sha256 IS NULL) missing_checksums
    FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id WHERE a.status<>'archived' ''').fetchone()
 r.save_gz(r.RUN/(target+'-baseline.json.gz'),{'captured_at':r.now(),'stats':stats,'media':media,'museums':museums,'pending_image_leads':lead_counts})
 print(json.dumps({'target':target,**stats,'museums':len(museums),'top20':[{'name':m['name'],'slug':m['slug'],'works':m['works'],'images':m['images']}for m in museums[:20]],'top10_image_leads':lead_counts[:10]},ensure_ascii=False),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('target',choices=['local','production']);args=p.parse_args();baseline(args.target)
