"""Offline Barnes policy checks against preserved public source captures."""
import copy
import gzip
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('barnes',Path(__file__).with_name('museum-expansion-barnes-20261006.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


def captured(path):
    key=hashlib.sha256((b.BASE+path).encode()).hexdigest()
    return gzip.decompress((b.n.RUN/'barnes/captures'/(key+'.body.gz')).read_bytes())


class BarnesPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api=json.loads(captured('/api/objects/4702'))
        cls.native=b.native_fields(captured('/objects/4702'))

    def test_explicit_object_date_survives_missing_api_end(self):
        self.assertEqual(self.api['endDate'],'')
        facts,reason=b.facts(self.api,self.native)
        self.assertIsNone(reason)
        self.assertEqual((facts['first'],facts['last'],facts['date_precision']),(1888,1890,'range'))
        self.assertEqual(facts['date_display'],'1888–1890')

    def test_source_circa_bounds_are_preserved_without_invented_tolerance(self):
        api=json.loads(captured('/api/objects/3104'))
        self.assertEqual(b.dates(api),(1915,1926,'circa_range'))
        self.assertEqual(api['displayDate'],'c. 1920–1921')

    def test_missing_creation_not_replaced_with_provenance_or_lifespan(self):
        api=dict(self.api,displayDate='',birthDate='1839',deathDate='1906')
        self.assertIsNone(b.dates(api))
        self.assertIn('1913',api['publishedProvenance'])

    def test_conflicting_bounds_and_cutoff_crossing_held(self):
        for changes in [dict(beginDate='1900'),dict(endDate='1887'),dict(displayDate='1960–1980'),dict(displayDate='c. 1970',beginDate='1965'),dict(displayDate='c. 1968',beginDate='1963',endDate='1973')]:
            with self.subTest(changes=changes):self.assertIsNone(b.dates(dict(self.api,**changes)))

    def test_collection_membership_and_native_identity_required(self):
        native=dict(self.native,canonical=self.native['canonical'].replace('/4702/','/4703/'))
        self.assertEqual(b.facts(self.api,native)[1],'native_object_identity_conflict')
        native=dict(self.native,description='Another museum collection')
        self.assertEqual(b.facts(self.api,native)[1],'native_collection_membership_not_confirmed')
        self.assertEqual(b.facts(dict(self.api,creditLine='On loan from a private collection'),self.native)[1],'credit_line_ownership_requires_review')

    def test_literal_qualified_creator_and_source_review_flag_preserved(self):
        api=dict(self.api,artistPrefix='Attributed to')
        facts,reason=b.facts(api,self.native)
        self.assertIsNone(reason);self.assertEqual(facts['creator_label'],'Attributed to Paul Cézanne')
        self.assertEqual(api['curatorialApproval'],'false')
        self.assertNotIn('on_view',facts);self.assertNotIn('published_at',facts)

    def test_translated_titles_and_source_variants_do_not_hide_identity(self):
        self.assertTrue(b.title_keys('House and Trees')&b.title_keys(self.api['title']))
        self.assertEqual(b.source_id(b.BASE+'/api/objects/4702'),'4702')
        self.assertEqual(b.source_id(self.native['canonical']),'4702')
        self.assertIsNone(b.source_id('https://example.org/objects/4702'))


if __name__=='__main__':unittest.main()
