import copy
import importlib.util
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('photos', Path(__file__).with_name('research-popular-painting-photos.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
delivery_spec = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('apply-night-prepared-local.py'))
delivery = importlib.util.module_from_spec(delivery_spec)
delivery_spec.loader.exec_module(delivery)


class ReviewedDelivery(unittest.TestCase):
    def test_later_unreviewed_file_is_not_attached(self):
        self.assertFalse(delivery.reviewed_image_allowed({'artwork_id': 'new', 'sha256': 'b' * 64}, {'reviewed': 'a' * 64}))

    def test_different_bytes_cannot_reuse_visual_review(self):
        with self.assertRaises(ValueError):
            delivery.reviewed_image_allowed({'artwork_id': 'reviewed', 'sha256': 'b' * 64}, {'reviewed': 'a' * 64})

    def test_exact_reviewed_file_is_allowed(self):
        self.assertTrue(delivery.reviewed_image_allowed({'artwork_id': 'reviewed', 'sha256': 'a' * 64}, {'reviewed': 'a' * 64}))


class RenderedPhotoRights(unittest.TestCase):
    def test_existing_exact_file_licence_passes_unchanged(self):
        proof = {'uri': 'https://creativecommons.org/licenses/by/4.0/'}
        with patch.object(m.m, 'rendered_rights_uri', return_value=proof):
            self.assertIs(m.rendered_photo_rights(object(), {}, {}, {}), proof)

    def test_unrelated_rights_error_cannot_trigger_an_override(self):
        with patch.object(m.m, 'rendered_rights_uri', side_effect=ValueError('Revision changed')):
            with self.assertRaisesRegex(ValueError, 'Revision changed'):
                m.rendered_photo_rights(object(), {}, {}, {})

    def test_museum_copy_is_not_cleared_as_an_original_photograph(self):
        with patch.object(m.m, 'rendered_rights_uri', side_effect=ValueError('Explicit rendered image licence absent or conflicting')), \
             patch.object(m.m.origin, 'verify', return_value='holding_institution_source'):
            with self.assertRaisesRegex(ValueError, 'independent original photography'):
                m.rendered_photo_rights(object(), {}, {}, {})


class IndependentPhotographSearch(unittest.TestCase):
    def test_skips_native_copy_and_continues_to_independent_photo(self):
        c = {'artwork_id': 'synthetic', 'qid': 'Q1', 'title': 'Painting', 'artist': 'Painter'}
        pages = [dict(pageid=n, title='File:Photo' + str(n), imageinfo=[{}]) for n in (1, 2)]
        responses = [
            {'query': {'search': [{'title': p['title']} for p in pages]}},
            {'query': {'pages': {str(p['pageid']): p for p in pages}}},
            {'entities': {}},
        ]
        def candidate(c, entity, page, structured, rendered, discovery):
            return {'page': page['title'], 'raw': {'independent_photo_discovery': discovery}}
        with tempfile.TemporaryDirectory() as folder, \
             patch.object(m.m, 'entity_match', return_value=None), \
             patch.object(m, 'queries', return_value=['synthetic query']), \
             patch.object(m.m, 'api', side_effect=responses), \
             patch.object(m, 'exact_photo'), \
             patch.object(m.m, 'rendered_rights_uri', return_value=None), \
             patch.object(m, 'candidate_image', side_effect=candidate), \
             patch.object(m, 'verify_original_photograph', side_effect=[ValueError('Native copy'), None]):
            result = m.research(c, {}, object(), Path(folder) / 'run', independent_photographers_only=True)
        self.assertEqual(result['page'], 'File:Photo2')
        self.assertTrue(result['raw']['independent_photo_discovery']['independent_photographers_only'])


class ExactPhotograph(unittest.TestCase):
    def setUp(self):
        self.c = {'qid': 'Q1', 'title': 'Synthetic painting', 'artist': 'Synthetic Artist'}
        self.page = {'ns': 6, 'pageid': 10, 'title': 'File:Synthetic painting.jpg',
                     'revisions': [{'revid': 20, 'slots': {'main': {'*': '{{Artwork\n|wikidata = Q1\n}}'}}}],
                     'imageinfo': [{'width': 1200, 'height': 800}]}

    def test_exact_artwork_template(self):
        m.exact_photo(self.c, self.page, {})

    def test_self_photograph_preserves_explicit_author_category_credit(self):
        self.page['revisions'][0]['slots']['main']['*'] += '\n{{Self-photographed}}\n[[Category:Images by SyntheticPhotographer]]'
        self.assertEqual(m.m.photographic_credits(self.c, self.page), ['SyntheticPhotographer'])

    def test_author_category_without_original_photo_statement_is_insufficient(self):
        self.page['revisions'][0]['slots']['main']['*'] += '\n[[Category:Images by SyntheticPhotographer]]'
        self.assertEqual(m.m.photographic_credits(self.c, self.page), [])

    def test_multiline_photographer_field_preserves_the_named_photographer(self):
        self.page['revisions'][0]['slots']['main']['*'] = '{{Art Photo\n |photographer = {{Creator:Synthetic Artist}}\n[[User:Example|Example Photographer]]\n |source = {{own}}\n}}'
        self.assertEqual(m.m.photographic_credits(self.c, self.page), ['Example Photographer'])

    def test_empty_photographer_field_does_not_capture_another_field(self):
        self.page['revisions'][0]['slots']['main']['*'] = '{{Art Photo\n |photographer =\n |description = [[User:Unrelated|Unrelated person]]\n}}'
        self.assertEqual(m.m.photographic_credits(self.c, self.page), [])

    def test_painter_category_does_not_supply_photographer_credit(self):
        self.page['revisions'][0]['slots']['main']['*'] += '\n{{Own}}\n[[Category:Images by Synthetic Artist]]'
        self.assertEqual(m.m.photographic_credits(self.c, self.page), [])

    def test_analysis_overlay_is_not_a_clean_reproduction(self):
        self.page['title'] = 'File:Schema prospettico of synthetic painting.jpg'
        with self.assertRaisesRegex(ValueError, 'Annotated'):
            m.exact_photo(self.c, self.page, {})

    def test_partial_category_blocks_generic_filename(self):
        self.page['revisions'][0]['slots']['main']['*'] += '\n[[Category:Details of paintings]]'
        with self.assertRaisesRegex(ValueError, 'category'):
            m.exact_photo(self.c, self.page, {})

    def test_empty_structured_data_array_does_not_break_resume(self):
        m.exact_photo(self.c, self.page, {'statements': []})

    def test_nonempty_malformed_structured_data_is_held(self):
        with self.assertRaises(ValueError):
            m.exact_photo(self.c, self.page, {'statements': ['unexpected']})

    def test_artificially_desaturated_reproduction_is_rejected(self):
        self.page['revisions'][0]['slots']['main']['*'] += '\nDigitally desaturated version'
        with self.assertRaises(ValueError):
            m.exact_photo(self.c, self.page, {})

    def test_editor_account_is_not_photographic_source_evidence(self):
        self.page['imageinfo'][0]['extmetadata'] = {'Credit': {'value': 'Digital processing done by myself (<a href="https://commons.wikimedia.org/wiki/User:Synthetic">Synthetic</a>)'}}
        with self.assertRaises(ValueError):
            m.m.origin.verify(self.c, self.page)

    def test_search_match_without_object_identity_is_insufficient(self):
        self.page['revisions'][0]['slots']['main']['*'] = 'Q1 is mentioned in prose only.'
        with self.assertRaises(ValueError):
            m.exact_photo(self.c, self.page, {})

    def test_conflicting_template_is_rejected(self):
        self.page['revisions'][0]['slots']['main']['*'] += '\n{{Artwork|wikidata=Q2}}'
        with self.assertRaises(ValueError):
            m.exact_photo(self.c, self.page, {})

    def test_conflicting_structured_object_is_rejected(self):
        sdc = {'claims': {'P6243': [{'mainsnak': {'snaktype': 'value', 'datavalue': {'value': {'id': 'Q2'}}}}]}}
        with self.assertRaises(ValueError):
            m.exact_photo(self.c, self.page, sdc)

    def test_exact_structured_object_without_template(self):
        self.page['revisions'][0]['slots']['main']['*'] = '{{Information}}'
        sdc = {'claims': {'P6243': [{'mainsnak': {'snaktype': 'value', 'datavalue': {'value': {'id': 'Q1'}}}}]}}
        m.exact_photo(self.c, self.page, sdc)

    def native_fixture(self):
        self.c.update(accession_number='INV123', website_url='https://museum.example',
                      native_identifiers=[{'url': 'https://museum.example/object/987'}])
        self.page['revisions'][0]['slots']['main']['*'] = '{{Artwork|accession number=INV123}}'
        self.page['imageinfo'][0]['extmetadata'] = {
            'Artist': {'value': 'Synthetic Artist'},
            'Credit': {'value': '<a href="https://museum.example/object/987">Museum object</a>'}}

    def test_exact_museum_object_accession_and_creator(self):
        self.native_fixture()
        m.exact_photo(self.c, self.page, {})

    def test_original_photo_description_links_exact_museum_object(self):
        self.native_fixture()
        meta=self.page['imageinfo'][0]['extmetadata']
        meta['Artist']={'value':'Synthetic Photographer'}
        meta['Credit']={'value':'Own work'}
        meta['ImageDescription']={'value':'Painting by Synthetic Artist, <a href="https://museum.example/object/987">Inv. INV123</a>'}
        self.page['revisions'][0]['slots']['main']['*']='{{Information}}'
        m.exact_photo(self.c,self.page,{})

    def test_description_route_does_not_match_another_creator(self):
        self.test_original_photo_description_links_exact_museum_object()
        self.c['artist']='Different Artist'
        with self.assertRaises(ValueError):m.exact_photo(self.c,self.page,{})

    def test_description_route_does_not_match_inventory_prefix(self):
        self.test_original_photo_description_links_exact_museum_object()
        self.c['accession_number']='INV12'
        with self.assertRaises(ValueError):m.exact_photo(self.c,self.page,{})

    def test_description_route_requires_object_link_not_homepage(self):
        self.test_original_photo_description_links_exact_museum_object()
        self.page['imageinfo'][0]['extmetadata']['ImageDescription']['value']='Painting by Synthetic Artist, <a href="https://museum.example">Inv. INV123</a>'
        with self.assertRaises(ValueError):m.exact_photo(self.c,self.page,{})

    def test_native_route_cannot_override_conflicting_object(self):
        self.native_fixture()
        self.page['revisions'][0]['slots']['main']['*'] += '{{Artwork|wikidata=Q2}}'
        with self.assertRaises(ValueError):
            m.exact_photo(self.c, self.page, {})

    def test_native_route_requires_all_independent_fields(self):
        for field in ('accession', 'creator', 'url'):
            self.native_fixture()
            if field == 'accession':
                self.c['accession_number'] = 'INV12'
            elif field == 'creator':
                self.c['artist'] = 'Different Artist'
            else:
                self.c['native_identifiers'][0]['url'] = 'https://museum.example/object/988'
            with self.subTest(field=field), self.assertRaises(ValueError):
                m.exact_photo(self.c, self.page, {})

    def test_object_query_parameters_remain_significant(self):
        self.assertNotEqual(m.source_key('https://museum.example/view?id=1'),
                            m.source_key('https://museum.example/view?id=2'))

    def test_partial_or_small_image_is_rejected(self):
        for change in ('detail', 'small'):
            page = copy.deepcopy(self.page)
            if change == 'detail':
                page['title'] = 'File:Synthetic painting detail.jpg'
            else:
                page['imageinfo'][0]['height'] = 200
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.exact_photo(self.c, page, {})

    def test_explicit_non_public_domain_notice_blocks_generic_pdm(self):
        self.page['imageinfo'][0]['extmetadata'] = {
            'LicenseShortName': {'value': 'Public domain'},
            'LicenseUrl': {'value': 'https://creativecommons.org/publicdomain/mark/1.0/'},
            'Copyrighted': {'value': 'False'}}
        self.page['revisions'][0]['slots']['main']['*'] += '{{Not-PD-US-URAA}}'
        with self.assertRaisesRegex(ValueError, 'rights dispute'):
            m.m.rights_and_identity(self.c, {}, self.page, {})

    def test_exact_identity_does_not_bypass_rights_or_origin_checks(self):
        with patch.object(m.m, 'rights_and_identity', side_effect=ValueError('Unapproved image origin')) as check:
            with self.assertRaises(ValueError):
                m.candidate_image(self.c, {}, self.page, {}, None, {})
            check.assert_called_once()


if __name__ == '__main__':
    unittest.main()
