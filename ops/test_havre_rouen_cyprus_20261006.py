"""Offline checks for the source formats used by the selected museum import."""
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('research-havre-rouen-cyprus-20261006.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class EvidenceTests(unittest.TestCase):
    def test_cvar_literal_calendar_date(self):
        d=m.parse_date('1938--03--01')
        self.assertEqual((d['first'],d['last'],d['precision'],d['date_display']),(1938,1938,'exact','1938--03--01'))
        self.assertEqual(m.parse_date('1938--02--31')['precision'],'unknown')

    def test_no_date_inferred_from_arbitrary_text(self):
        for text in ['[s.d.]',None,'Purchased in 1935','restored 1855','born 1884','1324 March 1']:
            with self.subTest(text=text):self.assertEqual(m.parse_date(text)['precision'],'unknown')

    def test_ranges_and_exclusive_before_preserved(self):
        self.assertEqual(m.parse_date('ca. 1859–1860')['precision'],'circa_range')
        d=m.parse_date('before 1954');self.assertIsNone(d['first']);self.assertEqual((d['last'],d['precision']),(1954,'before'))
        self.assertEqual((m.parse_date('between 1933 and 1936')['first'],m.parse_date('between 1933 and 1936')['last']),(1933,1936))
        d=m.parse_date('20th century');self.assertEqual((d['first'],d['last']),(1901,2000))

    def test_surrogates_are_not_treated_as_original_paintings(self):
        for medium in ['Watercolour and pen (colour photocopy)','Photo on canvas','Photogravure']:
            self.assertIsNone(m.kind(medium))

    def test_french_catalogue_date_precision(self):
        for literal,expected in [('1642-43',(1642,1643,'range')),('1523-27',(1523,1527,'range')),('XVIIIe',(1701,1800,'century')),('2nde moitié du XVIIe siècle',(1651,1700,'range')),('~1810-1820',(1810,1820,'circa_range'))]:
            d=m.parse_date(literal);self.assertEqual((d['first'],d['last'],d['precision']),expected);self.assertEqual(d['date_display'],literal)

    def test_reversed_creator_and_attribution_qualifier(self):
        self.assertEqual(m.creator_key('Bakst, Leon (1866-1924)'),m.creator_key('Léon Bakst'))
        self.assertNotEqual(m.creator_key('After Léon Bakst'),m.creator_key('Léon Bakst'))
        self.assertNotEqual(m.creator_key('Giovanni di Paolo'),m.creator_key('Giovanni Paolo Panini'))

    def test_reviewed_cyprus_plan_source_dates(self):
        plan,_=m.pinned('cyprus')
        for f in plan['records']:
            self.assertTrue(f['last']and f['last']<=1970)
            self.assertNotIn('sketchbook',f['title'].lower())
            if f['source_id']=='4805':
                self.assertIn('1324',f['title'])
                self.assertEqual(f['first'],1938)
            if f['museum_slug']=='state-gallery-cyprus':
                self.assertTrue(f['raw_fields']['collection'].startswith('State Gallery'))

if __name__=='__main__':unittest.main()
