"""Offline safeguards for creation dates, print editions and bounded Rhodes selection."""
import importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-rhodes-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r)
class RhodesTests(unittest.TestCase):
 def test_cutoff(self):
  rows=r.i.f.rows();self.assertEqual([v['number']for v in rows if v['metadata_state']=='outside_creation_scope'],[1,4,119])
 def test_repository_dates_not_creation(self):
  f=r.i.f.rows()[0]['facts'];self.assertEqual((f['first'],f['last']),(1948,1948));self.assertEqual(f['source_fields']['onlineAt'],'2023-12-12')
 def test_century_qualifier(self):
  self.assertEqual(r.i.f.date('αρχές 19ου αιώνα'),(1801,1900,'century'))
 def test_alternative_year(self):self.assertEqual(r.i.f.date('1777 ή 1778'),(1777,1778,'range'))
 def test_no_unknown_invention(self):self.assertEqual(r.i.f.date(None),(None,None,'unknown'))
 def test_unknown_syntax_fails(self):
  with self.assertRaises(ValueError):r.i.f.date('19ος ή20ός αιώνας')
 def test_edition_conflicts_explicit(self):
  ds={v['number']:v for v in r.build()};self.assertEqual(ds[78]['facts']['date_precision'],'range');self.assertEqual((ds[78]['facts']['first'],ds[78]['facts']['last']),(1752,1757));self.assertIn('1757',ds[78]['basis'])
 def test_probable_edition_preserved(self):
  ds={v['number']:v for v in r.build()};self.assertEqual(ds[32]['facts']['date_precision'],'circa');self.assertEqual(ds[81]['facts']['date_precision'],'circa_range')
 def test_duplicate_and_composite_holds(self):
  ds={v['number']:v for v in r.build()}
  for n in [26,37,70,73,84,105,115]:self.assertEqual(ds[n]['state'],'editorial_version_or_date_hold')
 def test_existing_source_not_duplicated(self):
  ds=r.build();self.assertTrue(any(v['state']=='already_catalogued'for v in ds));self.assertTrue(all(v['state']=='already_catalogued'for v in ds if v['comparison']['source_hits']))
 def test_study_is_not_finished_painting(self):
  ds={v['number']:v for v in r.build()};self.assertNotEqual(ds[82]['facts']['source_id'],ds[117]['facts']['source_id']);self.assertEqual(ds[74]['facts']['work_type'],'drawing')
 def test_empty_translation_never_matches_null_alternate(self):
  x=r.m.load(r.RUN/'production-identity-002.json.gz');self.assertLess(len(x['comparisons'][13]['hits']),10)
 def test_no_images_or_published_changes(self):
  for v in r.build():self.assertFalse(v['facts']['image_downloaded']);self.assertNotIn('status',v['facts'])
if __name__=='__main__':unittest.main()
