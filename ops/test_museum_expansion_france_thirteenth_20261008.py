"""Offline physical identity and chronology safeguards; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-thirteenth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={v['number']:v for v in r.build()}
 def test_all_notices_decided(self):self.assertEqual(set(self.ds),set(range(1,621)));self.assertEqual((len(r.NOTES),len(r.HOLDS)),(571,49))
 def test_after_cutoff_signed_drawing_held(self):self.assertEqual(self.ds[9]['state'],'editorial_hold');self.assertIn('1978',self.ds[9]['facts']['source_fields']['Precisions_inscriptions'])
 def test_later_casts_held(self):
  for n in [38,69,78,93,94,98,105,124,314]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_sparse_existing_versions_held(self):
  for n in [40,117,485,497]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_duplicate_physical_unit_not_assumed(self):
  for n in [58,82,217,222,385,390,391,392,393,394]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_mold_not_finished_sculpture(self):self.assertEqual(self.ds[418]['state'],'editorial_hold');self.assertIn('moule',self.ds[418]['facts']['source_fields']['Description'])
 def test_album_and_multiple_sheet_uncertainty_held(self):
  for n in [253,490,552,553]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_bronze_cast_date_differs_from_model(self):
  d=self.ds[266];self.assertEqual((d['facts']['first'],d['facts']['last']),(1937,1937));self.assertEqual(d['facts']['source_fields']['Millesime_de_creation'],'1936');self.assertEqual(d['derived_fields']['physical_creation_date']['original']['first'],1936)
 def test_cast_date_requires_invoice_evidence(self):
  f=copy.deepcopy(self.ds[266]['facts']);f['source_fields']['Commentaires']='model made in 1936'
  with self.assertRaises(AssertionError):r.derive_date(f,266)
 def test_supposed_print_year_not_exact(self):
  f=self.ds[426]['facts'];self.assertEqual((f['first'],f['last'],f['date_precision']),(1826,1850,'range'));self.assertEqual(f['date_display'],'1837 (supposé)');self.assertEqual(f['source_fields']['Millesime_de_creation'],'1837')
 def test_supposition_requires_independent_period(self):
  f=copy.deepcopy(self.ds[426]['facts']);f['source_fields']['Periode_de_creation']='19e siècle'
  with self.assertRaises(AssertionError):r.derive_date(f,426)
 def test_unapproved_date_override_rejected(self):
  r.notes.DATE_OVERRIDES[501]=dict(r.notes.DATE_OVERRIDES[266])
  try:
   with self.assertRaises(AssertionError):r.derive_date(copy.deepcopy(self.ds[501]['facts']),501)
  finally:del r.notes.DATE_OVERRIDES[501]
 def test_biography_conflict_remains_explicit(self):
  for n in r.notes.FRANCOIS_NUMBERS:
   f=self.ds[n]['facts'];self.assertEqual(f['source_fields']['Auteur'],'François André (1931-2019)');self.assertIn('en conflit',f['creator_label']);self.assertNotIn('1931',f['creator_label']);self.assertIn('authority_reference',self.ds[n]['derived_fields']['qualified_creator_label'])
 def test_oil_work_keeps_raw_graphic_domain(self):
  f=self.ds[504]['facts'];self.assertEqual(f['work_type'],'painting');self.assertEqual(f['source_fields']['Domaine'],'dessin');self.assertIsNone(f['medium']);self.assertIn('huile',f['source_fields']['Description'])
 def test_mixed_drawing_collage_not_pure_ink(self):self.assertIn('collage',self.ds[520]['facts']['source_fields']['Description']);self.assertEqual(self.ds[520]['facts']['work_type'],'drawing')
 def test_drawings_not_printed_campaign_posters(self):
  for n in [503,519,523,527,535,547,588,618,619,620]:self.assertEqual(self.ds[n]['facts']['work_type'],'drawing')
 def test_before_dates_keep_unknown_lower(self):
  for n in range(608,618):
   f=self.ds[n]['facts'];self.assertIsNone(f['first']);self.assertEqual(f['date_precision'],'before');self.assertLessEqual(f['last'],1971)
 def test_totempole_object_not_project_date(self):
  for n in [559,561,563,564,565,567,569,570,571]:
   f=self.ds[n]['facts'];self.assertEqual(f['first'],1970);self.assertIn('1975',f['source_fields']['Historique'])
 def test_multi_scene_sheet_counted_once(self):
  for n in [563,595,596,598]:self.assertIn('Deux',self.ds[n]['facts']['source_fields']['Precisions_sujets_representes'])
 def test_recto_verso_remain_one_inventory(self):
  for n in [517,573,575,576,577,579]:self.assertIn('verso',str(self.ds[n]['facts']['source_fields']).lower())
 def test_distinct_electric_circus_designs(self):
  ds=[self.ds[n]['facts'] for n in range(547,552)];self.assertEqual(len({v['inventory'] for v in ds}),5);self.assertEqual(len({v['source_fields']['Precisions_sujets_representes'] for v in ds}),5)
 def test_distinct_ski_designs(self):
  a,b=(self.ds[n]['facts'] for n in [519,588]);self.assertNotEqual(a['dimensions_text'],b['dimensions_text']);self.assertNotEqual(a['source_fields']['Precisions_sujets_representes'],b['source_fields']['Precisions_sujets_representes'])
 def test_distinct_materials_bronze_and_plaster(self):
  a,b=(self.ds[n]['facts'] for n in [263,289]);self.assertIn('Bronze',a['source_fields']['Description']);self.assertIn('plâtre',b['source_fields']['Description'].lower())
 def test_flattened_inventory_collision_not_merge(self):
  a,b=(self.ds[n]['facts'] for n in [61,119]);self.assertNotEqual(a['inventory'],b['inventory']);self.assertNotEqual(a['medium'],b['medium']);self.assertNotEqual(a['dimensions_text'],b['dimensions_text'])
 def test_creator_semicolon_inside_roles(self):self.assertEqual(len(r.identity.creator_labels("A (d'après;peintre) ; B (graveur)")),2)
 def test_translated_and_secondary_title_search(self):
  self.assertIn('Victor Hugo',r.identity.title_forms('Portrait en buste de Victor Hugo ; Victor Hugo'));self.assertIn('The Garden of Love',r.identity.title_forms("Jardin d'amour"))
 def test_maker_variants_and_given_names_not_ignored(self):
  for n,term in [(245,'raffet'),(501,'andre'),(502,'maurice'),(497,'subleyras')]:self.assertIn(term,self.ds[n]['comparison']['creator_terms'])
 def test_no_exact_source_duplicates(self):
  for d in self.ds.values():
   for k in ['native_url_hits','native_scheme_hits','source_record_hits']:self.assertFalse(d['comparison'][k])
 def test_raw_source_fields_never_rewritten(self):
  raw={v['number']:v for v in r.m.load(r.CANDIDATES)['rows']}
  for n,d in self.ds.items():self.assertEqual(d['facts']['source_fields'],raw[n]['facts']['source_fields'])
 def test_all_selected_dates_eligible_without_invented_years(self):
  for n in r.NOTES:
   f=self.ds[n]['facts'];self.assertTrue((f['first'] is None and f['date_precision']=='before' and f['last']<=1971) or (f['first'] is not None and f['first']<=f['last']<=1970))
if __name__=='__main__':unittest.main()
