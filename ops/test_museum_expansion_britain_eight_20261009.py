"""Offline adversarial checks for this holding reconciliation; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-britain-eight-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
class Review(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=r.m.load(r.RUN/'source-context-001.json.gz')['rows'];cls.initial=r.m.load(r.RUN/'initial-scope-001.json.gz');cls.decisions=r.build();cls.by={v['number']:v for v in cls.decisions};cls.native=r.native_rows()
 def row(self,n=1):return copy.deepcopy(self.rows[n-1])
 def test_wrong_museum(self):
  v=self.row();v['entity']['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_ended_holding(self):
  v=self.row();v['entity']['claims']['P195'][0].setdefault('qualifiers',{})['P582']=[{}]
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_inventory(self):
  v=self.row();v['artwork']['accession_number']='WRONG'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_inventory_scope(self):
  v=self.row();v['entity']['claims']['P217'][0]['qualifiers']['P195'][0]['datavalue']['value']['id']='Q1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_wrong_object(self):
  v=self.row();v['source_id']='Q1'
  with self.assertRaises(AssertionError):r.f.facts(v,self.initial)
 def test_title_change(self):
  v=self.row();v['artwork']['title']='Other object';self.assertIn('literal_title_mismatch',r.f.facts(v,self.initial)['issues'])
 def test_archived_exclusion(self):
  v=self.row();v['artwork']['status']='archived';self.assertIn('archived_record_excluded',r.f.facts(v,self.initial)['issues'])
 def test_post1970_flag(self):
  v=self.row();v['artwork']['creation_year_end']=1971;self.assertIn('post1970_catalogue_date',r.f.facts(v,self.initial)['issues'])
 def native_mutation(self,key,value):
  v=copy.deepcopy(self.native[45])
  if key in ['Date','Acquisition Number','Credit Line']:v['fields'][key]=value
  else:v[key]=value
  with self.assertRaises(AssertionError):r.native_guard(45,v,self.by[45]['facts'])
 def test_wrong_native_maker(self):self.native_mutation('native_creator','After Roland Penrose (1900-1984)')
 def test_wrong_native_title(self):self.native_mutation('native_title','Another painting')
 def test_wrong_native_date(self):self.native_mutation('Date','1971')
 def test_wrong_native_inventory(self):self.native_mutation('Acquisition Number','SOTAG : 1977/49')
 def test_missing_native_acquisition(self):self.native_mutation('Credit Line','')
 def test_wrong_native_publisher(self):self.native_mutation('url','https://example.org/object/sotag-197748/')
 def test_accession_conflict_held(self):
  self.assertEqual(self.by[13]['state'],'editorial_hold');self.assertEqual(self.by[13]['facts']['inventory'],'56/2006');self.assertEqual(self.native[13]['fields']['Acquisition Number'],'SOTAG : 2006/57')
 def test_triptych_not_three_count(self):
  for n in [12,52,140]:self.assertEqual(self.by[n]['state'],'editorial_hold');self.assertEqual(self.by[n]['facts']['inventory'],'CAC1985/25')
 def test_attribution_conflict_held(self):self.assertEqual(self.by[58]['state'],'editorial_hold');self.assertIn('filename_or_title_qualification',self.by[58]['source_issues'])
 def test_close_versions_held(self):
  for n in [43,155]:self.assertEqual(self.by[n]['state'],'editorial_hold')
 def test_study_is_separate_support(self):
  for n in [87,174]:self.assertEqual(self.by[n]['state'],'approved_existing_holding');self.assertIn('paper',self.by[n]['basis']);self.assertIn('canvas',self.by[n]['basis']);self.assertEqual(self.by[n]['facts']['date_precision'],'unknown')
 def test_physical_dimension_change_fails(self):
  src={v['number']:copy.deepcopy(v) for v in self.rows};src[174]['entity']['claims']['P2048'][0]['mainsnak']['datavalue']['value']['amount']='+230'
  with self.assertRaises(AssertionError):r.physical_guard(src)
 def test_physical_support_change_fails(self):
  src={v['number']:copy.deepcopy(v) for v in self.rows}
  for c in src[174]['entity']['claims']['P186']:
   if c['mainsnak']['datavalue']['value']['id']=='Q11472':c['mainsnak']['datavalue']['value']['id']='Q12321255'
  with self.assertRaises(AssertionError):r.physical_guard(src)
 def test_kidner_different_medium_and_format(self):
  d=self.by[35];self.assertEqual(d['state'],'approved_existing_holding');self.assertIn('acrylic on canvas',d['basis']);self.assertIn('126.4x101cm',d['basis']);self.assertEqual(d['facts']['date_precision'],'unknown')
 def test_modern_ramsay_not_old_painter(self):
  d=self.by[190];self.assertEqual(d['facts']['creator_qid'],'Q4730933');self.assertFalse(d['facts']['artist_links']);self.assertEqual(d['facts']['date_precision'],'unknown');self.assertIn('not the eighteenth-century',d['basis'])
 def test_unknown_not_date_eligible(self):
  ds=[d for d in self.decisions if d['state']=='approved_existing_holding' and d['facts']['date_precision']=='unknown'];self.assertEqual(len(ds),104);self.assertTrue(all(d['facts']['first'] is None and d['facts']['last'] is None and 'excluded from eligible-date totals' in d['basis'] for d in ds))
 def test_false_qualification_flags(self):
  for n in [99,137]:self.assertEqual(self.by[n]['state'],'approved_existing_holding');self.assertIn('filename_or_title_qualification',self.by[n]['resolved_issues'])
 def test_historical_registration_not_current_building(self):
  ds=[d for d in self.decisions if d['facts']['inventory'].startswith('HH')];self.assertTrue(ds);self.assertTrue(all('do not establish present building or display' in d['basis'] for d in ds))
 def test_loan_looking_inventory_not_ownership(self):
  d=self.by[89];self.assertEqual(d['state'],'approved_existing_holding');self.assertIn('without interpreting it as proof of loan or ownership',d['basis'])
 def test_secondary_evidence_marked(self):
  ds=[d for d in self.decisions if d['state']=='approved_existing_holding' and not d['selected_native_object_url']];self.assertTrue(all(d['confidence']==.8 and 'No exact native object corroboration' in d['basis'] for d in ds))
 def test_creator_evidence_tampering_fails(self):
  original=r.m.load
  def altered(path):
   x=original(path)
   if Path(path).name=='unlinked-creator-authorities-001.json.gz':x['rows'][0]['label_match']=False
   return x
  with patch.object(r.m,'load',side_effect=altered),self.assertRaises(AssertionError):r.verified_creators()
 def test_raw_html_tampering_fails(self):
  row=copy.deepcopy(self.native[45]);row['capture']['receipt']['sha256']='0'*64
  with self.assertRaises(AssertionError):r.raw_capture(row)
 def test_preservation(self):self.assertTrue(all(v['existing_status']=='review' and not v['derived_fields'] and v['previous_institution_id'] is None for v in self.decisions))
if __name__=='__main__':unittest.main()
