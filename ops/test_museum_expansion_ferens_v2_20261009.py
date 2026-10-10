"""Offline regressions for Ferens source identity, chronology and qualifications."""
import copy,importlib.util,unittest
from pathlib import Path
z=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-ferens-review-20261009.py'));r=importlib.util.module_from_spec(z);z.loader.exec_module(r);f=r.f;m=r.m;RUN=r.RUN
class FerensReview(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows={x['number']:x for x in m.load(RUN/'native-candidates-001.json.gz')['rows']};cls.decisions={x['number']:x for x in r.build()};cls.accepted=[d for d in cls.decisions.values() if d['state']=='approved_review_only_addition']
 def test_all_selected_metadata_reproduced(self):
  self.assertEqual(len(self.rows),180)
  for x in self.rows.values():self.assertEqual(f.facts(m.load(r.checked(x['source_reference']))),x['facts'])
 def test_official_https_native_source_chain(self):
  x=m.load(RUN/'holding-source-001.json');soup=f.p.n.BeautifulSoup(f.body(x['capture']),'html.parser');links={a['href'] for a in soup.select('a[href]')};self.assertEqual(x['url'],'https://www.hullmuseums.co.uk/collections-ferens');self.assertTrue(all(v['url'] in links for v in x['catalogue_links']));self.assertTrue(x['failed_transaction_rolled_back']);self.assertEqual(x['new_records_remaining'],0)
 def test_bounded_selection(self):
  s=m.load(RUN/'native-selection-001.json.gz');self.assertEqual((len(s['rows']),s['selected_count'],len(s['index_references'])),(288,180,3))
 def test_index_body_chain(self):
  s=m.load(RUN/'native-selection-001.json.gz')
  for dep in s['index_references']:
   x=m.load(r.checked(dep));rows,nxt=f.dates.index(f.body(x['capture']),x['capture']['receipt']['url']);self.assertEqual(rows,x['rows']);self.assertEqual(nxt,x['next_url'])
 def test_display_labels_are_not_current_display(self):
  self.assertTrue(all('Location on Display:' in x['facts']['native_fields'] for x in self.rows.values()));self.assertTrue(all('no current display' in x['facts']['source_limitation'] for x in self.rows.values()))
 def test_lifetimes_held(self):
  for n in [4,67]:self.assertEqual(self.decisions[n]['state'],'editorial_hold')
 def test_conflicting_native_creators_dates_held(self):
  for n in [43,47,48,57,208]:self.assertEqual(self.decisions[n]['state'],'editorial_hold')
 def test_rathbone_qualified_period(self):
  for n in [39,40]:
   x=self.rows[n]['facts'];self.assertEqual((x['first'],x['last'],x['date_display']),(1700,1799,'late eighteenth century'));self.assertEqual(x['native_date_display'],'1750-1807')
 def test_storck_creation_not_lifetime(self):
  x=self.rows[16]['facts'];self.assertEqual((x['first'],x['last']),(1600,1699));self.assertEqual(x['native_date_display'],'1641-1692')
 def test_stevens_discrepancy_retained_and_held(self):
  for n in [3,5]:
   self.assertEqual(self.rows[n]['facts']['date_display'],'about 1600');self.assertEqual(self.decisions[n]['state'],'editorial_hold')
 def test_attribution_is_not_upgraded(self):
  for n in [6,31,125]:self.assertTrue(self.rows[n]['facts']['creator_label'].startswith('Attributed to'))
 def test_copyist_not_prototype_artist(self):
  self.assertEqual(self.rows[38]['facts']['creator_label'],'Unknown artist; copy after Reynolds');self.assertIn('copy after Guido Reni',self.rows[45]['facts']['creator_label'])
 def test_ensemble_counted_once(self):
  x=self.decisions[2];self.assertIn('three-panel ensemble, counted once',x['basis']);self.assertEqual(sum(d['facts']['inventory']=='KINCM:2005.4735' for d in self.accepted),1)
 def test_two_russian_icons_included(self):
  for n in [69,70]:
   x=self.decisions[n];self.assertEqual(x['state'],'approved_review_only_addition');self.assertEqual(x['facts']['creator_label'],'Russian School');self.assertEqual(x['facts']['object_form'],'icon');self.assertEqual((x['facts']['first'],x['facts']['last']),(1800,1899))
 def test_anonymous_creator_retained(self):self.assertEqual(self.rows[72]['facts']['creator_label'],'unknown artist')
 def test_depicted_events_not_creation(self):
  self.assertEqual(self.rows[91]['facts']['first'],1819);self.assertEqual(self.rows[149]['facts']['first'],1852);self.assertEqual(self.rows[156]['facts']['first'],1855)
 def test_study_and_finished_work_separate(self):
  a,b=(self.rows[n]['facts'] for n in [197,207]);self.assertNotEqual(a['inventory'],b['inventory']);self.assertEqual(a['medium'],'Oil on panel');self.assertEqual(b['medium'],'Oil on canvas');self.assertIn('first of two preliminary',a['description']);self.assertEqual(a['first'],1872)
 def test_existing_hull_identities_held(self):
  for n in [201,203,204]:self.assertEqual(self.decisions[n]['state'],'editorial_hold');self.assertTrue(self.decisions[n]['comparison']['accession_alias_hits'])
 def test_circa_qualifier_not_dropped(self):self.assertEqual(self.rows[196]['facts']['date_precision'],'circa')
 def test_detail_index_tamper_rejected(self):
  x=copy.deepcopy(m.load(r.checked(self.rows[69]['source_reference'])));x['index']['title']='Different icon'
  with self.assertRaises(AssertionError):f.facts(x)
 def test_editorial_inventory_uniqueness_and_cutoff(self):
  self.assertEqual(len(self.accepted),136);self.assertEqual(len({x['facts']['inventory'] for x in self.accepted}),136);self.assertTrue(all(x['facts']['last']<=1970 for x in self.accepted));self.assertEqual(sum(x['state']=='editorial_hold' for x in self.decisions.values()),44)
if __name__=='__main__':unittest.main()
