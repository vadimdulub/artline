#!/usr/bin/env python3
"""Read-only Austrian holding-museum inventory, retaining missing country mappings."""
import argparse,importlib.util,json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
spec=importlib.util.spec_from_file_location('core',Path(__file__).with_name('enrich-artwork-images.py'));core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)

def snapshot(dsn,qids):
    with psycopg.connect(dsn,autocommit=True,row_factory=dict_row,options='-c default_transaction_read_only=on -c statement_timeout=90000') as db:
        institutions=db.execute("""SELECT i.id::text,i.slug,i.name,i.wikidata_id,i.website_url,i.place_id::text,p.name place_name,p.country_code,
          ARRAY(SELECT DISTINCT vp.country_code FROM institution_venues v JOIN places vp ON vp.id=v.place_id WHERE v.institution_id=i.id) venue_countries
          FROM institutions i LEFT JOIN places p ON p.id=i.place_id
          WHERE i.status<>'archived' AND (i.wikidata_id=ANY(%s) OR i.slug=ANY(%s)) ORDER BY i.name""",(qids,['belvedere','kunsthistorisches-museum','academy-fine-arts-vienna-paintings-gallery'])).fetchall()
        artworks=db.execute("""WITH selected AS MATERIALIZED (
          SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND status<>'archived'
          UNION SELECT a.id FROM artwork_location_assertions l JOIN artworks a ON a.id=l.artwork_id
          WHERE l.institution_id=ANY(%s::uuid[]) AND l.claim_type='holding' AND l.review_state='accepted' AND l.superseded_by IS NULL AND a.status<>'archived')
          SELECT a.id::text,a.slug,a.title,a.alternate_title,a.accession_number,a.current_institution_id::text,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.status,a.revision,a.primary_media_id::text,
          artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,
          coalesce(m.verified_at IS NOT NULL AND m.rights_status IN ('public_domain','cc0','cc_by','cc_by_sa','licensed') AND nullif(trim(m.alt_text),'') IS NOT NULL AND nullif(m.storage_path,'') IS NOT NULL,false) usable_image,
          ARRAY(SELECT e.external_id FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata') qids,
          ARRAY(SELECT p.display_name FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id) artists
          FROM selected s JOIN artworks a ON a.id=s.id LEFT JOIN media_assets m ON m.id=a.primary_media_id ORDER BY a.id""",([i['id'] for i in institutions],)*2).fetchall()
    for i in institutions:
        works=[a for a in artworks if a['current_institution_id']==i['id']];i['artworks']=len(works);i['paintings']=sum(a['work_type']=='painting' for a in works);i['usable_images']=sum(a['usable_image'] for a in works);i['painting_image_gaps']=sum(a['work_type']=='painting' and not a['usable_image'] for a in works)
    return {'institutions':institutions,'artworks':artworks,'totals':{'institutions':len(institutions),'artworks':len(artworks),'paintings':sum(a['work_type']=='painting' for a in artworks),'usable_images':sum(a['usable_image'] for a in artworks),'missing_images':sum(not a['usable_image'] for a in artworks),'institutions_without_country':sum(not i['country_code'] and 'AT' not in i['venue_countries'] for i in institutions)}}

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();qids=list(json.loads((a.run/'wikimedia/museum-entities.json').read_text()));out={'at':core.now(),'read_only':True,'scope':'Exact Austrian museum authorities plus existing verified Vienna gallery entries; institutional geography, not artist nationality. Current institutions and accepted holding assertions included.','targets':{}}
    for target,dsn in [('local','postgres://localhost/artline'),('cloud',core.cloud_dsn())]:out['targets'][target]=snapshot(dsn,qids);print(target,out['targets'][target]['totals'],flush=True)
    core.save_new(a.output,out)
if __name__=='__main__':main()
