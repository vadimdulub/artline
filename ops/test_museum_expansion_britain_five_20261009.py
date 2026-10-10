"""Offline tests of object identity, source conflicts and branch boundaries."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-britain-five-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
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
 def test_wrong_inventory(self):
  v=self.row();v['artwork']['accession_number']='WRONG'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_inventory_scope(self):
  v=self.row();v['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q4968867'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_object(self):
  v=self.row();v['source_id']='Q1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_primary_reference(self):
  v=self.row();v['entity']['claims']['P195'][0]['references'][0]['snaks']['P1679'][0]['datavalue']['value']='wrong-object-1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_changed_title(self):
  v=self.row();v['artwork']['title']='Different castle';self.assertIn('literal_title_mismatch',r.f.facts(v,self.initial)['issues'])
 def test_archived_exclusion(self):
  v=self.row();v['artwork']['status']='archived';self.assertIn('archived_record_excluded',r.f.facts(v,self.initial)['issues'])
 def test_post1970_flag(self):
  v=self.row();v['artwork']['creation_year_end']=1971;self.assertIn('post1970_catalogue_date',r.f.facts(v,self.initial)['issues'])
 def test_native_new_modern_date_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Date Made']=['1971']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_new_attribution_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Maker'][0]+=' (attributed)'
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_native_inventory_conflict_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[2]['parsed']['fields']['Object number']=['BIKGM.99999']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_perth_branch_needs_fine_art_evidence(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['objects'][0]['fields']['Associated concept']=['Social History']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_perth_inventory_conflict_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[1]['objects'][0]['fields']['Object number']=['WRONG']
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_perth_cross_type_inventory_collision(self):
  row=r.native_rows()[63];self.assertEqual(len(row['objects']),2);self.assertEqual(r.perth_object(row)['fields']['Title'],['The Fair City of Perth'])
 def test_double_sided_canvas_not_counted_twice(self):
  for n in [86,107]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_mixed_jug_portrait_source_held(self):self.assertEqual(self.by[83]['state'],'editorial_hold')
 def test_native_modern_work_held(self):self.assertEqual(self.by[171]['state'],'editorial_hold')
 def test_father_son_creator_conflict_held(self):self.assertEqual(self.by[160]['state'],'editorial_hold')
 def test_version_uncertainty_held(self):
  for n in [69,84,88,181]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_qualifications_preserved(self):
  for n in [23,134,198]:self.assertEqual(self.by[n]['state'],'editorial_hold')
  for n in [21,99,116]:self.assertEqual(self.by[n]['state'],'approved_existing_holding')
  self.assertIn('copy after',self.by[21]['facts']['title']);self.assertIn('copy after',self.by[116]['facts']['title'])
 def test_unknown_dates_and_missing_inventory_not_rewritten(self):
  self.assertIsNone(self.rows[54]['artwork']['accession_number']);self.assertIn('missing_catalogue_inventory',self.by[55]['resolved_issues'])
  ds=[v for v in self.decisions if v['state']=='approved_existing_holding' and v['facts']['date_precision']=='unknown'];self.assertTrue(ds);self.assertTrue(all(v['facts']['first'] is None and v['facts']['last'] is None and not v['derived_fields'] for v in ds))
 def test_branch_inference_and_history_explicit(self):
  ds=[v for v in self.decisions if v['state']=='approved_existing_holding' and v['previous_network_assertion_id']];self.assertTrue(ds);self.assertTrue(all(v['previous_institution_id']==r.NETWORK and 'editorial inference' in v['basis'] and v['selected_native_object_url'] for v in ds))
 def test_native_inventory_normalization_preserves_suffix(self):
  self.assertEqual(r.w.invkey('BIKGM.205e'),r.w.invkey('BIKGM:205E'));self.assertNotEqual(r.w.invkey('BIKGM.L215_31'),r.w.invkey('BIKGM.L215_174'));self.assertNotEqual(r.w.invkey('BIKGM.L217'),r.w.invkey('BIKGM.217'))
 def test_parser_anchor_and_repeated_keywords(self):
  raw=b'<p class="ehive-field ehive-identifier-public_profile_name"><span class="ehive-field-label">From:</span><a>Williamson Art Gallery and Museum</a></p><p class="ehive-field"><span class="ehive-field-label">Keyword</span><span class="ehive-field-value">river</span></p><p class="ehive-field"><span class="ehive-field-label">Keyword</span><span class="ehive-field-value">boat</span></p>'
  self.assertEqual(r.w.parsed(raw)['fields'],{'From:':['Williamson Art Gallery and Museum'],'Keyword':['river','boat']})
 def test_status_and_metadata_preserved(self):self.assertTrue(all(v['existing_status']=='review' and not v['derived_fields'] for v in self.decisions))
if __name__=='__main__':unittest.main()
