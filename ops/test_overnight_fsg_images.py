"""Synthetic FSG rights, attribution and date safeguards; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('fsg_test',Path(__file__).with_name('overnight-fsg-images.py'));fsg=importlib.util.module_from_spec(s);s.loader.exec_module(fsg)
def example():
    fields={'objectType':[{'label':'Type','content':'Painting'}], 'identifier':[{'label':'Accession Number','content':'F1900.1'}],
      'name':[{'label':'Artist','content':'Example Painter (1800-1870)'}], 'date':[{'label':'Date','content':'1850'}],
      'objectRights':[{'label':'Restrictions & Rights','content':'CC0'}], 'notes':[{'label':'Collection','content':'Freer Gallery of Art Collection'}],
      'place':[{'label':'Origin','content':'Japan'}]}
    o={'unitCode':'FSG','content':{'freetext':fields,'descriptiveNonRepeating':{'data_source':'National Museum of Asian Art','record_ID':'fsg_F1900.1',
      'record_link':'https://asia.si.edu/object/F1900.1/','metadata_usage':{'access':'CC0'},'title':{'content':'Synthetic painting'},
      'online_media':{'media':[{'type':'Images','usage':{'access':'CC0'},'idsId':'FS-SYNTHETIC','content':'https://ids.si.edu/ids/deliveryService?id=FS-SYNTHETIC'}]}}}}
    c={'external_id':'F1900.1','accession_number':'F1900.1','title':'Synthetic painting','work_type':'painting','roles':['primary'],'artist':'Example Painter','aliases':[],
      'date_display':'1850','creation_year_start':1850,'creation_year_end':1850,'date_precision':'exact','creation_place_display':'Japan'}
    return c,o
class Safety(unittest.TestCase):
    def test_exact_cc0(self):
        c,o=example();self.assertEqual(fsg.source_match(c,o)[2]['source_origin'],['Japan'])
    def test_media_rights_separate_from_metadata(self):
        c,o=example();o['content']['descriptiveNonRepeating']['online_media']['media'][0]['usage']={'access':'Educational use'}
        with self.assertRaises(ValueError):fsg.source_match(c,o)
    def test_multiple_views_require_review(self):
        c,o=example();media=o['content']['descriptiveNonRepeating']['online_media']['media'];media.append(copy.deepcopy(media[0]))
        with self.assertRaises(ValueError):fsg.source_match(c,o)
    def test_lifespan_not_creation(self):
        c,o=example();c.update(date_display='1800-1870',creation_year_start=1800,creation_year_end=1870,date_precision='range');o['content']['freetext']['date'][0]['content']='1800-1870'
        with self.assertRaisesRegex(ValueError,'lifespan'):fsg.source_match(c,o)
    def test_qualifications_preserved(self):
        for label in ('Formerly attributed to Example Painter','Signature of Example Painter','After Example Painter'):
            with self.assertRaises(ValueError):fsg.creator_variants(label)
    def test_bilingual_exact_variants(self):
        self.assertEqual(fsg.creator_variants('Example Painter 画家 (1800-1870)'),{'Example Painter 画家','Example Painter'})
    def test_dates(self):
        self.assertEqual(fsg.date_parts('ca. 1879-80'),(1879,1880,'circa_range'))
        self.assertEqual(fsg.date_parts('18th century'),(1700,1799,'century'))
        for v in ('after 1850','20th century','1965-1980','unknown','early 1800s'):
            with self.assertRaises(ValueError):fsg.date_parts(v)
    def test_exact_media_identity(self):
        c,o=example();o['content']['descriptiveNonRepeating']['online_media']['media'][0]['content']='https://ids.si.edu/ids/deliveryService?id=FS-OTHER'
        with self.assertRaises(ValueError):fsg.source_match(c,o)
    def test_origin_preserved(self):
        c,o=example();c['creation_place_display']='United States'
        with self.assertRaisesRegex(ValueError,'origin'):fsg.source_match(c,o)
if __name__=='__main__':unittest.main()
