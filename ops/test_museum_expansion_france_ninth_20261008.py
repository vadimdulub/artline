"""Offline physical-identity regressions on captured source records; no DB fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-ninth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={d['number']:d for d in r.build()};cls.context={v['candidate_number']:v['literal_primary_record'] for v in r.m.load(r.RUN/'physical-comparison-context-001.json.gz')['rows']}
 def test_wrong_museum_identity_fails(self):
  d=self.ds[1];q=copy.deepcopy(d['index']);q['museum']['city']='Montpellier'
  with self.assertRaises(AssertionError):r.f.parse(q,r.checked(d['source_reference']))
 def test_1970_inclusive_despite_later_artist_death(self):
  for n in [123,128,160]:
   d=self.ds[n];self.assertEqual((d['facts']['first'],d['facts']['last']),(1970,1970));self.assertEqual(d['state'],'approved_review_only_addition')
 def test_before_lower_bound_stays_unknown(self):
  for n,last in [(262,1876),(266,1892)]:
   f=self.ds[n]['facts'];self.assertIsNone(f['first']);self.assertEqual(f['last'],last);self.assertEqual(f['date_precision'],'before')
 def test_range_and_circa_not_invented_exact_dates(self):
  f=self.ds[28]['facts'];self.assertEqual((f['first'],f['last']),(1925,1935));self.assertEqual(f['date_precision'],'range')
  f=self.ds[29]['facts'];self.assertEqual((f['first'],f['last']),(1926,1950));self.assertEqual(f['date_display'],'1930 vers')
 def test_acquisition_not_creation(self):
  f=self.ds[123]['facts'];self.assertEqual(f['first'],1970);self.assertIn('1984',f['source_fields']['Date_d_acquisition'])
 def test_plate_maker_and_later_impression_separated(self):
  d=self.ds[85];self.assertEqual(d['facts']['first'],1835);self.assertIn('impression de 1835',d['facts']['creator_label']);self.assertIn('sycomore',d['derived_fields']['qualified_creator_label']['literal_evidence'])
 def test_disputed_signature_does_not_become_unqualified_creator(self):
  d=self.ds[104];self.assertEqual(d['facts']['first'],1787);self.assertIn('contestée',d['facts']['creator_label']);self.assertIn('1896',d['derived_fields']['qualified_creator_label']['literal_evidence'])
 def test_van_tilborch_attribution_preserved(self):
  d=self.ds[150];self.assertIn('attribué',d['facts']['creator_label']);self.assertNotIn('Egidius',d['facts']['creator_label']);self.assertIn('Egidius',d['facts']['source_fields']['Auteur'])
 def test_contested_girodet_labels_remain_qualified(self):
  for n in [183,211]:
   d=self.ds[n];self.assertIn('contest',d['facts']['creator_label']);self.assertIn('Sablet',d['derived_fields']['qualified_creator_label']['literal_evidence'])
 def test_nadar_conflict_not_silently_resolved(self):
  for n in [199,217,241]:
   d=self.ds[n];self.assertIn('Nadar',d['facts']['creator_label']);self.assertIn('Nadar Félix',d['derived_fields']['qualified_creator_label']['original'])
   if n==199:self.assertIn('Félix dans Auteur, Paul dans Historique',d['facts']['creator_label'])
   else:self.assertIn('discordants',d['facts']['creator_label'])
 def test_anonymous_copies_and_question_mark_retained(self):
  for n in [268,275,277]:self.assertIn('anonyme',self.ds[n]['facts']['creator_label'])
  self.assertIn('pastiche',self.ds[268]['facts']['creator_label']);self.assertIn('Rubens (d’après)',self.ds[275]['facts']['creator_label']);self.assertIn('?',self.ds[277]['facts']['creator_label'])
 def test_unknown_creators_not_filled(self):
  self.assertIsNone(self.ds[31]['facts']['creator_label']);self.assertIsNone(self.ds[176]['facts']['creator_label']);self.assertEqual(self.ds[205]['facts']['creator_label'],'anonyme(dessinateur)')
 def test_missing_dimensions_remain_unknown(self):
  for n in [21,25,26]:self.assertIsNone(self.ds[n]['facts']['dimensions_text'])
 def test_single_decorated_plate_not_whole_service(self):
  f=self.ds[176]['facts'];self.assertEqual(f['work_type'],'ceramic');self.assertIn('22',f['dimensions_text']);self.assertIn('866.1.246',f['source_fields']['Historique']);self.assertNotIn('866.1.246',f['inventory'])
 def test_paired_or_portfolio_units_held(self):
  for n in [30,93,131,136,158,167]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_conflicting_creation_and_inscription_held(self):
  for n in [19,257,307,334]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_restrike_chronology_held(self):
  for n in [77,201,218]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_uncertain_physical_version_and_attribution_held(self):
  for n in [120,188]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_sparse_same_title_duplicates_held(self):
  for n in [73,141,159,184,212,223,231,238,245,250,263]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_gauguin_separate_sheet_dimensions(self):
  self.assertIn('45.5',self.ds[6]['facts']['dimensions_text']);self.assertIn('38,6',self.context[6]['Mesures']);self.assertIn('Pont-Aven',self.context[6]['Localisation'])
 def test_print_collection_provenance_not_invented_measurements(self):
  self.assertIsNone(self.context[7]['measurements']);self.assertIn('Seltzer',self.context[7]['creditline']);self.assertIn('1984',self.ds[7]['facts']['source_fields']['Precisions_inscriptions'])
  self.assertEqual(self.context[115]['dimensions'],'');self.assertIn('Rosenwald',self.context[115]['creditline']);self.assertIn('Faguier',self.ds[115]['facts']['source_fields']['Ancienne_appartenance'])
 def test_braque_different_support_and_provenance(self):
  self.assertIn('Chine',self.ds[122]['facts']['source_fields']['Description']);self.assertIn('Arches',self.context[122]['Description']);self.assertIn('Laurens',self.context[122]['Ancienne_appartenance'])
 def test_rouault_verlaine_dimensions_and_date_distinct(self):
  self.assertEqual(self.ds[144]['facts']['first'],1926);self.assertEqual(self.context[144]['Object Date'],'1933');self.assertIn('72.7',self.context[144]['Dimensions']);self.assertIn('61,9',self.ds[144]['facts']['dimensions_text'])
 def test_hebert_watercolour_not_existing_oil(self):
  f=self.ds[290]['facts'];other=self.context[290];self.assertIn('aquarelle',f['medium']);self.assertIn('huile',other['Materiaux_techniques']);self.assertEqual(other['Numero_inventaire'],'RF 1978-268');self.assertEqual(f['inventory'],'MNEH1978.2.16')
 def test_recto_verso_is_one_sheet(self):
  f=self.ds[17]['facts'];self.assertIn('verso',f['source_fields']['Historique']);self.assertEqual(sum(d['source_id']==f['source_id'] for d in self.ds.values()),1)
 def test_same_mount_does_not_erase_individual_sheet_identity(self):
  a,b=[self.ds[n]['facts'] for n in [315,316]];self.assertEqual(a['dimensions_text'],b['dimensions_text']);self.assertNotEqual(a['inventory'],b['inventory']);self.assertIn('NO 34',a['source_fields']['Precisions_inscriptions']);self.assertIn('NO 33',b['source_fields']['Precisions_inscriptions'])
 def test_creator_accents_and_old_attributions_broaden_search(self):
  rows=r.m.load(r.CANDIDATES)['rows'];p=r.identity.params_for(rows);self.assertIn('%hébert%',p['raw_patterns']);self.assertIn('%vaucanu%',p['raw_patterns'])
  for n,term in [(39,'guibert'),(70,'flippart'),(104,'varin'),(150,'tilborch'),(183,'sablet'),(205,'vaucanu'),(263,'pirodon')]:self.assertIn(term,self.ds[n]['comparison']['creator_terms'])
 def test_accent_search_exposes_existing_hebert_comparison(self):
  self.assertIn('9fa6d613-76d1-4ee0-841a-2fc45da022d4',{v['id'] for v in self.ds[290]['comparison']['leads']})
 def test_literal_source_ownership_and_roles_unchanged(self):
  for d in self.ds.values():
   f=d['facts'];self.assertEqual(f['credit_line'],f['source_fields']['Statut_juridique'])
   if d['number'] not in r.notes.QUALIFIED:self.assertEqual(f['creator_label'],f['source_fields']['Auteur'])
 def test_short_inventory_collisions_have_specific_review(self):
  for n,ids in r.notes.INVENTORY_EXCEPTIONS.items():self.assertEqual({v['id'] for v in self.ds[n]['comparison']['inventory_hits'] if v['relevant']},ids);self.assertEqual(self.ds[n]['state'],'approved_review_only_addition')
if __name__=='__main__':unittest.main()
