"""Offline policy checks using preserved museum pages; no database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('ireland',Path(__file__).with_name('museum-expansion-ireland-20261006.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)


class IrelandPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=i.RUN/'captures'
        rc=i.m.load(root/'675ec41ee62f0a62783dd5a6e874a12a2fe93d2f1a158f5b5680704c2c3c2e0e.json')
        body=dict(receipt=rc,body_path=str((root/'675ec41ee62f0a62783dd5a6e874a12a2fe93d2f1a158f5b5680704c2c3c2e0e.body.gz').relative_to(i.m.ROOT)))
        cls.parsed=i.fields(i.captured_body(body))
        rc=i.m.load(root/'70cad5f0236b45c693131222f87615d1fc1e0d51f05a7381e0757abbae4f1ab2.json')
        body=dict(receipt=rc,body_path=str((root/'70cad5f0236b45c693131222f87615d1fc1e0d51f05a7381e0757abbae4f1ab2.body.gz').relative_to(i.m.ROOT)))
        rows,_=i.index_rows(i.captured_body(body),rc['url']);cls.index=next(r for r in rows if r['source_id']=='9045')

    def test_source_creation_is_separate_from_acquisition_and_artist_life(self):
        facts,reason=i.facts(self.parsed,self.index)
        self.assertIsNone(reason);self.assertEqual(facts['date_display'],'1523')
        self.assertEqual((facts['first'],facts['last']),(1523,1523))
        self.assertIn('1460-1528',facts['creator_label']);self.assertIn('1866',facts['holding_basis'])

    def test_index_must_match_same_native_title_date_and_creator(self):
        for key in ['title','date','creator']:
            changed=dict(self.index);changed[key]='different'
            with self.subTest(key=key):self.assertIsNone(i.facts(self.parsed,changed)[0])

    def test_incoming_loan_or_promised_gift_cannot_be_imported_as_acquisition(self):
        for credit in ['Purchased in 1866; returned to owner','Promised gift, 2020','Presented on loan, 1960']:
            altered=copy.deepcopy(self.parsed);altered['fields']['Credit Line']=credit
            self.assertEqual(i.facts(altered,self.index)[1],'custody_qualification_requires_review')

    def test_loan_and_compound_inventory_identity_is_held(self):
        for inv in ['L.14702','NGI.12/13','NGI.12a','']:
            altered=copy.deepcopy(self.parsed);altered['fields']['Object number']=inv
            self.assertEqual(i.facts(altered,self.index)[1],'inventory_or_loan_identity_requires_review')

    def test_copy_and_attribution_qualifications_are_not_removed(self):
        altered=copy.deepcopy(self.parsed);altered['creators']=['After Bernhard Strigel, German, 1460-1528']
        f,reason=i.facts(altered,self.index);self.assertIsNone(reason);self.assertTrue(f['creator_label'].startswith('After '))

    def test_explicit_periods_qualifiers_and_cutoff(self):
        for raw,expected in [('1570s',(1570,1579,'range')),('first quarter of the 16th century',(1501,1525,'range')),
                ('19th century',(1801,1900,'century')),('c.1560',(1560,1560,'circa')),('before 1971',(None,1971,'before'))]:
            self.assertEqual(i.creation_date(raw),expected)
        for raw in ['1600s','1970s','20th century','c.1970','1968-1972','after 1600','third half of the 16th century','']:
            with self.subTest(raw=raw):self.assertIsNone(i.creation_date(raw))

    def test_inventory_and_source_identity_variants(self):
        self.assertEqual(i.inventory_keys('NGI.6'),i.inventory_keys('6'))
        self.assertEqual(i.source_id('http://onlinecollection.nationalgallery.ie/objects/9045/old-title?x=y'),'9045')
        self.assertIsNone(i.source_id('https://example.test/objects/9045/other'))


if __name__=='__main__':unittest.main()
