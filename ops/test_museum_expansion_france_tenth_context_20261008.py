"""Offline guards for literal date formats and exact museum contexts; no DB fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-tenth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
class Context(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=f.m.load(f.RUN/'native-candidates-001.json.gz')['rows'];cls.by={r['number']:r for r in cls.rows}
 def raw(self,n):return copy.deepcopy(self.by[n]['facts']['source_fields'])
 def test_exact_museum_contexts_pass(self):
  for n in [1,101,107,197,222]:self.assertIsNotNone(f.n.holding_context(self.raw(n)))
 def test_wrong_city_rejected(self):
  for n in [1,101,107,197,222]:
   d=self.raw(n);d['Ville']='Paris';self.assertIsNone(f.n.screen(d)[0])
 def test_wrong_location_rejected(self):
  for n in [1,101,107,197,222]:
   d=self.raw(n);d['Localisation']='Paris ; musée du Louvre';self.assertIsNone(f.n.screen(d)[0])
 def test_deposits_rejected(self):
  for n in [1,101,107,197,222]:
   d=self.raw(n);d['Lieu_de_depot']='dépôt';self.assertIsNone(f.n.screen(d)[0])
 def test_missing_objects_rejected(self):
  for n in [1,101,107,197,222]:
   d=self.raw(n);d['MANQUANT']='oui';self.assertIsNone(f.n.screen(d)[0])
 def test_bayonne_louvre_owner_rejected(self):
  d=self.raw(222);d['Statut_juridique']="propriété de l'Etat;legs;musée du Louvre département des Arts graphiques";self.assertIsNone(f.n.screen(d)[0])
 def test_belfort_other_municipality_rejected(self):
  d=self.raw(101);d['Statut_juridique']='propriété de la commune;Delle';self.assertIsNone(f.n.screen(d)[0])
 def test_belfort_hospital_rejected(self):
  d=self.raw(101);d['Statut_juridique']='propriété publique;Belfort;centre hospitalier';self.assertIsNone(f.n.screen(d)[0])
 def test_saint_denis_legion_venue_rejected(self):
  d=self.raw(107);d['Localisation']="Saint-Denis ; maison d'éducation de la Légion d'Honneur";self.assertIsNone(f.n.screen(d)[0])
 def test_strasbourg_other_collection_rejected(self):
  d=self.raw(1);d['Localisation']='Strasbourg ; musée des beaux-arts';self.assertIsNone(f.n.screen(d)[0])
 def test_structured_city_absence_does_not_invent_db_place(self):
  r=self.by[222];self.assertEqual(r['museum']['city'],'');self.assertEqual(r['facts']['source_fields']['Ville'],'Bayonne');self.assertTrue(f.m.load(f.checked(r['facts']['holding_context_reference']))['museums']['M0094']['database_city_unknown_preserved'])
 def test_circa_parentheses_preserved(self):
  d=self.raw(198);v,reason=f.n.screen(d);self.assertIsNone(reason);self.assertEqual(v['facts']['date_display'],'1859 (vers)');self.assertEqual((v['facts']['first'],v['facts']['last'],v['facts']['date_precision']),(1851,1875,'circa_range'))
 def test_circa_range_uses_separate_period(self):
  v,_=f.n.screen(self.raw(202));self.assertEqual(v['facts']['date_display'],'1854 - 1859 (vers)');self.assertEqual((v['facts']['first'],v['facts']['last']),(1851,1875))
 def test_circa_without_separate_period_held(self):
  d=self.raw(202);d['Periode_de_creation']='';self.assertIsNone(f.n.screen(d)[0])
 def test_circa_reversed_range_held(self):
  d=self.raw(202);d['Millesime_de_creation']='1859-1854 (vers)';self.assertIsNone(f.n.screen(d)[0])
 def test_circa_conflicting_period_held(self):
  d=self.raw(202);d['Periode_de_creation']='1er quart 19e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_circa_crossing_cutoff_held(self):
  d=self.raw(202);d['Millesime_de_creation']='1968-1972 (vers)';d['Periode_de_creation']='2e moitié 20e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_compound_period_keeps_full_extent(self):
  d=self.raw(224);v,_=f.n.screen(d);self.assertEqual((v['facts']['first'],v['facts']['last'],v['facts']['date_precision']),(1876,1925,'range'));self.assertEqual(v['facts']['date_display'],d['Periode_de_creation'])
 def test_unknown_component_cannot_be_dropped(self):
  d=self.raw(224);d['Periode_de_creation']='4e quart 19e siècle;inconnu';self.assertIsNone(f.n.screen(d)[0])
 def test_post1970_component_cannot_be_dropped(self):
  d=self.raw(224);d['Periode_de_creation']='4e quart 19e siècle;2e moitié 20e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_qualified_period_not_turned_certain(self):
  d=self.raw(224);d['Periode_de_creation']='4e quart 19e siècle ?;1er quart 20e siècle';self.assertIsNone(f.n.screen(d)[0])
 def test_doubtful_numeric_dates_not_ignored_for_period(self):
  d=self.raw(224);d['Millesime_de_creation']='1897 ?';self.assertIsNone(f.n.screen(d)[0])
 def test_acquisition_not_substituted_for_unknown_creation(self):
  d=self.raw(224);d['Millesime_de_creation']='';d['Periode_de_creation']='';d['Date_d_acquisition']='1950';self.assertIsNone(f.n.screen(d)[0])
 def test_source_fields_unchanged_by_screen(self):
  for n in [1,101,107,197,198,202,222,224]:
   d=self.raw(n);original=copy.deepcopy(d);self.assertIsNotNone(f.n.screen(d)[0]);self.assertEqual(d,original)
 def test_bad_response_or_hash_rejected(self):
  x=f.m.load(f.checked(self.by[1]['source_reference']))
  for key,value in [('status',429),('sha256','0'*64)]:
   y=copy.deepcopy(x);y['receipt'][key]=value
   with self.assertRaises(AssertionError):f.body(y)
if __name__=='__main__':unittest.main()
