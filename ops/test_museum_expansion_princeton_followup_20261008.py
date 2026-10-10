"""Offline regressions for actual follow-up date and physical-identity hazards."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-princeton-followup-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows={v['number']:v for v in r.m.load(r.CANDIDATES)['rows']};cls.ds={v['number']:v for v in r.build()}
    def test_cutoff_1970_is_eligible_but_1964_71_is_held(self):
        self.assertEqual(self.ds[22]['state'],'approved_review_only_addition');self.assertEqual(self.ds[22]['facts']['last'],1970)
        self.assertEqual(self.ds[14]['state'],'editorial_hold');self.assertEqual(self.ds[14]['facts']['last'],1971)
    def test_nd_is_not_a_finite_creation_range(self):
        v=self.ds[15];self.assertEqual(v['facts']['date_display'],'n.d.');self.assertEqual((v['facts']['first'],v['facts']['last']),(1600,1900));self.assertEqual(v['state'],'editorial_hold')
    def test_sitter_reign_and_subject_event_are_not_creation(self):
        self.assertEqual((self.ds[18]['facts']['first'],self.ds[18]['facts']['last']),(1763,1775));self.assertIn('1673',self.ds[18]['facts']['title'])
        self.assertEqual(self.ds[19]['facts']['first'],1875);self.assertIn('884',self.ds[19]['facts']['title'])
    def test_nainsukh_mononym_is_in_actual_identity_query(self):
        x=r.m.load(r.IDENTITY);self.assertIn('%nainsukh%',x['params']['patterns']);self.assertIn('nainsukh',x['comparisons'][17]['creator_terms'])
    def test_former_reynolds_stays_former_and_unknown_sitter_held(self):
        v=self.ds[10];self.assertEqual(v['facts']['creator_label'],'British');self.assertEqual(v['state'],'editorial_hold');self.assertEqual(v['facts']['source_makers'][0]['role'],'Former Attribution')
    def test_attributions_and_unknown_creator_are_not_promoted(self):
        self.assertEqual(self.ds[18]['facts']['creator_label'],'Attributed to Nainsukh of Basohli');self.assertEqual(self.ds[55]['facts']['creator_label'],'Unknown American');self.assertIn('Circle of',self.ds[32]['facts']['creator_label'])
    def test_distinct_davis_sheets_keep_distinct_native_identities(self):
        a,b,c=[self.ds[n]['facts'] for n in [20,45,62]];self.assertEqual(len({v['source_id'] for v in [a,b,c]}),3);self.assertEqual(len({v['inventory'] for v in [a,b,c]}),3)
        self.assertEqual(b['first'],c['first']);self.assertEqual(b['dimensions_text'],c['dimensions_text']);self.assertNotEqual(b['source_fields']['primaryimage'],c['source_fields']['primaryimage'])
    def test_same_title_and_near_measurements_do_not_force_new_object(self):
        for n in [3,9,13,30,47,53,54]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
    def test_inconsistent_frame_and_long_source_ranges_are_preserved(self):
        v=self.ds[11]['facts'];self.assertEqual(v['dimensions_text'],v['source_fields']['dimensions']);self.assertIn('36 × 31',v['dimensions_text'])
        self.assertEqual((self.ds[35]['facts']['first'],self.ds[35]['facts']['last']),(1939,1959))
    def test_hash_mismatch_and_bad_http_status_fail(self):
        x=r.m.load(r.checked(self.rows[20]['source_reference']));cap=copy.deepcopy(x['capture']);cap['receipt']['status']=429
        with self.assertRaises(AssertionError):r.f.n.body(cap)
        cap=copy.deepcopy(x['capture']);cap['receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):r.f.n.body(cap)
if __name__=='__main__':unittest.main()
