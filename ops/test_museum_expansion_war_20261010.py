"""Offline import safeguards; no database connections or test fixtures."""
import copy,hashlib,importlib.util,unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-war-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
r,c,m,RUN=a.r,a.c,a.m,a.RUN

class ReviewChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records,cls.holdings=a.records();cls.before=m.load(RUN/'focused-comparators-001.json.gz')['snapshot'];cls.images=a.image_records(cls.before);cls.plan=dict(records=cls.records,holdings=cls.holdings,images=cls.images);cls.facts={x['facts']['number']:x['facts'] for x in cls.records}
    def test_existing_source_records_excluded(self):
        self.assertEqual(len(self.records),168);self.assertFalse(set(self.facts)&{8,15,18,32,33,112,186,187,188,191,192,193});self.assertFalse({x['artwork_id'] for x in self.records}&{x['id'] for x in self.before['artworks']})
    def test_all_new_remain_review(self):self.assertTrue(all(a.metadata(x)['status']=='review' and a.metadata(x)['research_candidate'] for x in self.records))
    def test_no_scope_padding_or_known_identity_conflicts(self):self.assertFalse(set(self.facts)&{10,11,44,53,31,65,71,81,103,104,105,123,132,135,169})
    def test_crossing_dates_preserved_without_images(self):
        crossing={n for n,f in self.facts.items() if f['last'] is not None and f['last']>1970};self.assertEqual(len(crossing),68);self.assertFalse(crossing&{x['number'] for x in self.images});self.assertTrue(all(self.facts[n]['source_facts']['date_scope_review_required'] for n in crossing))
    def test_uncertain_historical_dates_not_invented(self):
        unknown={n for n,f in self.facts.items() if f['first'] is None};self.assertEqual(unknown,{25,91,150,163,121,189,190,194,195});self.assertTrue(all(self.facts[n]['last'] is None and self.facts[n]['date_precision']=='unknown' for n in unknown))
    def test_qualified_dates_and_explicit_execution(self):
        self.assertEqual(self.facts[2]['date_precision'],'circa');self.assertEqual(self.facts[12]['date_precision'],'circa_range');self.assertEqual((self.facts[117]['first'],self.facts[117]['last']),(1928,1928));self.assertEqual(self.facts[149]['first'],1901)
    def test_copyist_not_prototype_artist(self):
        self.assertIn('after Delacroix',self.facts[115]['creator_label']);self.assertIsNone(self.facts[115]['artist_id']);self.assertEqual(self.facts[115]['date_precision'],'century');self.assertEqual(self.facts[151]['creator_label'],'Unidentified copyist')
    def test_media_and_object_types(self):
        self.assertEqual(self.facts[57]['work_type'],'photograph');self.assertIsNone(self.facts[57]['artist_id']);self.assertEqual(self.facts[133]['work_type'],'drawing');self.assertEqual(self.facts[152]['work_type'],'textile');self.assertEqual(self.facts[184]['object_form'],'cast replica');self.assertEqual(self.facts[183]['work_type'],'metalwork')
    def test_creator_identity_and_unillustrated_records(self):
        self.assertEqual(sum(f['artist_id']==r.THALIA for f in self.facts.values()),61);self.assertEqual({n for n,f in self.facts.items() if f['artist_id']==r.ROILOS},{3,4,116,124});self.assertIsNone(self.facts[58]['artist_id']);self.assertTrue({138,149,170}<=set(self.facts));self.assertFalse({138,149,170}&{x['number'] for x in self.images})
    def test_images_exact_original_jpegs(self):
        self.assertEqual(len(self.images),90)
        for im in self.images:
            raw=Path(im['prepared_path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),im['sha256']);self.assertEqual(raw,Path(im['original_reference']['path']).read_bytes());self.assertLessEqual(len(raw),100000)
            with Image.open(im['prepared_path']) as p:self.assertEqual(p.size,(im['width'],im['height']));self.assertEqual(p.format,'JPEG')
    def test_image_date_policy(self):
        eligible={n for n,f in self.facts.items() if f['last'] is not None and f['last']<=1970};self.assertEqual(len(eligible),91);self.assertEqual({x['number'] for x in self.images},eligible-{138});self.assertTrue(all(x['last']<=1955 for x in self.images))
    def test_source_licence_and_complete_frames(self):self.assertTrue(all(a.media_row(x)['rights_status']=='cc_by_sa' and x['rights_label']=='CC BY-SA 4.0' and x['complete_source_frame'] and x['changes']=='Source JPEG bytes unchanged. Complete supplied frame retained.' for x in self.images))
    def test_existing_state_unchanged(self):a.verify_existing(self.before,copy.deepcopy(self.before),self.plan,'offline-proof')
    def test_reject_old_metadata_changes(self):
        for key,value in [('title','Changed'),('creation_year_start',1900),('status','published'),('current_institution_id',None)]:
            after=copy.deepcopy(self.before);row=next(x for x in after['artworks'] if x['current_institution_id']==c.IID);self.assertNotEqual(row[key],value);row[key]=value
            with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_old_primary_replacement(self):
        after=copy.deepcopy(self.before);next(x for x in after['artworks'] if x['primary_media_id'])['primary_media_id']='replacement'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')
    def test_reject_old_identifier_mutation(self):
        after=copy.deepcopy(self.before);after['identifiers'][0]['external_id']='wrong'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline-proof')

if __name__=='__main__':unittest.main()
