"""Offline Auckland catalogue policy checks using preserved native pages."""
import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('auckland',Path(__file__).with_name('museum-expansion-auckland-20261006.py'))
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)


class AucklandPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def captured(url):
            key=hashlib.sha256(url.encode()).hexdigest();p=u.RUN/'captures'/key
            return u.captured_body(dict(receipt=u.m.load(p.with_suffix('.json')),body_path=str(p.with_suffix('.body.gz').relative_to(u.m.ROOT))))
        cls.rows,_=u.index_rows(captured(u.index_url(1)),u.index_url(1))
        cls.index=next(r for r in cls.rows if r['source_id']=='431')
        cls.raw=captured(cls.index['url']);cls.parsed=u.fields(cls.raw)

    def test_creation_does_not_use_acquisition_date(self):
        f,reason=u.facts(self.parsed,self.index)
        self.assertIsNone(reason);self.assertEqual((f['first'],f['last'],f['date_precision']),(1908,1908,'circa'))
        self.assertEqual(f['date_display'],'circa 1908');self.assertIn('1920',f['holding_basis'])

    def test_source_qualifiers_and_cutoff(self):
        self.assertEqual(u.creation_date('circa 1660-1690'),(1660,1690,'circa_range'))
        self.assertEqual(u.creation_date('late 19th century'),(1801,1900,'century'))
        self.assertEqual(u.creation_date('1730s'),(1730,1739,'range'))
        for text in ['circa 1970','early 20th century','1969-1972','1986','unknown','1890 or 1900']:
            self.assertIsNone(u.creation_date(text),text)

    def test_index_and_native_identity_must_agree(self):
        for key in ['source_id','title','date','creators']:
            row=copy.deepcopy(self.index);row[key]=[] if key=='creators' else 'different'
            self.assertIsNone(u.facts(self.parsed,row)[0])

    def test_rendered_fields_must_agree_with_native_state(self):
        p=copy.deepcopy(self.parsed);p['fields']['Accession No']='1900/1'
        self.assertEqual(u.facts(p,self.index)[1],'rendered_native_metadata_conflict')

    def test_incoming_loans_and_promised_gifts_are_not_accepted_holdings(self):
        for credit in ['Auckland Art Gallery, promised gift 2020','Auckland Art Gallery, purchased 1920, returned to owner','Auckland Art Gallery, gift on loan 2020']:
            p=copy.deepcopy(self.parsed);p['fields']['Credit line']=credit;p['native_route']['attributes']['credit_line']=credit
            self.assertEqual(u.facts(p,self.index)[1],'custody_qualification_requires_review')

    def test_qualified_creator_role_is_retained(self):
        p=copy.deepcopy(self.parsed);row=copy.deepcopy(self.index)
        p['fields']['Artist']='Robert Procter (after)';p['native_route']['attributes']['artists'][0]['role']='after';row['creators'][0]['role']='after'
        f,reason=u.facts(p,row);self.assertIsNone(reason);self.assertEqual(f['creator_label'],'Robert Procter (after)')
        p['fields']['Artist']='Robert Procter';self.assertEqual(u.facts(p,row)[1],'creator_role_label_requires_review')

    def test_legacy_url_and_title_alias_share_identity(self):
        self.assertEqual(u.source_id('http://www.aucklandartgallery.com/explore-art-and-ideas/artwork/431/old-title'),'431')
        self.assertEqual(u.source_id(self.index['url']),'431')
        self.assertIsNone(u.source_id('https://example.test/explore/art-and-artists/artwork/431/other'))

    def test_trust_holding_retains_relationship_and_multiline_credit(self):
        p=copy.deepcopy(self.parsed);native=p['native_route']['attributes']
        native['credit_line']=['Mackelvie Trust Collection, Auckland Art Gallery Toi o Tāmaki','Frame sponsored by a donor']
        p['fields']['Credit line']=' '.join(native['credit_line']);p['fields']['Accession No']=native['accession_no']='M1920/6'
        f,reason=u.facts(p,self.index);self.assertIsNone(reason);self.assertIn('permanent-loan holdings',f['holding_basis'])
        p['fields']['Accession No']=native['accession_no']='1920/6';self.assertEqual(u.facts(p,self.index)[1],'trust_inventory_credit_conflict')


if __name__=='__main__':unittest.main()
