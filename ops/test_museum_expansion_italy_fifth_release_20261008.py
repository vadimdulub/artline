"""Offline evidence-boundary checks; never create catalogue fixtures."""
import collections,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-italy-fifth-apply-20261008.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReleaseChecks(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records=a.records();cls.by={v['decision']['number']:v for v in cls.records};cls.rows={v['number']:v for v in a.m.load(a.r.SOURCE/'native-candidates-002.json.gz')['rows']}
 def test_distinct_objects_and_minimums(self):
  self.assertEqual(len(self.records),211);self.assertEqual(len({v['artwork_id'] for v in self.records}),211);counts=collections.Counter(v['institution_id'] for v in self.records);before=a.m.load(a.RUN/'initial-scope-001.json.gz')['counts'];self.assertEqual(sorted(counts.values()),[48,79,84]);self.assertTrue(all(before[i]['eligible']+c>=100 for i,c in counts.items()))
 def test_source_and_inventory_conflicts_excluded(self):
  self.assertTrue(all(not v['decision']['issues'] and not v['decision']['comparison']['source_hits'] for v in self.records));self.assertFalse([v for v in a.i.within_batch([v['decision'] for v in self.records]) if v['kind']=='inventory']);ctx=a.m.load(a.RUN/'comparison-source-context-001.json.gz');self.assertEqual({v['number'] for v in ctx['museum_local_inventory_hits']},{475});self.assertNotIn(475,self.by)
 def test_creator_qualifications_preserved(self):
  for n,v in self.by.items():self.assertEqual(v['facts']['creator_label'],self.rows[n]['facts']['creator_label'])
  for n in [473,474,483,513,591]:self.assertIn('attribuit',self.by[n]['facts']['creator_label'].lower())
 def test_priority_and_literal_support(self):
  self.assertIn('Greco',self.by[108]['facts']['creator_label']);self.assertIn('Veneto',self.by[109]['facts']['creator_label']);self.assertIn('rame',self.by[356]['facts']['medium']);self.assertIn('tavola',self.by[93]['facts']['medium']);self.assertEqual(self.by[465]['facts']['medium'],'Tela')
 def test_literal_dates_source_fields_and_unknowns(self):
  for n,v in self.by.items():
   for key in ['first','last','date_precision','date_display','source_fields','inventory','medium']:self.assertEqual(v['facts'][key],self.rows[n]['facts'][key])
  self.assertEqual((self.by[10]['facts']['first'],self.by[10]['facts']['last']),(1590,1610));self.assertIn('?',self.by[524]['facts']['title'])
 def test_whole_supports_not_depicted_parts(self):
  self.assertIn('one physical support',self.by[491]['decision']['basis']);self.assertIn('count once',self.by[354]['decision']['basis']);self.assertIn('panel only',self.by[359]['decision']['basis']);self.assertIn('count once',self.by[442]['decision']['basis'])
 def test_similar_titles_distinct_supports(self):
  for n in [432,433,434]:self.assertIn('118',self.by[n]['facts']['dimensions_text'])
  for x,y in [(504,508),(606,617),(86,118)]:self.assertNotEqual(self.by[x]['facts']['dimensions_text'],self.by[y]['facts']['dimensions_text'])
  self.assertIn('acquaforte',self.by[606]['facts']['medium']);self.assertIn('litografia',self.by[617]['facts']['medium'])
 def test_uncertain_versions_and_shared_inventory_held(self):
  self.assertFalse(set(a.r.DEFERRED)&set(self.by));self.assertFalse(set(range(559,565))&set(self.by));self.assertNotIn(116,self.by);self.assertNotIn(614,self.by)
 def parse_parts(self,n):
  f=a.r.f;row=self.rows[n];b=f.base.validated_batch(a.checked(row['source_reference']));page=next(v for v in b['pages'] if v['number']==n);uri='https://w3id.org/arco/resource/'+row['source_id'];return f,row,b,page,uri,f.base.graph_for(b,uri)
 def test_external_deposit_not_storage(self):
  f,row,b,page,uri,g=self.parse_parts(11);current=[u for u in g[uri][f.a.LOC+'hasTimeIndexedTypedLocation'] if f.a.LOC+'CurrentPhysicalLocation' in g[u][f.a.LOC+'hasLocationType']];self.assertEqual(len(current),1);g[current[0]][f.a.CORE+'specifications']={'deposito esterno presso altra sede'}
  with patch.object(f.base,'graph_for',return_value=g):self.assertIn('custody_narrative_review',f.parse(row,b,page)['issues'])
 def test_contradictory_city_not_resolved(self):
  f,row,b,page,uri,g=self.parse_parts(336);g[uri][f.a.DC+'coverage']={'Rome (RM)'}
  with patch.object(f.base,'graph_for',return_value=g):self.assertNotEqual(f.parse(row,b,page)['state'],'candidate')
 def test_slash_range_requires_agreeing_graph(self):
  f,row,b,page,uri,g=self.parse_parts(10);g[uri][f.a.DC+'date']={'1590-1620'}
  with patch.object(f.base,'graph_for',return_value=g):self.assertIn('creation_date_review',f.parse(row,b,page)['issues'])
 def test_cross_cutoff_and_approximate1970_not_automatic(self):
  self.assertIsNone(a.r.f.a.numeric_date('1965-1975'));self.assertIsNone(a.r.f.a.numeric_date('ca 1970'));self.assertTrue(all(v['facts']['last']<=1970 for v in self.records))
 def test_fresh_comparison_change_detected(self):
  before={'number':1,'creator_pool_ids':['a'],'hits':[]};irrelevant=dict(before,creator_pool_ids=['a','b']);relevant=dict(irrelevant,hits=[{'id':'b'}]);self.assertEqual(a.comparable(before),a.comparable(irrelevant));self.assertNotEqual(a.comparable(before),a.comparable(relevant))
if __name__=='__main__':unittest.main()
