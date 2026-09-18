"""Synthetic-only image rights and identity safeguards; never connects to a DB."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('mia',Path(__file__).with_name('overnight-mia-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TestMiaImageSelection(unittest.TestCase):
    def setUp(self):
        self.c={'external_id':'42','title':'Synthetic landscape','work_type':'painting','accession_number':'22.4','roles':['primary'],'artist':'Synthetic Painter','aliases':[],'creation_year_start':1800,'creation_year_end':1800,'date_precision':'exact'}
        self.o={'id':42,'title':'Synthetic landscape','classification':'Paintings','accession_number':'22.4','artist':'Synthetic Painter','dated':'1800','life_date':'1700–1801','creditline':'Museum purchase','rights_type':'Public Domain','image':'valid','public_access':1,'Rights_Image_Display':'Full','Cache_Location':'000000\\0\\40\\42','Primary_RenditionNumber':'mia_synthetic.jpg'}
    def test_exact_image(self):
        url,facts=m.source_match(self.c,self.o);self.assertEqual(url,'https://img.artsmia.org/web_objects_cache/000000/0/40/42/mia_synthetic_800.jpg');self.assertEqual(facts['source_year_start'],1800)
    def test_rights_fail_closed(self):
        for right in [None,'In Copyright','No Copyright–United States','Copyright Not Evaluated','CC BY-NC']:
            with self.subTest(right=right),self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'rights_type':right})
    def test_conflicting_image_copyright(self):
        with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'image_copyright':'Copyright photographer'})
    def test_restricted_image(self):
        with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'restricted':1})
    def test_loan_not_holding(self):
        with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'creditline':'On loan from a private collection'})
    def test_date_must_agree(self):
        for date in ['unknown','after 1900','1960–1980','1801']:
            with self.subTest(date=date),self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'dated':date})
    def test_other_image_path_rejected(self):
        for path in ['000000/41','../42','https://other.example/42']:
            with self.subTest(path=path),self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'Cache_Location':path})
    def test_qualified_creator(self):
        c={**self.c,'aliases':['After Synthetic Painter']}
        with self.assertRaises(ValueError):m.source_match(c,{**self.o,'artist':'After Synthetic Painter'})
    def test_other_object(self):
        with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'id':43})
    def test_other_type(self):
        with self.assertRaises(ValueError):m.source_match(self.c,{**self.o,'classification':'Photographs'})
    def test_print_publisher_is_separate_from_artist(self):
        c={**self.c,'work_type':'print'};o={**self.o,'classification':'Prints','artist':'Synthetic Painter; Publisher: Synthetic Press'}
        self.assertTrue(m.source_match(c,o)[0].endswith('_800.jpg'))
    def test_second_visual_creator_is_held(self):
        c={**self.c,'work_type':'print'};o={**self.o,'classification':'Prints','artist':'Synthetic Painter; Engraver: Another Person'}
        with self.assertRaises(ValueError):m.source_match(c,o)
    def test_unlabelled_second_creator_is_held(self):
        with self.assertRaises(ValueError):m.creator_name('Synthetic Painter; Another Person','print')
    def test_explicit_painter_role_is_primary(self):
        c={**self.c,'artist':'Painter: Synthetic Painter'}
        self.assertTrue(m.source_match(c,{**self.o,'artist':'Painter: Synthetic Painter'})[0])
if __name__=='__main__':unittest.main()
