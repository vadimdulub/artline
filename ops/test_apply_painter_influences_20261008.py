"""Pure import-policy checks; no database or fixtures are created."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('apply-painter-influences-20261008.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ImportPolicyTests(unittest.TestCase):
    def test_unverified_assertions_do_not_become_documented_consensus(self):
        for provider in ('WikiArt', 'Wikipedia', 'Wikidata'):
            level, confidence, note = m.grade([dict(provider=provider)])
            self.assertEqual(level, 'editorial_inference')
            self.assertNotEqual(confidence, 'high')
            self.assertIn('verif', note)

    def test_single_scholarly_interpretation_is_not_consensus(self):
        level, confidence, _ = m.grade([dict(provider='Scholarly publication', evidence_level='scholarly_interpretation')])
        self.assertEqual((level, confidence), ('editorial_inference', 'medium'))

    def test_read_documentation_retains_stronger_evidence(self):
        grade = m.grade([dict(provider='Wikidata'), dict(provider='Museum', evidence_level='documented')])
        self.assertEqual(grade[:2], ('documented', 'high'))

    def test_conflicting_authorities_remain_visible(self):
        edge = dict(source_authority_url='https://www.wikidata.org/wiki/Q1',
            evidence=[dict(source_wikidata_id='Q2')])
        self.assertEqual(m.source_qids(edge), {'Q1', 'Q2'})

    def test_real_provider_names_and_source_types(self):
        for provider, url, expected in [
            ('WikiArt', 'https://www.wikiart.org/en/test', 'WikiArt'),
            ('Wikipedia', 'https://en.wikipedia.org/w/index.php?oldid=123', 'Wikipedia'),
            ('Museum', 'https://www.nationalgallery.org.uk/artists/test', 'National Gallery'),
            ('Scholarly publication', 'https://www.icon-art.info/book_contents.php?book_id=115', 'Alpatov'),
        ]:
            source = m.source_definition(dict(provider=provider, source_url=url))
            self.assertIn(expected, source['name'])
            self.assertEqual(source['id'], m.source_definition(dict(provider=provider, source_url=url))['id'])

    def test_citations_preserve_revision_date_qualifications_and_identity_direction(self):
        evidence = dict(provider='Wikipedia', source_url='https://en.wikipedia.org/w/index.php?oldid=123',
            reviewed_at='2026-10-08', paragraph_sha256='abc', note='Influence specifically concerns calligraphy.',
            source_artist_id='research-source', target_artist_id='research-target')
        claim = dict(id=m.uid('test-claim'), relationship_type='influenced')
        source = m.source_definition(evidence)
        citations = m.citations_for(claim, [evidence], 'pinned-hash', '2026-10-09T00:00:00+00:00',
            {source['slug']: source['id']}, dict(source_artist_id='production-source', target_artist_id='production-target'))
        self.assertEqual(len(citations), 1)
        c = citations[0]
        self.assertEqual(c['source_url'], evidence['source_url'])
        self.assertEqual(c['retrieved_at'], '2026-10-08T00:00:00+00:00')
        self.assertEqual(c['page_or_locator'], 'paragraph abc')
        provenance = json.loads(c['evidence_note'])
        self.assertEqual(provenance['evidence'], [evidence])
        self.assertEqual(provenance['production_identity_context']['target_artist_id'], 'production-target')
        self.assertIn('creativecommons', provenance['license_url'])

    def test_same_page_evidence_merges_without_losing_assertions(self):
        evidence = [dict(provider='Wikidata', source_url='https://www.wikidata.org/wiki/Q1#P737',
            retrieved_at='2026-10-08T01:00:00+00:00', statement_url='http://www.wikidata.org/entity/statement/' + str(i)) for i in (1, 2)]
        claim = dict(id=m.uid('other-test-claim'), relationship_type='influenced')
        citations = m.citations_for(claim, evidence, 'hash', 'later', {'wikidata': 'source-id'}, {})
        self.assertEqual(len(citations), 1)
        self.assertEqual(len(json.loads(citations[0]['evidence_note'])['evidence']), 2)
        self.assertIn('/1', citations[0]['page_or_locator'])
        self.assertIn('/2', citations[0]['page_or_locator'])


if __name__ == '__main__':
    unittest.main()
