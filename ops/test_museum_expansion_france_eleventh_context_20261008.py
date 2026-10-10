"""Offline boundary checks for physical photographs and exact museum destinations."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-eleventh-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
class Context(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=f.m.load(f.RUN/'native-candidates-001.json.gz')['rows'];cls.by={r['number']:r for r in cls.rows}
 def raw(self,n):return copy.deepcopy(self.by[n]['facts']['source_fields'])
 def test_exact_museum_contexts_pass(self):
  for n in [1,88,213,354]:self.assertIsNotNone(f.n.holding_context(self.raw(n)))
 def test_wrong_city_rejected(self):
  for n in [1,88,213,354]:
   d=self.raw(n);d['Ville']='Paris';self.assertIsNone(f.n.screen(d)[0])
 def test_wrong_location_rejected(self):
  for n in [1,88,213,354]:
   d=self.raw(n);d['Localisation']='Paris ; musée du Louvre';self.assertIsNone(f.n.screen(d)[0])
 def test_deposit_rejected(self):
  d=self.raw(213);d['Lieu_de_depot']='dépôt';self.assertIsNone(f.n.screen(d)[0])
 def test_missing_object_rejected(self):
  d=self.raw(213);d['MANQUANT']='oui';self.assertIsNone(f.n.screen(d)[0])
 def test_vendome_other_museum_rejected(self):
  d=self.raw(88);d['Statut_juridique']='propriété de la collectivité locale;Autun;musée Rolin';self.assertIsNone(f.n.screen(d)[0])
 def test_vendome_exact_owner_label_preserved(self):
  d=self.raw(88);original=copy.deepcopy(d);self.assertIsNotNone(f.n.screen(d)[0]);self.assertEqual(d,original);self.assertIn('collectivité locale',d['Statut_juridique'])
 def test_beaune_dijon_owner_rejected(self):
  d=self.raw(1);d['Statut_juridique']='propriété de la commune;Dijon;musée des Beaux-Arts';self.assertIsNone(f.n.screen(d)[0])
 def test_beaune_louvre_deposit_rejected(self):
  d=self.raw(1);d['Statut_juridique']="propriété de l'Etat;musée du Louvre";self.assertIsNone(f.n.screen(d)[0])
 def test_photo_physical_process(self):
  v,_=f.n.screen(self.raw(318));self.assertEqual(v['facts']['work_type'],'photograph');self.assertIn('albuminé',v['facts']['medium'])
 def test_photo_not_subject_sculpture(self):
  d=self.raw(318);self.assertIn('Etex',d['Description']);self.assertEqual(f.n.screen(d)[0]['facts']['work_type'],'photograph')
 def test_no_photographic_support_rejected(self):
  d=self.raw(213);d['Materiaux_techniques']='papier';self.assertIsNone(f.n.screen(d)[0])
 def test_digital_image_not_physical_print(self):
  d=self.raw(213);d['Materiaux_techniques']='fichier numérique';d['Description']='Photographie numérique de la sculpture';self.assertIsNone(f.n.screen(d)[0])
 def test_modern_reprint_rejected(self):
  d=self.raw(213);d['Description']+=' ; tirage moderne de 2001';self.assertIsNone(f.n.screen(d)[0])
 def test_posthumous_reprint_rejected(self):
  d=self.raw(213);d['Historique']='Retirage posthume';self.assertIsNone(f.n.screen(d)[0])
 def test_mixed_frame_rejected_at_selector_when_explicit_form(self):
  d=self.raw(213);d['Denomination']='cadre';self.assertIsNone(f.n.screen(d)[0])
 def test_mixed_manuscript_photo_rejected(self):
  d=self.raw(213);d['Domaine']='photographie;manuscrit';self.assertIsNone(f.n.screen(d)[0])
 def test_subject_date_not_creation(self):
  d=self.raw(213);d['Millesime_de_creation']='';d['Periode_de_creation']='';d['Date_sujet_represente']='1871';self.assertIsNone(f.n.screen(d)[0])
 def test_acquisition_not_creation(self):
  d=self.raw(213);d['Millesime_de_creation']='';d['Periode_de_creation']='';d['Date_d_acquisition']='1950';self.assertIsNone(f.n.screen(d)[0])
 def test_post1970_photo_rejected(self):
  d=self.raw(213);d['Millesime_de_creation']='1971';d['Auteur']='anonyme';d['Periode_de_creation']='20e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_pastel_requires_domain_and_medium(self):
  d=self.raw(354);self.assertEqual(f.n.screen(d)[0]['facts']['work_type'],'drawing');d['Materiaux_techniques']='papier';self.assertIsNone(f.n.screen(d)[0])
 def test_circa_range_no_invented_tolerance(self):
  v,_=f.n.screen(self.raw(354));self.assertEqual(v['facts']['date_display'],'1854-1860 (vers)');self.assertEqual((v['facts']['first'],v['facts']['last']),(1851,1900))
 def test_circa_without_separate_period_held(self):
  d=self.raw(354);d['Periode_de_creation']='';self.assertIsNone(f.n.screen(d)[0])
 def test_circa_crossing_cutoff_held(self):
  d=self.raw(354);d['Auteur']='anonyme';d['Millesime_de_creation']='1968-1972 (vers)';d['Periode_de_creation']='2e moitié 20e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_explicit_between_interval(self):
  v,_=f.n.screen(self.raw(214));self.assertEqual((v['facts']['first'],v['facts']['last']),(1923,1926));self.assertEqual(v['facts']['date_display'],'1923 entre,1926 et')
 def test_reversed_between_rejected(self):
  d=self.raw(214);d['Millesime_de_creation']='1926 entre,1923 et';self.assertIsNone(f.n.screen(d)[0])
 def test_between_period_conflict_rejected(self):
  d=self.raw(214);d['Periode_de_creation']='1er quart 20e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_compound_period_unknown_not_dropped(self):
  d=self.raw(92);d['Periode_de_creation']='18e siècle;inconnu';self.assertIsNone(f.n.screen(d)[0])
 def test_source_fields_unchanged(self):
  for n in [1,88,92,213,214,216,318,354]:
   d=self.raw(n);original=copy.deepcopy(d);self.assertIsNotNone(f.n.screen(d)[0]);self.assertEqual(d,original)
 def test_bad_response_or_hash_rejected(self):
  x=f.m.load(f.checked(self.by[1]['source_reference']))
  for key,value in [('status',429),('sha256','0'*64)]:
   y=copy.deepcopy(x);y['receipt'][key]=value
   with self.assertRaises(AssertionError):f.body(y)
if __name__=='__main__':unittest.main()
