"""Offline physical-unit, dating, image and preservation regression checks."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-chania-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class Chania(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.news,cls.holds=a.records();cls.by={v['facts']['number']:v for v in cls.news};cls.before=a.m.load(a.RUN/'focused-comparators-001.json.gz')['snapshot'];cls.images=a.image_records(cls.before);cls.plan=dict(records=cls.news,holdings=cls.holds,images=cls.images)
    def after(self):
        out=copy.deepcopy(self.before);primary={v['artwork_id']:v['media_id'] for v in self.images if v['set_primary']}
        for row in out['artworks']:
            if row['id'] in primary:row.update(primary_media_id=primary[row['id']],revision=row['revision']+1,updated_at='synthetic change',updated_by=a.m.ACTOR)
        return out
    def test_one_cauldron_with_six_component_sources(self):
        v=self.by[120];self.assertEqual(len(v['facts']['source_ids']),6);self.assertEqual(len(a.identifier_values(v)),1)
        self.assertEqual(len({x['artwork_id'] for x in self.images if x['primary_number']==120}),1);self.assertEqual(sum(x['primary_number']==120 for x in self.images),6)
    def test_one_undated_hair_ornament_pair(self):
        v=self.by[67];self.assertEqual(len(v['facts']['source_ids']),2);self.assertIsNone(v['facts']['first']);self.assertEqual(len(a.identifier_values(v)),1)
        self.assertFalse(any(x['primary_number']==67 for x in self.images))
    def test_identifier_schema_and_source_records(self):
        keys=[(v['artwork_id'],'searchculture-edm') for v in self.news for sid,url in a.identifier_values(v)]
        self.assertEqual(len(keys),174);self.assertEqual(len(set(keys)),174);self.assertEqual(sum(len(v['facts']['source_ids']) for v in self.news),180)
    def test_grouped_sources_survive_citation_serialization(self):
        for n in [67,120]:self.assertEqual(json.loads(a.evidence(self.by[n],'offline'))['source_record']['facts']['source_ids'],self.by[n]['facts']['source_ids'])
    def test_unknown_dates_remain_unknown(self):
        unknown=[v for v in self.news if v['facts']['first'] is None];self.assertEqual(len(unknown),57)
        for v in unknown:self.assertIsNone(v['facts']['last']);self.assertEqual(v['facts']['date_precision'],'unknown')
    def test_date_cutoff_and_no_year_zero(self):
        numeric=[v['facts'] for v in self.news if v['facts']['first'] is not None];self.assertEqual(len(numeric),117)
        self.assertTrue(all(f['first']<=f['last']<=1970 and 0 not in [f['first'],f['last']] for f in numeric))
    def test_hadrian_range_and_tiberius_creation_not_reign(self):
        self.assertEqual((self.by[185]['facts']['first'],self.by[185]['facts']['last']),(117,138));self.assertEqual((self.by[197]['facts']['first'],self.by[197]['facts']['last']),(1,50))
    def test_approximate_dates_preserved(self):
        for n in [152,195]:self.assertEqual(self.by[n]['facts']['date_precision'],'circa_range')
    def test_physical_copy_not_original_date(self):
        self.assertIsNone(self.by[36]['facts']['first']);self.assertIn('Roman copy',self.by[36]['facts']['date_display'])
    def test_blank_source_heading_supported_title_and_accession(self):
        v=self.by[75];self.assertEqual(v['facts']['title'],'Περιδέραιο');self.assertEqual(a.metadata(v)['accession_number'],'Λ 2038')
    def test_makers_not_invented_from_subjects_or_mints(self):
        self.assertEqual(sum('workshop' in v['facts']['creator_label'] for v in self.news),9)
        self.assertTrue(all(v['facts']['source_facts']['painter_id'] is None for v in self.news))
    def test_image_holds_do_not_remove_metadata(self):
        for n in [38,110,161,67,78,99,187]:self.assertIn(n,self.by);self.assertFalse(any(x['primary_number']==n for x in self.images))
    def test_image_counts_complete_frames_and_rights(self):
        self.assertEqual((len(self.images),sum(v['set_primary'] for v in self.images)),(188,183))
        for im in self.images:self.assertLessEqual(im['bytes'],100000);self.assertTrue(im['complete_source_frame']);self.assertTrue(im['verified_https_source_image_url'].startswith('https://'));self.assertEqual(im['rights_status'],'restricted');self.assertEqual(im['rights_label'],'CC BY-NC-ND 3.0 GR')
    def test_new_records_remain_review(self):
        for v in self.news:self.assertEqual(a.metadata(v)['status'],'review');self.assertTrue(a.metadata(v)['research_candidate'])
    def test_only_expected_existing_image_updates(self):a.verify_existing(self.before,self.after(),self.plan,'offline')
    def test_rejects_existing_date_rewrite(self):
        after=self.after();old=next(x for x in after['artworks'] if x['current_institution_id']==a.c.IID);old['creation_year_start']=-400
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_publication_change(self):
        after=self.after();after['artworks'][0]['status']='published' if after['artworks'][0]['status']!='published' else 'review'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_previous_primary_replacement(self):
        after=self.after();old=next(x for x in after['artworks'] if x['primary_media_id'] and x['current_institution_id']!=a.c.IID);old['primary_media_id']='unrelated'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_artist_link_loss(self):
        after=self.after();after['artists']=after['artists'][1:]
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_current_display_claim(self):
        after=self.after();after['artworks'][0]['location_checked_at']='synthetic display date'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_existing_accession_change(self):
        after=self.after();after['artworks'][0]['accession_number']='changed'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_old_citation_loss(self):
        after=self.after();after['citations']=after['citations'][1:]
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_museum_record_mutation(self):
        after=self.after();after['museums'][0]['name']='changed'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')

if __name__=='__main__':unittest.main(verbosity=2)
