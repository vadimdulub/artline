"""Offline regressions for image permission/identity gates; no catalogue writes."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('gaps', Path(__file__).with_name('open-access-image-gaps.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ImageClearance(unittest.TestCase):
    def met(self):
        return {'provider':'met','external_id':'1','artist':'Claude Monet',
                'artist_slugs':['claude-monet'],'roles':['primary'],'aliases':[],
                'accession_number':'1900.1','title':'Landscape','work_type':'painting',
                'creation_year_start':1900,'creation_year_end':1900,
                'source_image_url':'https://images.metmuseum.org/example.jpg',
                'raw':{'objectID':1,'title':'Landscape','accessionNumber':'1900.1',
                       'artistDisplayName':'Claude Monet','isPublicDomain':True,
                       'rightsAndReproduction':'','primaryImageSmall':'https://images.metmuseum.org/example.jpg',
                       'objectName':'Painting','classification':'Paintings',
                       'objectBeginDate':1900,'objectEndDate':1900}}

    def test_exact_open_image(self):
        m.verify_identity(self.met())

    def test_original_fallback_requires_exact_api_original(self):
        im=self.met();im['raw']['primaryImage']='https://images.metmuseum.org/original.jpg'
        im['source_view']='original';im['source_image_url']=im['raw']['primaryImage']
        m.verify_identity(im)
        im['source_image_url']='https://images.metmuseum.org/unrelated.jpg'
        with self.assertRaises(ValueError):m.verify_identity(im)

    def test_original_cannot_bypass_known_primary_image_mismatch(self):
        im=self.met();im['external_id']='409630'
        im['raw']['primaryImageSmall']='https://images.metmuseum.org/CRDImages/dp/web-large/DP848650.jpg'
        im['raw']['primaryImage']='https://images.metmuseum.org/original.jpg'
        im['source_view']='original';im['source_image_url']=im['raw']['primaryImage']
        # Use a temporary exact conflict so this regression is independent of
        # edits to the production conflict registry.
        original=m.core.validate_source_image_identity
        def check(candidate):
            if candidate['source_image_url']==im['raw']['primaryImageSmall']:
                raise ValueError('Known source identity conflict')
        try:
            m.core.validate_source_image_identity=check
            with self.assertRaises(ValueError):m.verify_identity(im)
        finally:m.core.validate_source_image_identity=original

    def test_metadata_cc0_does_not_override_object_rights(self):
        for fields in [{'isPublicDomain':False}, {'rightsAndReproduction':'Copyright estate'},
                       {'isPublicDomain':None}]:
            with self.subTest(fields=fields):
                im=self.met(); im['raw'].update(fields)
                with self.assertRaises(ValueError):m.verify_identity(im)

    def test_wrong_object_creator_or_image_is_held(self):
        for fields in [{'accessionNumber':'1900.2'}, {'title':'Other work'},
                       {'artistDisplayName':'Other artist'}, {'primaryImageSmall':'https://images.metmuseum.org/other.jpg'}]:
            with self.subTest(fields=fields):
                im=self.met(); im['raw'].update(fields)
                with self.assertRaises(ValueError):m.verify_identity(im)

    def test_newer_or_unknown_source_dates_are_held(self):
        for date in [1971,None,0,True]:
            with self.subTest(date=date):
                im=self.met(); im['raw']['objectEndDate']=date
                with self.assertRaises(ValueError):m.verify_identity(im)

    def test_cleveland_conflicting_reproduction_terms_are_held(self):
        im=self.met(); im['provider']='cleveland'
        im['raw']={'id':1,'title':'Landscape','accession_number':'1900.1',
                   'creators':[{'role':'artist','description':'Claude Monet (French, 1840–1926)'}],
                   'share_license_status':'CC0','images':{'web':{'url':im['source_image_url']}},
                   'type':'Painting','creation_date_earliest':1900,'creation_date_latest':1900}
        m.verify_identity(im)
        bad=copy.deepcopy(im); bad['raw']['rights_and_reproductions']='Noncommercial only'
        with self.assertRaises(ValueError):m.verify_identity(bad)


if __name__=='__main__':unittest.main()
