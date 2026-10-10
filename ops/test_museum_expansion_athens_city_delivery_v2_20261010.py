"""Offline data-boundary and preservation tests; never connects to a database."""
import copy,gzip,hashlib,importlib.util,json,re,unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-athens-city-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN
REVIEW=m.load(a.REVIEW);RECORDS=REVIEW['records'];BY={v['facts']['number']:v for v in RECORDS};IMAGES=REVIEW['images']

class Delivery(unittest.TestCase):
    def test_01_unique_physical_units(self):
        self.assertEqual(len(RECORDS),135);self.assertEqual(len({v['artwork_id'] for v in RECORDS}),135);self.assertEqual(len({v['facts']['source_id'] for v in RECORDS}),135)
    def test_02_hold_and_old_records_excluded(self):
        self.assertFalse(set(BY)&{11,12,13,17,21,22,25,35,94,108});self.assertFalse({v['artwork_id'] for v in RECORDS}&set(m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids']))
    def test_03_creation_cutoff(self):
        dates=[v['facts'] for v in RECORDS if v['facts']['first'] is not None];self.assertEqual(len(dates),47);self.assertTrue(all(f['first']<=f['last']<=1970 for f in dates))
    def test_04_unknown_dates_preserved(self):
        undated=[v['facts'] for v in RECORDS if v['facts']['first'] is None];self.assertEqual(len(undated),88);self.assertTrue(all(f['last'] is None and f['date_precision']=='unknown' for f in undated))
    def test_05_date_enum_and_conflict(self):
        self.assertEqual(BY[57]['facts']['date_display'],'28/06/1858');self.assertEqual(a.metadata(BY[57])['date_precision'],'exact');self.assertEqual(BY[90]['facts']['date_precision'],'circa');self.assertIsNone(a.metadata(BY[111])['creation_year_start']);self.assertTrue(all(v['facts']['date_precision'] in {'exact','circa','range','unknown'} for v in RECORDS))
    def test_06_no_dates_from_events_or_inscriptions(self):
        for n in [1,2,3,7,8,31,49,50,62,105,112]:self.assertIsNone(BY[n]['facts']['first'])
    def test_07_icons_and_origin(self):
        self.assertEqual({n for n,v in BY.items() if v['facts']['object_form']=='icon'},set(range(49,63)));self.assertEqual({n:v['facts']['cultural_context'] for n,v in BY.items() if v['facts']['cultural_context']},{61:'Russian'});self.assertIsNone(BY[63]['facts']['object_form'])
    def test_08_manufacturers_not_creators(self):
        for n in [27,37]:self.assertIsNone(BY[n]['facts']['creator_label']);self.assertIsNone(BY[n]['facts']['artist_id'])
    def test_09_two_secure_creator_links(self):
        self.assertEqual({n for n,v in BY.items() if v['facts']['artist_id']},{103,117});self.assertTrue(all(a.r.artist_link(BY[n])['attribution_role']=='primary' for n in [103,117]));self.assertIsNone(BY[109]['facts']['artist_id'])
    def test_10_uncertain_roles_retained(self):
        for n in [31,84,87,90,106,111,162]:self.assertIsNone(BY[n]['facts']['artist_id']);self.assertIsNotNone(BY[n]['facts']['creator_label'])
    def test_11_copy_and_support_units(self):
        for n in [65,69,70,75,80]:self.assertIn('one physical sheet',BY[n]['facts']['description_md'])
        for n in range(140,153):self.assertIn('student work',BY[n]['facts']['description_md']);self.assertIsNone(BY[n]['facts']['first'])
    def test_12_private_contact_not_public(self):
        self.assertFalse(re.search(r'\d{7,}',BY[88]['facts']['description_md']));self.assertNotIn('Σηλάκου',BY[88]['facts']['description_md']);self.assertTrue(re.search(r'\d{7,}',' '.join(BY[88]['facts']['source_facts']['description_source'])))
    def test_13_actual_rights_preserved(self):
        self.assertTrue(all(x['rights_status']=='public_domain' and x['rights_label']=='Public Domain CC0' and x['rights_url']=='http://creativecommons.org/publicdomain/zero/1.0/' for x in IMAGES))
    def test_14_image_cutoff_and_identity(self):
        self.assertEqual(len(IMAGES),39);self.assertEqual(len({x['sha256'] for x in IMAGES}),39);self.assertTrue(all(x['last']<=1955 and x['artwork_id']==BY[x['number']]['artwork_id'] for x in IMAGES));self.assertFalse({31,42,111}&{x['number'] for x in IMAGES})
    def test_15_image_bytes_and_full_frames(self):
        for x in IMAGES:
            raw=Path(x['prepared_path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),x['sha256']);self.assertEqual(raw,Path(x['original_reference']['path']).read_bytes());self.assertEqual(len(raw),x['bytes']);self.assertLessEqual(len(raw),100000)
            with Image.open(x['prepared_path']) as im:self.assertEqual(im.format,'JPEG');self.assertEqual(im.size,(x['width'],x['height']))
    def test_16_source_bodies_are_pinned(self):
        for v in RECORDS:
            rc=v['facts']['source_facts']['source_receipt'];raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),rc['sha256']);self.assertEqual(rc['status'],200)
    def test_17_no_publish_or_display(self):
        for v in RECORDS:
            row=a.metadata(v);self.assertEqual(row['status'],'review');self.assertTrue(row['research_candidate']);self.assertNotIn('location_checked_at',row);self.assertNotIn('published_at',row)
    def test_18_existing_snapshot_mutation_rejected(self):
        old=m.load(RUN/'focused-comparators-001.json.gz')['snapshot'];p=dict(holdings=[],images=a.image_records(old));new=copy.deepcopy(old);a.verify_existing(old,new,p,'offline');new['artworks'][0]['title']='Changed'
        with self.assertRaises(AssertionError):a.verify_existing(old,new,p,'offline')
    def test_19_existing_primary_replacement_rejected(self):
        old=m.load(RUN/'focused-comparators-001.json.gz')['snapshot'];new=copy.deepcopy(old);row=next(v for v in new['artworks'] if v['primary_media_id']);row['primary_media_id']=None
        with self.assertRaises(AssertionError):a.verify_existing(old,new,dict(holdings=[],images=a.image_records(old)),'offline')
    def test_20_complete_old_primary_preservation(self):
        before=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];self.assertEqual(sum(bool(x['primary_media_id']) for x in before['artworks']),6);planned=a.image_records(before);self.assertTrue(all(x['set_primary'] and x['sort_order']==0 for x in planned));self.assertFalse({x['artwork_id'] for x in planned}&{x['id'] for x in before['artworks']})

if __name__=='__main__':unittest.main()
