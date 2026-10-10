"""Offline edge cases for creation evidence, versions and allowed holding-only changes."""
import copy,importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-southampton-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a);r=a.r;f=r.f;m=r.m
class SouthamptonReview(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows={v['number']:v for v in f.rows()};cls.ds={v['number']:v for v in r.build()}
 def test_actual_cutoff_not_lifetime(self):
  self.assertEqual(f.f.creation('1970')['first'],1970)
  for value in ['1971','1970 (c.)','1969–1971','1912 (exhibited)',None]:self.assertIsNotNone(f.f.creation(value)['date_issue'])
 def test_inventory_url_does_not_supply_accession(self):self.assertEqual(self.rows[43]['facts']['inventory'],'SOTAG : 3');self.assertIn('197914-3',self.rows[43]['facts']['source_url'])
 def test_inventory_aliases_do_not_change_catalogue_fact(self):self.assertEqual(f.f.inventory_aliases('SOTAG : 2006/57'),['2006/57','57/2006']);self.assertEqual(self.rows[32]['facts']['inventory'],'SOTAG : 2006/57')
 def test_acquisition_year_not_creation(self):
  for num in [4,10,23,39,41,47,49,54,56,61,78]:self.assertIsNone(self.rows[num]['facts']['first']);self.assertEqual(self.ds[num]['state'],'editorial_hold')
 def test_floating_bridge_exact_other_source_date(self):self.assertEqual(self.rows[6]['facts']['native_fields']['Date'],'');self.assertEqual(self.rows[6]['facts']['first'],1956);self.assertEqual(self.rows[6]['facts']['editorial_date_evidence'][0]['pdf_page_index'],16)
 def test_whole_triptychs_count_once(self):
  self.assertEqual(self.rows[42]['facts']['date_precision'],'circa');self.assertEqual(self.rows[42]['facts']['first'],1510)
  for num in [11,42]:self.assertIn('triptych',self.ds[num]['basis']);self.assertIsNone(self.rows[num]['facts']['object_form'])
 def test_impressions_cannot_inherit_design_dates(self):
  for num in [44,49]:self.assertEqual(self.ds[num]['state'],'editorial_hold');self.assertIsNone(self.rows[num]['facts']['first'])
 def test_conflicting_dates_remain_visible(self):
  v=self.rows[69]['facts'];self.assertEqual(v['native_fields']['Date'],'1911');self.assertEqual((v['first'],v['last']),(1911,1912));self.assertIn('conflicting',v['date_display'])
 def test_gosse_source_uncertainty_not_cleveland_date(self):
  v=self.rows[68]['facts'];self.assertEqual((v['first'],v['last'],v['date_precision']),(1912,1914,'circa_range'));self.assertEqual(v['native_fields']['Date'],'1912');self.assertIn('clasped hands',self.ds[68]['basis'])
 def test_circa_narrative_qualifies_exact_field(self):self.assertEqual(self.rows[40]['facts']['native_fields']['Date'],'1520');self.assertEqual(self.rows[40]['facts']['date_precision'],'circa')
 def test_ben_nicholson_title_not_date_parser(self):self.assertEqual(self.rows[29]['facts']['first'],1942);self.assertIn('1940-42',self.rows[29]['facts']['title'])
 def test_prior_accession_and_version_conflicts_held(self):
  for n in [20,32]:self.assertEqual(self.ds[n]['state'],'editorial_hold');self.assertTrue(self.ds[n]['comparison']['hits'])
 def test_misleading_tissot_alias_comparison_only(self):v=self.rows[55]['facts'];self.assertIn('The Last Evening',v['titles']);self.assertNotIn('Last Evening',v['title']);self.assertIn('distinguishes',self.ds[55]['basis'])
 def test_bonnard_alias_broadens_identity(self):self.assertTrue(any(h['id']=='9da5a58c-b878-4a8b-9882-6107da389986' for h in self.ds[58]['comparison']['hits']));self.assertIn('pressed board',self.ds[58]['basis'])
 def test_native_field_tamper_rejected(self):
  x=copy.deepcopy(m.load(f.checked(self.rows[6]['source_reference'])));x['parsed']['fields'][1]['value']='1956'
  with self.assertRaises(AssertionError):f.f.facts(x)
 def test_source_sets_disjoint(self):
  self.assertEqual(sum(v['state']=='approved_review_only_addition' for v in self.ds.values()),55);self.assertEqual(sum(v['state']=='approved_existing_holding' for v in self.ds.values()),6);self.assertEqual(sum(v['state']=='already_catalogued' for v in self.ds.values()),4)
 def test_legacy_metadata_immutable(self):
  before=dict(artworks=[dict(id='one',current_institution_id=None,updated_at='old',title='Original',date_precision='unknown',status='review',primary_media_id='existing-image')],artists=[],media=[],media_assets=[],identifiers=[],museums=[],citations=[],assertions=[]);after=copy.deepcopy(before);after['artworks'][0].update(current_institution_id=a.IID,updated_at='new');holds=[dict(artwork_id='one')]
  with patch.object(a,'verify_evidence_rows'):
   a.assert_delta(before,after,holds,'test')
   for field in ['title','date_precision','status','primary_media_id']:
    changed=copy.deepcopy(after);changed['artworks'][0][field]='unauthorized'
    with self.assertRaises(AssertionError):a.assert_delta(before,changed,holds,'test')
 def test_old_citations_not_deleted_or_changed(self):
  before=dict(artworks=[],artists=[],media=[],media_assets=[],identifiers=[],museums=[],citations=[dict(source_id='old',evidence_note='keep')],assertions=[]);after=copy.deepcopy(before);after['citations'][0]['evidence_note']='changed'
  with self.assertRaises(AssertionError):a.assert_delta(before,after,[],'test')
if __name__=='__main__':unittest.main()
