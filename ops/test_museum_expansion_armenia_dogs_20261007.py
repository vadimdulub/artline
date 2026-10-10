"""Physical-version regressions for the two Sarian Dogs paintings."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-armenia-dogs-20261007.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class SarianDogs(unittest.TestCase):
    def test_gallery_record_uses_primary_caption(self):
        r=d.record();self.assertEqual(r['facts']['dimensions'],'41x98.5 cm')
        self.assertEqual(r['facts']['date_display'],'1910');self.assertEqual(r['facts']['medium'],'Tempera on canvas')
        self.assertIsNone(r['facts']['accession'])

    def test_existing_house_museum_version_remains_distinct(self):
        r=d.record();v=r['raw_source_record']['version_review']
        self.assertEqual(v['existing_house_museum_id'],'bb1be2f2-3cb7-54b5-8549-4d71fa406b8e')
        self.assertNotEqual(r['artwork_id'],v['existing_house_museum_id'])
        self.assertIn('104',v['house_museum_comparison']['caption_details'][2])
        self.assertIn('139.2',v['house_museum_comparison']['caption_details'][2])

    def test_native_and_community_source_identity_agree(self):
        r=d.record();v=r['raw_source_record']['version_review']
        self.assertEqual(v['distinct_gallery_entity']['id'],'Q56248088')
        self.assertEqual(d.v.val(v['distinct_gallery_entity'],'P217'),'217')
        self.assertEqual(r['source_record_id'],'other_natgalleryarm_ger_7')

    def test_changed_dimensions_rejected(self):
        r=d.record();r['facts']['dimensions']='104x139.2 cm'
        with self.assertRaises(AssertionError):d.validate(dict(evidence=[],records=[r]))

    def test_duplicate_record_rejected(self):
        r=d.record()
        with self.assertRaises(AssertionError):d.validate(dict(evidence=[],records=[r,copy.deepcopy(r)]))

if __name__=='__main__':unittest.main()
