"""Offline identity and no-overwrite safeguards; never opens a catalogue connection."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('source-index-native-20261009.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m


def sample():
    return dict(state='captured',artwork_id='work',provider='chicago',target=dict(native_ids=['12'],artwork=dict(
        id='work',title='The Harbour',alternate_title=None,accession_number='1920.12',primary_media_id=None,
        medium_text=None,dimensions_text=None,creation_year_start=1885,creation_year_end=1885,date_precision='exact',date_display='1885')),
        facts=dict(native_id='12',accession='1920.12',titles=['The Harbour'],dates=dict(start=1885,end=1885,display='1885'),
        medium='Oil on canvas',dimensions='Framed: 120 x 90 cm; Canvas: 100 x 70 cm',page='https://www.artic.edu/artworks/12',
        qualified_creators=[],image='https://www.artic.edu/iiif/2/abc/full/843,/0/default.jpg',image_open=True))


class IdentityTests(unittest.TestCase):
    def test_tracking_removed_identity_queries_preserved(self):
        self.assertEqual(m.canonical_url('https://museum.test/object?id=12&utm_source=x&version=2#folio3'),'https://museum.test/object?id=12&version=2#folio3')

    def test_percent_encoded_and_repeated_query_identity_preserved(self):
        self.assertEqual(m.canonical_url('https://museum.test/q?ids=a%2Bb&ids=c+d'),'https://museum.test/q?ids=a%2Bb&ids=c+d')

    def test_native_fragments_not_merged(self):
        self.assertNotEqual(m.canonical_url('https://museum.test/album#1'),m.canonical_url('https://museum.test/album#2'))

    def test_invalid_and_credential_urls_rejected(self):
        for v in ['file:///etc/passwd','javascript:alert(1)','https://a:b@museum.test/x','https://museum.test:wrong/x',None]:
            self.assertIsNone(m.canonical_url(v))

    def test_wikidata_and_internal_mirrors_excluded(self):
        for u in ['https://query.wikidata.org/sparql?a=1','https://www.wikidata.org/wiki/Q1','https://en.wikipedia.org/wiki/A','https://storage.googleapis.com/artline-508319-images/research/a.csv']:
            self.assertTrue(m.excluded(u))
        self.assertFalse(m.excluded('https://commons.wikimedia.org/wiki/File:A.jpg'))

    def test_official_dataset_is_not_an_object(self):
        self.assertEqual(m.resource_kind('https://raw.githubusercontent.com/NationalGalleryOfArt/opendata/main/data/objects.csv','artwork'),'reference_dataset')

    def test_exact_identity_fills_only_empty_fields(self):
        d=n.assess(sample())
        self.assertEqual(d['decision'],'exact_identity')
        self.assertEqual(set(d['field_updates']),{'medium_text','dimensions_text'})
        self.assertTrue(d['image_candidate'])

    def test_populated_fields_not_overwritten(self):
        r=sample();r['target']['artwork'].update(medium_text='Old supplied medium',dimensions_text='Earlier measurement')
        self.assertEqual(n.assess(r)['field_updates'],{})

    def test_matching_title_cannot_override_inventory_conflict(self):
        r=sample();r['facts']['accession']='1920.13'
        d=n.assess(r);self.assertEqual(d['decision'],'hold');self.assertEqual(d['field_updates'],{});self.assertFalse(d['image_candidate'])

    def test_same_inventory_different_title_requires_review(self):
        r=sample();r['facts']['titles']=['Study for the Harbour']
        self.assertEqual(n.assess(r)['decision'],'hold')

    def test_existing_image_preserved(self):
        r=sample();r['target']['artwork']['primary_media_id']='existing'
        self.assertFalse(n.assess(r)['image_candidate'])

    def test_qualified_creator_requires_review(self):
        r=sample();r['facts']['qualified_creators']=[dict(role='after')]
        self.assertEqual(n.assess(r)['decision'],'hold')

    def test_rights_not_inferred_from_age(self):
        r=sample();r['facts']['image_open']=False
        self.assertFalse(n.assess(r)['image_candidate'])

    def test_unknown_source_date_remains_unknown(self):
        r=sample();r['facts']['dates'].update(start=None,end=None)
        d=n.assess(r);self.assertFalse(d['image_candidate']);self.assertNotIn('creation_year_start',d['field_updates'])

    def test_source_date_crossing_cutoff_held(self):
        r=sample();r['facts']['dates'].update(start=1960,end=1980)
        self.assertFalse(n.assess(r)['image_candidate'])

    def test_source_and_catalogue_date_conflict_held(self):
        r=sample();r['facts']['dates'].update(start=1886,end=1886)
        self.assertFalse(n.assess(r)['image_candidate'])

    def test_qualified_catalogue_date_does_not_become_exact(self):
        r=sample();r['target']['artwork']['date_precision']='after'
        d=n.assess(r);self.assertFalse(d['image_candidate']);self.assertNotIn('date_precision',d['field_updates'])

    def test_input_is_not_mutated(self):
        r=sample();before=copy.deepcopy(r);n.assess(r);self.assertEqual(r,before)


if __name__=='__main__':unittest.main()
