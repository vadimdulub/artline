"""Real-source creator separation checks; no database fixtures."""
import importlib.util,unittest
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-wallace-refinement-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

class WallaceCreatorParts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={v.get('facts',{}).get('inventory'):v for v in r.m.load(r.RUN/'native-candidates-002.json.gz')['rows'] if 'facts' in v}
 def parts(self,inv):
  row=self.rows[inv];src=r.m.load(r.m.ROOT/row['source_reference']['path']);el=BeautifulSoup(r.f.c.saved_body(src['capture']),'html.parser').select_one('#collectionDetail .ListArtist');return r.creator_parts(el)
 def test_approximate_birth_and_after_death_are_biography(self):
  v=self.parts('P758');self.assertEqual(v['creator_label'],'Antonio Bencini');self.assertEqual(v['parts'][0]['biographical_labels'],['c. 1710 - after 1780'])
 def test_activity_dates_stay_separate_from_name(self):
  v=self.parts('M86');self.assertEqual(v['creator_label'],'Julie Corneo');self.assertEqual(v['parts'][0]['biographical_labels'],['active between: c. 1800 - 1805'])
 def test_style_prefix_is_preserved(self):
  self.assertEqual(self.parts('M2')['creator_label'],'Style of Jacques-Antoine Arlaud')
 def test_after_attribution_survives_uncertain_lifespan(self):
  v=self.parts('P551');self.assertEqual(v['creator_label'],'After Joos van Cleve');self.assertIn('1540/1',v['parts'][0]['biographical_labels'][0])
 def test_generational_suffix_remains_label_but_query_uses_surname(self):
  v=self.parts('M25');self.assertEqual(v['creator_label'],'William Bone Senior');self.assertIn('bone',r.search_terms(dict(creator_label=v['creator_label'])))
 def test_fils_query_includes_distinguishing_name(self):
  v=self.parts('M16');self.assertEqual(v['creator_label'],'Berny fils');self.assertIn('berny',r.search_terms(dict(creator_label=v['creator_label'])))

if __name__=='__main__':unittest.main()
