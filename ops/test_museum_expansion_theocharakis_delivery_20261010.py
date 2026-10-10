"""Offline physical-unit, date, artist, existing-match and mutation-safety checks."""
import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-theocharakis-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class Theocharakis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.news,cls.holds=a.records();cls.by={v['facts']['number']:v for v in cls.news+cls.holds};cls.before=a.m.load(a.RUN/'focused-comparators-001.json.gz')['snapshot'];cls.images=a.image_records(cls.before);cls.plan=dict(records=cls.news,holdings=cls.holds,images=cls.images)
    def after(self):
        out=copy.deepcopy(self.before)
        for row in out['artworks']:
            if row['id']==a.r.BOAT:row.update(current_institution_id=a.c.IID,updated_at='synthetic holding update')
        return out
    def test_existing_boat_not_duplicated(self):
        self.assertEqual((len(self.news),len(self.holds)),(196,1));self.assertEqual(self.holds[0]['artwork_id'],a.r.BOAT);self.assertNotIn(a.r.BOAT,{v['artwork_id']for v in self.news})
    def test_eight_two_sided_sheets_count_once(self):
        groups=[v for v in self.news if len(v['facts']['source_ids'])==2];self.assertEqual(len(groups),8)
        for v in groups:self.assertEqual(len(a.identifier_values(v)),1);self.assertEqual(v['facts']['physical_unit']['physical_units_counted'],1)
    def test_canonical_identifier_constraint(self):
        ids=[(v['artwork_id'],'searchculture-edm')for v in self.news for sid,url in a.identifier_values(v)];self.assertEqual(len(ids),196);self.assertEqual(len(set(ids)),196)
    def test_all_source_records_remain_in_evidence(self):
        self.assertEqual(sum(len(v['facts']['source_ids'])for v in self.news+self.holds),205)
        for v in self.news:self.assertEqual(json.loads(a.evidence(v,'offline'))['source_record']['facts']['source_ids'],v['facts']['source_ids'])
    def test_unknown_dates_not_invented_from_lifespan(self):
        unknown=[v for v in self.news if v['facts']['first']is None];self.assertEqual(len(unknown),72)
        for v in unknown:self.assertIsNone(v['facts']['last']);self.assertEqual(v['facts']['date_precision'],'unknown')
    def test_catalogue_date_cutoff(self):
        known=[v['facts']for v in self.news if v['facts']['first']is not None];self.assertEqual(len(known),124);self.assertTrue(all(v['first']<=v['last']<=1970 for v in known))
    def test_native_broader_intervals(self):
        self.assertEqual((self.by[238]['facts']['first'],self.by[238]['facts']['last']),(1950,1955));self.assertEqual((self.by[251]['facts']['first'],self.by[251]['facts']['last']),(1948,1949))
    def test_pre1956_images_only(self):
        lookup={sid:v['facts']for v in self.news+self.holds for sid in v['facts']['source_ids']}
        self.assertTrue(all(lookup[im['source_id']]['last']is not None and lookup[im['source_id']]['last']<=1955 for im in self.images))
    def test_pear_image_hold_retains_metadata(self):
        self.assertIn(230,self.by);self.assertFalse(any(im['source_id']==self.by[230]['facts']['source_id']for im in self.images))
    def test_physical_identity_holds_excluded(self):
        held={v['source_id']for root in [a.c.RESEARCH,a.c.DATED]for v in a.m.load(root/'editorial-source-decisions-001.json.gz')['rows']if v['decision'].startswith('hold')};self.assertEqual(len(held),13);self.assertFalse(held&{sid for v in self.news+self.holds for sid in v['facts']['source_ids']})
    def test_full_image_frames_and_byte_limits(self):
        self.assertEqual((len(self.images),sum(v['set_primary']for v in self.images)),(114,110))
        for im in self.images:self.assertLessEqual(im['bytes'],100000);self.assertEqual(hashlib.sha256(Path(im['prepared_path']).read_bytes()).hexdigest(),im['sha256']);self.assertIn('No crop',im['changes']);self.assertEqual(a.media_row(im)['rights_status'],'cc_by_sa')
    def test_boat_image_is_alternate(self):
        im=next(im for im in self.images if im['artwork_id']==a.r.BOAT);self.assertFalse(im['set_primary']);self.assertEqual(a.media_row(im)['license_label'],'CC BY-SA 4.0')
    def test_verified_creator_links_keep_literal_evidence(self):
        for v in self.news:self.assertEqual(a.r.artist_link(v)['artist_id'],a.r.ARTIST);self.assertIn(v['facts']['creator_label'],a.r.artist_link(v)['attribution_note']);self.assertIsNone(a.metadata(v)['unlinked_creator_label'])
    def test_no_invented_accessions(self):
        for v in self.news:self.assertIsNone(a.metadata(v)['accession_number'])
    def test_review_state_preserved(self):
        for v in self.news:self.assertEqual(a.metadata(v)['status'],'review');self.assertTrue(a.metadata(v)['research_candidate'])
    def test_only_expected_existing_holding_change(self):a.verify_existing(self.before,self.after(),self.plan,'offline')
    def test_rejects_boat_date_rewrite(self):
        after=self.after();next(v for v in after['artworks']if v['id']==a.r.BOAT)['creation_year_start']=1949
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_old_primary_replacement(self):
        after=self.after();next(v for v in after['artworks']if v['id']==a.r.BOAT)['primary_media_id']='changed'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_existing_publication_change(self):
        after=self.after();after['artworks'][0]['status']='changed'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_existing_artist_link_loss(self):
        after=self.after();after['artists']=after['artists'][1:]
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_existing_citation_loss(self):
        after=self.after();after['citations']=after['citations'][1:]
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_current_display_claim(self):
        after=self.after();after['artworks'][0]['location_checked_at']='invented'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_museum_mutation(self):
        after=self.after();after['museums'][0]['name']='changed'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
if __name__=='__main__':unittest.main(verbosity=2)
