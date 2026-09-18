#!/usr/bin/env python3
"""Read-only final parity, source identity and export audit for selected Austrian works."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('austria_import', Path(__file__).with_name('import-austrian-catalogue.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def rows(db, ids):
    return db.execute("""SELECT a.id::text,a.slug,a.title,a.alternate_title,a.date_display,
      a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.medium_text,a.dimensions_text,
      a.accession_number,a.status,a.published_at,a.research_candidate,
      i.slug museum_slug,i.name museum,i.wikidata_id museum_authority_id,i.website_url museum_url,
      p.country_code museum_country,
      artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) date_scope,
      artline_has_selection_evidence(a.id) selection_evidence,
      EXISTS(SELECT 1 FROM artwork_location_assertions l WHERE l.artwork_id=a.id AND
        l.institution_id=i.id AND l.claim_type='holding' AND l.review_state='accepted' AND l.superseded_by IS NULL) verified_holding,
      coalesce((SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'slug',ar.slug,
        'birth_year',ar.birth_year,'death_year',ar.death_year,'entity_type',ar.entity_type,
        'attribution_role',aa.attribution_role,'countries',(SELECT coalesce(jsonb_agg(jsonb_build_object(
          'code',ac.country_code,'relationship_type',ac.relationship_type) ORDER BY ac.country_code,ac.relationship_type),'[]'::jsonb)
          FROM artist_countries ac WHERE ac.artist_id=ar.id)) ORDER BY ar.slug,aa.attribution_role)
        FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]'::jsonb) artists,
      coalesce((SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'source_object_id',e.external_id,
        'source_record_url',e.canonical_url) ORDER BY e.scheme,e.external_id)
        FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]'::jsonb) source_identifiers,
      coalesce((SELECT jsonb_agg(jsonb_build_object('field',c.field_name,'source_record_id',c.source_record_id,
        'source_url',c.source_url,'retrieved_at',c.retrieved_at,'source_name',s.name,'terms_url',s.terms_url)
        ORDER BY c.field_name,c.source_url,c.source_record_id,c.retrieved_at)
        FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]'::jsonb) citations,
      CASE WHEN m.verified_at IS NOT NULL AND m.storage_path IS NOT NULL THEN jsonb_build_object(
        'storage_path',m.storage_path,'source_name',m.provider_name,'image_source_url',m.source_page_url,
        'license_url',m.license_url,'license_label',m.license_label,'creator_credit',m.creator_credit,
        'attribution_text',m.attribution_text,'sha256',m.checksum_sha256,'bytes',m.byte_size,
        'rights_verified_at',m.verified_at,'retrieved_at',m.retrieved_at) END image
      FROM artworks a JOIN institutions i ON i.id=a.current_institution_id
      LEFT JOIN places p ON p.id=i.place_id LEFT JOIN media_assets m ON m.id=a.primary_media_id
      WHERE a.id=ANY(%s::uuid[]) ORDER BY a.slug""", (ids,)).fetchall()


def duplicates(db, ids):
    identities = db.execute("""WITH keys AS MATERIALIZED (SELECT DISTINCT scheme,external_id FROM external_identifiers
      WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]))
      SELECT e.scheme,e.external_id,array_agg(DISTINCT e.entity_id::text) artwork_ids
      FROM keys k JOIN external_identifiers e ON e.entity_type='artwork' AND e.scheme=k.scheme AND e.external_id=k.external_id
      GROUP BY e.scheme,e.external_id HAVING count(DISTINCT e.entity_id)>1""", (ids,)).fetchall()
    accessions = db.execute("""WITH selected AS MATERIALIZED (SELECT id,current_institution_id,
      lower(regexp_replace(accession_number,'[^[:alnum:]]','','g')) accession FROM artworks
      WHERE id=ANY(%s::uuid[]) AND nullif(trim(accession_number),'') IS NOT NULL)
      SELECT DISTINCT s.id::text selected_id,b.id::text possible_duplicate_id,b.title,b.accession_number
      FROM selected s JOIN artworks b ON b.current_institution_id=s.current_institution_id AND b.id<>s.id
      AND b.status<>'archived' AND lower(regexp_replace(b.accession_number,'[^[:alnum:]]','','g'))=s.accession
      WHERE s.accession<>''""", (ids,)).fetchall()
    titles = db.execute("""WITH selected AS MATERIALIZED (SELECT a.id,a.current_institution_id,a.normalized_title,
      a.creation_year_start,a.creation_year_end,aa.artist_id FROM artworks a
      JOIN artwork_artists aa ON aa.artwork_id=a.id WHERE a.id=ANY(%s::uuid[]))
      SELECT DISTINCT s.id::text selected_id,b.id::text possible_duplicate_id,b.title,b.accession_number
      FROM selected s JOIN artworks b ON b.current_institution_id=s.current_institution_id AND b.id<>s.id
      AND b.normalized_title=s.normalized_title AND b.status<>'archived'
      AND b.creation_year_start IS NOT DISTINCT FROM s.creation_year_start
      AND b.creation_year_end IS NOT DISTINCT FROM s.creation_year_end
      JOIN artwork_artists ba ON ba.artwork_id=b.id AND ba.artist_id=s.artist_id""", (ids,)).fetchall()
    return {'source_identity_collisions': identities, 'normalized_accession_candidates': accessions,
            'same_artist_title_date_museum_candidates': titles}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True, type=Path)
    args = parser.parse_args()
    run = args.run
    main_plan = a.load(run / 'metadata-plan.json')
    native = a.load(run / 'belvedere-highlight-plan.json')
    results, snapshots = {}, {}
    for target in ('local', 'cloud'):
        states = main_plan['targets'][target]['records'] + native['targets'][target]
        ids = sorted({s['artwork_id'] for s in states if s['action'] == 'new'})
        with a.connect(target, ro=True) as db:
            # jsonb timestamp text otherwise follows each server's timezone.
            db.execute("SET TIME ZONE 'UTC'")
            works = rows(db, ids)
            dup = duplicates(db, ids)
        assert len(works) == len(ids) == 725, 'Missing newly imported artwork'
        for work in works:
            assert work['status'] == 'review' and work['published_at'] is None
            assert work['museum_country'] == 'AT' and work['verified_holding'] and work['selection_evidence']
            assert work['work_type'] == 'painting' and work['artists'] and work['source_identifiers'] and work['citations']
            assert work['creation_year_end'] is None or work['creation_year_end'] <= 1970
        assert not dup['source_identity_collisions'], 'Conflicting source object identity'
        snapshots[target] = works
        results[target] = {'new_artworks_verified': len(works), 'new_artists': sum(p['new'] for p in main_plan['targets'][target]['artists'].values()),
                           'date_scope': dict(collections.Counter(w['date_scope'] for w in works)),
                           'image_count_among_new_artworks': sum(w['image'] is not None for w in works),
                           'duplicate_review': dup}
        print(target, len(works), 'records verified;', {k: len(v) for k, v in dup.items()}, flush=True)
    # UUIDs are not part of semantic parity. The same native source IDs and public
    # provenance must describe both targets, including artist cultural affiliations.
    semantic = lambda work: {k: v for k, v in work.items() if k != 'id'}
    differences = [left['slug'] for left, right in zip(snapshots['local'], snapshots['cloud'])
                   if semantic(left) != semantic(right)]
    audit = {'at': a.core.now(), 'read_only': True, 'targets': results, 'semantic_differences': differences,
             'limitations': 'Duplicate candidates require physical-object review; this audit neither merges nor deletes works. '
                            'It checks selected imports against the catalogue, not every historical catalogue pair.'}
    a.core.save_new(run / 'final-metadata-audit.json', audit)
    assert not differences, 'Local / production metadata differs'
    with (run / 'new-artworks.jsonl').open('x') as output:
        for row in snapshots['cloud']:
            row['hasPicture'] = row['image'] is not None
            output.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')
    images = {}
    for line in (run / 'local-attachments.jsonl').read_text().splitlines():
        record = json.loads(line)
        if record['outcome'] in ('attached', 'already_attached'):
            images[record['artwork_id']] = a.load(Path(record['receipt']))
        elif record['outcome'] == 'withdrawn':
            images.pop(record['artwork_id'], None)
    assert len(images) == 49
    with (run / 'approved-image-manifest.jsonl').open('x') as output:
        for key, record in sorted(images.items()):
            fields = ('title','artist','museum','country_code','source_name','source_object_id','source_record_url',
                      'source_image_url','image_license','image_license_url','rights_statement','creator_credit',
                      'attribution_text','creation_date','rights_verified_at','downloaded_at','path','sha256','bytes','popular')
            row = {field: record.get(field) for field in fields}
            row.update(artwork_id=key, target_ids=record['target_ids'], verified_local=True, verified_production=True,
                       verified_google_storage=True, verified_public_bytes=True)
            output.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')
    print('Saved 725 source-backed artwork rows and 49 approved-image manifest rows.', flush=True)


if __name__ == '__main__':
    main()
