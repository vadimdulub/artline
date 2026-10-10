#!/usr/bin/env python3
"""Offline source chronology, identity, grouping and mutation guards; no database fixtures."""
import copy,importlib.util,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-birmingham-apply-20261007.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a);w=a.w;m=a.m
class Dates(unittest.TestCase):
 def test_exact1970(self):self.assertEqual(w.creation('1970')['last'],1970)
 def test_circa1970_held(self):self.assertIsNotNone(w.creation('About 1970')['date_issue'])
 def test_post1970_held(self):self.assertIsNotNone(w.creation('1971')['date_issue'])
 def test_slash_envelope(self):self.assertEqual((w.creation('1624/1626')['first'],w.creation('1624/1626')['last']),(1624,1626))
 def test_short_slash(self):self.assertEqual((w.creation('About 1875/80')['first'],w.creation('About 1875/80')['last']),(1875,1880))
 def test_century_qualifier_whole_bounds(self):self.assertEqual((w.creation('Late 14th-early 15th century')['first'],w.creation('Late 14th-early 15th century')['last']),(1301,1500))
 def test_cross_cutoff_century(self):self.assertIsNotNone(w.creation('Early 20th century')['date_issue'])
 def test_cultural_context_suffix(self):self.assertEqual(w.creation('Qing dynasty (1644-1912), 1882')['first'],1882)
 def test_inconsistent_cultural_period(self):self.assertIsNotNone(w.creation('Qing dynasty (1644-1912), 1920')['date_issue'])
 def test_unknown_stays_unknown(self):self.assertEqual(w.creation(None)['date_precision'],'unknown')
 def test_open_after_held(self):self.assertIsNotNone(w.creation('After 1649')['date_issue'])
class Evidence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=a.records();cls.byid={r['facts']['source_id']:r for r in cls.records};cls.held={r['source_id']:r for r in m.load(a.RUN/'native-followup-queue-001.json.gz')['rows']}
 def test_all_chains_and_unique_objects(self):
  self.assertEqual(len(self.records),134);self.assertEqual(len({r['facts']['native_object_id'] for r in self.records}),134);self.assertEqual(len({r['facts']['inventory'] for r in self.records}),134)
 def test_all_selected_accounted(self):self.assertEqual(len(self.byid)+len(self.held),180)
 def test14_editorial_holds(self):self.assertEqual(sum(r['review_state']=='editorial_hold' for r in self.held.values()),14)
 def test32_source_holds(self):self.assertEqual(sum(r['review_state']=='source_hold' for r in self.held.values()),32)
 def test_existing_duplicates_held(self):self.assertTrue({'george-iii','the-gardener','sierra-storm','a-race-meeting-at-jacksonville-alabama','moroccan-scene'}.issubset(self.held))
 def test_date_conflict_not_new_work(self):self.assertIn('WikiArt1588',self.held['the-judgment-of-paris']['editorial_reason'])
 def test_alias_version_hold(self):self.assertIn('Cornelius Johnson',self.held['portrait-of-a-lady']['editorial_reason'])
 def test_source_sitter_conflict_held(self):self.assertIn('Sir George',self.held['sarah-rowlls-chad']['editorial_reason'])
 def test_source_artist_qualification(self):self.assertEqual(self.byid['judith']['facts']['creator_label'],'Possibly School of Guido Reni')
 def test_former_attribution_not_current_creator(self):
  f=self.byid['gilles-du-faing']['facts'];self.assertEqual(f['creator_label'],'Unknown artist, Flemish');self.assertIn('Formerly attributed',f['native_artist_field'])
 def test_workshop_not_definite_artist(self):self.assertTrue(self.byid['madonna-and-christ-child-with-infant-saint-john-the-baptist-and-three-angels']['facts']['creator_label'].startswith('Workshop'))
 def test_copy_own_date(self):
  f=self.byid['copy-of-lansdowne-portrait-of-george-washington-by-gilbert-stuart']['facts'];self.assertEqual(f['first'],1965);self.assertEqual(f['creator_label'],'Theodore Ramos')
 def test_sitter_death_not_creation(self):self.assertEqual(self.byid['margaret-george-mcglathery-died-about-1830']['facts']['first'],1817)
 def test_two_sided_mural_one_object(self):self.assertEqual(self.byid['the-pure-land-of-amitabha-front-the-miracles-of-wen-shu-manjusri-back']['facts']['inventory'],'1987.34.1-.2')
 def test_album_one_object(self):self.assertEqual(self.byid['album-of-bird-and-flower-paintings-10-leaves']['facts']['inventory'],'1991.752.1-.10')
 def test_genji_separate_accessioned_leaves(self):self.assertEqual(len({r['facts']['inventory'] for sid,r in self.byid.items() if 'tale-of-genji' in sid}),6)
 def test_copyright_not_accession(self):
  f=self.byid['ornette']['facts'];self.assertEqual(f['inventory'],'2002.129');self.assertIn('image',f['credit_line'])
 def test_native_post_id_not_accession(self):self.assertTrue(all(r['facts']['native_object_id']!=r['facts']['inventory'] for r in self.records))
 def test_unrelated_inventory_collisions_do_not_match(self):self.assertTrue(all(not h['relevant'] for r in self.records for h in r['decision']['comparison']['inventory_hits']))
 def test_rights_and_provenance_captured(self):
  r=self.byid['tragedy-at-sea'];self.assertIn('1929',r['facts']['provenance']);self.assertIn('1975',r['facts']['provenance']);self.assertTrue(w.checked_record(m.ROOT/r['decision']['source_reference']['path'])[1]['source_text'])
 def test_all_dates_eligible_no_display_projection(self):
  for r in self.records:
   f=r['facts'];self.assertLessEqual(f['last'],1970);v=a.expected_art(r);self.assertEqual(v['status'],'review');self.assertNotIn('current_location_text',v)
 def test_no_punctuation_title_alias(self):self.assertNotIn('?',self.byid['palden-lhamo-remati-with-retinue']['facts']['titles'])
 def test_official_ng_physical_version_review(self):self.assertIn('NG6593',self.byid['still-life-of-flowers-fruit-shells-and-insects']['decision']['basis'])
 def test_empty_facet_is_valid_zero_result(self):
  hits=[]
  for ref in m.load(a.RUN/'discovered-001.json.gz')['index_references']:
   x=m.load(m.ROOT/ref['path'])
   if x['request'].get('search')=='icon':hits.append(w.c.index(w.c.body(x['capture'])))
  self.assertEqual(len(hits),1);self.assertEqual(hits[0]['rows'],[]);self.assertEqual(hits[0]['pager']['total_rows'],0)
 def test_hash_mutation_rejected(self):
  with tempfile.TemporaryDirectory(prefix='artline-birmingham-proof-') as tmp:
   p=Path(tmp)/'record';p.write_bytes(b'changed')
   with self.assertRaises(AssertionError):a.checked_reference(dict(path=str(p),sha256='0'*64))
 def test_duplicate_fields_rejected(self):
  x=m.load(m.ROOT/self.records[0]['decision']['source_reference']['path']);p=copy.deepcopy(x['parsed']);p['fields'].append(p['fields'][0])
  with self.assertRaises(AssertionError):w.facts(x,p)
 def test_index_title_conflict_rejected(self):
  x=m.load(m.ROOT/self.records[0]['decision']['source_reference']['path']);x['index']['title']='Different work'
  with self.assertRaises(AssertionError):w.facts(x,x['parsed'])
if __name__=='__main__':unittest.main()
