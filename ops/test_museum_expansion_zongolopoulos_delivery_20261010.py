"""Offline preservation and source-specific regression checks; no database use."""
import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-zongolopoulos-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
r,c,m=a.r,a.c,a.m

class Delivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,cls.holdings=r.build();cls.by={v['facts']['source_id'].split('-')[-1]:v for v in cls.records};cls.review=m.load(a.REVIEW)
    def test_selection(self):
        self.assertEqual(len(self.records),198);self.assertEqual(self.holdings,[])
    def test_venice_additional_identity_held(self):
        self.assertNotIn('64302',self.by);self.assertIn('64304',self.by)
    def test_conflicting_source_image_held(self):self.assertNotIn('64218',self.by)
    def test_unknown_dates_never_invented(self):
        self.assertEqual(sum(v['facts']['first'] is None for v in self.records),149)
        for v in self.records:
            if v['facts']['first'] is None:self.assertIsNone(v['facts']['last']);self.assertEqual(a.metadata(v)['date_precision'],'unknown')
    def test_lithograph_inscription_not_impression_date(self):
        f=self.by['64290']['facts'];self.assertIsNone(f['first']);self.assertEqual(f['work_type'],'print');self.assertEqual(f['source_facts']['unit']['inscription_year'],1933);self.assertEqual(f['source_facts']['unit']['impression_number'],'17/20')
    def test_source_reported1960(self):self.assertEqual(self.by['64368']['facts']['first'],1960)
    def test_no_export_inventory_halving(self):
        f=self.by['64826']['facts'];self.assertEqual(f['inventory_source_literal'],'10921092');self.assertTrue(all(v['facts']['inventory'] is None for v in self.records))
    def test_qualified_creators(self):
        self.assertIn('Απόδοση αβέβαιη',self.by['64479']['facts']['creator_label']);self.assertIn('Αποδιδόμενο',self.by['64360']['facts']['creator_label'])
    def test_anonymous_not_assigned_founder(self):
        self.assertEqual(sum(v['facts']['creator_label']=='Άγνωστος δημιουργός' for v in self.records),37)
    def test_sides_count_once(self):
        self.assertEqual(sum(v['facts']['source_facts']['unit'].get('two_sided_support',False) for v in self.records),16)
        self.assertTrue(all(v['facts']['source_facts']['unit']['physical_units_counted']==1 for v in self.records))
    def test_no_artist_fabrication(self):self.assertTrue(all(v['facts']['source_facts']['unit']['painter_id'] is None for v in self.records))
    def test_review_and_cutoff(self):
        for v in self.records:
            md=a.metadata(v);self.assertEqual(md['status'],'review');self.assertTrue(md['research_candidate'])
            if md['creation_year_end'] is not None:self.assertLessEqual(md['creation_year_end'],1970)
    def test_reject_post1970(self):
        wave,u,d=r.selected()[0];u=copy.deepcopy(u);u['last']=1971
        with self.assertRaises(AssertionError):r.facts(wave,u,d)
    def test_reject_half_unknown(self):
        wave,u,d=r.selected()[0];u=copy.deepcopy(u);u['first']=None
        with self.assertRaises(AssertionError):r.facts(wave,u,d)
    def test_image_bytes_and_cutoff(self):
        self.assertEqual(len(self.review['images']),18)
        for im in self.review['images']:
            self.assertLessEqual(im['last'],1955);self.assertLessEqual(im['bytes'],100000);self.assertNotEqual(im['source_id'],r.VENICE_HOLD)
            raw=Path(im['prepared_path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),im['sha256']);self.assertEqual(im['sha256'],im['original_reference']['sha256'])
            with Image.open(im['prepared_path']) as image:self.assertEqual(image.size,(im['width'],im['height']));self.assertEqual(image.format,'JPEG')
    def test_actual_restricted_rights(self):
        for im in self.review['images']:
            im=dict(im,media_id='sample',storage_path='/sample.jpg');row=a.media_row(im);self.assertEqual(row['rights_status'],'restricted');self.assertEqual(row['license_label'],'CC BY-NC-ND 4.0');self.assertIn('by-nc-nd',row['license_url'])
    def test_new_primary_only(self):
        before=m.load(c.RUN/'production-initial-scope-001.json.gz')['snapshot'];images=a.image_records(before)
        self.assertTrue(all(im['set_primary'] for im in images));self.assertFalse({x['artwork_id'] for x in images}&{x['id'] for x in before['artworks']})
    def test_unchanged_old_snapshot_accepts(self):
        before=m.load(c.RUN/'focused-comparators-001.json.gz')['snapshot'];a.verify_existing(before,copy.deepcopy(before),dict(holdings=[],images=[]),'test')
    def test_old_metadata_change_rejected(self):
        before=m.load(c.RUN/'focused-comparators-001.json.gz')['snapshot'];after=copy.deepcopy(before);after['artworks'][0]['title']='changed'
        with self.assertRaises(AssertionError):a.verify_existing(before,after,dict(holdings=[],images=[]),'test')
    def test_old_primary_change_rejected(self):
        before=m.load(c.RUN/'focused-comparators-001.json.gz')['snapshot'];after=copy.deepcopy(before);after['artworks'][0]['primary_media_id']='changed'
        with self.assertRaises(AssertionError):a.verify_existing(before,after,dict(holdings=[],images=[]),'test')

if __name__=='__main__':unittest.main()
