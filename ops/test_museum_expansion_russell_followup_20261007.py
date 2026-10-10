"""Offline source-identity and preservation checks; no database or fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-russell-followup-apply-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

class FollowupPolicy(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.plan,cls.digest=r.validate_plan();cls.by={a['facts']['source_id']:a for a in cls.plan['records']};cls.candidates={a['source_id']:a for a in r.m.load(r.CANDIDATES)['rows']}
 def page(self,key):return copy.deepcopy(self.by[key]['native'])
 def test_plan_is_bounded_and_pinned(self):
  self.assertEqual(self.digest,'40808dde623cd0094588ba6a2b6cbfe53efe953a7ed1970cf8c8652576ad66bd');self.assertEqual(len(self.by),21)
 def test_all_prior_records_preserved_in_preimage(self):
  self.assertEqual(len(self.plan['before']['artworks']),234);self.assertEqual(len(self.plan['before']['citations']),529)
 def test_sitter_lifespan_is_not_creation(self):
  p=self.page('victoria-princess-royal-1840-1901');p['parsed']['caption_lines'][0]=p['parsed']['title']
  with self.assertRaises(AssertionError):r.n.source_facts(p)
 def test_cutoff_rejects_1971(self):
  p=self.page('sita');p['parsed']['caption_lines'][0]='Sita, 1971'
  with self.assertRaises(AssertionError):r.n.source_facts(p)
 def test_crossing_cutoff_rejected(self):
  p=self.page('sita');p['parsed']['caption_lines'][0]='Sita, 1960-1980'
  with self.assertRaises(AssertionError):r.n.source_facts(p)
 def test_multiple_inventory_lines_rejected(self):
  p=self.page('sita');p['parsed']['caption_lines'].append('SC64b')
  with self.assertRaises(AssertionError):r.n.source_facts(p)
 def test_inventory_namespace_and_suffixes_preserved(self):
  self.assertEqual(r.n.inventory_key('SC99 BORGM'),r.n.inventory_key('SC99'));self.assertNotEqual(r.n.inventory_key('SC64a'),r.n.inventory_key('SC64b'));self.assertNotEqual(r.n.inventory_key('BORGM99'),r.n.inventory_key('SC99'))
 def test_anonymous_russian_icon_supported(self):
  f=self.by['christ-pantocrator']['facts'];self.assertEqual((f['creator_label'],f['object_form'],f['cultural_context']),('Attribution unknown','icon','Russian Orthodox Church'));self.assertEqual(f['work_type'],'unknown');self.assertEqual((f['date_display'],f['first'],f['last']),('late 19th century',1800,1899))
 def test_qualified_print_attribution_retained(self):
  f=self.by['the-bells']['facts'];self.assertEqual(f['creator_label'],'Attributed to Carlo Pellegrini');self.assertEqual(f['native_creator'],'Carlo Pellegrini (1839-1889)')
 def test_type_not_invented_from_artist_biography(self):
  self.assertEqual(self.by['princess-alexandra']['facts']['work_type'],'unknown');self.assertEqual(self.by['victoria-princess-royal-1840-1901']['facts']['work_type'],'sculpture')
 def test_native_inventories_are_unique(self):
  self.assertEqual(len({r.n.inventory_key(x['facts']['inventory']) for x in self.by.values()}),21)
 def test_three_goldie_portraits_are_separate_objects(self):
  ids=['suspicion-a-maori-chief','a-maori-chieftainess','te-aho-te-rangi-wharepu'];self.assertEqual({self.by[k]['facts']['inventory'] for k in ids},{'BORGM 00900','BORGM 00899','BORGM 00901'})
 def test_source_typos_retained_without_artist_changes(self):
  f=self.by['sir-henry-irving-study-for-the-golden-jubilee-picture']['facts'];self.assertEqual(f['creator_label'],'William Ewart Lockhard');self.assertEqual(f['date_display'],'1887')
 def test_conflicting_casts_and_prototypes_held(self):
  review={d['source_id']:d for d in r.m.load(r.REVIEW)['decisions']}
  for key in ['lady-russell-cotes','sir-frederick-leighton','blossoms']:self.assertEqual(review[key]['state'],'hold_identity_or_source')
  for key in ['8398-2','nelusko','panefer']:self.assertEqual(review[key]['state'],'hold_source')
 def test_non_artwork_and_compound_objects_not_added(self):
  for key in ['skull','great-argus','collection-of-taiaha','double-handled-chocolate-cups','amida-butsu']:self.assertNotIn(key,self.by)
 def test_missing_creation_dates_remain_unresolved(self):
  for key in ['sir-henry-irving-4','the-bathers-alarmed','athena','the-sea-cave']:self.assertEqual(self.candidates[key]['state'],'hold_source')
 def test_all_88_source_decisions_accounted(self):
  ds=r.m.load(r.REVIEW)['decisions'];self.assertEqual(len(ds),88);self.assertEqual(len({d['source_id'] for d in ds}),88);self.assertEqual(sum(d['state']=='approved_review_only_addition' for d in ds),21)
 def test_source_comparisons_reject_same_title_equivalence(self):
  x=r.m.load(r.RUN/'native-exact-source-comparison-003.json.gz')['records'];self.assertIn('wall - painting',x[0]['parsed']);self.assertEqual(x[1]['parsed']['record']['objectType'],'Painting');self.assertEqual(x[1]['parsed']['record']['accessionNumber'],'IS.49-1979')

if __name__=='__main__':unittest.main()
