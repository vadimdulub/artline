"""Offline real-source safeguards; no database fixtures or test databases."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-fourth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={d['number']:d for d in r.build()}
 def test_source_attributions_are_retained(self):
  for n in [5,7,10,26,33,34,48,49,55,111,112,213]:
   d=self.ds[n];v=d['derived_fields']['qualified_creator_label'];self.assertEqual(v['literal_evidence'],d['facts']['source_fields'][v['source_field']]);self.assertEqual(v['derived'],d['facts']['creator_label']);self.assertEqual(v['original'],d['facts']['source_fields']['Auteur'])
 def test_alternative_makers_are_not_coauthors(self):
  for n in [5,26,33,48,213]:self.assertIn(' ou ',self.ds[n]['facts']['creator_label'])
 def test_model_makers_are_marked_after(self):
  for n in [34,55]:self.assertIn('d’après',self.ds[n]['facts']['creator_label'])
 def test_factory_attribution_not_promoted(self):
  f=self.ds[111]['facts'];self.assertIn('faïencerie, attribué à',f['creator_label']);self.assertIn('absence de marques',f['source_fields']['Precisions_sur_l_auteur'])
 def test_uncertain_signature_not_named_authority(self):
  self.assertIn('Fély (?) / Félix (?)',self.ds[112]['facts']['creator_label'])
 def test_factory_and_firstnamefirst_surnames_scoped(self):
  for n,term in [(20,'robj'),(24,'olerys'),(27,'fischetti'),(33,'savy'),(36,'johnston'),(38,'rateau'),(43,'vieillard'),(50,'artus'),(50,'lauriol'),(55,'barbieri'),(59,'denon'),(209,'baudouin')]:self.assertIn(term,self.ds[n]['comparison']['creator_terms'])
 def test_vitre_missing_city_does_not_invent_city(self):
  for n in range(141,191):
   d=self.ds[n];self.assertFalse(d['museum']['city']);self.assertEqual(d['facts']['source_fields']['Ville'],'Vitré');self.assertIn('database_city_unknown_source_city_explicit',d['review_flags'])
 def test_vitre_identity_rejects_other_museum(self):
  row=self.ds[141];item=copy.deepcopy(row['index']);item['museum']['name']='musée du château — Autre ville'
  with self.assertRaises(AssertionError):r.f.parse(item,r.checked(row['source_reference']))
 def test_unknown_creator_stays_unknown(self):
  for n in [1,104,121,191,219]:self.assertIsNone(self.ds[n]['facts']['creator_label'])
 def test_anonymous_denon_group_is_not_attributed(self):
  self.assertEqual(self.ds[59]['facts']['creator_label'],'anonyme')
 def test_missing_dimensions_not_invented(self):
  for n in [104,113]:self.assertIsNone(self.ds[n]['facts']['dimensions_text'])
 def test_conflicting_dates_held(self):
  for n in [8,23,61,154,206]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_known_duplicates_held(self):
  for n in [3,47,57,108,122,162,184,192,220,212,226,230,240]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_near_identical_service_pieces_not_multiplied(self):
  for n in [224,228,231,233,236,238]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_two_inventory_physical_group_held(self):
  d=self.ds[179];self.assertIn('INV 1910 ; INV 1911',d['facts']['inventory']);self.assertEqual(d['state'],'editorial_hold')
 def test_single_sheet_multiple_figures_and_rectoverso(self):
  for n in [4,5,63,80,82,84,85,86,94]:
   d=self.ds[n];self.assertEqual(d['state'],'approved_review_only_addition');self.assertEqual(sum(x['source_id']==d['source_id'] for x in self.ds.values()),1)
 def test_design_and_ceramic_distinguished(self):
  self.assertEqual((self.ds[9]['facts']['work_type'],self.ds[10]['facts']['work_type']),('ceramic','drawing'))
 def test_plate_requires_ceramic_medium(self):
  d=copy.deepcopy(self.ds[9]['facts']['source_fields']);d['Materiaux_techniques']='papier';self.assertIsNone(r.f.n.screen(d)[0])
 def test_group_or_album_rejected(self):
  d=copy.deepcopy(self.ds[145]['facts']['source_fields']);d['Description']='album de dessins';self.assertIsNone(r.f.n.screen(d)[0])
 def test_before_date_keeps_unknown_lower_bound(self):
  for n,last in [(56,1803),(102,1803),(103,1793),(153,1905),(155,1932),(156,1738)]:
   f=self.ds[n]['facts'];self.assertEqual((f['first'],f['last'],f['date_precision']),(None,last,'before'))
 def test_provenance_year_not_creation(self):
  f=self.ds[234]['facts'];self.assertEqual(f['first'],1882);self.assertIn('1939',f['source_fields']['Precisions_inscriptions'])
 def test_copy_not_original_deposit(self):
  f=self.ds[149]['facts'];self.assertEqual(f['first'],1905);self.assertIn("d'après",f['creator_label']);self.assertIn('reprise en 1905',f['source_fields']['Historique'])
 def test_cross_collection_inventory_collision_explicit(self):
  d=self.ds[229];hits={a['id']:a for a in d['comparison']['inventory_hits'] if a['relevant']};self.assertEqual(set(hits),r.notes.INVENTORY_EXCEPTIONS[229]);hit=next(iter(hits.values()));self.assertIn('pastel',hit['medium_text']);self.assertEqual(d['facts']['work_type'],'ceramic');self.assertEqual(d['state'],'approved_review_only_addition')
 def test_literal_creator_whitespace_kept_in_evidence(self):
  f=self.ds[188]['facts'];self.assertTrue(f['source_fields']['Auteur'].endswith(' '));self.assertEqual(f['creator_label'],f['source_fields']['Auteur'].strip())
 def test_unknown_inventory_is_not_a_duplicate_identity(self):
  for n in [155,158,161,163,183]:self.assertEqual(self.ds[n]['facts']['inventory'],'SN')
  self.assertNotEqual(self.ds[161]['facts']['title'],self.ds[183]['facts']['title']);self.assertNotEqual(self.ds[161]['facts']['dimensions_text'],self.ds[183]['facts']['dimensions_text'])
 def test_bad_http_and_hash_fail(self):
  x=r.m.load(r.checked(self.ds[1]['source_reference']))
  for key,value in [('status',429),('sha256','0'*64)]:
   bad=copy.deepcopy(x);bad['receipt'][key]=value
   with self.assertRaises(AssertionError):r.f.body(bad)
 def test_indexed_comparisons_equal_independent_scan(self):
  s=r.m.load(r.IDENTITY)['state']
  for n in [20,24,27,33,36,50,55,59,106,209,229]:
   d=self.ds[n];f=d['facts'];c=d['comparison'];ts=set(r.identity.terms(f));aids={a['id'] for a in s['artists'] if r.identity.i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in s['aliases'] if r.identity.i.tokens(a['alias'])&ts};pool={a['id'] for a in s['artworks'] if r.identity.i.tokens(a['unlinked_creator_label'])&ts}|{v['artwork_id'] for v in s['links'] if v['artist_id'] in aids};self.assertEqual(pool,set(c['creator_pool_ids']))
if __name__=='__main__':unittest.main()
