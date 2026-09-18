import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('depicts',Path(__file__).with_name('popular-commons-depicts.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def statement(value):
    return {'mainsnak':{'snaktype':'value','datavalue':{'value':value}}}

class OriginalPhotograph(unittest.TestCase):
    def setUp(self):
        self.c={'qid':'Q1','artist':'Synthetic Painter','institution_qid':'Q2','creators':[{'qid':'Q3','name':'Synthetic Painter'}]}
        self.e={'claims':{'P373':[statement('Synthetic Painting')]}}
        self.inst={'id':'Q2','labels':{'en':{'value':'Synthetic Museum'}}}
        self.page={'ns':6,'title':'File:Synthetic original.jpg','revisions':[{'slots':{'main':{'*':'Synthetic Painter at Synthetic Museum.\n[[Category:Synthetic Painting]]'}}}],
                   'imageinfo':[{'width':800,'height':600,'extmetadata':{'Credit':{'value':'Own work'},'Artist':{'value':'Synthetic Photographer'}}}]}
        self.sdc={'claims':{'P180':[statement({'id':'Q1'})]}}

    def check(self):
        with patch.object(m.m,'entity_match'):
            m.identity(self.c,self.e,self.page,self.sdc,self.inst)

    def test_exact_category_creator_museum_and_photographer_pass(self):self.check()

    def test_depicts_alone_cannot_import_mislabelled_sculpture(self):
        self.page['revisions'][0]['slots']['main']['*']='Synthetic Painter, Synthetic Museum. [[Category:Unrelated statue]]'
        with self.assertRaisesRegex(ValueError,'category'):self.check()

    def test_multiple_depicted_objects_are_held(self):
        self.sdc['claims']['P180'].append(statement({'id':'Q9'}))
        with self.assertRaisesRegex(ValueError,'single artwork'):self.check()

    def test_copy_category_blocks_otherwise_matching_picture(self):
        self.page['revisions'][0]['slots']['main']['*']+=' [[Category:Synthetic Painting - works after]]'
        with self.assertRaisesRegex(ValueError,'copied'):self.check()

    def test_annotation_is_not_a_clean_artwork_reproduction(self):
        self.page['title']='File:Schema prospettico of synthetic painting.jpg'
        with self.assertRaisesRegex(ValueError,'Annotated'):self.check()

    def test_conflicting_physical_object_is_not_overridden(self):
        self.sdc['claims']['P6243']=[statement({'id':'Q9'})]
        with self.assertRaises(ValueError):self.check()

    def test_artist_and_original_museum_are_required(self):
        for missing in ('Synthetic Painter','Synthetic Museum'):
            page=copy.deepcopy(self.page)
            self.page['revisions'][0]['slots']['main']['*']=self.page['revisions'][0]['slots']['main']['*'].replace(missing,'Unknown')
            with self.subTest(missing=missing),self.assertRaises(ValueError):self.check()
            self.page=page

    def test_book_scan_with_user_credit_is_not_original_photo(self):
        self.page['imageinfo'][0]['extmetadata']['Credit']['value']='Scanned from a book by User:Synthetic'
        with self.assertRaisesRegex(ValueError,'scan'):self.check()

    def test_photographer_is_required(self):
        self.page['imageinfo'][0]['extmetadata']['Artist']['value']='Synthetic Painter'
        with self.assertRaisesRegex(ValueError,'Photographer'):self.check()

if __name__=='__main__':unittest.main()
