"""Synthetic boundaries for attaching images without rewriting catalogue facts."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('nm_format',Path(__file__).with_name('followup-nationalmuseum-commons.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class ExistingFacts(unittest.TestCase):
    def setUp(self):
        self.facts=dict(title='Synthetic work',accession_number='NM 123',creation_year_start=1800,
                        creation_year_end=1800,date_display='1800',date_precision='exact',
                        work_type='painting',artist='Synthetic maker',artist_slug='synthetic-maker')
        self.im=dict(self.facts,accession_number='NM123',date_display='Made 1800',preserve_existing_catalogue_format=True)

    def test_format_only_keeps_original_record(self):
        before=copy.deepcopy(self.im);m.nm.verify_catalogue_facts(self.im,self.facts);self.assertEqual(before,self.im)

    def test_default_stays_strict(self):
        self.im.pop('preserve_existing_catalogue_format')
        with self.assertRaises(ValueError):m.nm.verify_catalogue_facts(self.im,self.facts)

    def test_accession_suffix_is_not_discarded(self):
        self.im['accession_number']='NM123A'
        with self.assertRaises(ValueError):m.nm.verify_catalogue_facts(self.im,self.facts)

    def test_contradictory_date_text_is_rejected(self):
        self.im['date_display']='1800 or 1810'
        with self.assertRaises(ValueError):m.nm.verify_catalogue_facts(self.im,self.facts)

    def test_changed_bounds_are_rejected(self):
        self.im['creation_year_start']=1799
        with self.assertRaises(ValueError):m.nm.verify_catalogue_facts(self.im,self.facts)

    def test_unknown_or_uncertain_date_is_not_formatting(self):
        for value in ['before 1800','c. 1800','1800?','after 1800','not 1800','acquired 1800']:
            with self.subTest(value=value):
                self.im['date_display']=value
                with self.assertRaises(ValueError):m.nm.verify_catalogue_facts(self.im,self.facts)


class TranscribedTitles(unittest.TestCase):
    def test_multiline_source_languages_are_explicit(self):
        wt=' |title = {{title|lang=fr|Titre\n |en=English title\n |sv=Svensk titel}}\n |description = Do not retain'
        block,names=m.multilingual_title(wt)
        self.assertEqual(names,{'english title','svensk titel'})
        projected=m.project_file({'imageinfo':[],'revisions':[{'slots':{'main':{'*':wt}}}]})
        result=projected['revisions'][0]['slots']['main']['*']
        self.assertIn(block,result);self.assertNotIn('Do not retain',result)

    def test_another_field_cannot_supply_title(self):
        self.assertEqual(m.multilingual_title(' |description = {{title|en=Wrong work}}')[1],set())

    def test_nested_unparsed_template_is_held(self):
        self.assertEqual(m.multilingual_title(' |title = {{title|en={{unresolved}}}}')[1],set())


if __name__=='__main__':unittest.main()
