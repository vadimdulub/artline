#!/usr/bin/env python3
"""Immutable read-only baseline of Japanese-associated catalogue coverage."""
import collections, json
from pathlib import Path
import psycopg
from psycopg.rows import dict_row

RUN=Path(__file__).resolve().parent
def save(name,value):
    path=RUN/name
    if path.exists():
        if json.loads(path.read_text())!=value: raise ValueError(f'immutable evidence differs: {path}')
        return
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str)+'\n')

def main():
    with psycopg.connect('postgresql://localhost/artline',row_factory=dict_row,
      options='-c default_transaction_read_only=on -c statement_timeout=120000') as db:
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        meta=db.execute("""SELECT current_database() database,current_setting('transaction_read_only') read_only,now() snapshot_at,
          (SELECT count(*) FROM artists WHERE status<>'archived') active_artists,
          (SELECT count(*) FROM artworks WHERE status<>'archived') active_artworks""").fetchone()
        artists=db.execute("""SELECT r.id::text,r.slug,r.display_name,r.status,r.entity_type,r.birth_year,r.death_year,r.timeline_basis,
          coalesce((SELECT jsonb_agg(to_jsonb(c)-'artist_id') FROM artist_countries c WHERE c.artist_id=r.id),'[]') countries,
          coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'id',e.external_id)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=r.id),'[]') identifiers,
          count(DISTINCT a.id) artworks,count(DISTINCT a.id) FILTER(WHERE a.work_type='painting') paintings_all_dates,
          count(DISTINCT a.id) FILTER(WHERE a.work_type='painting' AND a.creation_year_end<=1970) paintings_through_1970,
          count(DISTINCT a.id) FILTER(WHERE a.work_type='painting' AND a.creation_year_end<=1970 AND a.primary_media_id IS NOT NULL) paintings_through_1970_with_media,
          count(DISTINCT a.id) FILTER(WHERE a.creation_year_end IS NULL OR a.creation_year_start<=1970 AND a.creation_year_end>1970) date_review
          FROM artists r LEFT JOIN artwork_artists aa ON aa.artist_id=r.id LEFT JOIN artworks a ON a.id=aa.artwork_id AND a.status<>'archived'
          WHERE r.status<>'archived' AND EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=r.id AND c.country_code='JP')
          GROUP BY r.id ORDER BY r.display_name""").fetchall()
        institutions=db.execute("""SELECT i.id::text,i.slug,i.name,i.website_url,i.wikidata_id,i.status,p.name city,p.country_code,
          coalesce((SELECT jsonb_agg(DISTINCT q.country_code) FROM institution_venues v JOIN places q ON q.id=v.place_id WHERE v.institution_id=i.id),'[]') venue_countries
          FROM institutions i LEFT JOIN places p ON p.id=i.place_id ORDER BY i.name""").fetchall()
        jpids=[i['id'] for i in institutions if i['country_code']=='JP' or 'JP' in i['venue_countries']]
        works=db.execute("""WITH scope AS (
          SELECT aa.artwork_id id FROM artist_countries c JOIN artwork_artists aa ON aa.artist_id=c.artist_id WHERE c.country_code='JP'
          UNION SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])
          UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=ANY(%s::uuid[]) AND claim_type='holding' AND review_state IN ('accepted','review') AND superseded_by IS NULL)
          SELECT a.id::text,a.slug,a.title,a.date_display,a.creation_year_start,a.creation_year_end,a.work_type,a.status,a.accession_number,
          a.current_institution_id::text,a.primary_media_id::text,a.unlinked_creator_label FROM scope s JOIN artworks a ON a.id=s.id WHERE a.status<>'archived' ORDER BY a.id""",(jpids,jpids)).fetchall()
    associated={a['id'] for a in works}
    paintings=[a for a in works if a['work_type']=='painting' and a['creation_year_end'] is not None and a['creation_year_end']<=1970]
    summary={'snapshot':meta,'countries':{'JP':{'geocoded_institutions':len(jpids),'associated_artist_records':len(artists),
      'artist_records_without_artworks':sum(a['artworks']==0 for a in artists),'artist_records_without_dated_paintings':sum(a['paintings_through_1970']==0 for a in artists),
      'scoped_active_artworks':len(associated),'scoped_paintings_through_1970':len(paintings),
      'scoped_paintings_through_1970_with_media':sum(a['primary_media_id'] is not None for a in paintings),
      'scoped_paintings_through_1970_without_media':sum(a['primary_media_id'] is None for a in paintings)}},
      'limitations':['Existing country relationships are retained as recorded and are not nationality findings.','Japanese institutional geography can be incomplete.','Holding and current-display claims remain separate.','Numeric dates are coverage signals, not independent source validation.'],
      'database_writes':0,'image_downloads':0}
    save('local-snapshot.json',meta);save('artist-coverage.json',artists);save('all-institutions.json',institutions);save('scoped-artworks.json',works);save('audit-summary.json',summary)
    print(json.dumps(summary['countries']['JP'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
