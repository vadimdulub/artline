import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('e',Path(__file__).with_name('museum-expansion-fitzwilliam-review-20261007.py'));e=importlib.util.module_from_spec(s);s.loader.exec_module(e)

class FitzwilliamSources(unittest.TestCase):
 def obj(self,i):return e.m.load(e.RUN/'native-objects-001'/f'{i}.json.gz')
 def test_public_json_and_html_receipts(self):
  for i in [2153,125113,125132,30375,309474,169776]:
   p=e.RUN/'native-objects-001'/f'{i}.json.gz';self.assertEqual(e.checked_object(e.f.reference(p)),self.obj(i))
 def test_date_is_creation_not_acquisition(self):
  f=e.source_facts(self.obj(2153));self.assertEqual((f['first'],f['last'],f['date_display']),(1706,1706,'1706'));self.assertEqual(f['inventory'],'50')
 def test_missing_creation_not_filled_from_life_or_acquisition(self):
  self.assertEqual(e.source_facts(self.obj(470))['date_issue'],'creation date and period absent')
 def test_non_year_json_corruption_is_held(self):
  self.assertEqual(e.source_facts(self.obj(1429))['date_issue'],'non-year literal production date')
 def test_open_ended_date_not_made_exact(self):
  self.assertEqual(e.source_facts(self.obj(419))['date_issue'],'open-ended or uncertain date qualifier')
 def test_qualified_workshop_creator_survives(self):
  f=e.source_facts(self.obj(649));self.assertIn('(workshop of)',f['creator_label']);self.assertEqual(f['first'],1558)
 def test_copy_qualification_survives(self):
  self.assertIn('(copy after)',e.source_facts(self.obj(525))['creator_label'])
 def test_anonymous_russian_icon_supported(self):
  f=e.source_facts(self.obj(125113));self.assertEqual((f['creator_label'],f['object_form'],f['work_type']),('Unknown','icon','painting'));self.assertEqual((f['first'],f['last'],f['date_display']),(1600,1699,'17th Century'));self.assertEqual(f['school_or_style'],['Russian'])
 def test_geographic_uncertainty_retained(self):
  f=e.source_facts(self.obj(125132));self.assertIn('Russian / Ukrainian',f['creation_notes'][0]);self.assertEqual((f['first'],f['last']),(1750,1799))
 def test_early_period_does_not_invent_subdivision(self):
  f=e.source_facts(self.obj(125139));self.assertEqual((f['first'],f['last'],f['date_display']),(1500,1599,'16th Century, Early'))
 def test_date_note_must_remain_available_to_editor(self):
  self.assertEqual(e.source_facts(self.obj(1051))['date_notes'],['1761 or the year before'])
 def test_multiple_creation_dates_not_collapsed(self):
  self.assertEqual(e.source_facts(self.obj(169689))['date_issue'],'multiple alternative production dates')
 def test_printing_matrix_not_counted_as_impression(self):
  f=e.source_facts(self.obj(309474));self.assertEqual((f['work_type'],f['entity_names']),('unknown',['printing plate']));self.assertEqual(f['first'],1877)
 def test_fragment_is_not_assumed_whole_manuscript(self):
  f=e.source_facts(self.obj(169776));self.assertEqual(f['work_type'],'manuscript_illumination');self.assertIn('reverse blank',f['notes']['Description'][0]);self.assertIn('follower or assistant',f['creator_label'])
 def test_bad_date_endpoint_rejected(self):
  x=copy.deepcopy(self.obj(2153));x['json']['parsed']['lifecycle']['creation'][0]['date'][0]['latest']=1900;self.assertEqual(e.source_facts(x)['date_issue'],'machine date differs from literal')
 def test_unresolved_duplicates_and_source_conflicts_not_selected(self):
  review=e.m.load(e.RUN/'native-editorial-001.json.gz');selected=set(review['selected_source_ids']);self.assertFalse(selected&{'3637','3632','3956','3958','1429','2583','1051','3691','525','3332','3786','3989','4008','4028'})
 def test_source_update_warning_and_no_display_claim(self):
  review=e.m.load(e.RUN/'native-editorial-001.json.gz')
  for d in review['decisions']:
   if d['state']=='approved_review_only_addition':self.assertIn('April2026',d['limitation']);self.assertIn('no current display',d['limitation'])
 def test_new_record_has_review_and_no_media_or_artist_mutation(self):
  s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-fitzwilliam-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
  rs=a.records();self.assertEqual(len(rs),163)
  for r in rs:
   art=a.expected_art(r);self.assertEqual(art['status'],'review');self.assertTrue(art['research_candidate']);self.assertLessEqual(art['creation_year_end'],1970);self.assertIn(art['object_form'],[None,'icon'])

if __name__=='__main__':unittest.main()
