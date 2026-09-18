"""Synthetic boundary checks; no catalogue or live service access."""
import importlib.util
import datetime
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


joconde = load('research-popular-joconde-photos.py')
exact = load('research-popular-exact-file-leads.py')


class CachedArtworkAuthority(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'docs/research/synthetic/entities/Q1.json'
        self.path.parent.mkdir(parents=True)
        self.entity = {'id': 'Q1', 'claims': {}}
        url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q1'
        content = json.dumps({'entities': {'Q1': self.entity}}).encode()
        self.response = self.path.parent.parent / 'wikidata-evidence' / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        self.response.parent.mkdir()
        self.response.write_bytes(content)
        self.capture = {'entity': self.entity, 'receipt': {'url': url, 'bytes': len(content),
            'sha256': hashlib.sha256(content).hexdigest(),
            'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}}

    def verify(self):
        self.path.write_text(json.dumps(self.capture))
        return joconde.verified_cached_authority('Q1', [str(self.path.relative_to(self.root))], self.root)

    def test_intact_recent_capture(self):
        self.assertEqual(self.verify()[0], self.entity)

    def test_old_capture_is_deferred(self):
        self.capture['receipt']['retrieved_at'] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=49)).isoformat()
        with self.assertRaisesRegex(ValueError, 'within 48 hours'):
            self.verify()

    def test_modified_original_response_is_rejected(self):
        self.response.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.verify()

    def test_modified_extraction_is_rejected(self):
        self.capture['entity'] = {'id': 'Q1', 'claims': {'invented': []}}
        with self.assertRaisesRegex(ValueError, 'extraction differs'):
            self.verify()

    def test_unapproved_host_is_rejected(self):
        self.capture['receipt']['url'] = self.capture['receipt']['url'].replace('www.wikidata.org', 'mirror.example')
        with self.assertRaisesRegex(ValueError, 'source or requested identity'):
            self.verify()


class ArtworkWithoutPrimaryImage(unittest.TestCase):
    def setUp(self):
        self.c = {'qid': 'Q1', 'institution_qid': 'Q2', 'title': 'Synthetic painting',
                  'accession_number': None, 'creators': [{'qid': 'Q3'}],
                  'creation_year_start': 1800, 'creation_year_end': 1800}
        def claim(value):
            return [{'mainsnak': {'snaktype': 'value', 'datavalue': {'value': value}}}]
        self.claim = claim
        self.e = {'id': 'Q1', 'labels': {'en': {'value': 'Synthetic painting'}},
                  'claims': {'P31': claim({'id': 'Q3305213'}), 'P195': claim({'id': 'Q2'}),
                             'P170': claim({'id': 'Q3'}),
                             'P571': claim({'time': '+1800-00-00T00:00:00Z', 'precision': 9})}}

    def test_missing_image_allows_independent_discovery(self):
        self.assertIsNone(exact.m.entity_match(self.c, self.e, require_primary_image=False))

    def test_multiple_images_do_not_choose_an_arbitrary_primary(self):
        self.e['claims']['P18'] = self.claim('Synthetic A.jpg') + self.claim('Synthetic B.jpg')
        self.assertIsNone(exact.m.entity_match(self.c, self.e, require_primary_image=False))

    def test_without_primary_image_conflicting_holding_still_fails(self):
        self.e['claims']['P195'] = self.claim({'id': 'Q4'})
        with self.assertRaisesRegex(ValueError, 'Holding institution'):
            exact.m.entity_match(self.c, self.e, require_primary_image=False)

    def test_without_primary_image_conflicting_creator_still_fails(self):
        self.e['claims']['P170'] = self.claim({'id': 'Q4'})
        with self.assertRaisesRegex(ValueError, 'Creator authority'):
            exact.m.entity_match(self.c, self.e, require_primary_image=False)


class NationalCatalogueIdentity(unittest.TestCase):
    def entity(self, value, rank='normal'):
        return {'claims': {'P347': [{'rank': rank, 'mainsnak': {
            'snaktype': 'value', 'datavalue': {'value': value}}}]}}

    def test_nearby_catalogue_number_is_not_the_same_object(self):
        with self.assertRaises(ValueError):
            joconde.verify_native_source({'external_id': 'SYNTHETIC001'}, self.entity('SYNTHETIC0010'))

    def test_deprecated_identifier_is_not_current_authority(self):
        with self.assertRaises(ValueError):
            joconde.verify_native_source({'external_id': 'SYNTHETIC001'}, self.entity('SYNTHETIC001', 'deprecated'))

    def test_exact_identifier_does_not_bypass_creator_or_holding_checks(self):
        with patch.object(joconde.photo.m, 'entity_match', side_effect=ValueError('Creator conflict')):
            with self.assertRaisesRegex(ValueError, 'Creator conflict'):
                joconde.verify_native_source({'external_id': 'SYNTHETIC001'}, self.entity('SYNTHETIC001'))


class OriginalPhotographIdentity(unittest.TestCase):
    def page(self, source, author='Synthetic photographer'):
        return {'imageinfo': [{'extmetadata': {
            'Credit': {'value': source}, 'Artist': {'value': author}}}]}

    def test_identified_original_photograph(self):
        exact.verify_photo_origin({'artist': 'Synthetic painter'}, self.page('Own work'))

    def test_book_scan_is_not_an_original_photograph(self):
        with self.assertRaises(ValueError):
            exact.verify_photo_origin({'artist': 'Synthetic painter'}, self.page('Own work; scanned from a book'))

    def test_uploader_credit_does_not_clear_the_original(self):
        with self.assertRaises(ValueError):
            exact.verify_photo_origin({'artist': 'Synthetic painter'}, self.page('Original uploader User:Example'))

    def test_painter_name_does_not_credit_the_photograph(self):
        with self.assertRaisesRegex(ValueError, 'photographer credit'):
            exact.verify_photo_origin({'artist': 'Synthetic painter'}, self.page('Own work', 'Synthetic painter'))

    def test_retoucher_user_link_is_not_original_photographic_provenance(self):
        source = 'Retouched picture; modifications made by <a href="https://commons.wikimedia.org/wiki/User:Editor">Editor</a>'
        with self.assertRaises(ValueError):
            exact.verify_photo_origin({'artist': 'Synthetic painter'}, self.page(source))

    def test_own_work_does_not_override_a_retouching_source(self):
        with self.assertRaises(ValueError):
            exact.verify_photo_origin({'artist': 'Synthetic painter'}, self.page('Own work; colours adjusted from an earlier photo'))


if __name__ == '__main__':
    unittest.main()
