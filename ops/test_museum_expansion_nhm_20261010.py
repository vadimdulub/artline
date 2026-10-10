"""Offline NHM import safety checks; no database fixtures or connections."""
import copy,hashlib,importlib.util,unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-nhm-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
r,c,m,RUN=a.r,a.c,a.m,a.RUN

class ReviewChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review=m.load(a.REVIEW);cls.records,cls.holdings=a.records();cls.before=m.load(RUN/'focused-comparators-001.json.gz')['snapshot'];cls.images=a.image_records(cls.before);cls.plan=dict(records=cls.records,holdings=cls.holdings,images=cls.images);cls.facts={x['facts']['number']:x['facts'] for x in cls.records}
    def test_no_existing_work_insert(self):
        self.assertEqual(len(self.records),238);self.assertEqual(self.holdings,[]);self.assertFalse({x['artwork_id'] for x in self.records}&{x['id'] for x in self.before['artworks']});self.assertFalse(set(self.facts)&{1,159,*range(241,252)})
    def test_all_new_in_review(self):self.assertTrue(all(a.metadata(x)['status']=='review' and a.metadata(x)['research_candidate'] for x in self.records))
    def test_scope_and_uncertainty(self):
        self.assertEqual(sum(f['first'] is None for f in self.facts.values()),62);self.assertTrue(all(f['last'] is None or f['last']<=1970 for f in self.facts.values()))
    def test_no_document_padding(self):self.assertTrue(all(f['work_type'] in ['painting','drawing'] for f in self.facts.values()))
    def test_sitter_dates_not_creation(self):
        for n in [2,3,4,5,6,8,9,11,12,13,14,15,16,17,18,19,20,23,24,25,26,27,28,29,35,36,42,43,67,68,69,185]:self.assertIsNone(self.facts[n]['first'])
    def test_copy_maker_and_dates(self):
        for n in [30,31,32,33,34,165,174,179,182,183,184,188,189,190,191,192,193,196]:
            f=self.facts[n];self.assertIsNone(f['artist_id']);self.assertIsNone(f['first']);self.assertTrue('copy' in f['creator_label'].lower())
        self.assertIn('Attributed to',self.facts[68]['creator_label'])
    def test_iatridis_conflicts_remain_unresolved(self):
        for n in range(168,172):
            f=self.facts[n];self.assertIsNone(f['first']);self.assertIn('1824',f['date_display']);self.assertIn('1828–1832',f['date_display']);self.assertTrue(f['inventory'])
    def test_bridge_identity(self):
        self.assertEqual(self.facts[210]['inventory'],'15153-52');self.assertEqual(self.facts[230]['inventory'],'15153-7');self.assertNotEqual(self.facts[210]['dimensions_text'],self.facts[230]['dimensions_text']);self.assertEqual(self.facts[210]['first'],1838)
    def test_artist_links(self):self.assertEqual({n for n,f in self.facts.items() if f['artist_id']},set(range(197,241)))
    def test_prepared_images(self):
        self.assertEqual(len(self.images),176)
        for im in self.images:
            raw=Path(im['prepared_path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),im['sha256']);self.assertLessEqual(len(raw),100000)
            with Image.open(im['prepared_path']) as p:self.assertEqual(p.size,(im['width'],im['height']));self.assertEqual(p.format,'JPEG')
            self.assertEqual((im['width'],im['height']),(im['original_width'],im['original_height']))
    def test_image_date_holds(self):
        self.assertEqual({im['number'] for im in self.images},{n for n,f in self.facts.items() if f['first'] is not None});self.assertTrue(all(im['last']<=1955 for im in self.images))
    def test_restricted_labels_and_resolution(self):
        self.assertTrue(all(a.media_row(im)['rights_status']=='restricted' and 'BY-NC-ND' in im['rights_label'] and im['aggregator_rights_label']=='CC BY 4.0' and im['resolution_limitation'] for im in self.images))
    def test_existing_state_unchanged(self):a.verify_existing(self.before,copy.deepcopy(self.before),self.plan,'offline-proof')
    def test_reject_old_metadata_changes(self):
        for key,value in [('title','Changed'),('creation_year_start',1900),('status','published'),('current_institution_id',None)]:
            after=copy.deepcopy(self.before);row=next(x for x in after['artworks'] if x['current_institution_id']==c.IID);self.assertNotEqual(row[key],value);row[key]=value
            with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_primary_replacement(self):
        after=copy.deepcopy(self.before);next(x for x in after['artworks'] if x['primary_media_id'])['primary_media_id']='replacement'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_old_identifier_mutation(self):
        after=copy.deepcopy(self.before);after['identifiers'][0]['external_id']='wrong'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')

if __name__=='__main__':unittest.main()
