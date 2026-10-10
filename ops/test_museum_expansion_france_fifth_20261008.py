"""Offline safeguards using captured source evidence; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-fifth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={d['number']:d for d in r.build()}
 def test_lam_acquisition_does_not_become_ownership(self):
  for n in [52,57,68,109]:
   f=self.ds[n]['facts'];self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique']);self.assertNotIn('propriété',f['credit_line']);self.assertIsNotNone(f['holding_context_reference']);self.assertFalse(r.m.load(r.checked(f['holding_context_reference']))['legal_title_claim'])
 def test_lam_old_name_is_preserved(self):
  f=self.ds[52]['facts'];self.assertEqual(f['source_fields']['Localisation'],"Villeneuve-d'Ascq ; musée d'art moderne Lille Métropole");self.assertIn('LaM',self.ds[52]['museum']['name'])
 def test_lam_other_city_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']);d['Ville']='Hornu';self.assertIsNone(r.f.n.lam_context(d));self.assertIsNone(r.f.n.screen(d)[0])
 def test_lam_wrong_museum_code_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']);d['Code_Museofile']='M5025';self.assertIsNone(r.f.n.lam_context(d))
 def test_lam_deposit_elsewhere_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']);d['Lieu_de_depot']='Hornu ; musée des Arts contemporains';self.assertIsNone(r.f.n.lam_context(d));self.assertIsNone(r.f.n.screen(d)[0])
 def test_lam_missing_work_rejected(self):
  for k in ['MANQUANT','MANQUANT_COM']:
   d=copy.deepcopy(self.ds[52]['facts']['source_fields']);d[k]='manquant';self.assertIsNone(r.f.n.lam_context(d))
 def test_lam_other_acquisition_recipient_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']);d['Statut_juridique']='donation;Paris;autre musée';self.assertIsNone(r.f.n.lam_context(d));self.assertIsNone(r.f.n.screen(d)[0])
 def test_lam_historical_deposit_retains_end_date(self):
  d=self.ds[109];self.assertEqual(d['state'],'approved_review_only_addition');self.assertIn('2010/04/12',d['facts']['source_fields']['Commentaires']);self.assertIn('custody_narrative_review',d['review_flags'])
 def test_armee_city_unknown_not_invented(self):
  d=self.ds[202];self.assertFalse(d['museum']['city']);self.assertEqual(d['facts']['source_fields']['Ville'],'Paris');self.assertIn('database_city_unknown_source_city_explicit',d['review_flags'])
 def test_armee_missing_city_exception_is_narrow(self):
  d=self.ds[202];item=copy.deepcopy(d['index']);item['museum']['name']='musée de l’armée — Autre ville'
  with self.assertRaises(AssertionError):r.f.parse(item,r.checked(d['source_reference']))
 def test_before_dates_keep_unknown_lower_bounds(self):
  for n,last in [(2,1905),(68,1953),(75,1897),(80,1949),(90,1957),(91,1962),(105,1945),(138,1731)]:
   f=self.ds[n]['facts'];self.assertEqual((f['first'],f['last'],f['date_precision']),(None,last,'before'))
 def test_post_cutoff_creation_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']);d['Millesime_de_creation']='1971';d['Periode_de_creation']='4e quart 20e siècle';self.assertIsNone(r.f.n.screen(d)[0])
 def test_creation_range_crossing_cutoff_rejected(self):
  d=copy.deepcopy(self.ds[52]['facts']['source_fields']);d['Millesime_de_creation']='1969-1972';d['Periode_de_creation']='2e moitié 20e siècle';self.assertIsNone(r.f.n.screen(d)[0])
 def test_military_non_art_object_not_automatically_art(self):
  d=copy.deepcopy(self.ds[202]['facts']['source_fields']);d['Domaine']='armée';d['Denomination']='insigne';self.assertIsNone(r.f.n.screen(d)[0])
 def test_books_and_ambiguous_print_units_held(self):
  for n in [56,101,112]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_signature_date_conflicts_held(self):
  for n in [28,157,171]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_unclear_duplicate_sheets_held(self):
  for n in [36,44,63,117,77,126,160,176]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_known_title_and_maker_duplicate_held(self):
  self.assertEqual(self.ds[5]['state'],'editorial_hold');self.assertIn('583116fe-5cb5-4e0d-8c08-8e77e99d65b9',{a['id'] for a in self.ds[5]['comparison']['leads']})
 def test_copy_and_model_roles_retained(self):
  for n in [1,9,168,169]:self.assertEqual(self.ds[n]['facts']['creator_label'],self.ds[n]['facts']['source_fields']['Auteur'].strip())
 def test_qualified_attributions_not_promoted(self):
  for n in [129,130,131,132,133,136,137,141,143,146,149,150,151,152,154,158,163,165,172,174,178]:
   f=self.ds[n]['facts'];self.assertIn('attribu',f['creator_label'].lower());self.assertEqual(f['creator_label'],f['source_fields']['Auteur'].strip())
 def test_former_attributions_remain_comparison_only(self):
  for n,term in [(63,'casier'),(66,'derriennic'),(84,'coadou'),(87,'mccarthy'),(129,'cuyp'),(136,'napoletano'),(147,'grimaldi'),(159,'ribera'),(168,'bourdon'),(169,'valentin'),(189,'barbieri'),(191,'preti'),(193,'beham')]:self.assertIn(term,self.ds[n]['comparison']['creator_terms'])
 def test_unknown_and_anonymous_creators_preserved(self):
  self.assertIsNone(self.ds[127]['facts']['creator_label'])
  for n in [10,19,20,108,166,179,195,197]:self.assertEqual(self.ds[n]['facts']['creator_label'],'anonyme')
 def test_rectoverso_is_one_object(self):
  for n in [54,80,180,190,198]:
   d=self.ds[n];self.assertEqual(d['state'],'approved_review_only_addition');self.assertEqual(sum(x['source_id']==d['source_id'] for x in self.ds.values()),1)
 def test_distinct_rooster_directions_preserved(self):
  a,b=self.ds[162]['facts'],self.ds[177]['facts'];self.assertIn('gauche',a['source_fields']['Precisions_sujets_representes']);self.assertIn('droite',b['source_fields']['Precisions_sujets_representes']);self.assertNotEqual(a['medium'],b['medium'])
 def test_two_part_bust_is_one_physical_work(self):
  d=self.ds[197];self.assertIn('Partie 1/2',d['facts']['dimensions_text']);self.assertIn('Partie 2/2',d['facts']['dimensions_text']);self.assertEqual(d['state'],'approved_review_only_addition')
 def test_inventory_number_collision_needs_explicit_review(self):
  for n in [166,173,181]:self.assertEqual({a['id'] for a in self.ds[n]['comparison']['inventory_hits'] if a['relevant']},r.notes.INVENTORY_EXCEPTIONS[n])
 def test_missing_structured_medium_is_not_filled_from_guess(self):
  f=self.ds[52]['facts'];self.assertIsNone(f['medium']);self.assertIn('Pastel gras',f['source_fields']['Description'])
 def test_bad_http_or_hash_fails(self):
  x=r.m.load(r.checked(self.ds[1]['source_reference']))
  for key,value in [('status',429),('sha256','0'*64)]:
   bad=copy.deepcopy(x);bad['receipt'][key]=value
   with self.assertRaises(AssertionError):r.f.body(bad)
 def test_indexed_comparison_matches_independent_scan(self):
  s=r.m.load(r.IDENTITY)['state']
  for n in [55,63,87,129,136,147,168,169,189,191,193]:
   d=self.ds[n];ts=set(r.identity.terms(d['facts']));aids={a['id'] for a in s['artists'] if r.identity.i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in s['aliases'] if r.identity.i.tokens(a['alias'])&ts};pool={a['id'] for a in s['artworks'] if r.identity.i.tokens(a['unlinked_creator_label'])&ts}|{v['artwork_id'] for v in s['links'] if v['artist_id'] in aids};self.assertEqual(pool,set(d['comparison']['creator_pool_ids']))
if __name__=='__main__':unittest.main()
