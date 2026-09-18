import importlib.util
import unittest
from pathlib import Path


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


audit = module('release_content_test', 'audit-release-content.py')
gap = module('release_gap_test', 'deliver-reviewed-release-gap.py')
citations = module('release_citations_test', 'deliver-release-citations.py')


class ReleaseAuditTests(unittest.TestCase):
    def test_keyset_queries_bound_rows_before_foreign_key_enrichment(self):
        meta = {'columns': [('id','uuid','NEVER'),('slug','text','NEVER'),('current_institution_id','uuid','NEVER')], 'primary_key':['id']}
        query = audit.statement('artworks', meta, [('current_institution_id','institutions','id')], 500, '["11111111-1111-1111-1111-111111111111"]')
        self.assertIn('WITH scoped AS MATERIALIZED', query)
        self.assertIn('LIMIT 500', query)
        self.assertIn('FROM scoped t LEFT JOIN', query)
        self.assertNotIn('OFFSET', query)
        self.assertIn('jsonb_populate_record', query)

    def test_composite_cursor_retains_every_key_column(self):
        meta = {'columns':[('snapshot_id','uuid','NEVER'),('source_key','text','NEVER')], 'primary_key':['snapshot_id','source_key']}
        query = audit.statement('research_records', meta, [], 500, '["11111111-1111-1111-1111-111111111111","museum"]')
        self.assertIn('WHERE ("snapshot_id","source_key") >', query)
        self.assertIn('ORDER BY t."snapshot_id",t."source_key"', query)

    def test_fingerprints_do_not_discard_editorial_or_artwork_date_fields(self):
        self.assertFalse({'status','creation_year_start','creation_year_end','date_precision','evidence_note','rights_status'} & set(audit.r.CLOCKS))

    def test_shared_media_identity_does_not_require_a_redundant_index_lookup(self):
        meta = {'columns':[('media_id','uuid','NEVER')], 'primary_key':['media_id']}
        query = audit.statement('media_rights_evidence', meta, [('media_id','media_assets','id')], 500)
        self.assertIn('t."media_id"::text', query)
        self.assertNotIn('JOIN "media_assets"', query)

    def test_gap_delivery_is_only_the_two_named_existing_records(self):
        self.assertEqual(gap.SLUGS, ['wikimedia-artwork-q28026294','wikimedia-artwork-q28038359'])
        self.assertNotIn('artists', gap.ORDER)
        self.assertNotIn('editor_accounts', gap.ORDER)

    def test_citation_delivery_is_evidence_only(self):
        self.assertEqual(citations.FIELDS, {'research_image_policy','geography_primary_authority','official_object_identity'})


if __name__ == '__main__': unittest.main()
