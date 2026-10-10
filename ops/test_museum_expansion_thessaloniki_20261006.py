"""Offline checks using retained real collection pages; no database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('t',Path(__file__).with_name('museum-expansion-thessaloniki-20261006.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


class ThessalonikiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research=t.m.load(t.RUN/'thessaloniki-001-research.json.gz')
        cls.records={r['source_record_id']:r for r in cls.research['records']}

    def test_selected_real_capture_roundtrip(self):
        self.assertEqual(len(self.records),7)
        for record in self.records.values():
            body=t.captured_body(dict(receipt=record['source_receipt'],body_path=record['body_path']))
            self.assertEqual(t.validate_record(record,body),record['facts'])

    def test_patrons_do_not_become_creators(self):
        for oid in ['chalkografia-geniki-apopsi-tou-agiou-or','chalkografia-geniki-apopsi-tou-orous-si']:
            self.assertIsNone(self.records[oid]['facts']['creator_label'])
        self.assertEqual(self.records['chalkografia-i-panagia-gerontissa']['facts']['creator_label'],'Ioannis Kaldis')

    def test_copies_use_modern_creation_and_material(self):
        copies=[r for r in self.records.values() if r['raw_source_record']['native_fields']['fields']['Type']=='Copy of a fresco']
        self.assertEqual(len(copies),3)
        for r in copies:
            self.assertEqual((r['facts']['first'],r['facts']['last']),(1950,1960))
            self.assertEqual(r['facts']['work_type'],'painting')
            self.assertEqual(r['facts']['medium'],'Watercolor on manila paper attached to canvas')

    def test_literal_creation_and_identity_cannot_drift(self):
        r=self.records['chalkografia-i-panagia-gerontissa'];original=r['raw_source_record']['native_fields'];index=r['raw_source_record']['index_record']
        for column,value in [('Chronology','1800'),('Code','ΒΧει 92'),('Type','Icon')]:
            parsed=copy.deepcopy(original);parsed['fields'][column]=value
            with self.assertRaises(AssertionError):t.facts(parsed,index)
        parsed=copy.deepcopy(original);parsed['canonical']=parsed['canonical'].replace('gerontissa','other-object')
        with self.assertRaises(AssertionError):t.facts(parsed,index)

    def test_source_attribution_anchor_required(self):
        r=self.records['chalkografia-i-panagia-gerontissa'];parsed=copy.deepcopy(r['raw_source_record']['native_fields'])
        parsed['descriptions']=['The Virgin Mary is shown standing.']
        with self.assertRaises(AssertionError):t.facts(parsed,r['raw_source_record']['index_record'])

    def test_inventory_script_and_leading_zero_variants(self):
        for x,y in [('ΝΕΤ 009','NET 9'),('ΒΧει 091','BXei 91'),('ΒΕΙ 0049','BEI49')]:
            self.assertEqual(t.inventory_keys(x),t.inventory_keys(y))
        self.assertNotEqual(t.inventory_keys('NET 9'),t.inventory_keys('BEI 9'))

    def test_conflicts_and_compound_work_not_selected(self):
        held={r['index']['source_id']:r for r in self.research['held']}
        self.assertEqual(set(t.HOLDS)-set(held),set())
        self.assertFalse(set(t.HOLDS)&set(self.records))
        self.assertEqual(held['eikastiko-ergo-the-end-ergo-tou-nikou-alexio']['reason'],'post_1970_creation')


if __name__=='__main__':unittest.main()
