"""Identity/rights regression checks; no database or network access."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('research-production-wikiart-images-20261006.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)


class WikiArtIdentityTests(unittest.TestCase):
    def sample(self):
        work={'id':'example','title':'The Lady of Shalott','alternate_title':None,'creation_year_start':1888,
            'creation_year_end':1888,'date_precision':'exact','primary_media_id':None,
            'creators':[{'artist_id':'waterhouse','role':'primary'}]}
        candidate={'title':work['title'],'artist_url':'https://www.wikiart.org/en/john-william-waterhouse',
            'image_url':'https://uploads1.wikiart.org/images/john-william-waterhouse/the-lady-of-shalott-1888.jpg!Large.jpg'}
        item={'work':work,'candidate':candidate,'candidate_count':1,'missing_target_count':1}
        page={'url':candidate['artist_url']+'/the-lady-of-shalott-1888','metadata':{'title':work['title'],
            'artistUrl':'/en/john-william-waterhouse','artistName':'John William Waterhouse'},
            'image_url':candidate['image_url'],'date':(1888,1888),'rights_status':'public_domain',
            'rights_label':'Public domain','fields':{'Location':'Tate Britain, London, UK'}}
        return item,page,{'slug':'tate','name':'Tate'}

    def test_empty_translation_never_matches_missing_alternate_title(self):
        self.assertNotIn('',q.title_keys({'title':'Étude pour les Muses quittant Apollon','alternate_title':None}))
        self.assertEqual(set(),q.title_keys({'title':'','alternate_title':None}))

    def test_same_title_different_dated_version_is_rejected(self):
        item,page,museum=self.sample();page['date']=(1894,1894)
        self.assertEqual('page_date_conflict',q.assess_one(item,page,museum))

    def test_qualified_creator_and_duplicate_targets_are_held(self):
        item,page,museum=self.sample();item['missing_target_count']=2
        self.assertEqual('multiple_catalogue_targets',q.assess_one(item,page,museum))
        item['missing_target_count']=1;item['work']['creators'][0]['role']='workshop'
        self.assertEqual('qualified_or_multiple_creators',q.assess_one(item,page,museum))

    def test_territorial_rights_label_is_not_unrestricted(self):
        item,page,museum=self.sample();page['rights_label']='Public domain US'
        self.assertEqual('rights_restricted_unknown_or_territorial',q.assess_one(item,page,museum))

    def test_conflicting_museum_is_held(self):
        item,page,museum=self.sample();page['fields']['Location']='Private Collection'
        self.assertEqual('museum_location_needs_reconciliation',q.assess_one(item,page,museum))

    def test_generic_national_gallery_name_does_not_match_washington(self):
        museum={'slug':'national-gallery-london','name':'National Gallery'}
        self.assertFalse(q.museum_agrees(museum,'National Gallery of Art, Washington, DC, US'))
        self.assertTrue(q.museum_agrees(museum,'National Gallery, London, UK'))

    def test_verified_creator_title_date_museum_match(self):
        self.assertEqual('high_creator_title_date_museum',q.assess_one(*self.sample()))

    def test_reproductive_print_is_not_the_source_painting(self):
        item,page,museum=self.sample();item['work']['work_type']='print';page['fields']['Media']='oil, canvas'
        self.assertEqual('artwork_medium_conflict',q.assess_one(item,page,museum))

    def test_cutoff_and_unknown_dates_require_review(self):
        item,_,_=self.sample();w=item['work']
        w['creation_year_end']=1971
        self.assertFalse(q.date_compatible(w,(1888,1888)))
        w['creation_year_end']=1888;w['creation_year_start']=None
        self.assertFalse(q.date_compatible(w,(1888,1888)))


if __name__=='__main__':unittest.main()
