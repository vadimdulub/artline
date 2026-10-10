"""Offline identity, scope and preservation guards; no catalogue test fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-britain-four-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
class Review(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=r.m.load(r.RUN/'source-context-001.json.gz')['rows'];cls.initial=r.m.load(r.RUN/'initial-scope-001.json.gz');cls.decisions=r.build();cls.by={v['number']:v for v in cls.decisions}
 def row(self,n=1):return copy.deepcopy(self.rows[n-1])
 def test_wrong_museum(self):
  v=self.row();v['entity']['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q4968867'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_ended_holding(self):
  v=self.row();v['entity']['claims']['P195'][0].setdefault('qualifiers',{})['P582']=[{}]
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_inventory_conflict(self):
  v=self.row();v['artwork']['accession_number']='NMW A 5053'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_inventory_museum_conflict(self):
  v=self.row();v['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q4968867'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_changed_title(self):
  v=self.row();v['artwork']['title']='Different castle';self.assertIn('literal_title_mismatch',r.f.facts(v,self.initial)['issues'])
 def test_source_object_mismatch(self):
  v=self.row();v['source_id']='Q1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_bad_reference(self):
  v=self.row();v['entity']['claims']['P195'][0]['references'][0]['snaks']['P1679'][0]['datavalue']['value']='wrong-object-1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_post1970_flag(self):
  v=self.row();v['artwork']['creation_year_end']=1971;self.assertIn('post1970_catalogue_date',r.f.facts(v,self.initial)['issues'])
 def test_archived_exclusion(self):
  v=self.row();v['artwork']['status']='archived';self.assertIn('archived_record_excluded',r.f.facts(v,self.initial)['issues'])
 def test_network_refinement_requires_exact_department(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['parsed']['headings']=['FOLK LIFE : PAINTINGS']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_network_history_identified(self):
  ds=[d for d in self.decisions if d['state']=='approved_existing_holding' and d['previous_network_assertion_id']];self.assertTrue(ds);self.assertTrue(all(d['previous_institution_id']==r.NETWORK and 'editorial inference' in d['basis'] for d in ds))
 def test_unknown_dates_not_inferred(self):
  ds=[d for d in self.decisions if d['state']=='approved_existing_holding' and d['facts']['date_precision']=='unknown'];self.assertTrue(ds);self.assertTrue(all(d['facts']['first'] is None and d['facts']['last'] is None and not d['derived_fields'] for d in ds))
 def test_native_modern_dates_held(self):
  for n in [62,76,235]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_native_creator_conflict_held(self):
  self.assertEqual(self.by[75]['state'],'editorial_hold')
 def test_qualified_attributions_held(self):
  for n in [29,100,194]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_copy_and_subject_qualifications_preserved(self):
  for n in [83,236]:self.assertEqual(self.by[n]['state'],'approved_existing_holding')
  self.assertIn('after Joshua Reynolds',self.by[83]['facts']['title']);self.assertIn('School',self.by[236]['facts']['title'])
 def test_version_uncertainty_not_quota_approved(self):
  for n in [67,78,98,156]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_native_inventory_mismatch_rejected(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['parsed']['fields']['Catalogue Number']=['WRONG']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_new_qualification_rejected(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['parsed']['fields']['Maker'][0]+=' (attributed to)'
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_post1970_creation_rejected(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['parsed']['fields']['Date Made']=['1971']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_physical_versions_kept_distinct(self):
  self.assertNotEqual(self.by[89]['facts']['inventory'],self.by[229]['facts']['inventory']);self.assertTrue(all(self.by[n]['state']=='approved_existing_holding' for n in [89,229]))
 def test_review_status_preserved(self):
  self.assertTrue(all(d['existing_status']=='review' and not d['derived_fields'] for d in self.decisions))
if __name__=='__main__':unittest.main()
