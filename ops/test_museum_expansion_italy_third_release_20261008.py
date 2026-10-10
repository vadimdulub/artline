"""Offline release checks. Never connect to or create test databases."""
import collections,copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-italy-third-apply-20261008.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReleaseChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records=a.records();cls.by={v['decision']['number']:v for v in cls.records};cls.rows={v['number']:v for v in a.m.load(a.RUN/'native-candidates-002.json.gz')['rows']}
 def test_distinct_objects_and_minimums(self):
  self.assertEqual(len(self.records),242);self.assertEqual(len({v['artwork_id'] for v in self.records}),242)
  counts=collections.Counter(v['institution_id'] for v in self.records);before=a.m.load(a.RUN/'initial-scope-001.json.gz')['counts'];self.assertEqual(sorted(counts.values()),[4,35,39,60,104]);self.assertTrue(all(v['eligible']+counts[iid]>=100 for iid,v in before.items()))
 def test_source_and_identity_conflicts_not_released(self):
  self.assertTrue(all(not v['decision']['issues'] and not v['decision']['comparison']['source_hits'] for v in self.records))
 def test_inventory_collisions_are_held(self):
  self.assertFalse({239,245,246,289,322,339}&set(self.by));audit=a.m.load(a.RUN/'comparison-source-context-002.json.gz');self.assertEqual({v['number'] for v in audit['museum_local_inventory_hits']},{239,289,322,339});self.assertFalse([v for v in a.i.within_batch([v['decision'] for v in self.records]) if v['kind']=='inventory'])
 def test_unknown_units_and_medium_remain_unknown(self):
  self.assertIn('(unit not stated)',self.by[126]['facts']['dimensions_text']);self.assertNotIn('cm',self.by[126]['facts']['dimensions_text']);self.assertNotIn('olio',(self.by[382]['facts']['medium'] or '').lower())
 def test_qualified_and_priority_creators_preserved(self):
  self.assertEqual(self.by[202]['facts']['creator_label'],'Ambito Cretese');self.assertEqual(self.by[204]['facts']['creator_label'],'Ambito Bizantino');self.assertIn('maniera',self.by[286]['facts']['creator_label']);self.assertIn('bottega',self.by[362]['facts']['creator_label'])
 def test_custody_is_not_ownership_or_display(self):
  self.assertIn('detenzione',self.by[169]['facts']['credit_line'].lower());self.assertIn('deposito',self.by[225]['facts']['current_location_source_notes'])
 def test_external_deposit_is_not_storage_exception(self):
  row=self.rows[225];f=a.r.f;b=f.validated_batch(a.checked(row['source_reference']));page=next(v for v in b['pages'] if v['number']==225);uri='https://w3id.org/arco/resource/'+row['source_id'];g=f.graph_for(b,uri)
  current=[u for u in g[uri][f.a.LOC+'hasTimeIndexedTypedLocation'] if f.a.LOC+'CurrentPhysicalLocation' in g[u][f.a.LOC+'hasLocationType']];self.assertEqual(len(current),1);g[current[0]][f.a.CORE+'specifications']={'deposito esterno presso altra sede'}
  with patch.object(f,'graph_for',return_value=g):self.assertIn('custody_narrative_review',f.parse(row,b,page)['issues'])
 def test_wrong_city_cannot_establish_holding(self):
  row=self.rows[1];f=a.r.f;b=f.validated_batch(a.checked(row['source_reference']));page=next(v for v in b['pages'] if v['number']==1);bad=copy.deepcopy(row)
  for v in bad['authority_candidates']:v['catalogue_city']='Rome (RM)'
  self.assertIn('unique_museum_and_city_review',f.parse(bad,b,page)['issues'])
 def test_bad_dates_and_shared_supports_held(self):
  self.assertFalse({6,9,11,23,25,77,78,80,90,91,110,112,117,296,302,303,354,363,433,434,469}&set(self.by));self.assertIsNone(a.r.f.a.numeric_date('1965-1975'));self.assertIsNone(a.r.f.a.numeric_date('ca 1970'))
 def test_panel_and_canvas_are_not_same_sebastian(self):
  self.assertIn('tavola',self.by[467]['facts']['medium']);self.assertIn('tela',self.by[519]['facts']['medium']);self.assertNotEqual(self.by[467]['facts']['inventory'],self.by[519]['facts']['inventory'])
 def test_related_pisa_scope_and_historical_inventory(self):
  x=a.m.load(a.RUN/'selected-identity-004.json.gz')['state']['related_collection_scope'];self.assertEqual(len(x['institution_ids']),5);self.assertEqual(len(x['artwork_ids']),111);ctx=a.m.load(a.RUN/'comparison-source-context-002.json.gz')['rows'];cano=next(v for v in ctx if v['artwork_id']=='d910390f-a783-4027-991e-1a0b7bec9193');self.assertIn('1803',cano['inventory'])
 def test_bari_repairs_keep_failed_evidence(self):
  x=a.m.load(a.RUN/'bari-repair-001.json');self.assertEqual(len(x['batches']),6);self.assertEqual(len(x['previous_incomplete']),6)
  for dep in x['batches']+x['previous_incomplete']:a.checked(dep)
 def test_fresh_comparison_change_is_detected(self):
  before={'number':1,'creator_pool_ids':['a'],'hits':[]};irrelevant=dict(before,creator_pool_ids=['a','b']);relevant=dict(irrelevant,hits=[{'id':'b'}]);self.assertEqual(a.comparable(before),a.comparable(irrelevant));self.assertNotEqual(a.comparable(before),a.comparable(relevant))
if __name__=='__main__':unittest.main()
