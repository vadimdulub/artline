"""Offline source/parser regression tests; no database connection or fixture writes."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-baltimore-review-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);f=r.f
class NativeEvidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={x['number']:x for x in f.m.load(r.CANDIDATES)['rows']}
 def raw(self,n):return f.c.body(f.m.load(f.checked(self.rows[n]['source_reference']))['capture'])
 def test_all_completed_pages_reparse_without_source_changes(self):
  for x in self.rows.values():self.assertEqual(x,f.parse(f.checked(x['source_reference'])))
 def test_all_artist_contributors_survive_truncated_hero(self):
  x=self.rows[8]['facts'];self.assertIn('Aubry-Lecomte',x['creator_label']);self.assertIn('Gérard',x['creator_label']);self.assertNotIn('Lemercier',x['creator_label'])
 def test_printers_and_publishers_remain_evidence_with_roles(self):
  x=self.rows[8]['facts'];self.assertTrue(any(v['name']=='Lemercier' and v['role']=='Printer' for v in x['source_makers']));self.assertTrue(any(v['role']=='Publisher' for v in x['source_makers']))
 def test_century_does_not_use_artist_biography(self):
  x=self.rows[9]['facts'];self.assertEqual((x['first'],x['last'],x['date_precision']),(1501,1600,'century'))
 def test_acquisition_prefix_not_creation_date(self):
  x=self.rows[1]['facts'];self.assertTrue(x['inventory'].startswith('2009'));self.assertEqual((x['first'],x['last']),(1947,1947))
 def test_creation_cutoff_and_unknown_date_require_review(self):
  self.assertIsNotNone(f.c.dates.creation('1971')['date_issue']);self.assertIsNotNone(f.c.dates.creation('1965-1975')['date_issue']);self.assertIsNotNone(f.c.dates.creation(None)['date_issue']);self.assertIsNone(f.c.dates.creation('1970')['date_issue'])
 def test_trimmed_sheet_dimension_split_preserves_qualification(self):
  medium,dimensions=f.physical('Engraving, Sheet (trimmed within platemark): 231 × 142 mm.');self.assertEqual(medium,'Engraving');self.assertEqual(dimensions,'Sheet (trimmed within platemark): 231 × 142 mm.')
 def test_frame_and_sight_are_not_combined_or_converted(self):
  x=self.rows[10]['facts'];self.assertTrue(x['dimensions_text'].startswith('Framed:'));self.assertIn('Sight:',x['dimensions_text']);self.assertEqual(x['medium'],'Oil on canvas')
 def test_loan_hold_and_sketchbook_hold_are_excluded(self):
  self.assertIn('holding_or_custody_requires_review',self.rows[23]['review_flags']);ds={v['number']:v for v in r.build()}
  for n in [15,23]:self.assertEqual(ds[n]['state'],'editorial_hold')
  self.assertEqual(sum(v['state']=='approved_review_only_addition' for v in ds.values()),21)
 def test_multi_sketch_prints_remain_single_separate_sheets(self):
  a=self.rows[5]['facts'];b=self.rows[6]['facts'];self.assertNotEqual(a['inventory'],b['inventory']);self.assertIn('Plate 40',str(a['source_fields']));self.assertIn('Plate 51',str(b['source_fields']))
 def test_conflicting_declared_urls_are_rejected(self):
  raw=self.raw(1).decode();soup=f.BeautifulSoup(raw,'html.parser');tag=soup.new_tag('link',rel='canonical',href='https://example.invalid/different-object');soup.head.append(tag)
  with self.assertRaises(AssertionError):f.extract(str(soup))
 def test_error_capture_cannot_be_parsed_as_success(self):
  x=f.m.load(f.RUN/'objects-001/object-001.json.gz');cap=copy.deepcopy(x['capture']);cap['receipt']['status']=429
  with self.assertRaises(AssertionError):f.c.body(cap)
 def test_partial_capture_never_claims_selected_queue_complete(self):
  x=f.m.load(r.CANDIDATES);self.assertTrue(x['partial']);self.assertEqual(x['capture_count'],23);self.assertEqual(x['expected_capture_count'],244)
 def test_source_subject_does_not_invent_cultural_context(self):
  for row in self.rows.values():self.assertNotIn('cultural_context',row['facts'])
if __name__=='__main__':unittest.main()
