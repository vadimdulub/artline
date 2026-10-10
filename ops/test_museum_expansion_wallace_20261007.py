"""Offline creation and source chain checks on real retained Wallace pages."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-wallace-facts-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
s=importlib.util.spec_from_file_location('identity',Path(__file__).with_name('museum-expansion-wallace-identity-20261007.py'));identity=importlib.util.module_from_spec(s);s.loader.exec_module(identity)

class WallaceEvidence(unittest.TestCase):
 def test_explicit_about_range_retains_circa_and_expands_abbreviation(self):
  v=f.creation('about 1808-12');self.assertEqual((v['first'],v['last'],v['date_precision']),(1808,1812,'circa_range'))
 def test_period_alternatives_keep_whole_century(self):
  v=f.creation('mid or late 18th century');self.assertEqual((v['first'],v['last'],v['date_precision']),(1700,1799,'century'))
 def test_unknown_or_cutoff_crossing_dates_are_held(self):
  for value in [None,'about 1970','20th century','1960-1980','before 1980','1800 or 1900']:
   with self.subTest(value=value):self.assertIsNotNone(f.creation(value)['date_issue'])
 def test_initial_object_is_reparsed_with_provenance_and_signature(self):
  r,p,t=f.checked_record(f.RUN/'native-objects-001/page-001-row-00.json.gz');v=f.facts(r,p,t);self.assertEqual(v['inventory'],'P618');self.assertEqual(v['first'],1849);self.assertIn('1866',v['provenance']);self.assertIn('1849',v['marks'])
 def test_frame_measurements_are_evidence_but_not_object_dimensions(self):
  r,p,t=f.checked_record(f.RUN/'native-objects-001/page-001-row-00.json.gz');v=f.facts(r,p,t);self.assertEqual(v['dimensions_text'],'Image size: 46.2 x 68.3 cm');self.assertIn('Frame size: 78 x 97 x 10 cm',v['all_dimensions'])
 def test_creator_qualification_survives_lifespan_removal(self):
  r,p,t=f.checked_record(f.RUN/'native-objects-001/page-001-row-07.json.gz');self.assertEqual(p['creator_label'],'Style of Jacques-Antoine Arlaud');self.assertIn('1668 - 1743',p['creator_statement']);v=f.facts(r,p,t);self.assertEqual((v['first'],v['last']),(1700,1799))
 def test_minature_repetition_does_not_collapse_distinct_inventories(self):
  a=f.checked_record(f.RUN/'native-objects-001/page-001-row-12.json.gz')[1];b=f.checked_record(f.RUN/'native-objects-001/page-001-row-13.json.gz')[1];self.assertEqual(a['title'],b['title']);self.assertNotEqual(a['source_id'],b['source_id']);self.assertNotEqual(a['inventory'],b['inventory'])
 def test_hyphenated_native_surname_checks_shorter_authority_alias(self):
  r,p,t=f.checked_record(f.RUN/'native-objects-001/page-001-row-03.json.gz');terms=identity.search_terms(f.facts(r,p,t));self.assertIn('arlaud',terms);self.assertIn('jurine',terms)
 def test_stable_native_url_checks_query_order_and_default_port_variants(self):
  r,p,t=f.checked_record(f.RUN/'native-objects-001/page-001-row-00.json.gz');params=identity.params_for([dict(facts=f.facts(r,p,t))]);self.assertIn(p['literal_bookmark'],params['source_urls']);self.assertIn('https://wallacelive.wallacecollection.org/eMP/eMuseumPlus?module=collection&objectId=65552&service=ExternalInterface',params['source_urls'])

if __name__=='__main__':unittest.main()
