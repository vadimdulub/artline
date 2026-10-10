"""Offline Tretyakov rendered-object source and identity policy checks."""
import copy
import gzip
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('tretyakov',Path(__file__).with_name('museum-expansion-tretyakov-20261006.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class TretyakovPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=t.m.load(t.RUN/'captures/9337.json')
        cls.body=gzip.decompress((t.RUN/'captures/9337.body.gz').read_bytes())
        cls.parsed=t.fields(cls.body)
        cls.url=cls.receipt['final_url']

    def test_rendered_object_is_complete_before_excluded_global_state(self):
        self.assertIn(b'</footer>',self.body);self.assertNotIn(t.MARKER,self.body)
        self.assertFalse(self.receipt['complete_http_response'])
        self.assertEqual(self.parsed['title'],'Демьяново. Осенью в парке')
        self.assertEqual(self.parsed['fields']['Инвентарный номер'],'МКВ Ж-163')

    def test_creation_date_is_not_acquisition_or_lifespan(self):
        facts,why=t.facts(self.parsed,self.url)
        self.assertIsNone(why);self.assertEqual((facts['first'],facts['last']),(1903,1917))
        self.assertIn('1998',self.parsed['acquisition']);self.assertIn('1856-1933',facts['creator_label'])
        changed=dict(self.parsed,date_display='')
        self.assertEqual(t.facts(changed,self.url)[1],'creation_date_requires_review')

    def test_inventory_prefixes_do_not_merge_distinct_departments(self):
        self.assertEqual(t.inventory_keys('Инв.3856'),t.inventory_keys('3856'))
        self.assertEqual(t.inventory_keys('GTG 3856'),t.inventory_keys('3856'))
        self.assertNotEqual(t.inventory_keys('МКВ Ж-163'),t.inventory_keys('Ж-163'))

    def test_display_dimension_units_are_not_invented(self):
        f,why=t.facts(self.parsed,self.url);self.assertIsNone(why)
        self.assertEqual(f['dimensions'],'31,7 x 40,8')
        self.assertNotIn('on_view',f);self.assertIn('without claiming physical presence',f['holding_basis'])

    def test_ryabovo_watercolor_keeps_drawing_medium_and_department(self):
        parsed=t.fields(gzip.decompress((t.RUN/'captures/9300.body.gz').read_bytes()))
        f,why=t.facts(parsed,'https://my.tretyakov.ru/app/masterpiece/9300')
        self.assertIsNone(why);self.assertEqual(f['work_type'],'watercolor')
        self.assertEqual(f['medium'],'акварель, карандаш; бумага на картоне')
        self.assertEqual(f['accession'],'МКВ ГР-266')
        self.assertEqual((f['first'],f['last']),(1919,1919))
        self.assertIn('1984',parsed['acquisition'])

    def test_conflicting_titles_and_temporary_custody_held(self):
        self.assertEqual(t.facts(dict(self.parsed,og_title='Another work'),self.url)[1],'native_titles_conflict')
        changed=dict(self.parsed,acquisition='Поступило на временную выставку. 2020')
        self.assertEqual(t.facts(changed,self.url)[1],'custody_qualification_requires_review')

    def test_cutoff_and_unsupported_technique_are_held(self):
        for raw in ['1971','1960-1980','Около 1970','1903 или 1917']:
            with self.subTest(raw=raw):self.assertIsNone(t.dates(raw))
        changed=copy.deepcopy(self.parsed);changed['fields']['Техника']='литье'
        self.assertEqual(t.facts(changed,self.url)[1],'object_technique_requires_review')


if __name__=='__main__':unittest.main()
