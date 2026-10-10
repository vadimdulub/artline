"""Offline checks for material catalogue and holding-evidence boundaries."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('nordic',Path(__file__).with_name('nordic-museums-20261008.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)

def claim(value,**extra):
    return dict(rank='normal',mainsnak=dict(snaktype='value',datavalue=dict(value=value)),**extra)

class EvidenceBoundaries(unittest.TestCase):
    def setUp(self):
        self.museum=dict(qid='Q100',institution_id='00000000-0000-0000-0000-000000000001')
        self.work=dict(id='Q200',labels={'en':{'value':'Anonymous painting'}},claims={
            'P31':[claim({'id':'Q3305213'})],
            'P195':[claim({'id':'Q100'},references=[{'snaks':{'P854':[{'snaktype':'value','datavalue':{'value':'https://museum.example/object/1'}}]}}])],
            'P571':[claim(dict(time='+1900-00-00T00:00:00Z',precision=9,before=0,after=0,calendarmodel='http://www.wikidata.org/entity/Q1985727'))],
        })
    def evaluate(self):return n.work_fields(self.work,self.museum,{},dict(retrieved_at='2026-10-08T00:00:00Z'))
    def test_anonymous_dated_object_keeps_unknown_creator(self):
        row,error=self.evaluate();self.assertIsNone(error);self.assertIsNone(row['creator_label']);self.assertEqual(row['first'],1900)
    def test_missing_date_is_preserved_without_inventing_year(self):
        del self.work['claims']['P571'];row,error=self.evaluate();self.assertIsNone(error);self.assertEqual(row['precision'],'unknown');self.assertIsNone(row['first'])
    def test_post_cutoff_is_not_selected(self):
        self.work['claims']['P571'][0]['mainsnak']['datavalue']['value']['time']='+1971-00-00T00:00:00Z'
        row,error=self.evaluate();self.assertIsNone(row);self.assertIn('cutoff',error)
    def test_approximate_cutoff_needs_review(self):
        d=self.work['claims']['P571'][0];d['mainsnak']['datavalue']['value']['time']='+1970-00-00T00:00:00Z';d['qualifiers']={'P1480':[{'datavalue':{'value':{'id':'Q5727902'}}}]}
        self.assertIsNone(self.evaluate()[0])
    def test_past_holding_is_not_current_holding(self):
        self.work['claims']['P195'][0]['qualifiers']={'P582':[{'datavalue':{'value':{'time':'+1990-00-00T00:00:00Z'}}}]}
        row,error=self.evaluate();self.assertIsNone(row);self.assertIn('qualifier',error)
    def test_two_collections_require_object_review(self):
        self.work['claims']['P195'].append(claim({'id':'Q101'}));self.assertIsNone(self.evaluate()[0])
    def test_uncited_collection_is_not_automatically_accepted(self):
        self.work['claims']['P195'][0]['references']=[];row,error=self.evaluate();self.assertIsNone(row);self.assertIn('source reference',error)
    def test_diptych_part_does_not_become_independent_object(self):
        self.work['claims']['P361']=[claim({'id':'Q300'})];row,error=self.evaluate();self.assertIsNone(row);self.assertIn('ensemble',error)
    def test_qualified_artist_is_not_silently_made_primary(self):
        self.work['claims']['P170']=[claim({'id':'Q400'},qualifiers={'P3831':[{'datavalue':{'value':{'id':'Q100'}}}]})]
        row,error=self.evaluate();self.assertIsNone(row);self.assertIn('creator',error)
    def test_swedish_and_smithsonian_portrait_galleries_are_distinct(self):
        with self.assertRaises(AssertionError):
            n.validate_institution_crosswalks([dict(qid='Q2817221',reason=None,before={'wikidata_id':'Q1967614'})])
    def test_documented_branch_uses_verified_canonical_authority(self):
        n.validate_institution_crosswalks([dict(qid='Q113468011',canonical_qid='Q4976948',reason=None,before={'wikidata_id':'Q4976948'})])

if __name__=='__main__':unittest.main()
