"""Offline object-identity/date safeguards against captured sources, no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-sixth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds={d['number']:d for d in r.build()}
 def test_collection_biography_is_not_album(self):
  d=self.ds[71];self.assertIsNone(r.f.n.screen(d['facts']['source_fields'])[0]);self.assertIsNotNone(r.f.screen(d['facts']['source_fields'])[0]);self.assertEqual(d['state'],'approved_review_only_addition');self.assertIn('carnet',d['facts']['source_fields']['Commentaires'])
 def test_moulin_exception_rejects_changed_object_unit(self):
  for k,v in [('Denomination','album'),('Description','ensemble de dessins'),('Genese','folio'),('Historique','album de 1936')]:
   d=copy.deepcopy(self.ds[71]['facts']['source_fields']);d[k]=v;self.assertIsNone(r.f.screen(d)[0])
 def test_moulin_exception_rejects_changed_biography(self):
  d=copy.deepcopy(self.ds[71]['facts']['source_fields']);d['Commentaires']+=' Cet objet est un album.';self.assertIsNone(r.f.screen(d)[0])
 def test_moulin_exception_rejects_other_reference(self):
  d=copy.deepcopy(self.ds[71]['facts']['source_fields']);d['Reference']='04670009999';self.assertIsNone(r.f.screen(d)[0])
 def test_wrong_museum_fails(self):
  d=self.ds[71];q=copy.deepcopy(d['index']);q['museum']['city']='Cambrai'
  with self.assertRaises(AssertionError):r.f.parse(q,r.checked(d['source_reference']))
 def test_post1970_creation_rejected(self):
  d=copy.deepcopy(self.ds[159]['facts']['source_fields']);d['Millesime_de_creation']='1971';d['Periode_de_creation']='4e quart 20e siècle';self.assertIsNone(r.f.screen(d)[0])
 def test_cutoff_crossing_range_rejected(self):
  d=copy.deepcopy(self.ds[159]['facts']['source_fields']);d['Millesime_de_creation']='1969-1972';d['Periode_de_creation']='2e moitié 20e siècle';self.assertIsNone(r.f.screen(d)[0])
 def test_album_requires_review(self):
  d=copy.deepcopy(self.ds[167]['facts']['source_fields']);d['Denomination']='album';self.assertIsNone(r.f.screen(d)[0])
 def test_bad_response_or_hash_fails(self):
  x=r.m.load(r.checked(self.ds[71]['source_reference']))
  for k,v in [('status',429),('sha256','0'*64)]:
   y=copy.deepcopy(x);y['receipt'][k]=v
   with self.assertRaises(AssertionError):r.f.body(y)
 def test_existing_delacroix_copy_is_held(self):
  d=self.ds[67];self.assertEqual(d['state'],'editorial_hold');self.assertIn('afc7c83a-00b4-51d5-9aa5-a8ae3c6cdb05',{v['id'] for v in d['comparison']['inventory_hits'] if v['relevant']})
 def test_duthoit_alternatives_not_coauthors(self):
  for n in [178,180,187,194,201,208,215,222,229,236]:
   d=self.ds[n];self.assertIn(' ou ',d['facts']['creator_label']);self.assertIn('Les deux attributions sont plausibles',d['derived_fields']['qualified_creator_label']['literal_evidence']);self.assertEqual(d['derived_fields']['qualified_creator_label']['original'],d['facts']['source_fields']['Auteur'])
 def test_brouwer_attribution_qualified(self):
  d=self.ds[100];self.assertIn('(attribué à)',d['facts']['creator_label']);self.assertEqual(d['derived_fields']['qualified_creator_label']['source_field'],'Historique')
 def test_teniers_copy_qualified(self):
  d=self.ds[103];self.assertIn('(d’après)',d['facts']['creator_label']);self.assertIn('réplique',d['derived_fields']['qualified_creator_label']['literal_evidence']);self.assertEqual(d['facts']['date_display'],'18e siècle')
 def test_venetian_alternatives_preserved(self):
  f=self.ds[175]['facts'];self.assertIn('ou MAGGIOTTO',f['creator_label']);self.assertIn('CAPPELLA',f['creator_label']);self.assertIn('sans écarter',f['source_fields']['Precisions_sujets_representes'])
 def test_narrative_circa_has_no_invented_tolerance(self):
  for n in [193,200]:
   d=self.ds[n];f=d['facts'];self.assertEqual((f['first'],f['last'],f['date_precision'],f['date_display']),(1850,1850,'circa','1850 vers'));self.assertEqual(d['derived_fields']['qualified_creation_date']['original_precision'],'exact')
 def test_depicted_year_does_not_date_drawing(self):
  for n,year in [(7,1918),(181,1864),(200,1850),(222,1850),(232,1801)]:self.assertEqual(self.ds[n]['facts']['first'],year)
 def test_kozirki_lifespan_not_creation(self):
  for n in [182,189,196,203,210,217,224,231,238]:
   f=self.ds[n]['facts'];self.assertEqual((f['first'],f['last']),(1945,1948));self.assertIn('1987',f['source_fields']['Precisions_sur_l_auteur'])
 def test_unknown_medium_and_dimensions_stay_unknown(self):
  f=self.ds[119]['facts'];self.assertIsNone(f['medium']);self.assertIsNone(f['dimensions_text'])
 def test_source_creator_question_marks_preserved(self):
  for n in [20,117]:
   f=self.ds[n]['facts'];self.assertIn('?',f['creator_label']);self.assertEqual(f['creator_label'],f['source_fields']['Auteur'])
 def test_one_sheet_not_one_per_motif(self):
  for n in [33,37,41,43,52,57,60,65,158,164,167,171]:
   d=self.ds[n];self.assertEqual(d['state'],'approved_review_only_addition');self.assertEqual(sum(v['source_id']==d['source_id'] for v in self.ds.values()),1)
 def test_same_title_busson_series_are_distinct(self):
  a,b=self.ds[132]['facts'],self.ds[142]['facts'];self.assertIn('Série D',a['source_fields']['Precisions_inscriptions']);self.assertIn('Série A',b['source_fields']['Precisions_inscriptions']);self.assertNotEqual(a['inventory'],b['inventory'])
 def test_same_title_ketzing_sheets_are_distinct(self):
  a,b=self.ds[153]['facts'],self.ds[154]['facts'];self.assertEqual((a['first'],b['first']),(1948,1949));self.assertNotEqual(a['dimensions_text'],b['dimensions_text'])
 def test_same_title_actress_sheets_are_distinct(self):
  a,b=self.ds[212]['facts'],self.ds[233]['facts'];self.assertEqual((a['first'],b['first']),(1906,1909));self.assertNotEqual(a['dimensions_text'],b['dimensions_text']);self.assertNotEqual(a['inventory'],b['inventory'])
 def test_cast_not_conflated_with_model(self):
  self.assertIn('plâtre',self.ds[96]['facts']['medium']);self.assertIn('Bronze',self.ds[96]['facts']['source_fields']['Commentaires']);self.assertIn('terre cuite',self.ds[81]['facts']['medium']);self.assertIn('bronze',self.ds[81]['facts']['source_fields']['Historique'])
 def test_woodcut_not_woodblock(self):
  f=self.ds[141]['facts'];self.assertEqual(f['work_type'],'print');self.assertIn('papier',f['medium']);self.assertIn('A.98.5.56',f['source_fields']['Historique'])
 def test_fountain_and_double_face_are_one_work(self):
  for n in [84,85]:self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
  self.assertIn('avec vasque',self.ds[84]['facts']['dimensions_text']);self.assertIn('deux faces',self.ds[85]['facts']['source_fields']['Description'])
 def test_physical_date_conflicts_are_held(self):
  for n in [9,123,124,128,129,185]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_sparse_possible_duplicates_are_held(self):
  for n in [95,102,109,116]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_inventory_collisions_reviewed_explicitly(self):
  for n in [75,98,105,115]:self.assertEqual({a['id'] for a in self.ds[n]['comparison']['inventory_hits'] if a['relevant']},r.notes.INVENTORY_EXCEPTIONS[n])
 def test_archived_source_distinguishes_drawings_from_oils(self):
  x=r.m.load(r.RUN/'comparison-source-extracts-001.json');self.assertEqual(len(x['rows']),4)
  for n in [14,34,46,52]:self.assertEqual(self.ds[n]['facts']['work_type'],'drawing');self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
 def test_former_and_model_names_broaden_comparisons(self):
  for n,term in [(10,'pasquil'),(22,'lepautre'),(76,'reboul'),(98,'snyders'),(109,'corot'),(124,'huet'),(175,'piazzetta'),(207,'gourdain'),(211,'siffait'),(239,'amand')]:self.assertIn(term,self.ds[n]['comparison']['creator_terms'])
 def test_indexed_identity_matches_independent_scan(self):
  state=r.m.load(r.IDENTITY)['state']
  for n in [22,67,109,116,175,207,239]:
   d=self.ds[n];ts=set(r.identity.terms(d['facts']));aids={a['id'] for a in state['artists'] if r.identity.i.tokens(a['display_name'])&ts}|{a['artist_id'] for a in state['aliases'] if r.identity.i.tokens(a['alias'])&ts};pool={a['id'] for a in state['artworks'] if r.identity.i.tokens(a['unlinked_creator_label'])&ts}|{a['artwork_id'] for a in state['links'] if a['artist_id'] in aids};self.assertEqual(pool,set(d['comparison']['creator_pool_ids']))
if __name__=='__main__':unittest.main()
