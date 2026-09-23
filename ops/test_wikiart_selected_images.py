"""Regression checks for identity and honest rights labels; no database access."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('wikiart',Path(__file__).with_name('wikiart-selected-images.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SelectionTests(unittest.TestCase):
    def record(self,year='1950',title='Example',public=False):
        source={'title':title,'year':year,'artistUrl':'/en/example-artist','_id':'source-object'}
        html='<div class="wiki-layout-painting-info-bottom" ng-init=\'paintingJson = '+json.dumps(source)+'\'></div>'
        html+='<img itemprop="image" src="https://uploads8.wikiart.org/example.jpg"/>'
        html+='<div class="copyright-wrapper"><a class="copyright">'+('<i class="copyright-icon-public-domain"></i>Public domain' if public else 'Copyright protected')+'</a></div>'
        work={'artwork_id':'example-id','title':'Example','alternate_title':None,'creation_year_start':1900,'creation_year_end':1955,
              'artist':{'display_name':'Example Artist','slug':'example-artist'}}
        return module.page_record({'work':work},html,{'final_url':'https://www.wikiart.org/en/example-artist/example','sha256':'x'})

    def test_age_does_not_invent_public_domain(self):
        self.assertEqual(self.record()['rights_status'],'restricted')

    def test_source_public_domain_label_preserved(self):
        self.assertEqual(self.record(public=True)['rights_status'],'public_domain')

    def test_creation_cutoff_blocks_later_image(self):
        with self.assertRaisesRegex(ValueError,'cutoff'):self.record(year='1956')

    def test_date_range_is_preserved(self):
        record=self.record(year='1950-1952')
        self.assertEqual((record['source_year'],record['source_year_end']),(1950,1952))

    def test_range_crossing_cutoff_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'cutoff'):self.record(year='1954-1956')

    def test_html_entities_do_not_change_title_identity(self):
        self.assertEqual(module.norm('d&#39;Etremon'),module.norm("d'Etremon"))

    def test_wrong_artwork_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'title'):self.record(title='Different artwork')

    def test_unknown_year_is_not_invented(self):
        with self.assertRaisesRegex(ValueError,'date'):self.record(year='')

    def test_evidence_cannot_be_silently_overwritten(self):
        with tempfile.TemporaryDirectory(prefix='wikiart-unit-',dir='/tmp') as folder:
            p=Path(folder)/'receipt.json';module.save_atomic(p,{'source':'first'})
            module.save_atomic(p,{'source':'first'})
            with self.assertRaisesRegex(ValueError,'differs'):module.save_atomic(p,{'source':'second'})
            self.assertEqual(json.loads(p.read_bytes()),{'source':'first'})

    def test_multiple_source_objects_do_not_attach_arbitrarily(self):
        previous=module.RUN
        try:
            with tempfile.TemporaryDirectory(prefix='wikiart-unit-',dir='/tmp') as folder:
                module.RUN=Path(folder)
                matches=[{'work':{'artwork_id':'one'},'wikiart':{'url':url}} for url in ('source-a','source-b')]
                module.save_atomic(module.RUN/'discovery-v2'/'artist.json',{'matches':matches})
                self.assertEqual(module.discovered_matches(),[])
                module.save_atomic(module.RUN/'identity-resolutions'/'one.json',{'selected_url':'source-b'})
                self.assertEqual(module.discovered_matches(),[matches[1]])
        finally:module.RUN=previous


if __name__=='__main__':unittest.main()
