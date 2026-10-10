"""Offline physical-object, date and exact-museum guards, using saved source records."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-thirteenth-native-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class Context(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.by={r['raw_source_record']['Reference']:r['raw_source_record'] for r in n.m.load(n.DISCOVERY)['rows']}
 def raw(self,sid):return copy.deepcopy(self.by[sid])
 def test_five_destinations_reconciled(self):
  for sid in ['M0537017569','10980003408','06340036167','000DE014607','07840001255']:self.assertIsNotNone(n.holding_context(self.raw(sid)))
 def test_city_mismatch_excluded(self):
  d=self.raw('06340036167');d['Ville']='Paris';self.assertIsNone(n.screen(d)[0])
 def test_generic_municipal_destination_requires_exact_code(self):
  d=self.raw('000DE014607');d['Code_Museofile']='M0784';self.assertIsNone(n.screen(d)[0])
 def test_private_imagerie_not_municipal_museum(self):
  d=self.raw('M0537017569');d['Statut_juridique']="propriété privée;Epinal;musée de l'image";self.assertIsNone(n.screen(d)[0])
 def test_epinal_departmental_deposit_distinct(self):
  d=self.raw('M0537017569');d['Statut_juridique']="propriété du département;Vosges;musée de l'image";self.assertIsNone(n.screen(d)[0])
 def test_state_deposit_excluded(self):
  d=self.raw('06340036167');d['Lieu_de_depot']='dépôt';self.assertIsNone(n.screen(d)[0])
 def test_missing_object_excluded(self):
  d=self.raw('10980003408');d['MANQUANT']='oui';self.assertIsNone(n.screen(d)[0])
 def test_encoding_anomaly_preserved(self):
  d=copy.deepcopy(next(d for d in self.by.values() if d['Code_Museofile']=='M0634' and 'u2013' in d['Statut_juridique']));before=copy.deepcopy(d);self.assertIsNotNone(n.holding_context(d));self.assertEqual(d,before)
 def test_original_drawing_component_supported(self):
  d=self.raw('10980003408');v,_=n.screen(d);self.assertEqual(v['facts']['work_type'],'drawing');self.assertEqual(d['Denomination'],"élément d'ensemble");self.assertEqual(d['Materiaux_techniques'],'')
 def test_drawing_requires_physical_support(self):
  d=self.raw('10980003408');d['Description']='image numérique';self.assertIsNone(n.screen(d)[0])
 def test_drawing_requires_physical_dimensions(self):
  d=self.raw('10980003408');d['Mesures']='';self.assertIsNone(n.screen(d)[0])
 def test_bound_drawing_unit_held(self):
  d=self.raw('10980003408');d['Description']='encre sur papier collé sur une page';self.assertIsNone(n.screen(d)[0])
 def test_mixed_collage_held(self):self.assertIsNone(n.screen(self.raw('10980002928'))[0])
 def test_sculpture_missing_form_remains_literal(self):
  d=self.raw('07840001255');v,_=n.screen(d);self.assertEqual(v['facts']['work_type'],'sculpture');self.assertEqual(d['Denomination'],'')
 def test_sculpture_requires_three_dimensional_material(self):
  d=self.raw('07840001255');d['Materiaux_techniques']='papier';d['Description']='Photographie du bronze';self.assertIsNone(n.screen(d)[0])
 def test_pedestal_unit_held(self):self.assertIsNone(n.screen(self.raw('06340036166'))[0])
 def test_medal_domain_not_inferred_sculpture(self):
  d=self.raw('06340036167');d['Domaine']='numismatique';d['Denomination']='médaille';self.assertIsNone(n.screen(d)[0])
 def test_cast_after_cutoff_excluded(self):
  d=self.raw('06340036167');d['Auteur']='anonyme';d['Millesime_de_creation']='1980';d['Periode_de_creation']='4e quart 20e siècle';self.assertIsNone(n.screen(d)[0])
 def test_cast_conflicting_with_creator_life_held(self):
  d=self.raw('06340036167');d['Millesime_de_creation']='1965';d['Periode_de_creation']='3e quart 20e siècle';self.assertIsNone(n.screen(d)[0])
 def test_colon_circa_keeps_broad_period(self):
  d=self.raw('06340036167');v,_=n.screen(d);self.assertEqual(v['facts']['date_display'],d['Millesime_de_creation']);self.assertEqual((v['facts']['first'],v['facts']['last']),(1926,1950))
 def test_circa_period_crossing_cutoff_held(self):
  d=self.raw('06340036167');d['Millesime_de_creation']='1965 : vers';d['Periode_de_creation']='3e quart 20e siècle';self.assertIsNone(n.screen(d)[0])
 def test_circa_without_period_held(self):
  d=self.raw('06340036167');d['Periode_de_creation']='';self.assertIsNone(n.screen(d)[0])
 def test_exact_year_period_conflict_held(self):self.assertIsNone(n.screen(self.raw('06340036171'))[0])
 def test_range_period_conflict_held(self):self.assertIsNone(n.screen(self.raw('10980003770'))[0])
 def test_acquisition_not_creation(self):
  d=self.raw('06340036167');d['Millesime_de_creation']='';d['Periode_de_creation']='';d['Date_d_acquisition']='1960';self.assertIsNone(n.screen(d)[0])
 def test_source_period_component_unknown_held(self):
  d=self.raw('07840001255');d['Periode_de_creation']='1ère moitié 20e siècle;inconnu';self.assertIsNone(n.screen(d)[0])
 def test_1970_boundary_supported(self):
  v,_=n.screen(self.raw('000DE014704'));self.assertEqual(v['facts']['year'],1970)
 def test_1971_boundary_excluded(self):
  d=self.raw('000DE014704');d['Millesime_de_creation']='1971';self.assertIsNone(n.screen(d)[0])
 def test_source_fields_never_changed(self):
  for sid in ['M0537017569','10980003408','06340036167','000DE014607','07840001255']:
   d=self.raw(sid);before=copy.deepcopy(d);self.assertIsNotNone(n.screen(d)[0]);self.assertEqual(d,before)
if __name__=='__main__':unittest.main()
