import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('sizes',Path(__file__).with_name('enforce-catalogue-image-size.py'))
sizes=importlib.util.module_from_spec(spec);spec.loader.exec_module(sizes)


class CompressionMetadataTests(unittest.TestCase):
    def test_only_file_fields_and_change_notice_change(self):
        old={'id':'example','storage_path':'/assets/old.jpg','byte_size':200000,
             'checksum_sha256':'old','width':2000,'height':1000,'mime_type':'image/jpeg',
             'rights_status':'cc_by_sa','license_url':'https://creativecommons.org/licenses/by-sa/4.0/',
             'attribution_text':'Original credit and licence.','source_page_url':'https://museum.example/art/1',
             'verified_at':'2026-09-01','updated_at':'2026-09-01','creator_credit':'Original creator'}
        record={'old':{'local':old},'path':'/assets/new.jpg','bytes':99999,'sha256':'new','width':1000,'height':500}
        updated=sizes.expected(record,'local')
        changed={k for k in old if old[k]!=updated[k]}
        self.assertEqual(changed,{'storage_path','byte_size','checksum_sha256','width','height','attribution_text'})
        self.assertTrue(updated['attribution_text'].startswith(old['attribution_text']))
        self.assertEqual(record['old']['local'],old)

    def test_concurrency_comparison_preserves_every_non_timestamp_field(self):
        self.assertEqual(sizes.stable({'updated_at':'old','rights_status':'cc0'}),sizes.stable({'updated_at':'new','rights_status':'cc0'}))
        self.assertNotEqual(sizes.stable({'rights_status':'cc0'}),sizes.stable({'rights_status':'unknown'}))


if __name__=='__main__':unittest.main()
