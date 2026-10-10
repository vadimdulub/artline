"""Source-parser regression checks; no database connections or fixtures."""
import copy
import gzip
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('all-museums-minimum-100-20261006.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)


class AargauerSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        records=c.load(c.RUN/'waves/aargauer-002/source-verified.json.gz')['records']
        cls.record=next(x for x in records if x['facts']['title']=='Die Seine bei Charenton')
        cls.raw=gzip.decompress((c.ROOT/cls.record['body_path']).read_bytes())
        cls.index=cls.record['raw_source_record']['index']

    def test_html_comments_do_not_become_artwork_medium(self):
        parsed,reason=c.aargauer_native(self.raw,self.index)
        self.assertIsNone(reason)
        self.assertEqual(parsed['facts']['medium'],'Öl auf Holz')
        self.assertEqual(parsed['facts']['dimensions'],'14.3 x 23.9 x 3 cm')

    def test_changed_native_title_cannot_be_imported(self):
        changed=self.raw.replace(b'<i>Die Seine bei Charenton</i>',b'<i>Different artwork</i>',1)
        self.assertEqual(c.aargauer_native(changed,self.index)[1],'native_index_title_creator_date_conflict')

    def test_incoming_loan_is_held(self):
        changed=self.raw.replace(b'Aargauer Kunsthaus / Legat Dr. Max Fretz, 1958',b'Aargauer Kunsthaus / Dauerleihgabe private collection',1)
        self.assertEqual(c.aargauer_native(changed,self.index)[1],'qualified_collection_custody_requires_review')

    def test_wrong_object_url_is_held(self):
        index=copy.deepcopy(self.index);index['url']='https://aargauerkunsthaus.ch/werk/different/'
        self.assertEqual(c.aargauer_native(self.raw,index)[1],'canonical_object_conflict')

    def test_cutoff_and_unresolved_creation_dates(self):
        for value in ['1971','1969 - 1972','um 1970','ohne Jahr','1923 / 1963']:
            self.assertIsNone(c.aargauer_date(value),value)
        self.assertEqual(c.aargauer_date('1970'),(1970,1970,'exact'))
        self.assertEqual(c.aargauer_date('um 1885'),(1885,1885,'circa'))


if __name__=='__main__':unittest.main()
