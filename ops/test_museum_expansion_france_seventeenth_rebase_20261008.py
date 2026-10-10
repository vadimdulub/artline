"""Unrelated creator-pool growth must not conceal changed object matches."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-france-seventeenth-apply-v2-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class RebaseTests(unittest.TestCase):
 def test_unrelated_pool_growth_ignored(self):
  x={'source_id':'object','creator_pool_ids':['one'],'exact_title_hits':[]};y=copy.deepcopy(x);y['creator_pool_ids'].append('unrelated')
  self.assertEqual(a.comparable(x),a.comparable(y))
 def test_new_identity_hit_not_ignored(self):
  x={'source_id':'object','creator_pool_ids':['one'],'exact_title_hits':[]};y=copy.deepcopy(x);y['exact_title_hits']=[{'id':'new'}]
  self.assertNotEqual(a.comparable(x),a.comparable(y))
 def test_mutated_comparator_not_ignored(self):
  x={'source_id':'object','creator_pool_ids':['one'],'leads':[{'id':'one','medium_text':'oil'}]};y=copy.deepcopy(x);y['leads'][0]['medium_text']='ivory'
  self.assertNotEqual(a.comparable(x),a.comparable(y))
if __name__=='__main__':unittest.main()
