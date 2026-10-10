"""Offline identity, scope and preservation guards; no catalogue test fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-britain-three-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
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
 def test_network_not_merged_or_reassigned(self):
  numbers={v['number'] for v in self.rows if v['artwork']['current_institution_id']==r.NETWORK};self.assertEqual(len(numbers),123);self.assertTrue(all(self.by[n]['state']=='editorial_hold' for n in numbers))
 def test_unknown_dates_not_inferred(self):
  ds=[v for v in self.decisions if v['state']=='approved_existing_holding' and v['facts']['date_precision']=='unknown'];self.assertEqual(len(ds),41);self.assertTrue(all(v['facts']['first'] is None and v['facts']['last'] is None and not v['derived_fields'] for v in ds))
 def test_acquisition_not_creation(self):
  d=self.by[1];self.assertEqual(d['facts']['first'],1910);self.assertEqual(r.f.w.year(r.f.qual(d['facts']['source_collection_statements'][0],'P580')),1947)
 def test_existing_published_status_preserved(self):
  d=self.by[278];self.assertEqual((d['state'],d['existing_status']),('approved_existing_holding','published'));self.assertEqual(d['derived_fields'],[])
 def test_copy_qualifications_preserved(self):
  for number,year in [(60,1730),(125,1845)]:
   d=self.by[number];self.assertEqual(d['state'],'approved_existing_holding');self.assertIn('after',d['facts']['title']);self.assertEqual(d['facts']['first'],year)
 def test_subject_words_not_attribution(self):
  self.assertTrue(all(self.by[n]['state']=='approved_existing_holding' for n in [12,229]))
 def test_reverse_not_double_counted(self):
  self.assertEqual(self.by[33]['state'],'editorial_hold');self.assertEqual(self.by[131]['state'],'approved_existing_holding')
 def test_uncertain_version_and_attribution_held(self):
  self.assertTrue(all(self.by[n]['state']=='editorial_hold' for n in [31,85,139,157,233]));self.assertIn('two artists',self.by[157]['basis'])
 def test_sketch_distinguished_from_painting(self):
  for n in [237,283]:self.assertEqual(self.by[n]['state'],'approved_existing_holding')
  self.assertNotEqual(self.by[237]['facts']['inventory'],self.by[283]['facts']['inventory']);self.assertIn('Sketch',self.by[283]['facts']['title'])
 def test_native_inventory_mismatch_rejected(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['parsed']['fields']['Item Number']='NMW A 5053'
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_qualified_creator_rejected(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['parsed']['creators'][0]['name']+=' (attributed to)'
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
if __name__=='__main__':unittest.main()
