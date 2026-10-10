"""Offline preservation and source-boundary checks. No database fixtures."""
import collections,copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-augustiner-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ds=a.r.build();cls.by={v['number']:v for v in cls.ds};cls.news,cls.links=a.records()
 def test_decision_totals(self):self.assertEqual(collections.Counter(v['state'] for v in self.ds),{'approved_review_only_addition':129,'editorial_hold':1})
 def test_unknown_dates(self):self.assertEqual([v['decision']['number'] for v in self.news if v['facts']['first'] is None],[6,121,129]);self.assertTrue(all(v['facts']['last'] is None and v['facts']['date_precision']=='unknown' for v in self.news if v['facts']['first'] is None))
 def test_nonempty_required_date(self):self.assertTrue(all(a.expected_art(v)['date_display'] for v in self.news))
 def test_creation_cutoff(self):self.assertEqual(sum(v['facts']['first'] is not None for v in self.news),126);self.assertTrue(all(v['facts']['last']<=1970 for v in self.news if v['facts']['last'] is not None))
 def test_date_conflict_held(self):self.assertEqual(self.by[103]['state'],'editorial_hold');self.assertIn('1852/53',self.by[103]['hold_reason'])
 def test_acquisition_not_creation(self):self.assertEqual(self.by[119]['facts']['first'],1884);self.assertIn('2024',self.by[119]['facts']['source_fields']['report'])
 def test_reproductive_print_not_original(self):self.assertEqual(self.by[100]['facts']['first'],1807);self.assertIn('1761',self.by[100]['facts']['title']);self.assertEqual(self.by[101]['facts']['first'],1809)
 def test_publisher_and_inventor_roles(self):self.assertIn('(Erfinder)',self.by[89]['facts']['creator_label']);self.assertIn('(Verleger)',self.by[89]['facts']['creator_label']);self.assertIn('(Inventor)',self.by[99]['facts']['creator_label'])
 def test_companion_objects_distinct(self):self.assertNotEqual(self.by[72]['facts']['title'],self.by[73]['facts']['title']);self.assertEqual(len({self.by[n]['facts']['title'] for n in [77,78,79]}),3)
 def test_repeat_acquisition_one_object(self):self.assertEqual(sum(v['facts']['native_id']=='graessel-muehlenbach' for v in self.ds),1)
 def test_original_and_reproduction_separate(self):self.assertEqual(self.by[118]['facts']['first'],1880);self.assertEqual(self.by[118]['facts']['work_type'],'drawing');self.assertIn('1916',self.by[118]['comparison_basis'])
 def test_mixed_technique_not_invented_type(self):self.assertEqual(self.by[3]['facts']['work_type'],'unknown');self.assertTrue(self.by[3]['source_fidelity_corrections'])
 def test_group_medium_not_individual(self):self.assertTrue(all(self.by[n]['facts']['medium'] is None for n in range(60,67)))
 def test_sitter_uncertainty_preserved(self):self.assertIn('Marie Hanemann?',self.by[106]['facts']['title'])
 def test_unknown_creator_label_preserved(self):self.assertEqual(self.by[112]['facts']['creator_label'],'Monogrammist WW')
 def test_no_existing_reassignment(self):self.assertFalse(self.links);self.assertEqual(len({v['artwork_id'] for v in self.news}),129)
 def test_no_images_or_publication(self):
  for v in self.news:
   art=a.expected_art(v);self.assertEqual(art['status'],'review');self.assertNotIn('primary_media_id',art);self.assertNotIn('published_at',art)
 def test_reject_title_change(self):
  b={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};b['artworks']=[dict(id='original',title='Original',current_institution_id=None)];c=copy.deepcopy(b);c['artworks'][0]['title']='Changed'
  with self.assertRaises(AssertionError):a.assert_delta(b,c,[],'digest')
 def test_reject_media_change(self):
  b={k:[] for k in ['artworks','artists','media','media_assets','identifiers','museums','citations','assertions']};c=copy.deepcopy(b);c['media']=[dict(artwork_id='unexpected')]
  with self.assertRaises(AssertionError):a.assert_delta(b,c,[],'digest')
 def test_report_sections_and_selected_scope(self):
  titles={v['facts']['title'] for v in self.ds};self.assertFalse(titles&{'Personae','Schwarzwald-Cego','Schattenorchester III','Hop Frog'});self.assertEqual({v['institution_id'] for v in self.ds},{a.IID})
if __name__=='__main__':unittest.main(verbosity=2)
