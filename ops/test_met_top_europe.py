"""Offline source and delivery gates; no catalogue connection or test database."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import requests

spec=importlib.util.spec_from_file_location('review',Path(__file__).with_name('met-top-europe-review.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


class MetSafetyTests(unittest.TestCase):
    def setUp(self):
        self.lead={'source_object_id':'42','object':{'Object ID':'42','Object Number':'A.1'},'work_type':'painting',
            'artist':{'id':'synthetic-artist','display_name':'Synthetic Artist','qid':'Q42','slug':'synthetic-artist','popular':False,'country_codes':['FR']}}
        self.obj={'objectID':42,'isPublicDomain':True,'rightsAndReproduction':'','primaryImageSmall':'https://images.metmuseum.org/synthetic.jpg',
            'accessionNumber':'A.1','artistWikidata_URL':'https://www.wikidata.org/entity/Q42',
            'constituents':[{'role':'Artist','constituentWikidata_URL':'https://www.wikidata.org/entity/Q42'}],
            'repository':'The Metropolitan Museum of Art','creditLine':'Gift, 1900',
            'objectURL':'https://www.metmuseum.org/art/collection/search/42','objectBeginDate':1850,'objectEndDate':1850,
            'objectDate':'1850','classification':'Paintings','objectName':'Painting','title':'Synthetic Work'}

    def test_explicit_cc0_source_passes(self):
        c=review.research.verify(self.lead,self.obj)
        self.assertEqual(c['artist_qid'],'Q42')
        self.assertEqual(c['date_precision'],'exact')

    def test_restricted_or_changed_source_is_held(self):
        changes=[{'isPublicDomain':False},{'rightsAndReproduction':'Copyright'},
            {'primaryImageSmall':'https://example.invalid/image.jpg'},{'objectID':43},
            {'artistWikidata_URL':'https://www.wikidata.org/entity/Q43'},
            {'artistPrefix':'Attributed to'},{'accessionNumber':'A.2'},
            {'constituents':[]},{'creditLine':'On loan from private collection'},
            {'objectDate':'1971','objectBeginDate':1971,'objectEndDate':1971},
            {'classification':'Photographs','objectName':'Photograph'}]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(ValueError):
                review.research.verify(self.lead,dict(copy.deepcopy(self.obj),**change))

    def test_404_is_object_hold_but_403_pauses_provider(self):
        for status in (404,403):
            with self.subTest(status=status),tempfile.TemporaryDirectory(prefix='artline-met-unit-') as folder:
                root=Path(folder);run=root/'fresh-selection'
                review.core.save_new(run/'source-candidates.json',[self.lead])
                response=requests.Response();response.status_code=status
                error=requests.HTTPError('Synthetic source status',response=response)
                with patch.object(review.core.Fetcher,'metadata',side_effect=error):
                    review.fresh(SimpleNamespace(run=root,limit=1))
                self.assertEqual((run/'review-held/42.json').exists(),status==404)
                self.assertEqual((run/'source-pause-42.json').exists(),status==403)

    def test_explicit_creator_roles_are_work_type_specific(self):
        for kind,role in [('drawing','Draftsman'),('drawing','Draughtsman'),('print','Etcher'),('print','Artist and publisher')]:
            with self.subTest(kind=kind,role=role):
                lead=dict(self.lead,work_type=kind);obj=copy.deepcopy(self.obj)
                obj.update(classification=kind+'s',objectName=kind)
                obj['constituents'][0]['role']=role
                self.assertEqual(review.research.verify(lead,obj)['work_type'],kind)
                with self.assertRaises(ValueError):review.research.verify(self.lead,obj)

    def test_publisher_and_multiple_makers_are_not_promoted_to_artist(self):
        for role in ('Publisher','Sitter','After','Artist of original'):
            obj=copy.deepcopy(self.obj);obj['constituents'][0]['role']=role
            with self.subTest(role=role),self.assertRaises(ValueError):review.research.verify(self.lead,obj)
        obj=copy.deepcopy(self.obj);obj['constituents'].append(dict(obj['constituents'][0],constituentWikidata_URL='https://www.wikidata.org/wiki/Q43'))
        with self.assertRaises(ValueError):review.research.verify(self.lead,obj)

    def test_conflicting_creator_life_year_is_held_unknown_is_preserved(self):
        lead=copy.deepcopy(self.lead);lead['artist'].update(birth_year=1800,death_year=None)
        obj=dict(self.obj,artistBeginDate='1801',artistEndDate='1880')
        with self.assertRaisesRegex(ValueError,'life date'):review.research.verify(lead,obj)
        self.assertEqual(review.research.verify(lead,dict(obj,artistBeginDate='1800'))['artist_id'],'synthetic-artist')


if __name__=='__main__':unittest.main()
