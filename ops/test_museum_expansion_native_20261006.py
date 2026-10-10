"""Offline native catalogue policy tests; no database reads or writes."""
import copy
import gzip
import hashlib
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('museum-expansion-native-20261006.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)


class MauritshuisPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=n.RUN/'mauritshuis/captures'
        url=n.SITES['mauritshuis']+'/en/our-collection'
        raw=gzip.decompress((root/(hashlib.sha256(url.encode()).hexdigest()+'.body.gz')).read_bytes())
        cls.item=next(v for v in n.mauritshuis_index(raw,url)[0] if v['source_id']=='868')
        raw=gzip.decompress((root/(hashlib.sha256(cls.item['url'].encode()).hexdigest()+'.body.gz')).read_bytes())
        cls.parsed=n.mauritshuis_fields(raw)

    def test_current_transfer_is_separate_from_historical_loan(self):
        f,reason=n.mauritshuis_facts(self.parsed,self.item)
        self.assertIsNone(reason);self.assertEqual(f['accession'],'868')
        self.assertEqual(f['creator_label'],'Jan van der Heyden (Gorinchem 1637 - 1712 Amsterdam)')
        self.assertEqual((f['first'],f['last'],f['date_precision']),(1670,1670,'circa'))
        self.assertIn('transferred, 1960',f['holding_basis'])

    def test_current_loan_restitution_and_promised_gift_are_held(self):
        for tail in ['on loan from another museum, 2020','returned to the heirs, 2020','promised gift, 2020']:
            p=copy.deepcopy(self.parsed);p['provenance']=[p['provenance'][0]+'; '+tail]
            with self.subTest(tail=tail):self.assertEqual(n.mauritshuis_facts(p,self.item)[1],'latest_custody_or_ownership_event_requires_review')

    def test_missing_provenance_does_not_use_on_view_as_holding(self):
        p=copy.deepcopy(self.parsed);p['provenance']=[]
        self.assertTrue(p['fields']['On view in'])
        self.assertEqual(n.mauritshuis_facts(p,self.item)[1],'provenance_requires_review')

    def test_explicit_outward_loan_preserves_owner_without_claiming_custody(self):
        p=copy.deepcopy(self.parsed);p['provenance']=['acquired by King William I for the Mauritshuis, 1823; on long-term loan to the Rijksmuseum, Amsterdam, since 1927']
        facts,reason=n.mauritshuis_facts(p,self.item)
        self.assertIsNone(reason);self.assertIn('does not claim physical custody',facts['holding_basis'])
        p['provenance']=['acquired by the Rijksmuseum, 1823; on long-term loan to the Mauritshuis, since 1927']
        self.assertEqual(n.mauritshuis_facts(p,self.item)[1],'latest_custody_or_ownership_event_requires_review')

    def test_anonymous_cultural_qualification_remains_literal(self):
        p=copy.deepcopy(self.parsed);p['fields']['Artist']='Anonymous (Southern Netherlands)'
        facts,reason=n.mauritshuis_facts(p,dict(self.item,creator='Anonymous'))
        self.assertIsNone(reason);self.assertEqual(facts['creator_label'],'Anonymous (Southern Netherlands)')

    def test_inventory_and_canonical_identity_conflicts_held(self):
        p=copy.deepcopy(self.parsed);p['fields']['Inventory number']='869'
        self.assertEqual(n.mauritshuis_facts(p,self.item)[1],'native_inventory_identity_conflict')
        p=copy.deepcopy(self.parsed);p['canonical']=self.item['url']+'-different'
        self.assertEqual(n.mauritshuis_facts(p,self.item)[1],'native_canonical_identity_conflict')

    def test_qualified_creator_cannot_be_silently_unqualified(self):
        p=copy.deepcopy(self.parsed);p['fields']['Artist']+=' (studio of)'
        self.assertEqual(n.mauritshuis_facts(p,self.item)[1],'index_native_attribution_conflict')
        item=dict(self.item,creator=self.item['creator']+' (studio of)')
        facts,reason=n.mauritshuis_facts(p,item)
        self.assertIsNone(reason);self.assertTrue(facts['creator_label'].endswith('(studio of)'))

    def test_source_creation_date_not_provenance_or_artist_lifespan(self):
        p=copy.deepcopy(self.parsed);p['fields']['Dated']=''
        self.assertEqual(n.mauritshuis_facts(p,self.item)[1],'creation_date_requires_review')
        for date in ['1971','c. 1970','1960-1980','1670 or 1671','1637 - 1712 Amsterdam','']:
            with self.subTest(date=date):self.assertIsNone(n.creation_date(date))

    def test_explicit_before_date_preserves_unknown_lower_bound(self):
        self.assertEqual(n.creation_date('before 1637'),(None,1637,'before'))
        self.assertEqual(n.creation_date('before 1971'),(None,1971,'before'))
        for raw in ['before 1972','before c. 1970','after 1637']:
            with self.subTest(raw=raw):self.assertIsNone(n.creation_date(raw))

    def test_localized_legacy_urls_resolve_only_explicit_inventory_ids(self):
        self.assertEqual(n.source_id('https://www.mauritshuis.nl/nl-nl/verdiep/de-collectie/kunstwerken/view-868/'),'868')
        self.assertEqual(n.source_id(self.item['url']),'868')
        self.assertIsNone(n.source_id('https://other.example/artworks/868-view'))

    def test_foreign_inventory_is_retained_despite_different_title(self):
        plan=n.m.load(n.m.RUN/'mauritshuis-002-current-plan.json.gz')
        row=next(r for r in plan['records'] if r['source_record_id']=='1067')
        self.assertEqual(n.foreign_inventory_references(row['raw_source_record']['native_fields']),['SK-C-1657'])
        self.assertEqual(n.foreign_inventory_references(self.parsed),[])

    def test_captured_index_distinguishes_letter_ids_from_features(self):
        url=n.SITES['mauritshuis']+'/en/our-collection?p=17'
        path=n.RUN/'mauritshuis/captures'/(hashlib.sha256(url.encode()).hexdigest()+'.body.gz')
        rows,_=n.mauritshuis_index(gzip.decompress(path.read_bytes()),url)
        self.assertEqual({r['source_id'] for r in rows if r['source_id'] and r['source_id'].startswith('l')},{'l120','l60'})
        self.assertEqual([r['title'] for r in rows if r['source_id'] is None],['The lift of the Mauritshuis'])

    def test_captured_sculptures_and_drawings_keep_native_inventory_references(self):
        plan=n.m.load(n.m.RUN/'mauritshuis-005-current-plan.json.gz')
        expected={'906':('sculpture','BK-1963-101'),'1134':('drawing','RP-T-2006-152'),'834':('drawing','RP-T-BR-2006-1')}
        for row in plan['records']:
            if row['source_record_id'] not in expected:continue
            with self.subTest(inventory=row['source_record_id']):
                body=gzip.decompress((n.m.ROOT/row['body_path']).read_bytes())
                facts=n.validate_record(row,body)
                kind,reference=expected[row['source_record_id']]
                self.assertEqual(facts['work_type'],kind)
                self.assertEqual(n.foreign_inventory_references(row['raw_source_record']['native_fields']),[reference])
        self.assertTrue(set(expected)<={r['source_record_id'] for r in plan['records']})


if __name__=='__main__':unittest.main()
