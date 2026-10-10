"""Offline source-authoritative identity checks; no catalogue/network writes."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

n=module('round2','research-production-wikiart-round2-20261006.py')
e=module('expanded','wikiart-authoritative-expansion-20261006.py');e.configure(n)
fixtures=module('fixtures','test_production_wikiart_images_20261006.py')


class ExpandedIdentityTests(unittest.TestCase):
    def evaluate(self,item,page,museum):
        out=[]
        with patch.object(e,'inherit',lambda *args:None),patch.object(n,'assess',lambda:out.append(n.q.assess_one(item,page,museum))):
            e.assess()
        return out[0]

    def sample(self,title='Harold Gilman'):
        item,page,museum=fixtures.WikiArtIdentityTests().sample()
        item['work']['title']=item['candidate']['title']=page['metadata']['title']=title
        page['fields'].pop('Location');return item,page,museum

    def test_distinctive_short_title_with_one_dated_source(self):
        self.assertEqual('high_WikiArt_unique_title_creator_narrow_date',self.evaluate(*self.sample()))

    def test_generic_title_stays_held(self):
        for title in ['Untitled','Landscape','Self-Portrait','Portrait of a Woman']:
            self.assertEqual('insufficient_object_corroboration',self.evaluate(*self.sample(title)))

    def test_other_versions_stay_held(self):
        item,page,museum=self.sample();item['candidate_count']=2
        self.assertEqual('insufficient_object_corroboration',self.evaluate(item,page,museum))

    def test_exact_surname_first_does_not_strip_attribution(self):
        item,page,museum=self.sample();item['work']['creators']=[]
        item['work']['unlinked_creator_label']='Waterhouse, John William'
        self.assertTrue(self.evaluate(item,page,museum).startswith('high_'))
        item['work']['unlinked_creator_label']='after Waterhouse, John William'
        self.assertEqual('object_creator_needs_review',self.evaluate(item,page,museum))

    def test_named_other_museum_and_reproductive_medium_stay_held(self):
        item,page,museum=self.sample();page['fields']['Location']='Louvre, Paris, France'
        self.assertEqual('museum_location_needs_reconciliation',self.evaluate(item,page,museum))
        page['fields'].pop('Location');item['work']['work_type']='print';page['fields']['Media']='oil, canvas'
        self.assertEqual('artwork_medium_conflict',self.evaluate(item,page,museum))

    def test_unknown_dates_and_territorial_rights_stay_held(self):
        item,page,museum=self.sample();item['work']['creation_year_start']=None
        self.assertEqual('page_date_conflict',self.evaluate(item,page,museum))
        item['work']['creation_year_start']=1888;page['rights_label']='Public domain US'
        self.assertEqual('rights_restricted_unknown_or_territorial',self.evaluate(item,page,museum))

    def test_original_title_alias_must_be_reverified(self):
        item,page,museum=self.sample();item['candidate'].update(language='original_title',english_title='English source title')
        page['metadata']['title']='English source title'
        self.assertEqual('original_title_not_reverified',self.evaluate(item,page,museum))
        page['fields']['Original Title']='Harold Gilman'
        self.assertTrue(self.evaluate(item,page,museum).startswith('high_'))

    def test_source_date_review_requires_a_specific_museum_and_preserves_dates(self):
        item,page,museum=self.sample();item['candidate']['date']=(1888,1888)
        item['work'].update(creation_year_start=1887,creation_year_end=1887)
        before=copy.deepcopy(item['work'])
        with patch.object(e,'DATE_REVIEW',True):
            self.assertEqual('source_date_requires_exact_museum_version',self.evaluate(item,page,museum))
            page['fields']['Location']='Tate Britain, London, UK'
            self.assertTrue(self.evaluate(item,page,museum).startswith('high_editorially_reviewed_'))
        self.assertEqual(before,item['work'])

    def test_source_date_policy_holds_large_conflicts_and_post_cutoff(self):
        item,page,museum=self.sample();w=item['work']
        self.assertIsNone(e.source_date_basis(w,(1910,1910)))
        self.assertIsNone(e.source_date_basis(w,(1971,1971)))
        w.update(creation_year_start=None,creation_year_end=None,date_precision='unknown')
        self.assertIn('editorial_review',e.source_date_basis(w,(1888,1888)))
        w.update(creation_year_start=1968,creation_year_end=1972,date_precision='range')
        self.assertIsNone(e.source_date_basis(w,(1969,1969)))


if __name__=='__main__':unittest.main()
