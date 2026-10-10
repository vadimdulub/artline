"""Offline source/date/object-boundary checks; no database connection or fixtures."""
import gzip,hashlib,importlib.util,unittest
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-athens-city-photographs-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c,m,RUN=a.c,a.m,a.RUN
REVIEW=m.load(a.REVIEW);ROWS=REVIEW['records'];BY={v['facts']['number']:v for v in ROWS}

class Delivery(unittest.TestCase):
    def test_01_selected_units_unique(self):
        self.assertEqual(len(ROWS),55);self.assertEqual(len({v['artwork_id'] for v in ROWS}),55);self.assertEqual(len({v['facts']['source_id'] for v in ROWS}),55)
    def test_02_old_units_excluded(self):
        self.assertFalse(set(BY)&{8,9,10,11,12,61,62,63,64,65});self.assertFalse({v['artwork_id'] for v in ROWS}&set(m.load(RUN/'production-initial-scope-001.json.gz')['scoped_ids']))
    def test_03_conflicting_dates_remain_unknown(self):
        self.assertEqual({n for n,v in BY.items() if v['facts']['first'] is None},set(range(1,8)))
        for n in range(1,8):f=BY[n]['facts'];self.assertIsNone(f['last']);self.assertEqual(f['date_precision'],'unknown');self.assertIn('1960',f['date_display']);self.assertIn('1965–1970',f['date_display'])
    def test_04_creation_cutoff(self):
        dated=[v['facts'] for v in ROWS if v['facts']['first'] is not None];self.assertEqual(len(dated),48);self.assertTrue(all(1965<=f['first']<=f['last']<=1970 for f in dated))
    def test_05_abbreviated_range_not_exact(self):
        self.assertEqual((BY[13]['facts']['first'],BY[13]['facts']['last'],BY[13]['facts']['date_precision']),(1965,1970,'range'));self.assertEqual(BY[13]['facts']['date_display'],'1965-70');self.assertEqual(BY[21]['facts']['last'],1968)
    def test_06_building_dates_not_creation(self):
        self.assertEqual(BY[51]['facts']['first'],1965);self.assertIn('1866',BY[51]['facts']['description_md']);self.assertEqual(BY[44]['facts']['last'],1970);self.assertEqual(BY[3]['facts']['first'],None)
    def test_07_digital_medium_explicit(self):
        for v in ROWS:self.assertEqual(a.metadata(v)['medium_text'],'Ψηφιακή φωτογραφία μόνο');self.assertIn('original negative or print support',v['facts']['description_md']);self.assertIn('digital photograph only',v['limitation'])
    def test_08_archive_credit_not_unqualified_artist(self):
        for v in ROWS:self.assertIsNone(a.metadata(v)['unlinked_creator_label']);self.assertIn('Φωτογραφικό Αρχείο',v['facts']['description_md']);self.assertEqual(len(v['facts']['source_facts']['creator_source_literals']),1)
    def test_09_no_placeholder_or_invented_accession(self):
        for v in ROWS:self.assertTrue(v['facts']['source_id'].startswith('DigAthensMuseum/000190-'));self.assertEqual(a.metadata(v)['work_type'],'photograph');self.assertIsNone(a.metadata(v)['accession_number']);self.assertIsNone(a.metadata(v)['dimensions_text'])
    def test_10_review_without_publish_or_display(self):
        for v in ROWS:self.assertEqual(a.metadata(v)['status'],'review');self.assertTrue(a.metadata(v)['research_candidate']);self.assertNotIn('published_at',a.metadata(v));self.assertNotIn('location_checked_at',a.metadata(v))
    def test_11_no_image_delivery(self):
        self.assertEqual(REVIEW['images'],[]);self.assertEqual(REVIEW['holdings'],[]);self.assertEqual(m.load(RUN/'source-review-summary-001.json')['images_selected_for_delivery'],0)
    def test_12_complete_source_body_proofs(self):
        for v in ROWS:
            rc=v['facts']['source_facts']['source_receipt'];raw=gzip.decompress((m.ROOT/rc['body_path']).read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),rc['sha256']);self.assertEqual(rc['status'],200)
    def test_13_research_images_all_decode_and_match(self):
        vis=m.load(RUN/'visual-references-001.json');self.assertEqual(len(vis['rows']),65);self.assertEqual(vis['exact_duplicate_groups'],[])
        for x in vis['rows']:
            self.assertEqual(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest(),x['sha256'])
            with Image.open(x['path']) as im:self.assertEqual(im.format,'JPEG');self.assertEqual(im.size,(x['width'],x['height']))
    def test_14_qualified_places_preserved(self):
        for n in [14,18,27,38,57]:self.assertTrue(any('Qualified place' in x for x in BY[n]['facts']['source_facts']['review_notes']))
    def test_15_counterpart_reconciliation_scope(self):
        obs=m.load(RUN/'production-identity-001.json.gz');self.assertEqual(len(obs['state']['artwork_ids']),153);self.assertEqual({x['artwork_id'] for x in obs['state']['creator_links']}&{v['artwork_id'] for v in ROWS},set());self.assertEqual(len(REVIEW['existing_source_mapping']),10);self.assertEqual(obs['state']['matching_media'],[])
    def test_16_actual_rights_and_donation_labels(self):
        for v in ROWS:
            f=v['facts']['source_facts']['source_fields'];self.assertEqual(f['Δικαιώματα'],['http://creativecommons.org/publicdomain/zero/1.0/']);self.assertEqual(f['Επιμέρους συλλογή'],['Δωρεά Κουτσαπλή'])
    def test_17_originals_and_existing_images_preserved(self):
        before=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];self.assertEqual(len(before['artworks']),153);self.assertEqual(sum(bool(x['primary_media_id']) for x in before['artworks']),45);self.assertEqual(REVIEW['new_primary_images'],0)
    def test_18_local_scope_read_only(self):
        local=m.load(RUN/'initial-scope-001.json.gz');self.assertTrue(local['read_only']);self.assertEqual(local['scoped_ids'],[]);self.assertEqual(local['counts'],{c.IID:dict(linked=0,eligible=0)})

if __name__=='__main__':unittest.main()
