"""Offline regressions for the selected WikiArt source facts and identity guards."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('w',Path(__file__).with_name('museum-expansion-armenia-wikiart-20261007.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);m=w.m


class ArmeniaWikiArt(unittest.TestCase):
    def source(self,number):
        return next(r['source'] for r in m.load(w.RUN/'wikiart-followup-review-001.json')['records'] if r['number']==number)

    def parsed(self,number):
        source=self.source(number)
        return w.parse(w.body(source['capture']))

    def test_selected_capture_fields_reproduce(self):
        for number in w.SELECTED:
            with self.subTest(number=number):
                source=self.source(number);parsed=self.parsed(number)
                self.assertEqual(parsed['fields'],source['fields'])
                self.assertEqual(parsed['canonical_urls'],[source['source_url']])
                self.assertEqual(parsed['creator'],source['creator'])
                self.assertEqual(parsed['rights_labels'],['Public domain'])

    def test_full_range_overrides_single_machine_date(self):
        source=self.source(4);facts=w.facts(self.parsed(4),source['source_url'])
        self.assertEqual(source['date_created_literal'],'1876')
        self.assertEqual((facts['first'],facts['last'],facts['date_precision']),(1874,1876,'range'))

    def test_circa_and_creation_place_kept_distinct(self):
        source=self.source(5);facts=w.facts(self.parsed(5),source['source_url'])
        self.assertEqual((facts['date_display'],facts['first'],facts['last'],facts['date_precision']),('c. 1620',1620,1620,'circa'))
        self.assertIn('Antwerp',self.parsed(5)['fields']['Date'])

    def test_cityscape_does_not_invent_physical_type(self):
        source=self.source(4);facts=w.facts(self.parsed(4),source['source_url'])
        self.assertEqual(facts['work_type'],'unknown')
        self.assertIsNone(facts['medium']);self.assertIsNone(facts['dimensions'])

    def test_unknown_date_rejected(self):
        source=self.source(2)
        with self.assertRaises(AssertionError):w.facts(self.parsed(2),source['source_url'])

    def test_cutoff_uncertainty_rejected(self):
        for value in ['1971','1969 - 1971','c. 1970','c. 1969 - 1970','1880s','1900 or 1901','1902 - 1901']:
            with self.subTest(value=value),self.assertRaises(AssertionError):w.creation_date(value)

    def test_exact_cutoff_and_en_dash_range(self):
        self.assertEqual(w.creation_date('1970'),('1970',1970,1970,'exact'))
        self.assertEqual(w.creation_date('1874–1876'),('1874–1876',1874,1876,'range'))

    def test_wrong_creator_page_rejected(self):
        source=self.source(1);parsed=self.parsed(1);parsed['creator_url']='https://www.wikiart.org/en/another-artist'
        with self.assertRaises(AssertionError):w.facts(parsed,source['source_url'])

    def test_wrong_canonical_rejected(self):
        source=self.source(1);parsed=self.parsed(1);parsed['canonical_urls']=[source['source_url']+'-copy']
        with self.assertRaises(AssertionError):w.facts(parsed,source['source_url'])

    def test_wrong_museum_rejected(self):
        raw=w.body(self.source(1)['capture']).replace(b'National Gallery of Armenia',b'Another Museum of Armenia')
        with self.assertRaises(AssertionError):w.parse(raw)

    def test_capture_hash_required(self):
        capture=copy.deepcopy(self.source(1)['capture']);capture['receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):w.body(capture)

    def test_full_plan_and_original_title_evidence(self):
        plan,digest=w.validate_plan()
        self.assertEqual(len(plan['records']),7);self.assertEqual(len(plan['held']),5)
        record=next(r for r in plan['records'] if r['raw_source_record']['queue_number']==6)
        self.assertEqual(record['raw_source_record']['parsed']['fields']['Original Title'],'Бульвар зимой')
        self.assertTrue(all(r['facts']['accession'] is None for r in plan['records']))

    def test_invented_medium_rejected(self):
        plan=m.load(w.PLAN);record=next(r for r in plan['records'] if r['raw_source_record']['queue_number']==4)
        record['facts']['medium']='oil on canvas'
        with self.assertRaises(AssertionError):w.validate(plan)

    def test_duplicate_source_entry_rejected(self):
        plan=m.load(w.PLAN);plan['records'][-1]=copy.deepcopy(plan['records'][0])
        with self.assertRaises(AssertionError):w.validate(plan)

    def test_changed_evidence_rejected(self):
        plan=m.load(w.PLAN);plan['evidence'][0]['sha256']='0'*64
        with self.assertRaises(AssertionError):w.validate(plan)


if __name__=='__main__':unittest.main()
