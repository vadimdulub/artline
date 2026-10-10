"""Offline adversarial holding/date checks on captured records; no DB fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-france-ninth-facts-20261008.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
class Context(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=f.m.load(f.RUN/'native-candidates-001.json.gz')['rows'];cls.by={r['number']:r for r in cls.rows}
 def raw(self,n):return copy.deepcopy(self.by[n]['facts']['source_fields'])
 def test_actual_four_contexts_pass(self):
  for n in [31,116,176,261]:self.assertIsNotNone(f.n.holding_context(self.raw(n)))
 def test_state_deposit_cannot_use_municipal_alias(self):
  q=self.raw(31);q['Statut_juridique']="propriété de l'Etat;achat;musée national des châteaux de Versailles et de Trianon";self.assertIsNone(f.n.screen(q)[0])
 def test_deposit_flag_rejected(self):
  for n in [31,116,176,261]:
   q=self.raw(n);q['Lieu_de_depot']='Paris;musée du Louvre';self.assertIsNone(f.n.screen(q)[0])
 def test_missing_object_rejected(self):
  for n in [31,116,176,261]:
   q=self.raw(n);q['MANQUANT']='oui';self.assertIsNone(f.n.screen(q)[0])
 def test_wrong_city_rejected(self):
  for n in [31,116,176,261]:
   q=self.raw(n);q['Ville']='La Tronche';self.assertIsNone(f.n.screen(q)[0])
 def test_other_hebert_collection_rejected(self):
  q=self.raw(261);q['Localisation']='La Tronche ; musée Hébert';self.assertIsNone(f.n.screen(q)[0])
 def test_hebert_louvre_owner_rejected(self):
  q=self.raw(261);q['Statut_juridique']="propriété de l'Etat;donation;musée du Louvre département des Peintures";self.assertIsNone(f.n.screen(q)[0])
 def test_chalons_other_venues_rejected(self):
  for venue in ['musée Garinet','musée du cloître de Notre-Dame-en-Vaux','Musées municipaux']:
   q=self.raw(31);q['Localisation']='Châlons-en-Champagne ; '+venue;self.assertIsNone(f.n.screen(q)[0])
 def test_chalons_bishopric_rejected(self):
  q=self.raw(31);q['Statut_juridique']='propriété de la commune;Châlons-en-Champagne;évêché';self.assertIsNone(f.n.screen(q)[0])
 def test_metz_owner_not_generalized(self):
  q=self.raw(176);q['Statut_juridique']="propriété de la communauté d'agglomération;achat;Bernay;musée municipal";self.assertIsNone(f.n.screen(q)[0])
 def test_metz_other_institution_rejected(self):
  q=self.raw(116);q['Statut_juridique']="propriété de la communauté d'agglomération;achat;Metz;Centre Pompidou";self.assertIsNone(f.n.screen(q)[0])
 def test_original_legal_and_location_fields_unchanged(self):
  for n in [31,116,176,261]:
   q=self.raw(n);before=copy.deepcopy(q);self.assertIsNotNone(f.n.screen(q)[0]);self.assertEqual(q,before);self.assertEqual(self.by[n]['facts']['credit_line'],q['Statut_juridique'])
 def test_post1970_rejected(self):
  q=self.raw(116);q['Millesime_de_creation']='1971';q['Periode_de_creation']='4e quart 20e siècle';self.assertIsNone(f.n.screen(q)[0])
 def test_crossing1970_rejected(self):
  q=self.raw(116);q['Millesime_de_creation']='1969-1972';q['Periode_de_creation']='2e moitié 20e siècle';self.assertIsNone(f.n.screen(q)[0])
 def test_unknown_year_not_filled(self):
  q=self.raw(116);q['Millesime_de_creation']='';q['Periode_de_creation']='';self.assertIsNone(f.n.screen(q)[0])
 def test_compound_period_not_collapsed(self):
  q=self.raw(261);q['Millesime_de_creation']='';q['Periode_de_creation']='2e moitié 19e siècle;1er quart 20e siècle';self.assertIsNone(f.n.screen(q)[0])
 def test_private_owner_rejected(self):
  q=self.raw(176);q['Statut_juridique']='propriété privée;Bernay;musée municipal';self.assertIsNone(f.n.screen(q)[0])
 def test_bad_response_or_hash_rejected(self):
  x=f.m.load(f.checked(self.by[1]['source_reference']))
  for key,value in [('status',429),('sha256','0'*64)]:
   q=copy.deepcopy(x);q['receipt'][key]=value
   with self.assertRaises(AssertionError):f.body(q)
if __name__=='__main__':unittest.main()
