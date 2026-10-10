"""Offline checks of actual captured object/image bindings and conservative dates."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('secondary',Path(__file__).with_name('source-index-secondary-20261010.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class SourceBindingTests(unittest.TestCase):
    def test_smk_subobject_identifiers_are_not_truncated(self):
        refs=[dict(id='one',provider_id='smk',url='https://open.smk.dk/artwork/image/DEP1069/11'),
              dict(id='two',provider_id='smk',url='https://api.smk.dk/api/v1/art?object_number=DEP1069%2F12')]
        with patch.object(s.n.m,'resources',return_value=refs):result,_=s.n.refs()
        self.assertEqual(set(result['smk']),{'DEP1069/11','DEP1069/12'})

    def test_qualified_century_keeps_conservative_bounds(self):
        self.assertEqual(s.bounds('Конец XVIII века'),(1701,1800,'century'))

    def test_unexplained_year_in_prose_is_not_a_creation_date(self):
        self.assertEqual(s.bounds('Acquired in 1920'),(None,None,'unknown'))
        self.assertEqual(s.bounds('Donated 1904; accessioned 1923'),(None,None,'unknown'))

    def test_russian_explicit_creation_year(self):
        self.assertEqual(s.bounds('1905 г.'),(1905,1905,'exact'))

    def test_mixed_walters_class_does_not_force_a_painting(self):
        r=dict(provider='walters',raw={},facts=dict(classification='Painting & Drawing',medium='ink on paper'))
        self.assertEqual(s.r.effective_facts(r)['work_type'],'drawing')

    def page(self,key):
        return s.m.load(s.RUN/'object-pages'/(key+'.json.gz'))

    def work(self):return dict(current_institution_id='museum',work_type='painting')

    def test_chicago_image_must_have_its_own_cc0_grant(self):
        page=self.page('src_00e361ef81fb911313c11755');f,_=s.parse(page,self.work())
        self.assertEqual(f['rights_status'],'cc0');self.assertIn('/full/',f['image'])
        sp=s.soup(page)
        for tag in sp.select('[data-gallery-img-credit]'):tag['data-gallery-img-credit']=''
        with patch.object(s,'soup',return_value=sp):
            with self.assertRaises(AssertionError):s.parse(page,self.work())

    def test_thessaloniki_uses_object_title_and_creation_field(self):
        page=self.page('src_04397c547e7eab0f87558273');f,_=s.parse(page,self.work())
        self.assertEqual(f['titles'],['General view of Mount Athos'])
        self.assertEqual(f['dates']['end'],1767)
        self.assertEqual(f['rights_status'],'restricted')

    def test_taiwan_larger_image_keeps_attribution_license(self):
        native=[s.m.load(s.m.ROOT/x['native_file']) for x in s.m.load(s.RUN/'secondary-resolution-005.json.gz')['rows'] if x['provider']=='domain:digitalarchive.npm.gov.tw']
        larger=[x for x in native if x['raw']['image_dimensions_and_tier']['Width']*x['raw']['image_dimensions_and_tier']['Height']>1100000]
        self.assertTrue(larger)
        for x in larger:
            self.assertEqual(x['facts']['rights_status'],'cc_by')
            self.assertIn('CC BY 4.0',x['facts']['credit'])
            self.assertEqual(x['facts']['license_url'],'https://creativecommons.org/licenses/by/4.0/')

if __name__=='__main__':unittest.main()
