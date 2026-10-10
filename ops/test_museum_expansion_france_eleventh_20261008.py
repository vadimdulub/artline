"""Offline physical-object identity regressions; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-eleventh-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={d['number']:d for d in r.build()};cls.ctx={v['source_record_id']:v['literal_primary_record'] for v in r.m.load(r.RUN/'physical-comparison-context-001.json.gz')['rows']}
 def test_every_captured_record_has_individual_decision(self):
  self.assertEqual(set(self.ds),set(range(1,355)));self.assertFalse(set(r.NOTES)&set(r.HOLDS))
 def test_approved_inventory_units_unique(self):
  ds=[d for d in self.ds.values() if d['state']=='approved_review_only_addition'];self.assertEqual(len(ds),len({(d['institution_id'],d['facts']['inventory']) for d in ds}))
 def test_sparse_possible_duplicates_held(self):
  for n in [11,22,30,40,41,45,93,353]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_mors_vitrix_study_not_finished_canvas(self):
  self.assertIn('bois',self.ds[17]['facts']['medium']);self.assertEqual(self.ctx['000PE029566']['Numero_inventaire'],'884.6.2');self.assertIn('300 H',self.ctx['000PE029566']['Mesures']);self.assertIn('44.54',self.ctx['000PE029566']['Historique'])
 def test_two_friends_study_distinct(self):
  self.assertEqual(self.ds[52]['facts']['inventory'],'72.3.2');self.assertIn('40.5',self.ds[52]['facts']['dimensions_text']);self.assertIn('81 H',self.ctx['000PE029589']['Mesures']);self.assertIn('72.3.2',self.ctx['000PE029589']['Historique'])
 def test_copy_of_michaud_is_not_self_portrait_original(self):
  self.assertIn("d'après",self.ds[3]['facts']['creator_label']);self.assertEqual(self.ctx['000PE029338']['Numero_inventaire'],'27.3.1');self.assertNotEqual(self.ds[3]['facts']['dimensions_text'],self.ctx['000PE029338']['Mesures'])
 def test_qualified_joint_roles(self):
  self.assertIn('animaux',self.ds[2]['facts']['creator_label']);self.assertIn('figures',self.ds[4]['facts']['creator_label']);self.assertIn('médaillon central',self.ds[9]['facts']['creator_label'])
 def test_old_attribution_not_promoted(self):
  self.assertEqual(self.ds[50]['facts']['creator_label'],'anonyme');self.assertIn('GUERCINO',self.ds[50]['facts']['source_fields']['Ancienne_attribution'])
 def test_mounted_print_components_held(self):
  for n in [95,98,122,123,124,125,143]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_shared_photo_frame_held(self):
  for n in [222,224]:self.assertIn('Deux photographies',self.ds[n]['facts']['source_fields']['Commentaires']);self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_source_original_relationship_held(self):
  for n in [229,330,333,335]:self.assertIn('Original',self.ds[n]['facts']['source_fields']['Historique']);self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_conflicting_chronology_held(self):
  for n in [28,114,118,137,163,194]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_similigravure_subject_date_held(self):
  for n in [115,175]:self.assertIn('similigravure',self.ds[n]['facts']['medium']);self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_facsimile_not_original_drawing(self):
  self.assertEqual(self.ds[186]['facts']['work_type'],'print');self.assertIn('Fac-similé',self.ds[186]['facts']['source_fields']['Historique']);self.assertEqual(self.ds[186]['facts']['last'],1900)
 def test_old_inventory_collision_not_same_object(self):
  self.assertIn('2932',self.ds[187]['facts']['inventory']);self.assertIn('2932',self.ctx['M0277002393']['Numero_inventaire']);self.assertNotEqual(self.ds[187]['facts']['title'],self.ctx['M0277002393']['Titre']);self.assertNotEqual(self.ds[187]['facts']['dimensions_text'],self.ctx['M0277002393']['Mesures'])
 def test_generic_bare_inventory_collision_not_same_object(self):
  self.assertEqual(self.ctx['000PE013801']['Numero_inventaire'],'299');self.assertEqual(self.ds[198]['facts']['work_type'],'print');self.assertIn('huile',self.ctx['000PE013801']['Materiaux_techniques'])
 def test_photograph_of_sculpture_not_sculpture(self):
  for n in [318,319]:self.assertEqual(self.ds[n]['facts']['work_type'],'photograph');self.assertIn('Etex',self.ds[n]['facts']['source_fields']['Description'])
 def test_cropped_and_wider_prints_distinct(self):
  a,b=self.ds[311]['facts'],self.ds[312]['facts'];self.assertIn('recadrée',a['source_fields']['Description']);self.assertIn('plus large',b['source_fields']['Description']);self.assertNotEqual(a['inventory'],b['inventory']);self.assertIn('29',a['source_fields']['Precisions_inscriptions']);self.assertIn('30',b['source_fields']['Precisions_inscriptions'])
 def test_photomaton_one_strip(self):
  f=self.ds[216]['facts'];self.assertEqual(f['work_type'],'photograph');self.assertIn('3,8',f['dimensions_text']);self.assertEqual(f['date_precision'],'circa_range')
 def test_subject_and_creation_dates_separated(self):
  self.assertEqual(self.ds[142]['facts']['last'],1900);self.assertIn('XVI',self.ds[142]['facts']['source_fields']['Precisions_inscriptions'])
 def test_creation_before_unknown_lower_preserved(self):
  for n in [1,6,7,8,10,12,17,24]:self.assertIsNone(self.ds[n]['facts']['first']);self.assertEqual(self.ds[n]['facts']['date_precision'],'before')
 def test_pastel_circa_not_acquisition(self):
  f=self.ds[354]['facts'];self.assertEqual((f['first'],f['last']),(1851,1900));self.assertIn('2005',f['source_fields']['Date_d_acquisition']);self.assertEqual(f['work_type'],'drawing')
 def test_literal_ownership_and_source_dates_preserved(self):
  for d in self.ds.values():
   f=d['facts'];self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique']);self.assertEqual(f['date_display'],f['source_fields']['Millesime_de_creation'] or f['source_fields']['Periode_de_creation'])
 def test_previous_lancon_holds_not_reselected(self):
  self.assertFalse(any('lancon' in r.m.norm(d['facts']['creator_label']) for d in self.ds.values()));q=r.m.load(r.RUN/'selected-metadata-queue-001.json');self.assertTrue(any('Lançon' in h['reason'] for h in q['held']))
 def test_creator_model_variants_searched(self):
  for n,term in [(23,'morisot'),(70,'hondecooter'),(90,'correggio'),(129,'nadar'),(194,'vase'),(198,'michelangelo')]:self.assertIn(term,self.ds[n]['comparison']['creator_terms'])
if __name__=='__main__':unittest.main()
