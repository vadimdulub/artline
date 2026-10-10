"""Offline identity, attribution, physical-unit and date safeguards; no DB fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-fourteenth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ds={d['number']:d for d in r.build()};cls.raw={d['number']:d for d in r.m.load(r.CANDIDATES)['rows']};cls.ctx={v['number']:v for v in r.m.load(r.CONTEXT)['rows']}
 def test_every_candidate_has_one_decision(self):self.assertEqual(set(self.ds),set(range(1,606)));self.assertEqual((len(r.NOTES),len(r.HOLDS)),(481,124))
 def test_raw_metadata_never_rewritten(self):
  for n,d in self.ds.items():self.assertEqual(d['facts']['source_fields'],self.raw[n]['facts']['source_fields'])
 def test_dates_and_unknowns_preserved(self):
  for n,d in self.ds.items():
   for k in ['first','last','date_display','date_precision','medium','dimensions_text','credit_line','inventory']:self.assertEqual(d['facts'][k],self.raw[n]['facts'][k])
 def test_dates_are_creation_not_acquisition(self):
  for n in r.NOTES:
   f=self.ds[n]['facts'];self.assertTrue((f['first'] is None and f['date_precision']=='before' and f['last']<=1971) or (f['first'] is not None and f['first']<=f['last']<=1970))
 def test_bound_components_are_held(self):
  for n in [22,23,24,253,290,475,510,542,556,572,578,580,584,587,588]+list(range(590,605)):self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_ambiguous_same_impressions_are_held(self):
  for n in [30,31,32,36,422,499,540,544,548,549,551,557]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_after_cutoff_and_conflicting_dates_held(self):
  for n in [212,525,585]:self.assertEqual(self.ds[n]['state'],'editorial_hold')
 def test_failed_native_capture_not_approved(self):self.assertEqual(self.ds[583]['state'],'editorial_hold');self.assertNotIn(583,self.ctx)
 def test_primary_oils_resolve_print_holds(self):
  p={v['existing_artwork_id']:v['literal_primary_record'] for v in r.m.load(r.RUN/'physical-comparison-context-002.json.gz')['rows']}
  for n,aid in [(56,'ccec6560-64de-4c88-b618-c8d5fb43048d'),(119,'9d770d43-bfd3-4914-a3dd-cf843c37e804')]:
   self.assertEqual(self.ds[n]['state'],'approved_review_only_addition');self.assertIn("huile",p[aid]['Materiaux_techniques']);self.assertIn('lithograph',r.m.norm(self.ctx[n]['literal_detail_text']))
 def test_native_attribution_qualifiers_survive(self):
  for n in [47,113,231,368,375,385,406,412,417,427,431,435,541]:self.assertIn('attribué à',self.ds[n]['facts']['creator_label'])
 def test_missing_native_qualification_rejected(self):
  c=copy.deepcopy(self.ctx[47]);c['literal_detail_text']=c['literal_detail_text'].replace('Attribué à','').replace('attribué à','')
  with self.assertRaises(AssertionError):r.derive_creator(copy.deepcopy(self.raw[47]['facts']),47,c)
 def test_mismatched_native_identity_rejected(self):
  c=copy.deepcopy(self.ctx[47]);c['source_id']='wrong-object'
  with self.assertRaises(AssertionError):r.derive_creator(copy.deepcopy(self.raw[47]['facts']),47,c)
 def test_jules_david_conflict_is_auditable(self):
  for n in [173,259,294]:
   self.assertIn('1808-1892',self.ds[n]['facts']['creator_label']);self.assertIn('1848-1923',self.ds[n]['facts']['source_fields']['Auteur']);self.assertIn('original',self.ds[n]['derived_fields']['qualified_creator_label'])
 def test_missing_creator_supplied_only_from_exact_native_object(self):
  for n in [456,537,555]:self.assertFalse(self.raw[n]['facts']['creator_label']);self.assertIn('Hugo Victor',self.ds[n]['facts']['creator_label'])
 def test_model_and_printmaker_roles_separate(self):
  for n in [313,320,324,343,367,468,528]:self.assertIn('modèle',self.ds[n]['facts']['creator_label'])
 def test_blank_legal_label_not_invented(self):
  blank=[n for n in r.NOTES if not self.raw[n]['facts']['credit_line']];self.assertTrue(blank)
  for n in blank:self.assertEqual(self.ds[n]['facts']['credit_line'],self.raw[n]['facts']['credit_line'])
 def test_shared_inventory_cannot_double_count(self):
  rows=list(self.raw.values());r.NOTES[499]='deliberately invalid shared-inventory test'
  try:
   with self.assertRaises(AssertionError):r.batch_review(rows)
  finally:r.NOTES.pop(499)
 def test_new_lead_requires_explicit_review(self):
  old=r.m.load(r.RUN/'native-identity-001.json.gz')['comparisons'];new=r.m.load(r.IDENTITY)['comparisons'];saved=r.notes.SUPPLEMENTAL_REVIEW.pop(119)
  try:
   with self.assertRaises(AssertionError):r.coverage(list(self.raw.values()),old,new)
  finally:r.notes.SUPPLEMENTAL_REVIEW[119]=saved
 def test_no_existing_exact_source_hits(self):
  for n in r.NOTES:
   for k in ['native_scheme_hits','native_url_hits','source_record_hits']:self.assertFalse(self.ds[n]['comparison'][k])
 def test_transferred_alias_checks_and_slash_id_repair(self):
  s=r.m.load(r.RUN/'supplemental-context-001.json.gz');self.assertFalse(s['citation_hits']);self.assertFalse(s['external_hits']);self.assertEqual({v['node_id'] for v in s['transferred_object_aliases']},{'102005','102009'});self.assertEqual(s['resolved_primary_records'][0]['literal_primary_record']['Reference'],'0643D-3/2-1967')
if __name__=='__main__':unittest.main()
