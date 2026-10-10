"""Offline checks using captured museum records; no database or catalogue fixtures."""
import copy, importlib.util, unittest
from pathlib import Path
s = importlib.util.spec_from_file_location('r', Path(__file__).with_name('museum-expansion-france-eighth-review-20261008.py'))
r = importlib.util.module_from_spec(s); s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.ds = {d['number']: d for d in r.build()}
 def test_wrong_museum_fails(self):
  d=self.ds[1]; q=copy.deepcopy(d['index']); q['museum']['city']='Montpellier'
  with self.assertRaises(AssertionError): r.f.parse(q,r.checked(d['source_reference']))
 def test_bad_response_and_hash_fail(self):
  x=r.m.load(r.checked(self.ds[1]['source_reference']))
  for k,v in [('status',429),('sha256','0'*64)]:
   y=copy.deepcopy(x); y['receipt'][k]=v
   with self.assertRaises(AssertionError): r.f.body(y)
 def test_post1970_creation_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']); d['Millesime_de_creation']='1971'; d['Periode_de_creation']='4e quart 20e siècle'; self.assertIsNone(r.f.n.screen(d)[0])
 def test_cutoff_crossing_range_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']); d['Millesime_de_creation']='1969-1972'; d['Periode_de_creation']='2e moitié 20e siècle'; self.assertIsNone(r.f.n.screen(d)[0])
 def test_album_requires_object_unit_review(self):
  d=copy.deepcopy(self.ds[67]['facts']['source_fields']); d['Denomination']='album'; self.assertIsNone(r.f.n.screen(d)[0])
 def test_1970_drawing_retained(self):
  d=self.ds[52]; self.assertEqual(d['facts']['first'],1970); self.assertIn('1970',d['facts']['source_fields']['Precisions_inscriptions']); self.assertEqual(d['state'],'approved_review_only_addition')
 def test_before_endpoints_not_filled_from_lifespans(self):
  for n in [5,6,14,60,122,150]:
   f=self.ds[n]['facts']
   if f['date_precision']=='before': self.assertIsNone(f['first'])
  self.assertEqual(self.ds[5]['facts']['last'],1970)
 def test_depicted_year_not_creation(self):
  f=self.ds[186]['facts']; self.assertIn('1831',f['title']); self.assertEqual((f['first'],f['last']),(1872,1872))
 def test_acquisition_inventory_not_creation(self):
  f=self.ds[245]['facts']; self.assertEqual(f['inventory'],'2025.0.84'); self.assertEqual(f['first'],1965)
 def test_print_model_date_separated(self):
  f=self.ds[97]['facts']; self.assertEqual(f['first'],1886); self.assertIn('1885',f['source_fields']['Precisions_inscriptions']); self.assertEqual(f['work_type'],'print')
 def test_original_versus_copy_qualification(self):
  d=self.ds[230]; self.assertIn('d’après',d['facts']['creator_label']); self.assertNotIn('d’après',d['facts']['source_fields']['Auteur']); self.assertIn('Original copié',d['derived_fields']['qualified_creator_label']['literal_evidence']); self.assertEqual(d['facts']['last'],1950)
 def test_current_artist_generation_takes_precedence_over_index(self):
  d=self.ds[210]; self.assertIn('source_changed_Auteur',d['review_flags']); self.assertIn('III',d['facts']['creator_label']); self.assertNotIn('III',d['index']['raw_source_record']['Auteur'])
 def test_hiroshige_generations_not_reconciled_to_authority(self):
  for n in [252,258,259,260]: self.assertEqual(self.ds[n]['facts']['creator_label'],self.ds[n]['facts']['source_fields']['Auteur'])
  self.assertIn('1826-1869',self.ds[258]['facts']['creator_label']); self.assertIn('1842-1894',self.ds[259]['facts']['creator_label'])
 def test_literal_source_roles_and_question_marks(self):
  for n in [74,88,110,118,127,138]: self.assertEqual(self.ds[n]['facts']['creator_label'],self.ds[n]['facts']['source_fields']['Auteur'])
  self.assertIn('?',self.ds[138]['facts']['creator_label']); self.assertIn('incertaine',self.ds[110]['facts']['creator_label'])
 def test_unknown_makers_retained(self):
  for n in [1,171,201]: self.assertIn(self.ds[n]['facts']['creator_label'],[None,'anonyme','Anonyme'])
 def test_missing_dimensions_retained(self): self.assertIsNone(self.ds[234]['facts']['dimensions_text'])
 def test_girodet_recto_verso_one_record(self):
  f=self.ds[67]['facts']; self.assertIn('recto',f['title']); self.assertIn('verso',f['title']); self.assertEqual(sum(d['source_id']==f['source_id'] for d in self.ds.values()),1)
 def test_complete_triptych_is_single_catalogue_unit(self):
  for n in [204,225,229,233,250,262,263,265]:
   f=self.ds[n]['facts']; self.assertIn('triptyque',f['dimensions_text']); self.assertEqual(sum(d['facts']['inventory']==f['inventory'] for d in self.ds.values()),1)
 def test_incomplete_triptychs_explicit(self):
  for n in [203,205,217,224,236,259,261]: self.assertIn('incomplet',self.ds[n]['facts']['source_fields']['Description'])
 def test_multiple_impressions_and_vases_held(self):
  for n in [71,78,257]: self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_ambiguous_attributions_held(self): self.assertEqual(self.ds[84]['state'],'editorial_hold')
 def test_conflicting_dates_and_reproductions_held(self):
  for n in [17,26,37,54,75,111,137,249,251]: self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_possible_duplicates_held(self):
  for n in [68,70,94,106,152]: self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_cadastral_plan_not_quota_filler(self): self.assertEqual(self.ds[131]['state'],'editorial_hold')
 def test_two_brouardel_days_distinguished(self):
  f=self.ds[83]['facts']; self.assertIn('29 janvier 1910',f['source_fields']['Precisions_inscriptions']); c=r.m.load(r.RUN/'physical-comparison-context-001.json.gz')['rows'][0]; self.assertIn('28 Janvier 1910',c['literal_primary_record']['source_fields']['Precisions_inscriptions'])
 def test_same_subject_calamattas_distinct_impressions(self):
  fs=[self.ds[n]['facts'] for n in [19,20,21]]; self.assertEqual(len({f['inventory'] for f in fs}),3); self.assertEqual(len({f['dimensions_text'] for f in fs}),3); self.assertEqual([f['first'] for f in fs],[1837,1836,1837])
 def test_bourdelle_duncan_sheets_distinct(self):
  fs=[self.ds[n]['facts'] for n in [140,173,187]]; self.assertEqual(len({f['inventory'] for f in fs}),3); self.assertEqual(len({f['dimensions_text'] for f in fs}),3)
 def test_claude_prints_not_originals(self):
  for n in [116,117]: self.assertEqual(self.ds[n]['facts']['work_type'],'print'); self.assertIn('19e',self.ds[n]['facts']['date_display']); self.assertIn('17e',self.ds[n]['facts']['source_fields']['Periode_de_l_original_copie'])
 def test_short_inventory_collisions_explicitly_reviewed(self):
  for n,ids in r.notes.INVENTORY_EXCEPTIONS.items():
   self.assertEqual({v['id'] for v in self.ds[n]['comparison']['inventory_hits'] if v['relevant']},ids); self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
 def test_source_holding_and_dates_not_silently_rewritten(self):
  for d in self.ds.values():
   f=d['facts']; self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique'])
  self.assertEqual(self.ds[188]['facts']['date_display'],'3e quart 19e siècle')
 def test_source_note_names_broaden_comparison(self):
  for n,t in [(16,'deblois'),(49,'delaroche'),(68,'dietrich'),(74,'gellee'),(87,'mene'),(92,'vorsterman'),(105,'sabatier'),(203,'hashimoto'),(210,'konobu'),(264,'baichoro')]: self.assertIn(t,self.ds[n]['comparison']['creator_terms'])
 def test_multilingual_title_forms_preserve_specific_identity(self):
  f=self.ds[258]['facts']; forms=r.identity.title_forms(f['title']); self.assertIn('Futagawa',forms); self.assertIn(f['title'],forms); self.assertIn('c4b44cb4-d665-5d49-9a0d-4ff18a875d49',{v['id'] for v in self.ds[258]['comparison']['exact_title_hits']})
if __name__=='__main__': unittest.main()
