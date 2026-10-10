"""Offline safeguards against captured real evidence; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-seventh-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={d['number']:d for d in r.build()}
 def test_wrong_museum_fails(self):
  d=self.ds[1];q=copy.deepcopy(d['index']);q['museum']['city']='Auxerre'
  with self.assertRaises(AssertionError):r.f.parse(q,r.checked(d['source_reference']))
 def test_unknown_city_stays_unknown(self):
  d=self.ds[1];self.assertFalse(d['museum']['city']);self.assertEqual(d['facts']['source_fields']['Ville'],'Saint-Cloud');self.assertIn('database_city_unknown_source_city_explicit',d['review_flags'])
 def test_unknown_city_exception_rejects_different_museum(self):
  d=self.ds[1];q=copy.deepcopy(d['index']);q['museum']['id']='01d9a277-e513-490d-89f4-2bf46decd44d'
  with self.assertRaises(AssertionError):r.f.parse(q,r.checked(d['source_reference']))
 def test_auxerre_abbreviation_has_primary_context(self):
  f=self.ds[124]['facts'];self.assertIsNotNone(r.f.n.auxerre_context(f['source_fields']));self.assertNotIn('Saint-Germain',f['source_fields']['Localisation']);self.assertIn('Saint-Germain',f['source_fields']['Nom_officiel_musee'])
 def test_auxerre_context_rejects_wrong_code(self):
  d=copy.deepcopy(self.ds[124]['facts']['source_fields']);d['Code_Museofile']='M0185';self.assertIsNone(r.f.n.auxerre_context(d))
 def test_auxerre_context_rejects_wrong_location(self):
  d=copy.deepcopy(self.ds[124]['facts']['source_fields']);d['Localisation']='Paris ; musée du Louvre';self.assertIsNone(r.f.n.auxerre_context(d))
 def test_auxerre_context_rejects_deposit(self):
  d=copy.deepcopy(self.ds[124]['facts']['source_fields']);d['Lieu_de_depot']='Paris';self.assertIsNone(r.f.n.auxerre_context(d))
 def test_auxerre_context_rejects_missing_object(self):
  d=copy.deepcopy(self.ds[124]['facts']['source_fields']);d['MANQUANT']='oui';self.assertIsNone(r.f.n.auxerre_context(d))
 def test_auxerre_context_rejects_private_ownership(self):
  d=copy.deepcopy(self.ds[124]['facts']['source_fields']);d['Statut_juridique']='propriété privée;Auxerre;musée d’Art et d’Histoire';self.assertIsNone(r.f.n.auxerre_context(d))
 def test_source_ownership_labels_are_literal(self):
  for n in [25,50,53,101,125,137]:self.assertEqual(self.ds[n]['facts']['credit_line'],self.ds[n]['facts']['source_fields']['Statut_juridique'])
 def test_post1970_creation_rejected(self):
  d=copy.deepcopy(self.ds[42]['facts']['source_fields']);d['Millesime_de_creation']='1971';d['Periode_de_creation']='4e quart 20e siècle';self.assertIsNone(r.f.n.screen(d)[0])
 def test_cutoff_crossing_range_rejected(self):
  d=copy.deepcopy(self.ds[42]['facts']['source_fields']);d['Millesime_de_creation']='1969-1972';d['Periode_de_creation']='2e moitié 20e siècle';self.assertIsNone(r.f.n.screen(d)[0])
 def test_album_requires_review(self):
  d=copy.deepcopy(self.ds[31]['facts']['source_fields']);d['Denomination']='album';self.assertIsNone(r.f.n.screen(d)[0])
 def test_bad_response_or_hash_fails(self):
  x=r.m.load(r.checked(self.ds[1]['source_reference']))
  for k,v in [('status',429),('sha256','0'*64)]:
   y=copy.deepcopy(x);y['receipt'][k]=v
   with self.assertRaises(AssertionError):r.f.body(y)
 def test_old_new_catalogue_ids_do_not_duplicate_artworks(self):
  for n,aid in [(41,'1028a60e-f81f-4f36-b180-14cc08aa0c9e'),(46,'f82e9d35-5da8-4fcc-98a1-f2be630ee4e0'),(48,'c3402982-f4cb-4ed6-bb49-a9c75766922d'),(54,'38d5c967-641e-4816-be3b-b001c2006a9f')]:
   self.assertEqual(self.ds[n]['state'],'editorial_hold');self.assertIn(aid,{a['id'] for a in self.ds[n]['comparison']['inventory_hits']})
 def test_depicted_year_does_not_date_object(self):
  self.assertEqual(self.ds[24]['facts']['first'],1874);self.assertIn('1852',self.ds[24]['facts']['title']);self.assertIsNone(self.ds[2]['facts']['first']);self.assertEqual(self.ds[2]['facts']['last'],1952)
 def test_acquisition_year_does_not_date_object(self):
  f=self.ds[86]['facts'];self.assertEqual(f['inventory'],'1971.1.6');self.assertLess(f['last'],1971)
 def test_ceramic_edition_numbers_do_not_multiply_works(self):
  for n,edition in [(28,'20/30'),(42,'27/40')]:
   f=self.ds[n]['facts'];self.assertEqual(f['work_type'],'ceramic');self.assertIn(edition,f['source_fields']['Precisions_inscriptions']);self.assertEqual(sum(d['source_id']==f['source_id'] for d in self.ds.values()),1)
 def test_galanis_recto_verso_one_sheet(self):
  f=self.ds[31]['facts'];self.assertIn('Galanis',f['source_fields']['Precisions_inscriptions']);self.assertIn('verso',f['source_fields']['Precisions_sujets_representes']);self.assertEqual(f['work_type'],'drawing')
 def test_genin_same_title_distinct_dated_sheets(self):
  a,b=self.ds[32]['facts'],self.ds[44]['facts'];self.assertEqual((a['first'],b['first']),(1938,1931));self.assertNotEqual(a['inventory'],b['inventory']);self.assertNotEqual(a['dimensions_text'],b['dimensions_text'])
 def test_genpaul_same_sitter_distinct_physical_drawings(self):
  a,b=self.ds[45]['facts'],self.ds[47]['facts'];self.assertEqual((a['first'],b['first']),(1958,1952));self.assertIn('crayon',a['medium']);self.assertIn('encre',b['medium'])
 def test_blank_makers_not_inferred_from_signatures(self):
  for n in [25,50,53]:self.assertIsNone(self.ds[n]['facts']['creator_label']);self.assertTrue(self.ds[n]['facts']['source_fields']['Precisions_inscriptions'])
 def test_durand_name_has_literal_note_derivation(self):
  d=self.ds[123];self.assertEqual(d['facts']['creator_label'],'DURAND Charles');self.assertIsNone(d['derived_fields']['qualified_creator_label']['original']);self.assertEqual(d['derived_fields']['qualified_creator_label']['literal_evidence'],'DURAND Charles')
 def test_workshop_and_copy_qualifications_preserved(self):
  for n in [120,121,122,147,148]:self.assertEqual(self.ds[n]['facts']['creator_label'],self.ds[n]['facts']['source_fields']['Auteur'])
  self.assertIn('fausse',self.ds[122]['facts']['source_fields']['Precisions_inscriptions'])
 def test_question_mark_and_monogram_not_expanded(self):
  self.assertIn('?',self.ds[72]['facts']['creator_label']);self.assertEqual(self.ds[137]['facts']['creator_label'],'Monogrammiste E8E');self.assertIn('PETERS',self.ds[96]['facts']['creator_label'])
 def test_physical_date_conflicts_held(self):
  for n in [17,52,56,73,76,85,110,117,132]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_sparse_possible_duplicates_held(self):
  for n in [34,79,103,111,114,131,135,143,144,149,150,156,159]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_bridoux_copy_sheets_distinguished(self):
  a,b=self.ds[61]['facts'],self.ds[107]['facts'];self.assertNotEqual(a['inventory'],b['inventory']);self.assertNotEqual(a['dimensions_text'],b['dimensions_text']);self.assertIn('pointe d’argent'.replace('’',"'"),a['medium'])
 def test_short_inventory_collision_is_unrelated(self):
  d=self.ds[15];a=next(a for a in d['comparison']['inventory_hits'] if a['relevant']);self.assertEqual(a['id'],'6699b55f-a901-41a8-9cb9-3255691938c8');self.assertIn('Clouet',a['creators'][0]);self.assertEqual(d['facts']['work_type'],'print')
 def test_untitled_rowlandson_not_thomas_child_study(self):
  d=self.ds[100];a=d['comparison']['untitled_creator_hits'][0];self.assertEqual(a['creators'],['Thomas Rowlandson']);self.assertEqual(a['work_type'],'print');self.assertEqual(d['facts']['work_type'],'drawing');self.assertEqual(d['facts']['first'],1788)
 def test_former_and_signature_names_broaden_comparisons(self):
  for n,t in [(25,'derain'),(50,'seyssaud'),(53,'friesz'),(101,'alost'),(102,'seghers'),(123,'durand'),(139,'cerquozzi'),(162,'vigee'),(163,'blanchard')]:self.assertIn(t,self.ds[n]['comparison']['creator_terms'])
 def test_indexed_identity_matches_independent_scan(self):
  state=r.m.load(r.IDENTITY)['state']
  for n in [25,41,52,100,123,131,143,162]:
   d=self.ds[n];ts=set(r.identity.terms(d['facts']));aids={a['id'] for a in state['artists'] if r.identity.i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in state['aliases'] if r.identity.i.tokens(a['alias'])&ts};pool={a['id'] for a in state['artworks'] if r.identity.i.tokens(a['unlinked_creator_label'])&ts}|{a['artwork_id'] for a in state['links'] if a['artist_id'] in aids};self.assertEqual(pool,set(d['comparison']['creator_pool_ids']))
if __name__=='__main__':unittest.main()
