"""Source-specific unknown-date, object identity and preservation checks; no database."""
import collections
import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-kilkis-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
r,c,m=a.r,a.c,a.m

class Delivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,cls.holdings=r.build();cls.review=m.load(a.REVIEW);cls.by={v['facts']['source_id'].split('-')[-1]:v for v in cls.records};cls.source=m.load(c.RUN/'source-review-001.json.gz')['rows']
    def test_selection_counts(self):self.assertEqual(len(self.records),38);self.assertEqual(self.holdings,[])
    def test_complete_public_index_review(self):
        self.assertEqual(len(self.source),68);self.assertEqual(sum(v['source_scheme']=='searchculture-edm' for v in self.source),65)
    def test_no_unverified_5044_components(self):self.assertFalse(any('5044' in v['facts']['source_id'] for v in self.records))
    def test_original_holds_remain(self):
        for key in ['1594','1595','5859','5862','3','134']:self.assertNotIn(key,self.by)
    def test_greave_pair_once(self):
        self.assertIn('784',self.by);self.assertEqual(self.by['784']['facts']['source_facts']['physical_units_counted'],1)
    def test_reused_blocks_once(self):
        for key in ['128','929']:self.assertEqual(self.by[key]['facts']['source_facts']['physical_units_counted'],1)
    def test_all_dates_unknown(self):
        for v in self.records:
            row=a.metadata(v);self.assertIsNone(row['creation_year_start']);self.assertIsNone(row['creation_year_end']);self.assertEqual(row['date_precision'],'unknown')
    def test_no_discovery_date_as_creation(self):
        f=self.by['2046']['facts'];self.assertIsNone(f['first']);self.assertIn('1994',f['source_facts']['source_entry']['discovery'])
    def test_book_dates_qualified(self):
        for key in ['331','2046']:self.assertIn('Possibly',self.by[key]['facts']['date_display'])
    def test_book_identifiers_not_pdf_identity(self):
        one=self.by['331'];two=self.by['2046'];self.assertEqual(one['facts']['source_url'],two['facts']['source_url']);self.assertNotEqual(a.identifier_values(one),a.identifier_values(two));self.assertEqual(one['facts']['source_scheme'],'museum-catalogue-isbn-9789601226781')
    def test_creator_not_inferred(self):self.assertTrue(all(a.metadata(v)['unlinked_creator_label'] is None for v in self.records))
    def test_review_only(self):self.assertTrue(all(a.metadata(v)['status']=='review' for v in self.records))
    def test_literal_accessions(self):
        for v in self.records:self.assertEqual(a.metadata(v)['accession_number'],v['facts']['source_facts']['inventory_literal'])
    def test_actual_work_types(self):
        self.assertEqual(dict(collections.Counter(v['facts']['work_type'] for v in self.records)),dict(sculpture=13,unknown=25))
    def test_native_period_conflict_explicit(self):
        f=self.by['27']['facts'];self.assertEqual(f['date_display'],'Ρωμαϊκή Eποχή');self.assertIn('conflicts',f['description_md'])
    def test_image_counts_and_old_targets(self):
        images=self.review['images'];self.assertEqual(len(images),53);self.assertEqual(sum(v['role']=='existing_record' for v in images),17)
        self.assertFalse(any(v['source_id'].endswith('-2') for v in images))
    def test_no_book_plates_invented(self):
        ids={v['artwork_id'] for v in self.review['images']}
        for key in ['331','2046']:self.assertNotIn(self.by[key]['artwork_id'],ids)
    def test_image_periods_not_numeric_dates(self):
        self.assertNotIn('Unknown',a.image_scope.PERIODS)
        for im in self.review['images']:self.assertIn(im['image_period_literal'],a.image_scope.PERIODS);self.assertTrue(im['date_policy_passed'])
    def test_authentic_full_frame_bytes(self):
        for im in self.review['images']:
            self.assertLessEqual(im['bytes'],100000);self.assertTrue(im['complete_source_frame']);self.assertEqual(hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest(),im['sha256'])
            with Image.open(im['prepared_path']) as image:self.assertEqual(image.size,(im['width'],im['height']));self.assertEqual(image.format,'JPEG')
            source=im['original_reference'];self.assertEqual(hashlib.sha256(Path(source['path']).read_bytes()).hexdigest(),source['sha256']);self.assertLess(abs(im['width']/im['height']-source['width']/source['height']),.005)
    def test_restricted_rights_preserved(self):
        for im in self.review['images']:
            row=a.media_row(dict(im,media_id='sample',storage_path='/sample.jpg'));self.assertEqual(row['rights_status'],'restricted');self.assertEqual(row['license_label'],'CC BY-NC-ND 4.0')
    def test_prior_metadata_unchanged_accepts(self):
        before=m.load(c.RUN/'focused-comparators-001.json.gz')['snapshot'];a.verify_existing(before,copy.deepcopy(before),dict(holdings=[],images=[]),'test')
    def test_reject_old_title_date_or_status_mutation(self):
        before=m.load(c.RUN/'focused-comparators-001.json.gz')['snapshot']
        for key,value in [('title','changed'),('creation_year_start',1900),('status','published'),('current_institution_id','changed')]:
            after=copy.deepcopy(before);after['artworks'][0][key]=value
            with self.assertRaises(AssertionError):a.verify_existing(before,after,dict(holdings=[],images=[]),'test')
    def test_no_foreign_primary_replacement(self):
        before=m.load(c.RUN/'focused-comparators-001.json.gz')['snapshot'];images=a.image_records(before);foreign={v['id'] for v in before['artworks'] if v['primary_media_id']}
        self.assertEqual(sum(v['set_primary'] for v in images),53);self.assertFalse(foreign&{v['artwork_id'] for v in images})

if __name__=='__main__':unittest.main()
