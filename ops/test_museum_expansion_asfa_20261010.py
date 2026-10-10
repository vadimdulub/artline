"""Offline delivery invariants and preservation regression checks; no database fixtures."""
import copy,hashlib,importlib.util,json,unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-asfa-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
r,c,m,RUN=a.r,a.c,a.m,a.RUN

class ReviewChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review=m.load(a.REVIEW);cls.records,cls.holdings=a.records();cls.before=m.load(RUN/'focused-comparators-001.json.gz')['snapshot'];cls.images=a.image_records(cls.before);cls.plan=dict(records=cls.records,holdings=cls.holdings,images=cls.images)
    def test_no_same_work_insert(self):
        self.assertEqual(len(self.records),248);self.assertEqual({x['artwork_id'] for x in self.holdings},set(r.EXISTING.values()));self.assertFalse({x['artwork_id'] for x in self.records}&set(r.EXISTING.values()))
    def test_all_new_in_review(self):
        self.assertTrue(all(a.metadata(x)['status']=='review' and a.metadata(x)['research_candidate'] for x in self.records))
    def test_scope_and_uncertainty(self):
        self.assertEqual({x['facts']['number'] for x in self.records if x['facts']['first'] is None},{131,132,133,140,141,199});self.assertTrue(all(x['facts']['last'] is None or x['facts']['last']<=1970 for x in self.records))
    def test_no_document_padding(self):self.assertTrue(all(x['facts']['work_type'] in ['painting','drawing','print','sculpture'] for x in self.records))
    def test_orphan_not_person(self):
        self.assertTrue(all(x['facts']['creator_label'] is None and x['facts']['artist_id'] is None for x in self.records if x['facts']['source_facts']['creator_source_literals'][0]=='Ορφανό'))
    def test_copy_attribution(self):
        f=next(x['facts'] for x in self.records if x['facts']['number']==198);self.assertIsNone(f['artist_id']);self.assertIn('copyist unidentified',f['creator_label']);self.assertEqual(f['first'],1958)
    def test_artist_links(self):self.assertEqual(sum(bool(x['facts']['artist_id']) for x in self.records),10)
    def test_prepared_images(self):
        self.assertEqual(len(self.images),142)
        for im in self.images:
            raw=Path(im['prepared_path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),im['sha256']);self.assertLessEqual(len(raw),100000)
            with Image.open(im['prepared_path']) as p:self.assertEqual(p.size,(im['width'],im['height']));self.assertEqual(p.format,'JPEG')
            self.assertLess(abs(im['width']/im['height']-im['original_width']/im['original_height']),.003)
    def test_image_date_holds(self):
        self.assertTrue(all(im['last']<=1955 for im in self.images));self.assertFalse({131,132,133,140,141,171,172,198,199}&{x['number'] for x in self.images})
    def test_restricted_labels(self):
        self.assertTrue(all(a.media_row(im)['rights_status']=='restricted' and 'BY-NC-ND' in im['rights_label'] and im['aggregator_rights_label']=='CC BY-SA 4.0' for im in self.images))
    def test_primary_and_alternate_assignment(self):
        self.assertEqual(sum(x['set_primary'] for x in self.images),141);self.assertEqual([x['number'] for x in self.images if not x['set_primary']],[17]);self.assertTrue(next(x for x in self.images if x['number']==24)['set_primary'])
    def changed(self):
        after=copy.deepcopy(self.before)
        for row in after['artworks']:
            if row['id'] in r.EXISTING.values():row['current_institution_id']=c.IID
            if row['id']==r.EXISTING[24]:row.update(primary_media_id=next(x['media_id'] for x in self.images if x['number']==24),revision=row['revision']+1,updated_by=m.ACTOR)
        return after
    def test_allowed_holding_image_changes(self):a.verify_existing(self.before,self.changed(),self.plan,'offline-proof')
    def test_reject_title_change(self):
        after=self.changed();next(x for x in after['artworks'] if x['id']==r.EXISTING[17])['title']='Changed'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_date_rewrite(self):
        after=self.changed();next(x for x in after['artworks'] if x['id']==r.EXISTING[24])['creation_year_start']=1930
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_primary_replacement(self):
        after=self.changed();next(x for x in after['artworks'] if x['id']==r.EXISTING[17])['primary_media_id']='replacement'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_status_change(self):
        after=self.changed();after['artworks'][0]['status']='published'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_old_identifier_mutation(self):
        after=self.changed();after['identifiers'][0]['external_id']='wrong'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')

if __name__=='__main__':unittest.main()
