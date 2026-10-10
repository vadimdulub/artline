"""Offline destination, eligibility and immutable-source guards; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-twelfth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
class Context(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.by={r['number']:r for r in f.m.load(f.RUN/'native-candidates-001.json.gz')['rows']}
 def raw(self,n):return copy.deepcopy(self.by[n]['facts']['source_fields'])
 def test_five_exact_contexts_pass(self):
  for n in [2,68,131,201,232]:self.assertIsNotNone(f.n.screen(self.raw(n))[0])
 def test_wrong_city_rejected(self):
  for n in [2,68,131,201,232]:
   d=self.raw(n);d['Ville']='Paris';self.assertIsNone(f.n.screen(d)[0])
 def test_wrong_museum_rejected(self):
  for n in [2,68,131,201,232]:
   d=self.raw(n);d['Localisation']='Paris ; musée du Louvre';self.assertIsNone(f.n.screen(d)[0])
 def test_wrong_code_rejected(self):
  d=self.raw(68);d['Code_Museofile']='M0550';self.assertIsNone(f.n.screen(d)[0])
 def test_deposit_excluded(self):
  d=self.raw(68);d['Lieu_de_depot']='dépôt';self.assertIsNone(f.n.screen(d)[0])
 def test_missing_object_excluded(self):
  d=self.raw(232);d['MANQUANT']='oui';self.assertIsNone(f.n.screen(d)[0])
 def test_state_owner_excluded(self):
  d=self.raw(2);d['Statut_juridique']="propriété de l'Etat;Sens;musée municipal";self.assertIsNone(f.n.screen(d)[0])
 def test_rodez_fenaille_distinct(self):
  d=self.raw(131);d['Statut_juridique']='propriété de la commune;Rodez;musée Fenaille';self.assertIsNone(f.n.screen(d)[0])
 def test_senlecq_pontoise_distinct(self):
  d=self.raw(68);d['Statut_juridique']="propriété de la commune;Pontoise;musée d'art et d'histoire Louis Senlecq";self.assertIsNone(f.n.screen(d)[0])
 def test_sens_society_excluded(self):
  d=self.raw(2);d['Statut_juridique']='propriété privée;Sens;société archéologique';self.assertIsNone(f.n.screen(d)[0])
 def test_lavaur_historical_owner_preserved(self):
  d=self.raw(201);d['Statut_juridique']='propriété de la collectivité locale;Lavaur;musée du pays vaurais';original=copy.deepcopy(d);self.assertIsNotNone(f.n.screen(d)[0]);self.assertEqual(d,original)
 def test_acquisition_never_supplies_missing_creation(self):
  d=self.raw(201);d['Millesime_de_creation']='';d['Periode_de_creation']='';d['Date_d_acquisition']='1950';self.assertIsNone(f.n.screen(d)[0])
 def test_subject_never_supplies_missing_creation(self):
  d=self.raw(232);d['Millesime_de_creation']='';d['Periode_de_creation']='';d['Date_sujet_represente']='1848';self.assertIsNone(f.n.screen(d)[0])
 def test_post_cutoff_creation_excluded(self):
  d=self.raw(68);d['Millesime_de_creation']='1971';d['Periode_de_creation']='20e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_unknown_period_component_excluded(self):
  d=self.raw(224);d['Periode_de_creation']='14e siècle;inconnu';self.assertIsNone(f.n.screen(d)[0])
 def test_compound_medieval_period_preserved(self):
  v,_=f.n.screen(self.raw(224));self.assertEqual((v['facts']['first'],v['facts']['last']),(1376,1425))
 def test_circa_without_independent_period_excluded(self):
  d=self.raw(64);d['Periode_de_creation']='';d['Millesime_de_creation']='1836 (vers)';self.assertIsNone(f.n.screen(d)[0])
 def test_circa_crossing_cutoff_excluded(self):
  d=self.raw(64);d['Auteur']='anonyme';d['Periode_de_creation']='2e moitié 20e siècle';d['Millesime_de_creation']='1968-1972 (vers)';self.assertIsNone(f.n.screen(d)[0])
 def test_matrix_not_print(self):
  d=self.raw(232);d['Denomination']='matrice';self.assertIsNone(f.n.screen(d)[0])
 def test_album_not_individual_print(self):
  d=self.raw(232);d['Historique']='album';self.assertIsNone(f.n.screen(d)[0])
 def test_source_input_unmodified(self):
  for n in [2,64,68,93,131,144,201,224,232,267]:
   d=self.raw(n);original=copy.deepcopy(d);self.assertIsNotNone(f.n.screen(d)[0]);self.assertEqual(d,original)
 def test_bad_status_or_hash_rejected(self):
  x=f.m.load(f.checked(self.by[2]['source_reference']))
  for key,value in [('status',429),('sha256','0'*64)]:
   y=copy.deepcopy(x);y['receipt'][key]=value
   with self.assertRaises(AssertionError):f.body(y)
if __name__=='__main__':unittest.main()
