"""Offline source-backed identity regressions; no catalogue fixtures or test database."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-tenth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={d['number']:d for d in r.build()};cls.ctx={v['source_record_id']:v['literal_primary_record'] for v in r.m.load(r.RUN/'physical-comparison-context-001.json.gz')['rows']}
 def test_complete_individual_decisions(self):
  self.assertEqual(set(self.ds),set(range(1,332)));self.assertFalse(set(r.NOTES)&set(r.HOLDS))
 def test_exact_inventory_duplicates_held(self):
  for n in [4,22,23,96]:self.assertEqual(self.ds[n]['state'],'editorial_hold');self.assertTrue([v for v in self.ds[n]['comparison']['inventory_hits'] if v['relevant']])
 def test_strasbourg_codes_not_merged(self):
  self.assertEqual(self.ctx['00160009390']['Code_Museofile'],'M0016');self.assertEqual(self.ds[4]['facts']['source_fields']['Code_Museofile'],'M0013')
 def test_mixed_frame_components_held(self):
  for n in r.notes.FRAME_UNITS:self.assertEqual(self.ds[n]['state'],'editorial_hold');self.assertIn('cadre',self.ds[n]['facts']['source_fields']['Description'])
 def test_single_portrait_frame_not_group(self):
  d=self.ds[111];self.assertEqual(d['state'],'approved_review_only_addition');self.assertIn('unique portrait',d['facts']['source_fields']['Description'])
 def test_lancon_scene_and_impression_dates_separated(self):
  self.assertEqual(len(r.notes.LANCON_CHRONOLOGY_HOLDS),52)
  for n in r.notes.LANCON_CHRONOLOGY_HOLDS:self.assertEqual(self.ds[n]['state'],'editorial_hold');self.assertIn('1870',self.ds[n]['facts']['date_display'])
 def test_printed_reproduction_type_preserved(self):
  d=self.ds[226];self.assertEqual(d['facts']['work_type'],'print');self.assertEqual(d['derived_fields']['physical_work_type']['original'],'drawing');self.assertIn('d’après',d['facts']['creator_label'].replace("d'après",'d’après'))
 def test_verso_attribution_qualified(self):
  d=self.ds[18];self.assertIn('attribuée',d['facts']['creator_label']);self.assertIn('Wechtlin',d['derived_fields']['qualified_creator_label']['literal_evidence'])
 def test_alternative_attribution_not_coauthorship(self):
  self.assertIn('autre attribution',self.ds[228]['facts']['creator_label'])
 def test_model_not_same_physical_object(self):
  d=self.ds[199];self.assertEqual(d['facts']['work_type'],'drawing');self.assertIn('pastel',d['facts']['medium']);self.assertIn("d'après",d['facts']['creator_label'])
 def test_primary_sparse_oils_resolved(self):
  for sid in ['M0094003701','M0094006380','M0094006282','M0094002072']:self.assertIn('huile sur toile',self.ctx[sid]['Description'])
  for n in [224,236,250,260,288]:self.assertIn(self.ds[n]['facts']['work_type'],['drawing','print']);self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
 def test_strasbourg_portrait_is_drawing(self):
  self.assertIn('Pastel',self.ctx['00160011444']['Description']);self.assertEqual(self.ctx['00160011444']['Date_d_acquisition'],'1925');self.assertEqual(self.ds[311]['facts']['work_type'],'print')
 def test_prints_separated_by_sheet_and_provenance(self):
  self.assertIn('49,6',self.ds[293]['facts']['dimensions_text']);self.assertIn('H.39',self.ctx['M0228014312']['Mesures']);self.assertEqual(self.ctx['M0228014312']['Date_d_acquisition'],'1992');self.assertEqual(self.ds[293]['facts']['source_fields']['Date_d_acquisition'],'1989')
 def test_separate_drawings_on_common_mount(self):
  for n in [290,292,294,296,298,300]:
   f=self.ds[n]['facts'];self.assertIn('48 cm',f['dimensions_text']);self.assertIn('(dessin)',f['dimensions_text']);self.assertTrue(f['inventory'].startswith('CMNI 3017.'))
  self.assertEqual(len({self.ds[n]['facts']['inventory'] for n in [290,292,294,296,298,300]}),6)
 def test_separate_catalogue_fragments(self):
  for n in [312,318,320,322,324,326]:self.assertIn('5 autres dessins',self.ds[n]['facts']['source_fields']['Historique']);self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
 def test_recto_verso_one_record(self):
  for n in [18,220,252,266,268,304,308,328,330]:
   f=self.ds[n]['facts'];self.assertEqual(sum(v['source_id']==f['source_id'] for v in self.ds.values()),1)
 def test_black_and_colour_queen_proofs_distinct(self):
  a,b=[self.ds[n]['facts'] for n in [317,325]];self.assertNotEqual(a['inventory'],b['inventory']);self.assertIn('en couleur',a['source_fields']['Historique']);self.assertIn('en noir',b['source_fields']['Historique']);self.assertNotEqual(a['dimensions_text'],b['dimensions_text'])
 def test_unknown_lower_date_not_invented(self):
  for n in [13,31,59,70,90,93,232]:self.assertIsNone(self.ds[n]['facts']['first']);self.assertEqual(self.ds[n]['facts']['date_precision'],'before')
 def test_compound_period_broad_bounds(self):
  for n,bounds in [(50,(1576,1625)),(68,(1826,1900)),(112,(1876,1925)),(233,(1876,1950))]:self.assertEqual((self.ds[n]['facts']['first'],self.ds[n]['facts']['last']),bounds)
 def test_acquisition_not_creation(self):
  self.assertEqual(self.ds[222]['facts']['first'],1880);self.assertEqual(self.ds[222]['facts']['last'],1890);self.assertIn('2015',self.ds[222]['facts']['source_fields']['Date_d_acquisition'])
 def test_conflicting_dates_held(self):
  for n in [3,9,10,15,16,78,79,81,151,205,263,301,307,319]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_literal_ownership_preserved(self):
  for d in self.ds.values():self.assertEqual(d['facts']['credit_line'],d['facts']['source_fields']['Statut_juridique'])
 def test_source_note_creator_variants_searched(self):
  for n,t in [(6,'arapov'),(32,'altdorfer'),(61,'merian'),(70,'kubin'),(275,'sickert')]:self.assertIn(t,self.ds[n]['comparison']['creator_terms'])
 def test_sparse_identity_holds_not_negative_matches(self):
  for n in [57,103,104,106,107,117,118,200,203,209]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
if __name__=='__main__':unittest.main()
