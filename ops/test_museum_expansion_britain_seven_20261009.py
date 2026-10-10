"""Offline tests of object identity, source conflicts and branch boundaries."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-britain-seven-review-v2-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
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
 def mutate_native(self,field,value):
  rows=copy.deepcopy(r.native_rows())
  for f in rows[72][0]['parsed']['fields']:
   if f['label']==field:f['value']=value
  return rows
 def test_native_changed_creation_fails(self):
  with patch.object(r,'native_rows',return_value=self.mutate_native('Date Created','1971')),self.assertRaises(AssertionError):r.build()
 def test_native_qualified_creator_fails(self):
  with patch.object(r,'native_rows',return_value=self.mutate_native('Creator','Attributed to Briton Rivière')),self.assertRaises(AssertionError):r.build()
 def test_native_wrong_title_fails(self):
  with patch.object(r,'native_rows',return_value=self.mutate_native('Title','Different temptation')),self.assertRaises(AssertionError):r.build()
 def test_native_wrong_collection_fails(self):
  with patch.object(r,'native_rows',return_value=self.mutate_native('Location','Tate')),self.assertRaises(AssertionError):r.build()
 def test_native_wrong_publisher_fails(self):
  rows=copy.deepcopy(r.native_rows());rows[72][0]['parsed']['publisher_heading']='Other publisher'
  with patch.object(r,'native_rows',return_value=rows),self.assertRaises(AssertionError):r.build()
 def test_exact_reference_suffix(self):
  v=self.row(2);r.referenced_object_guard(v)
  v['entity']['claims']['P195'][0]['references'][0]['snaks']['P854'][0]['datavalue']['value']='https://artuk.org/discover/artworks/'
  with self.assertRaises(AssertionError):r.referenced_object_guard(v)
 def test_creator_authority_changed_fails(self):
  original=r.m.load
  def altered(path):
   x=original(path)
   if Path(path).name=='unlinked-creator-authorities-001.json.gz':x['rows'][0]['label_match']=False
   return x
  with patch.object(r.m,'load',side_effect=altered),self.assertRaises(AssertionError):r.build()
 def test_duplicate_pending_one_held_object(self):
  d=self.by[102];self.assertEqual(d['state'],'editorial_hold');self.assertEqual(len(d['additional_pending_assertion_ids']),1);self.assertEqual(len([v for v in self.decisions if v['existing_artwork_id']==d['existing_artwork_id']]),1)
 def test_keats_branch_not_guildhall(self):
  for n in [102,107,127,139,164,167]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_paired_sides_held(self):
  for n in [3,49,85]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_attribution_conflicts_held(self):
  for n in [42,69,77,158]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_qualified_copy_title_preserved(self):
  d=self.by[54];self.assertEqual(d['state'],'approved_existing_holding');self.assertIn('after Thornton Rippingille',d['facts']['title']);self.assertEqual(d['facts']['creator_label'],'Samuel Sidley')
 def test_life_dates_not_new_eligibility(self):self.assertEqual(self.by[17]['state'],'editorial_hold')
 def test_modern_event_and_unknown_date_held(self):
  for n in [13,126,182]:self.assertEqual(self.by[n]['state'],'editorial_hold');self.assertEqual(self.by[n]['facts']['date_precision'],'unknown')
 def test_close_versions_held(self):
  for n in [22,53,66,103]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_distinct_aqueduct_versions(self):
  for n in [12,165]:self.assertEqual(self.by[n]['state'],'approved_existing_holding');self.assertIn('23x33cm',self.by[n]['basis']);self.assertIn('96.5x122cm',self.by[n]['basis'])
 def test_duplicate_publisher_assets_one_object(self):
  self.assertEqual(len(r.native_rows()[95]),2);self.assertEqual(len([v for v in self.decisions if v['number']==95]),1)
 def test_joint_credit_preserved_in_evidence(self):self.assertIn('Francis Wheatley',self.by[60]['basis']);self.assertEqual(self.by[60]['derived_fields'],[])
 def test_unknown_is_not_eligible(self):
  ds=[d for d in self.decisions if d['state']=='approved_existing_holding' and d['facts']['date_precision']=='unknown'];self.assertEqual(len(ds),83);self.assertTrue(all(d['facts']['first'] is None and d['facts']['last'] is None and 'excluded from eligible-date totals' in d['basis'] for d in ds))
 def test_secondary_basis_separate(self):
  ds=[d for d in self.decisions if d['state']=='approved_existing_holding' and not d['selected_native_object_url']];self.assertTrue(all(d['confidence']==.8 and 'No exact native object corroboration' in d['basis'] for d in ds))
 def test_keyword_false_positive_resolved(self):
  for n in [7,144]:self.assertEqual(self.by[n]['state'],'approved_existing_holding');self.assertIn('filename_or_title_qualification',self.by[n]['resolved_issues'])
 def test_preservation(self):self.assertTrue(all(v['existing_status']=='review' and not v['derived_fields'] and v['previous_institution_id'] is None for v in self.decisions))
if __name__=='__main__':unittest.main()
