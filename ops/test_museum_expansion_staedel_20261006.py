"""Offline Städel policy checks using preserved real catalogue pages."""
import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-staedel-20261006.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
identity_spec=importlib.util.spec_from_file_location('identity',Path(__file__).with_name('museum-expansion-staedel-identity-001-20261006.py'))
identity=importlib.util.module_from_spec(identity_spec);identity_spec.loader.exec_module(identity)


class StaedelPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def captured(url):
            p=s.RUN/'captures'/hashlib.sha256(url.encode()).hexdigest()
            return s.captured_body(dict(receipt=s.m.load(p.with_suffix('.json')),body_path=str(p.with_suffix('.body.gz').relative_to(s.m.ROOT))))
        cls.capture=staticmethod(captured)
        cls.rows,cls.total,cls.preview=s.index_rows(captured(s.index_url(1)),s.index_url(1))
        cls.index=next(r for r in cls.rows if r['source_id']=='1003')
        cls.parsed=s.fields(captured(cls.index['url']))

    def test_unknown_named_master_and_support_are_retained(self):
        f,reason=s.facts(self.parsed,self.index)
        self.assertIsNone(reason);self.assertEqual(f['creator_label'],'Sienese Master ca. 1430')
        self.assertEqual(f['medium'],'Poplar');self.assertEqual(f['date_display'],'ca. 1430')
        self.assertEqual((f['first'],f['last'],f['date_precision']),(1430,1430,'circa'))
        self.assertIn('1865',f['holding_basis'])

    def test_pagination_and_preview_are_not_double_counted(self):
        self.assertEqual(len(self.rows),120);self.assertEqual(len(self.preview),10)
        self.assertGreater(self.total,120)
        with self.assertRaises(AssertionError):s.index_rows(self.capture(s.index_url(1)),s.index_url(2))

    def test_compound_inventory_is_retained_as_a_hold(self):
        compound=[r for r in self.rows if r['source_id'] is None]
        self.assertTrue(compound)
        self.assertTrue(all(len(s.inventory_keys(r['accession']))>1 for r in compound))

    def test_creation_cutoff_and_cast_date_are_not_conflated(self):
        self.assertEqual(s.creation_date('1969 – 1970'),(1969,1970,'range'))
        for date in ['ca. 1970','1969 – 1971','1936 (casting 1979)','after 1900','unknown']:
            self.assertIsNone(s.creation_date(date),date)

    def test_native_identity_and_role_must_agree(self):
        for key in ['title','date','creator','accession','url']:
            row=copy.deepcopy(self.index);row[key]='different'
            self.assertIsNone(s.facts(self.parsed,row)[0],key)

    def test_changed_permalink_or_acquisition_is_rejected(self):
        p=copy.deepcopy(self.parsed);p['permalinks']=['https://www.staedelmuseum.de/go/ds/1004']
        self.assertEqual(s.facts(p,self.index)[1],'native_permalink_identity_conflict')
        for acquisition in ['Acquired in 1865, returned to owner','Acquired as a temporary loan','Promised gift']:
            p=copy.deepcopy(self.parsed);p['fields']['Acquisition']=acquisition;p['repeated'].pop('Acquisition',None)
            self.assertIsNone(s.facts(p,self.index)[0])

    def test_permanent_loan_requires_separate_editorial_route(self):
        row=next(r for r in self.rows if r['source_id']=='lg118')
        parsed=s.fields(self.capture(row['url']))
        self.assertEqual(s.facts(parsed,row)[1],'loan_or_other_collection_requires_review')
        self.assertIn('permanent loan',parsed['fields']['Acquisition'])

    def test_qualified_attribution_is_not_upgraded(self):
        row=next(r for r in self.rows if r['source_id']=='1981');parsed=s.fields(self.capture(row['url']))
        f,reason=s.facts(parsed,row);self.assertIsNone(reason)
        self.assertEqual(f['creator_label'],'Francisco de Goya ?')
        self.assertIn('1942',parsed['fields']['Object History'])

    def test_reordered_creator_labels_are_identity_leads(self):
        self.assertTrue(identity.label_matches('Veit Philipp',['Philipp Veit']))
        self.assertTrue(identity.label_matches('Y LUCIENTES Francisco de (peintre) GOYA',['Francisco de Goya']))
        self.assertTrue(identity.label_matches('Théodule (peintre) RIBOT',['Théodule Ribot']))

    def test_surname_alone_does_not_establish_creator_identity(self):
        self.assertFalse(identity.label_matches('Jan Brueghel the Younger',['Jan Brueghel the Elder']))
        self.assertFalse(identity.label_matches('Germain Ribot',['Théodule Ribot']))
        self.assertFalse(identity.label_matches(None,['Philipp Veit']))


if __name__=='__main__':unittest.main()
