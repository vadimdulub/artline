"""Offline AGSA policy checks; preserved HTML only, no catalogue fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('agsa',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class AGSAPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        key='d09157eff566e5ff045ade23b23bfc36afbc1a0fd17967a841b5f3b2af66e043'
        rc=a.m.load(a.RUN/'captures'/(key+'.json'))
        cls.raw=a.captured_body(dict(receipt=rc,body_path=str((a.RUN/'captures'/(key+'.body.gz')).relative_to(a.m.ROOT))))
        cls.parsed=a.fields(cls.raw)
        cls.index=dict(source_id='24143',url=rc['url'],title='Alone in a shoe shop',creator_names=['Mortimer Menpes'],
            date='1887-88',medium='oil on wood panel (original frame)',accession='752P3')

    def test_creation_is_separate_from_lifespan_and_acquisition(self):
        f,reason=a.facts(self.parsed,self.index)
        self.assertIsNone(reason);self.assertEqual((f['first'],f['last'],f['date_precision']),(1887,1888,'range'))
        self.assertIn('1855 – 1938',f['creator_label']);self.assertIn('1975',f['holding_basis'])

    def test_shorthand_ranges_and_cutoff(self):
        for raw,expected in [('c.1633-35',(1633,1635,'circa_range')),('1899–01',(1899,1901,'range')),('1967',(1967,1967,'exact'))]:
            self.assertEqual(a.creation_date(raw),expected)
        for raw in ['1969-72','c.1970','1858-87?','early 1890s','1930 or 1932','']:
            self.assertIsNone(a.creation_date(raw))

    def test_source_index_agreement_is_required(self):
        for key in ['title','creator_names','date','medium','accession']:
            changed=dict(self.index);changed[key]=['Different'] if key=='creator_names' else 'Different'
            with self.subTest(key=key):self.assertIsNone(a.facts(self.parsed,changed)[0])

    def test_incoming_and_promised_holdings_are_held(self):
        for credit in ['Gift on loan 1975','Promised gift 2020','Purchased 1880; returned to owner']:
            p=copy.deepcopy(self.parsed);p['fields']['Credit line']=credit
            self.assertEqual(a.facts(p,self.index)[1],'custody_qualification_requires_review')

    def test_classification_and_compound_inventory_are_not_inferred(self):
        p=copy.deepcopy(self.parsed);p['fields']['Media category']='Print'
        self.assertEqual(a.facts(p,self.index)[1],'painting_or_medium_identity_requires_review')
        p=copy.deepcopy(self.parsed);p['fields']['Accession number']='752P3/4';index=dict(self.index,accession='752P3/4')
        self.assertEqual(a.facts(p,index)[1],'inventory_or_component_identity_requires_review')

    def test_qualified_creator_text_is_retained(self):
        p=copy.deepcopy(self.parsed);p['creator_label']='After Mortimer Menpes Britain/Australia 1855 – 1938'
        f,reason=a.facts(p,self.index);self.assertIsNone(reason);self.assertTrue(f['creator_label'].startswith('After '))

    def test_source_identity_ignores_title_alias_but_requires_official_host(self):
        self.assertEqual(a.source_id('http://www.artgallery.sa.gov.au/collection-publications/collection/works/other-title/24143/'),'24143')
        self.assertIsNone(a.source_id('https://example.test/collection-publications/collection/works/other-title/24143/'))


if __name__=='__main__':unittest.main()
