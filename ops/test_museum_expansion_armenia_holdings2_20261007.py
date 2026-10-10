"""Source guards for existing holdings with unknown inventories and repeated subjects."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-armenia-holdings2-20261007.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);m=v.m

class ArmeniaHoldingFollowup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=v.source_rows();scope=m.load(v.RUN/'existing-holding-followup-002.json.gz')
        arts={r['id']:r for r in scope['before']['artworks']}
        cls.arts={r['external_id']:arts[r['entity_id']] for r in scope['before']['identifiers'] if r['scheme']=='wikidata'}

    def data(self,qid='Q29203229'):
        e=copy.deepcopy(self.sources[qid]['entity']);return e,copy.deepcopy(self.arts[qid]),v.val(e,'P170')['id']

    def test_missing_accession_is_retained(self):
        f=v.facts(*self.data());self.assertIsNone(f['inventory']);self.assertEqual(f['year'],1883)

    def test_exact_sixteen_decisions(self):
        rows=v.records();self.assertEqual(len(rows),16)
        self.assertEqual(sum(r['facts']['inventory'] is None for r in rows),13)
        self.assertNotIn('Q28925577',{r['facts']['qid'] for r in rows})

    def test_inventory_qualified_collection_accepted(self):
        self.assertEqual(v.facts(*self.data('Q107481755'))['inventory'],'58')

    def test_wrong_creator_rejected(self):
        e,a,q=self.data()
        with self.assertRaises(AssertionError):v.facts(e,a,'Q718409')

    def test_conflicting_holder_rejected(self):
        e,a,q=self.data();e['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q13054028'
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_unknown_date_rejected(self):
        e,a,q=self.data();del e['claims']['P571']
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_creation_date_conflict_rejected(self):
        e,a,q=self.data();a['creation_year_start']=1884
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_after_cutoff_rejected(self):
        e,a,q=self.data();e['claims']['P571'][0]['mainsnak']['datavalue']['value']['time']='+1971-00-00T00:00:00Z';a['creation_year_start']=a['creation_year_end']=1971
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_qualified_attribution_rejected(self):
        e,a,q=self.data();e['claims']['P170'][0]['qualifiers']={'P1480':[{}]}
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_expired_holding_rejected(self):
        e,a,q=self.data();e['claims']['P195'][0]['qualifiers']={'P582':[{}]}
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_invented_accession_rejected(self):
        e,a,q=self.data();a['accession_number']='109'
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_wrong_existing_inventory_rejected(self):
        e,a,q=self.data('Q107481755');a['accession_number']='59'
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_title_collision_rejected(self):
        e,a,q=self.data();a['title']='Ararat'
        with self.assertRaises(AssertionError):v.facts(e,a,q)

    def test_held_versions_cannot_be_approved_implicitly(self):
        for qid in ['Q77863193','Q61904289','Q55284022','Q55283902','Q28925577','Q28871584']:
            with self.subTest(qid=qid),self.assertRaises(AssertionError):v.facts(*self.data(qid))

    def test_capture_integrity_required(self):
        cap=copy.deepcopy(self.sources['Q29203229']['capture']);cap['receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):v.capture_body(cap)

if __name__=='__main__':unittest.main()
