"""Offline checks for real observed lifespan/activity ambiguities and former attributions."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('v',Path(__file__).with_name('museum-expansion-detroit-followup-20261007.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class Followup(unittest.TestCase):
 def row(self,n):return v.parse(v.f.RUN/('objects-001/object-%03d.json.gz'%n))
 def test_full_lifespan_date_range_is_held_without_rewriting_it(self):
  r=self.row(21);self.assertIn('creation_range_matches_creator_lifespan',r['review_flags']);self.assertEqual(r['facts']['date_display'],'between 1482 and 1525');self.assertEqual((r['facts']['first'],r['facts']['last']),(1482,1525))
 def test_alternative_birth_years_still_flag_lifespan_bounds(self):
  r=self.row(33);self.assertIn('creation_range_matches_creator_lifespan',r['review_flags']);self.assertEqual(r['facts']['date_display'],'between 1448 and 1494');self.assertIn('Lorenzo Costa',r['facts']['identity_creator_labels'])
 def test_activity_dates_are_not_described_as_lifespan(self):
  r=self.row(36);self.assertIn('creation_range_matches_creator_activity',r['review_flags']);self.assertNotIn('creation_range_matches_creator_lifespan',r['review_flags']);self.assertEqual(r['facts']['date_display'],'between 1356 and 1399')
 def test_former_attributions_expand_identity_without_changing_creator(self):
  r=self.row(19);self.assertEqual(r['facts']['creator_label'],'Francesco dai Libri');self.assertIn('Vincenzo Foppa',r['facts']['identity_creator_labels']);self.assertIn('Maestro dei Garofani',r['facts']['identity_creator_labels'])
if __name__=='__main__':unittest.main()
