"""Synthetic evidence guards; no catalogue or network access."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('refresh', Path(__file__).with_name('refresh-verified-image-evidence.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ExistingEvidence(unittest.TestCase):
    def setUp(self):
        self.im = dict(target_ids={'local': 'art1'}, media_id='media1', path='/assets/artworks/test.jpg',
                       sha256='a' * 64, bytes=100, page='https://commons.wikimedia.org/wiki/File:Example.jpg',
                       policy_url='https://creativecommons.org/licenses/by/4.0/', license_label='CC BY 4.0',
                       creator_credit='Photographer', attribution_text='Photographer / CC BY 4.0',
                       rights_status='cc_by', external_id='INV1', source_image_url='https://upload.wikimedia.org/example.jpg')
        self.row = dict(artwork_id='art1', primary_media_id='media1', status='review', published_at=None,
                        media=dict(id='media1', storage_path=self.im['path'], checksum_sha256=self.im['sha256'],
                                   byte_size=100, source_page_url=self.im['page'], license_url=self.im['policy_url'],
                                   license_label='CC BY 4.0', creator_credit='Photographer',
                                   attribution_text=self.im['attribution_text'], rights_status='cc_by'),
                        rights=dict(media_id='media1', source_record_id='INV1', source_image_url=self.im['source_image_url'],
                                    policy_url=self.im['policy_url'], evidence_json=dict(media_id='media1', sha256='a' * 64)))

    def test_exact_existing_image_can_be_reverified(self):
        before=copy.deepcopy(self.row)
        m.validate_existing(self.im,self.row,'local')
        self.assertEqual(self.row,before)

    def test_different_image_or_source_cannot_reuse_evidence(self):
        for section, field in [('media','checksum_sha256'),('media','source_page_url'),
                               ('rights','source_record_id'),('rights','source_image_url')]:
            row=copy.deepcopy(self.row);row[section][field]='different'
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.validate_existing(self.im,row,'local')

    def test_credit_and_rights_changes_are_not_silently_accepted(self):
        for field in ('creator_credit','license_url','rights_status'):
            row=copy.deepcopy(self.row);row['media'][field]='different'
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.validate_existing(self.im,row,'local')

    def test_another_artwork_or_published_record_is_held(self):
        for field,value in [('artwork_id','art2'),('primary_media_id','media2'),('status','published'),('published_at','2026-01-01')]:
            row=copy.deepcopy(self.row);row[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):
                m.validate_existing(self.im,row,'local')

    def test_prior_evidence_for_other_bytes_is_held(self):
        self.row['rights']['evidence_json']['sha256']='b'*64
        with self.assertRaises(ValueError):
            m.validate_existing(self.im,self.row,'local')


if __name__=='__main__':
    unittest.main()
