"""Offline duplicate-discovery safeguards for observed Detroit attribution changes."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-detroit-followup-v3-20261007.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class IdentityAliases(unittest.TestCase):
 def row(self,n):return v.parse(v.f.RUN/('objects-001/object-%03d.json.gz'%n))
 def test_former_attribution_does_not_replace_current_creator(self):
  r=self.row(52);self.assertEqual(r['facts']['creator_label'],'Antonio Gonzalez Velazquez');self.assertIn('%giaquinto%',v.i.params_for([r])['patterns']);self.assertEqual(r['facts']['inventory'],'73.100')
 def test_current_school_qualifier_survives_named_artist_aliases(self):
  r=self.row(78);self.assertEqual(r['facts']['creator_label'],'School of Rembrandt Harmensz van Rijn');p=v.i.params_for([r]);self.assertTrue({'%rembrandt%','%hoogstraten%','%flinck%','%bray%','%dou%'}.issubset(p['patterns']));self.assertIn('version_or_qualified_creator_review',r['review_flags'])
 def test_historical_sitter_is_discovery_only(self):
  r=self.row(75);self.assertEqual(r['facts']['title'],'Portrait of Sophia, Princess Palatine');self.assertIn('elizabeth of bohemia',v.i.params_for([r])['title_keys']);self.assertEqual(r['facts']['date_display'],'1641')
 def test_school_work_has_bounded_subject_discovery(self):
  r=self.row(12);p=v.i.params_for([r]);self.assertIn('%pilat%wash%',p['subject_patterns']);self.assertLessEqual(len(p['subject_patterns']),4);self.assertEqual(r['facts']['creator_label'],'School of Florence');self.assertEqual(r['facts']['source_makers'],[])
if __name__=='__main__':unittest.main()
