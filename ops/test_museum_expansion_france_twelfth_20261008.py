"""Offline identity, physical-unit and source chronology regressions; no DB fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-twelfth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={d['number']:d for d in r.build()};cls.ctx={v['source_record_id']:v['literal_primary_record'] for name in ['001','002'] for v in r.m.load(r.RUN/('physical-comparison-context-'+name+'.json.gz'))['rows']}
 def test_every_record_decided(self):
  self.assertEqual(set(self.ds),set(range(1,280)));self.assertEqual((len(r.NOTES),len(r.HOLDS)),(218,61))
 def test_sparse_duplicates_held(self):
  for n in [1,20,21,29,41,51,135,163,164,268,276]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_conflicting_impression_dates_held(self):
  for n in [6,15,16,43,84,109,117,157,185,188,196,231,240,244,245,246,272]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_bound_or_mounted_components_held(self):
  for n in [63,81,87,110,111,113,114,115,119,183,220]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_qualified_engraver_and_model_roles(self):
  f=self.ds[108]['facts'];self.assertIn('Hubert (graveur)',f['creator_label']);self.assertNotEqual(f['creator_label'],f['source_fields']['Auteur']);self.assertIn('Hubert',f['source_fields']['Precisions_inscriptions'])
 def test_unknown_chromolithographer_not_invented(self):
  self.assertEqual(self.ds[144]['facts']['creator_label'],"CONDAMIN Henri (peintre, d'après)");self.assertEqual(self.ds[144]['facts']['work_type'],'print')
 def test_conflicting_painted_model_preserved(self):
  self.assertIn('incertaine',self.ds[168]['facts']['creator_label']);self.assertIn('Velasquez',self.ds[236]['facts']['creator_label'])
 def test_greek_sculptor_included(self):
  f=self.ds[68]['facts'];self.assertIn('APARTIS',f['source_fields']['Precisions_inscriptions']);self.assertEqual((f['work_type'],f['first'],f['last']),('sculpture',1935,1935))
 def test_anonymous_medieval_sculpture_included(self):
  f=self.ds[224]['facts'];self.assertEqual((f['first'],f['last']),(1376,1425));self.assertEqual(f['work_type'],'sculpture')
 def test_distinct_academy_impressions(self):
  a,b=(self.ds[n]['facts'] for n in [232,277]);self.assertNotEqual(a['inventory'],b['inventory']);self.assertIn('Vinit',a['source_fields']['Precisions_inscriptions']);self.assertIn('Duvivier',b['source_fields']['Precisions_inscriptions'])
 def test_victor_notice_duplicate_counts_once(self):
  self.assertEqual(self.ds[266]['state'],'approved_review_only_addition');self.assertEqual(self.ds[275]['state'],'editorial_hold')
  for n in [266,275]:
   self.assertIn('LOV 723',self.ds[n]['facts']['inventory']);self.assertIn('doublon',self.ds[n]['facts']['source_fields']['Historique'])
 def test_separate_victor_sheet(self):
  self.assertNotEqual(self.ds[235]['facts']['dimensions_text'],self.ds[266]['facts']['dimensions_text']);self.assertNotEqual(self.ds[235]['facts']['medium'],self.ds[266]['facts']['medium'])
 def test_print_and_drawing_not_same_maniel(self):
  self.assertEqual(self.ds[234]['facts']['work_type'],'drawing');self.assertEqual(self.ds[264]['facts']['work_type'],'print')
 def test_distinct_dedications_same_size_thisbe(self):
  a,b=(self.ds[n]['facts'] for n in [256,257]);self.assertEqual(a['dimensions_text'],b['dimensions_text']);self.assertNotEqual(a['inventory'],b['inventory']);self.assertIn('Louise',b['source_fields']['Precisions_inscriptions'])
 def test_different_lettering_christ_states(self):
  a,b=(self.ds[n]['facts'] for n in [250,251]);self.assertNotEqual(a['inventory'],b['inventory']);self.assertNotEqual(a['source_fields']['Description'],b['source_fields']['Description'])
 def test_st_francis_four_physical_states(self):
  ds=[self.ds[n]['facts'] for n in [238,255,271,278]];self.assertEqual(len({v['inventory'] for v in ds}),4);self.assertEqual(len({v['dimensions_text'] for v in ds}),4);self.assertEqual(ds[-1]['first'],1887)
 def test_date_before_keeps_unknown_lower_bound(self):
  f=self.ds[143]['facts'];self.assertIsNone(f['first']);self.assertEqual((f['last'],f['date_precision']),(1964,'before'))
 def test_acquisition_not_creation(self):
  f=self.ds[105]['facts'];self.assertEqual(f['first'],1960);self.assertIn('1978',f['source_fields']['Precisions_inscriptions'])
 def test_inventory_collision_not_same_cherubini(self):
  f=self.ds[249]['facts'];self.assertIn('226',f['inventory']);self.assertEqual(len(r.notes.INVENTORY_EXCEPTIONS[249]),3);self.assertIn('INV 5423',self.ctx['000PE001563']['Numero_inventaire']);self.assertIn('huile',self.ctx['000PE001563']['Materiaux_techniques'])
 def test_model_paintings_are_separate_objects(self):
  for n,sid in [(64,'000PE001105'),(250,'000PE001775'),(258,'000PE025634'),(274,'000PE003312')]:
   f=self.ds[n]['facts'];self.assertEqual(f['work_type'],'print');self.assertNotEqual(f['dimensions_text'],self.ctx[sid]['Mesures']);self.assertIn('huile',self.ctx[sid]['Materiaux_techniques'])
 def test_creator_qualifier_semicolons_not_people(self):
  text="DUFLOS Claude (graveur) ; NATTIER Jean-Marc (d'après;peintre)";self.assertEqual(len(r.identity.creator_labels(text)),2)
  facts=dict(self.ds[168]['facts'],creator_label=text);self.assertEqual(r.identity.terms(facts),['duflos','nattier'])
 def test_unclosed_final_role_not_new_maker(self):
  f=dict(self.ds[168]['facts'],creator_label="LAMOTTE Alphonse (graveur) ; NATTIER Jean-Marc (d'après;peintre");self.assertEqual(r.identity.terms(f),['lamotte','nattier'])
 def test_inscription_name_variants_searched(self):
  for n,term in [(99,'morigot'),(108,'hubert'),(118,'chalarnel'),(120,'chapuy'),(162,'gagliardus'),(168,'nattier'),(178,'lacroix'),(192,'cooper'),(199,'hoeye'),(206,'devoisins'),(221,'tang'),(236,'velazquez'),(264,'rousseau')]:self.assertIn(term,self.ds[n]['comparison']['creator_terms'])
 def test_translations_find_sparse_existing_versions(self):
  for n,aid in [(20,'4586f077-df54-450d-ac71-2371f4c9588f'),(21,'d75b3388-d4f1-5c2d-b04d-8b352add04e4'),(51,'3fc29368-7aa3-4750-b60e-a325331928e1')]:self.assertIn(aid,{a['id'] for a in self.ds[n]['comparison']['leads']+self.ds[n]['comparison']['exact_title_hits']})
 def test_source_values_remain_literal(self):
  for d in self.ds.values():
   f=d['facts'];self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique']);self.assertEqual(f['date_display'],f['source_fields']['Millesime_de_creation'] or f['source_fields']['Periode_de_creation'])
if __name__=='__main__':unittest.main()
