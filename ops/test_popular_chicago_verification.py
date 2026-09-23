"""Synthetic identity/rights regression cases; no catalogue or network writes."""
import copy
import importlib.util
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('chicago',Path(__file__).with_name('popular-chicago-verification.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class Verification(unittest.TestCase):
    def setUp(self):
        self.artist=dict(display_name='Example Painter',aliases=[],birth_year=1800,death_year=1880,qid='Qsynthetic')
        self.person=dict(id=1,title='Example Painter',alt_titles=[],birth_date=1800,death_date=1880,is_artist=True)
        self.obj=dict(id=2,title='Synthetic work',artist_id=1,artist_pivots=[dict(is_preferred=True,artist_id=1,role_title='Artist')],
                      artist_display='Example Painter (1800–1880)',artwork_type_title='Painting',date_start=1840,date_end=1840,
                      date_display='1840',main_reference_number='1900.1',credit_line='Gift of Example Donor',is_public_domain=True,
                      copyright_notice=None,image_id='12345678-1234-1234-1234-123456789abc')
        self.im=dict(id=self.obj['image_id'],type='image',credit_line='CC0 Public Domain Designation',
                     iiif_url='/'+self.obj['image_id'],artwork_ids=[2],width=1000,height=1000)
    def test_verified_metadata_without_image(self):
        self.obj.update(image_id=None,is_public_domain=False,copyright_notice='Rights reserved')
        self.assertEqual(m.metadata(self.obj,self.artist,self.person)['work_type'],'painting')
        with self.assertRaises(ValueError):m.image(self.obj,self.im)
    def test_qualified_creator_rejected_even_when_api_artist_id_matches(self):
        for text in ['A different artist, after Example Painter','Example Painter, style of','Example Painter, imitator of']:
            with self.subTest(text=text),self.assertRaises(ValueError):m.metadata({**self.obj,'artist_display':text},self.artist,self.person)
    def test_later_printing_is_not_the_design_date(self):
        for text in ['1840, printed 1900','1840 (printed later)']:
            with self.subTest(text=text),self.assertRaises(ValueError):m.metadata({**self.obj,'date_display':text,'artwork_type_title':'Print'},self.artist,self.person)
    def test_abbreviated_textual_range_is_not_lost(self):
        actual=m.metadata({**self.obj,'date_display':'1840–42'},self.artist,self.person)
        self.assertEqual((actual['creation_year_start'],actual['creation_year_end'],actual['date_precision']),(1840,1842,'range'))
    def test_loan_and_unknown_date_rejected(self):
        for patch in [dict(credit_line='On loan from private collection'),dict(fiscal_year_deaccession=2020),dict(date_display='n.d.'),dict(date_display='after 1840'),dict(date_start=1965,date_end=1980)]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):m.metadata({**self.obj,**patch},self.artist,self.person)
    def test_metadata_cc0_cannot_license_image(self):
        for credit in ['', 'Copyright Reserved', 'CC BY-NC 4.0']:
            with self.subTest(credit=credit),self.assertRaises(ValueError):m.image(self.obj,{**self.im,'credit_line':credit})
    def test_image_must_be_uniquely_attached_to_exact_object(self):
        for ids in [[3],[2,3],[]]:
            with self.subTest(ids=ids),self.assertRaises(ValueError):m.image(self.obj,{**self.im,'artwork_ids':ids})
    def test_conflicting_object_copyright_overrides_image_cc0(self):
        with self.assertRaises(ValueError):m.image({**self.obj,'copyright_notice':'All rights reserved'},self.im)
    def test_exact_cc0_image(self):
        self.assertTrue(m.image(self.obj,self.im).endswith('/full/843,/0/default.jpg'))
    def test_artist_life_conflict(self):
        with self.assertRaises(ValueError):m.metadata(self.obj,self.artist,{**self.person,'death_date':1900})
    def test_artist_lifespan_is_not_an_artwork_date(self):
        with self.assertRaises(ValueError):m.metadata({**self.obj,'date_start':1800,'date_end':1880,'date_display':'1800–1880'},self.artist,self.person)

if __name__=='__main__':unittest.main()
