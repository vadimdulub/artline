"""Offline rejection tests; never connects to a catalogue database."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('research_images',Path(__file__).with_name('enrich-research-images.py'))
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ResearchImageIdentity(unittest.TestCase):
    def setUp(self):
        self.c={'external_id':'KMS123 verso','title':'A study','creation_year_start':1901,
          'creation_year_end':1902,'facts_json':{'painter':{'source_id':'12_person'}}}
        self.raw={'object_number':'KMS123 verso','titles':[{'title':'A study'}],
          'production':[{'creator_lref':'12_person'}],
          'production_date':[{'start':'1901-01-01','end':'1902-12-31'}]}

    def test_exact_side_and_unresolved_creator_source_are_valid(self):
        m.validate_current(self.c,self.raw)

    def test_front_cannot_illustrate_verso(self):
        self.raw['object_number']='KMS123'
        with self.assertRaisesRegex(ValueError,'side mismatch'):m.validate_current(self.c,self.raw)

    def test_changed_source_creator_rejected(self):
        self.raw['production'][0]['creator_lref']='13_person'
        with self.assertRaisesRegex(ValueError,'creator differs'):m.validate_current(self.c,self.raw)

    def test_changed_title_rejected(self):
        self.raw['titles'][0]['title']='Another study'
        with self.assertRaisesRegex(ValueError,'title differs'):m.validate_current(self.c,self.raw)

    def test_cross_cutoff_and_unknown_dates_rejected(self):
        for dates in [[],[{'start':'1901-01-01'}],[{'start':'1901-01-01','end':'1971-12-31'}]]:
            with self.subTest(dates=dates):
                raw=copy.deepcopy(self.raw);raw['production_date']=dates
                with self.assertRaises(ValueError):m.validate_current(self.c,raw)

    def test_research_identity_change_rejected(self):
        candidate={k:'same' for k in m.KEYS}
        row={**candidate,'entry_sha256':'changed'}
        class DB:
            def execute(self,*args):return self
            def fetchall(self):return [row]
        with self.assertRaisesRegex(ValueError,'identity'):m.lookup(DB(),candidate)

    def test_accession_filename_requires_exact_open_museum_record(self):
        c={**self.c,'provider':'smk'}
        raw={**self.raw,'public_domain':True,'rights':m.core.POLICIES['smk'],'has_image':True,
             'image_native':'https://api.smk.dk/api/v1/thumbnail/kms938.jpg'}
        class Fetcher:
            def metadata(self,url):return {'items':[raw]}
        for extension in ['jpg','JPG']:
            raw['image_native']='https://api.smk.dk/api/v1/thumbnail/kms938.'+extension
            self.assertEqual(m.image_record(c,Fetcher(),{}, {})['source_image_url'],raw['image_native'])
        for url in ['https://api.smk.dk/api/v1/thumbnail/../secret.jpg','https://elsewhere.example/kms938.jpg']:
            raw['image_native']=url
            self.assertIsNone(m.image_record(c,Fetcher(),{},{}))
        raw['image_native']='https://api.smk.dk/api/v1/thumbnail/kms938.jpg'
        raw['public_domain']=False
        self.assertIsNone(m.image_record(c,Fetcher(),{},{}))


if __name__=='__main__':unittest.main()
