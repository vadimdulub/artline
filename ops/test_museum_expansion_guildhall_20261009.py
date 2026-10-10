"""Offline regression checks for dates, physical versions and collection attribution."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-guildhall-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r);f=r.f;m=r.m;RUN=r.RUN
class GuildhallReview(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={x['number']:x for x in f.rows()};cls.decisions={x['number']:x for x in r.build()};cls.accepted=[v for v in cls.decisions.values() if v['state']=='approved_review_only_addition']
 def test_source_facts_reconstructed(self):self.assertEqual(list(self.rows.values()),m.load(RUN/'native-candidates-003.json.gz')['rows'])
 def test_creation_cutoff_boundary(self):
  self.assertEqual(f.creation('1970')['first'],1970)
  for raw in ['1971','c.1970','1969–1971','Unknown',None,'1860 (exhibited)']:self.assertIsNotNone(f.creation(raw)['date_issue'])
 def test_creation_range_and_circa(self):
  self.assertEqual((f.creation('c.1833')['first'],f.creation('c.1833')['date_precision']),(1833,'circa'));self.assertEqual(f.creation('1829–1831')['last'],1831)
 def test_no_event_date_inferred(self):
  for n in [6,35]:self.assertIsNone(self.rows[n]['facts']['first']);self.assertEqual(self.decisions[n]['state'],'editorial_hold')
  self.assertEqual(self.rows[22]['facts']['first'],1832)
 def test_copy_dates_stay_unknown(self):
  for n in [10,28]:self.assertIsNone(self.rows[n]['facts']['first']);self.assertEqual(self.decisions[n]['state'],'editorial_hold')
 def test_anonymous_signature_is_qualified(self):self.assertEqual(self.rows[1]['facts']['creator_label'],'Unidentified artist; signature read as J.W.S.')
 def test_lavery_not_added_twice(self):self.assertEqual(self.decisions[3]['state'],'already_catalogued');self.assertNotIn(3,{v['number'] for v in self.accepted})
 def test_documentation_and_duplicate_presentations_excluded(self):
  for n in [8,24]:self.assertEqual(self.decisions[n]['state'],'editorial_hold')
  self.assertEqual(len({v['source_id'] for v in self.accepted}),22)
 def test_two_clytemnestra_physical_versions(self):
  v=self.rows[5]['facts'];self.assertEqual((v['inventory'],v['date_display'],v['dimensions_text']),('577','1882','239 x 174 cm'));self.assertIn('FAO3',self.decisions[5]['basis']);self.assertTrue(any(h['accession_number']=='FAO3' for h in self.decisions[5]['comparison']['hits']))
 def test_hunt_study_and_finished_work(self):
  self.assertIn('four arches',self.decisions[12]['basis']);self.assertNotEqual(self.rows[11]['source_id'],self.rows[12]['source_id']);self.assertEqual(self.rows[12]['facts']['medium'],'Oil')
 def test_griffier_conflicting_source_date_preserved(self):
  v=self.rows[7]['facts'];self.assertEqual(v['native_fields']['Date Created'],'1739');self.assertEqual((v['first'],v['last']),(1739,1740))
 def test_dyce_three_presentations_count_once(self):
  v=self.rows[14]['facts'];self.assertEqual((v['source_id'],v['first'],v['medium']),('qwF9gzxjLpAUCA',1860,'Oil on canvas'));self.assertEqual(len(v['native_page_urls']),2)
 def test_loan_publisher_is_not_holding_institution(self):
  v=self.rows[20]['facts'];self.assertTrue(v['publisher_heading'].startswith('Dordrechts'));self.assertEqual(self.rows[20]['institution_id'],f.IID);self.assertEqual(v['source_id'],'DAEy9HYrq2u2SA');self.assertIn('unverified',v['source_note']);self.assertEqual((v['first'],v['last']),(1829,1831));self.assertEqual(v['native_fields']['Date Created'],'1829')
 def test_millais_watercolour_crosswalk_held(self):self.assertEqual(self.decisions[23]['state'],'editorial_hold');self.assertTrue(self.rows[23]['facts']['native_issues'])
 def test_post1970_works_held(self):
  for n in [27,30,33]:self.assertEqual(self.decisions[n]['state'],'editorial_hold');self.assertIsNotNone(self.rows[n]['facts']['date_issue'])
 def test_modern_artist_eligible_creation_retained(self):
  self.assertEqual(self.rows[29]['facts']['first'],1969);self.assertEqual(self.rows[34]['facts']['first'],1962)
 def test_nebot_version_not_assumed_from_museum(self):self.assertEqual(self.decisions[36]['state'],'editorial_hold');self.assertIn('N01453',self.decisions[36]['basis'])
 def test_source_parsed_field_tamper_rejected(self):
  x=copy.deepcopy(m.load(f.checked(self.rows[37]['source_reference'])));x['parsed']['fields'][0]['value']='Altered title'
  with self.assertRaises(AssertionError):f.newfacts(x)
 def test_publisher_alone_does_not_prove_holding(self):
  x=m.load(f.checked(self.rows[20]['source_reference']));self.assertTrue(f.newfacts(x)['native_issues'])
 def test_scope_identity_and_unknowns(self):
  self.assertEqual(len(self.accepted),22);self.assertEqual(sum(v['state']=='editorial_hold' for v in self.decisions.values()),17);self.assertTrue(all(v['facts']['last']<=1970 and not v['comparison']['source_hits'] and not v['comparison']['presentation_alias_hits'] for v in self.accepted));self.assertEqual(sum(v['facts']['inventory'] is not None for v in self.accepted),1)
if __name__=='__main__':unittest.main()
