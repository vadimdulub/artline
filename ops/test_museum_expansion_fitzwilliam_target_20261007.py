import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-fitzwilliam-target-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class FitzwilliamTarget(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records=a.records();cls.holdings=a.holding_records()
 def test_selection_contains_russian_painting(self):
  r=next(r for r in self.records if r['facts']['source_id']=='3022');self.assertEqual(r['facts']['creator_label'],'Kustodiev, Boris');self.assertEqual(r['facts']['first'],1926);self.assertEqual(r['facts']['inventory'],'1770')
 def test_retained_panel_not_whole_retable(self):
  r=next(r for r in self.records if r['facts']['source_id']=='3041');self.assertIn('only this panel',r['decision']['identity_note']);self.assertEqual(r['facts']['creator_label'],'Unknown');self.assertEqual(r['facts']['dimensions_text'],'61 69.8')
 def test_rejected_historical_attribution_stays_unknown(self):
  r=next(r for r in self.records if r['facts']['source_id']=='3016');self.assertEqual(r['facts']['creator_label'],'Unknown');self.assertIn('Ruysch',r['facts']['creation_notes'][0])
 def test_separate_vernet_inventories(self):
  rs=[r for r in self.records if r['facts']['source_id'] in ['2986','2988']];self.assertEqual({r['facts']['inventory'] for r in rs},{'PD.20-1997','PD.22-1997'})
 def test_followup_not_reusing_existing_objects(self):
  self.assertEqual(len(self.records),26);self.assertFalse({r['facts']['source_id'] for r in self.records}&{'3051','3158','3637','3956','4008','4028'})
 def test_holding_reconciles_four_existing_ids(self):
  self.assertEqual(len(self.holdings),4);self.assertEqual({r['facts']['source_id'] for r in self.holdings},{'3637','3956','4008','4028'})
 def test_inventory_asterisk_not_erased(self):
  r=next(r for r in self.holdings if r['facts']['source_id']=='4008');self.assertEqual(r['facts']['inventory'],'456*')
 def test_wikidata_exact_native_pointer(self):
  r=next(r for r in self.holdings if r['facts']['source_id']=='4028');entity=r['source']['parsed']['entities']['Q50821640'];self.assertEqual(a.value(entity,'P8910'),'4028');self.assertEqual(a.value(entity,'P217'),'657')
 def test_nonunique_object_pointer_rejected(self):
  r=next(r for r in self.holdings if r['facts']['source_id']=='4028');entity=copy.deepcopy(r['source']['parsed']['entities']['Q50821640']);entity['claims']['P8910'].append(copy.deepcopy(entity['claims']['P8910'][0]))
  with self.assertRaises(AssertionError):a.value(entity,'P8910')
 def test_harvard_portrait_not_linked_to_fitzwilliam(self):
  self.assertNotIn('3958',a.HOLDINGS);src=a.m.load(a.RUN/'existing-followup-exact-sources-001.json.gz');j=next(r for r in src['records'] if r['url'].endswith('Q106874666.json'))['parsed']['entities']['Q106874666'];self.assertEqual({r['mainsnak']['datavalue']['value'] for r in j['claims']['P217']},{'1943.928'})
 def test_unconfirmed_generic_mason_landscape_not_linked(self):self.assertNotIn('3632',a.HOLDINGS)
 def test_holdings_do_not_authorize_metadata_replacement(self):
  before=a.m.load(a.RUN/'existing-followup-scope-001.json.gz')['before'];after=copy.deepcopy(before);aid=self.holdings[0]['artwork_id'];next(r for r in after['artworks'] if r['id']==aid)['creation_year_start']=1900
  with self.assertRaises(AssertionError):a.assert_delta(before,after,self.holdings,'test')
 def test_actual_new_source_fields_survive(self):
  for r in self.records:
   art=a.prior.expected_art(r);self.assertEqual(art['status'],'review');self.assertEqual(art['creation_year_start'],r['facts']['first']);self.assertLessEqual(art['creation_year_end'],1970)
 def test_update_limitation_retained_on_all_actions(self):
  for r in self.records+self.holdings:self.assertIn('April2026',r['decision']['limitation'])

if __name__=='__main__':unittest.main()
