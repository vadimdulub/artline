"""Offline source-policy checks; no database connections or catalogue fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-hamburg-facts2-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)

class HamburgSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.objects={**f.f.sources('wikidata-selected-capture-001.json.gz'),**f.f.sources('wikidata-selected-capture-002.json.gz')}
  cls.labels={**f.f.sources('wikidata-creator-capture-001.json.gz'),**f.f.sources('wikidata-extra-label-capture-002.json.gz')}
 def entity(self,q):return copy.deepcopy(self.objects[q]['entity'])
 def facts(self,q):return f.facts(self.entity(q),self.labels)
 def date(self,year):
  r=copy.deepcopy(f.w.one(self.entity('Q102425731'),'P571'));r['mainsnak']['datavalue']['value']['time']=f'+{year:04d}-00-00T00:00:00Z';r.pop('qualifiers',None);return r
 def test_real_source_count(self):self.assertEqual(len(self.objects),260)
 def test_actual1964date(self):self.assertEqual((self.facts('Q102425731')['first'],self.facts('Q102425731')['last']),(1964,1964))
 def test_actual_range_retained(self):
  r=self.facts('Q101310453');self.assertEqual((r['first'],r['last'],r['date_precision']),(1887,1889,'range'))
 def test_julian_year_not_dropped_or_converted(self):
  r=self.facts('Q114036745');self.assertEqual((r['first'],r['date_precision']),(1537,'circa'));self.assertTrue(f.val(r['creation_statement'])['calendarmodel'].endswith('Q1985786'))
 def test_default_multilingual_creator_label(self):self.assertEqual(self.facts('Q111479587')['creator_label'],'Paul Klee')
 def test_missing_inventory_stays_unknown(self):self.assertIsNone(self.facts('Q104145945')['inventory'])
 def test_missing_native_reference_is_explicit(self):self.assertEqual(self.facts('Q110949126')['native_page_urls'],[])
 def test_unknown_material_stays_unknown(self):self.assertEqual(self.facts('Q102425731')['material_claims'],[])
 def test_support_qualifier_is_preserved(self):
  r=self.facts('Q100994480');self.assertEqual(r['material_claims'][1]['qualifiers']['P518'][0]['datavalue']['value']['id'],'Q861259')
 def test_units_retained(self):self.assertEqual(self.facts('Q100994480')['dimension_claims'][0]['unit_label'],'centimetre')
 def test_historical_picasso_claims_not_collapsed(self):
  with self.assertRaises(AssertionError):self.facts('Q1018269')
 def test_preferred_collection_does_not_hide_another(self):
  e=self.entity('Q102425731');e['claims']['P195'][0]['rank']='preferred';other=copy.deepcopy(e['claims']['P195'][0]);other['rank']='normal';other['mainsnak']['datavalue']['value']['id']='Q812285';e['claims']['P195'].append(other)
  with self.assertRaises(AssertionError):f.facts(e,self.labels)
 def test_ended_collection_requires_review(self):
  e=self.entity('Q102425731');e['claims']['P195'][0]['qualifiers']={'P582':[]}
  with self.assertRaises(AssertionError):f.facts(e,self.labels)
 def test_qualified_creator_not_silently_unqualified(self):
  e=self.entity('Q102425731');e['claims']['P170'][0]['qualifiers']={'P1480':[]}
  with self.assertRaises(AssertionError):f.facts(e,self.labels)
 def test_unscoped_inventory_requires_review(self):
  e=self.entity('Q102425731');e['claims']['P217'][0].pop('qualifiers',None)
  with self.assertRaises(AssertionError):f.facts(e,self.labels)
 def test_1970exact_is_eligible(self):self.assertEqual(f.creation(self.date(1970)),(1970,1970,'exact'))
 def test_1971not_eligible(self):
  with self.assertRaises(AssertionError):f.creation(self.date(1971))
 def test_circa1970held(self):
  r=self.date(1970);r['qualifiers']=copy.deepcopy(f.w.one(self.entity('Q114036745'),'P571')['qualifiers'])
  with self.assertRaises(AssertionError):f.creation(r)
 def test_decade_not_invented_as_year(self):
  r=self.date(1960);r['mainsnak']['datavalue']['value']['precision']=8
  with self.assertRaises(AssertionError):f.creation(r)
 def test_unknown_calendar_held(self):
  r=self.date(1850);r['mainsnak']['datavalue']['value']['calendarmodel']='http://www.wikidata.org/entity/Q99999999'
  with self.assertRaises(AssertionError):f.creation(r)
 def test_unknown_uncertainty_held(self):
  r=self.date(1850);r['mainsnak']['datavalue']['value']['after']=2
  with self.assertRaises(AssertionError):f.creation(r)
 def test_one_sided_range_not_filled(self):
  r=copy.deepcopy(f.w.one(self.entity('Q101310453'),'P571'));r['qualifiers'].pop('P1326')
  with self.assertRaises(AssertionError):f.creation(r)
 def test_grouping_claim_held(self):
  e=self.entity('Q102425731');e['claims']['P361']=[dict(rank='normal',mainsnak=dict(snaktype='value',datavalue=dict(value={'id':'Q1'})))]
  with self.assertRaises(AssertionError):f.facts(e,self.labels)

if __name__=='__main__':unittest.main()
