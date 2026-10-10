"""Offline release and source-boundary checks; no database fixtures or writes."""
import collections,copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-italy-fourth-apply-20261008.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReleaseChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records=a.records();cls.by={v['decision']['number']:v for v in cls.records};cls.rows={v['number']:v for v in a.m.load(a.RUN/'native-candidates-002.json.gz')['rows']}
 def test_distinct_objects_and_minimums(self):
  self.assertEqual(len(self.records),135);self.assertEqual(len({v['artwork_id'] for v in self.records}),135);counts=collections.Counter(v['institution_id'] for v in self.records);before=a.m.load(a.RUN/'initial-scope-001.json.gz')['counts'];self.assertEqual(sorted(counts.values()),[63,72]);self.assertTrue(all(before[i]['eligible']+c>=100 for i,c in counts.items()))
 def test_source_identity_and_inventory_conflicts_excluded(self):
  self.assertTrue(all(not v['decision']['issues'] and not v['decision']['comparison']['source_hits'] for v in self.records));self.assertFalse([v for v in a.i.within_batch([v['decision'] for v in self.records]) if v['kind']=='inventory']);ctx=a.m.load(a.RUN/'comparison-source-context-001.json.gz');self.assertEqual({v['number'] for v in ctx['museum_local_inventory_hits']},{475});self.assertNotIn(475,self.by)
 def test_historical_attributions_preserved(self):
  for n in [258,262,280,287,299]:
   f=self.by[n]['facts'];self.assertIn('; attribuito',f['creator_label']);self.assertEqual(f['source_fields']['ATTRIBUZIONI'],self.rows[n]['facts']['source_fields']['ATTRIBUZIONI']);self.assertIn('creator_label',self.by[n]['decision']['derived_fields'])
 def test_priority_qualified_creators(self):
  self.assertIn('bottega',self.by[288]['facts']['creator_label']);self.assertIn('attribuit',self.by[290]['facts']['creator_label']);self.assertIn('attribuit',self.by[299]['facts']['creator_label'])
 def test_literal_dates_and_source_fields_preserved(self):
  for n,v in self.by.items():
   for key in ['first','last','date_precision','date_display','source_fields','inventory','medium']:self.assertEqual(v['facts'][key],self.rows[n]['facts'][key])
  self.assertIn('/',self.by[275]['facts']['date_display']);self.assertEqual((self.by[329]['facts']['first'],self.by[329]['facts']['last']),(1590,1610))
 def test_shared_physical_supports_count_once(self):
  self.assertIn('one physical object',self.by[300]['decision']['basis'].lower());self.assertIn(632,self.by);self.assertIn('flap',self.by[663]['decision']['basis'].lower());self.assertEqual(len([v for v in self.records if v['decision']['number']==673]),1)
 def test_uncertain_versions_remain_out(self):
  self.assertFalse(set(a.r.s.UNCERTAIN)&set(self.by));self.assertNotIn(121,self.by);self.assertFalse(set(a.r.DEFERRED)&set(self.by))
 def parse_parts(self,n):
  f=a.r.f;row=self.rows[n];b=f.base.validated_batch(a.checked(row['source_reference']));page=next(v for v in b['pages'] if v['number']==n);uri='https://w3id.org/arco/resource/'+row['source_id'];return f,row,b,page,uri,f.base.graph_for(b,uri)
 def test_external_deposit_not_storage(self):
  f,row,b,page,uri,g=self.parse_parts(11);current=[u for u in g[uri][f.a.LOC+'hasTimeIndexedTypedLocation'] if f.a.LOC+'CurrentPhysicalLocation' in g[u][f.a.LOC+'hasLocationType']];self.assertEqual(len(current),1);g[current[0]][f.a.CORE+'specifications']={'deposito esterno presso altra sede'}
  with patch.object(f.base,'graph_for',return_value=g):self.assertIn('custody_narrative_review',f.parse(row,b,page)['issues'])
 def test_contradictory_city_not_resolved(self):
  f,row,b,page,uri,g=self.parse_parts(336);g[uri][f.a.DC+'coverage']={'Rome (RM)'}
  with patch.object(f.base,'graph_for',return_value=g):self.assertNotEqual(f.parse(row,b,page)['state'],'candidate')
 def test_slash_range_requires_agreeing_graph(self):
  f,row,b,page,uri,g=self.parse_parts(275);g[uri][f.a.DC+'date']={'1675-1690'}
  with patch.object(f.base,'graph_for',return_value=g):self.assertIn('creation_date_review',f.parse(row,b,page)['issues'])
 def test_cross_cutoff_and_approximate1970_not_automatic(self):
  self.assertIsNone(a.r.f.a.numeric_date('1965-1975'));self.assertIsNone(a.r.f.a.numeric_date('ca 1970'));self.assertTrue(all(v['facts']['last']<=1970 for v in self.records))
 def test_panel_not_existing_mural(self):
  self.assertIn('tavola',self.by[324]['facts']['medium']);self.assertIn('mural',self.by[324]['decision']['basis']);self.assertIn('oil on panel',self.by[299]['decision']['basis'])
 def test_fresh_comparison_change_detected(self):
  before={'number':1,'creator_pool_ids':['a'],'hits':[]};irrelevant=dict(before,creator_pool_ids=['a','b']);relevant=dict(irrelevant,hits=[{'id':'b'}]);self.assertEqual(a.comparable(before),a.comparable(irrelevant));self.assertNotEqual(a.comparable(before),a.comparable(relevant))
if __name__=='__main__':unittest.main()
