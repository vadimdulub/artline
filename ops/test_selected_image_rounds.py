"""Offline date-review guards; no database connection or fixtures."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('rounds',Path(__file__).with_name('run-selected-image-rounds.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class CurrentMuseumDate(unittest.TestCase):
    def test_current_cutoff_allowed(self):
        image={'raw':{'creation_date_latest':1970}}
        with patch.object(m,'original_record',return_value=image):
            self.assertIs(m.reviewed_image_record({'provider':'cleveland'},None,{},{}),image)

    def test_newer_unknown_and_malformed_dates_held_before_download(self):
        for value in [1971,None,0,True,'1900']:
            with self.subTest(value=value),patch.object(m,'original_record',return_value={'raw':{'objectEndDate':value}}):
                with self.assertRaisesRegex(ValueError,'Metadata needs review'):
                    m.reviewed_image_record({'provider':'met'},None,{},{})

    def test_rights_skip_remains_skip(self):
        with patch.object(m,'original_record',return_value=None):
            self.assertIsNone(m.reviewed_image_record({'provider':'chicago'},None,{},{}))

    def test_only_known_museum_image_timeouts_are_retryable(self):
        event={'outcome':'failed','error':"HTTPSConnectionPool(host='www.artic.edu', port=443): Read timed out. (read timeout=45)"}
        self.assertTrue(m.source_timeout('chicago',event))
        event['error']=event['error'].replace('www.artic.edu','storage.googleapis.com')
        self.assertFalse(m.source_timeout('chicago',event))

    def test_storage_failures_cannot_be_held_as_missing_source_images(self):
        for host in ['storage.googleapis.com','www.artic.edu.example.com']:
            event={'outcome':'failed','error':f'403 Client Error: Forbidden for url: https://{host}/image.jpg'}
            self.assertFalse(m.source_unavailable('chicago',event))
        event['error']='403 Client Error: Forbidden for url: https://www.artic.edu/iiif/2/image'
        self.assertTrue(m.source_unavailable('chicago',event))


if __name__=='__main__':unittest.main()
