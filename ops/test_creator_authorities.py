"""Offline adversarial identity cases; no database access or fixtures."""
import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('reconcile-creator-authorities.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

class CreatorAuthorities(unittest.TestCase):
    def test_only_explicit_closed_lifespan_is_parsed(self):
        self.assertEqual(a.a.l.parse('Example Jean (1800–1870)')['birth'],1800)
        for name in ['Example (active 1800–1870)','Example (c.1800–1870)','Example (1800–1870) workshop','Example (peintre)','Example (1800–?)']:
            self.assertIsNone(a.a.l.parse(name))

    def test_alternate_name_collision_blocks_new_person(self):
        existing={'id':'one','display_name':'Jean Example','aliases':['J. Example'],'birth_year':1800,'death_year':1870,'status':'review','entity_type':'person','authorities':[]}
        planned={'slug':'new','identity_ids':[],'identity_names':['Example, J.']}
        with self.assertRaises(AssertionError):a.no_new_collision(planned,a.m.Matcher([existing]))

    def test_museum_identifier_blocks_differently_named_duplicate(self):
        existing={'id':'one','display_name':'Completely Different Name','aliases':[],'birth_year':None,'death_year':None,'status':'review','entity_type':'person','authorities':[{'scheme':'nga-constituent','id':'123'}]}
        planned={'slug':'new','identity_ids':[{'scheme':'nga-constituent','id':'123'}],'identity_names':['Jean Example']}
        with self.assertRaises(AssertionError):a.no_new_collision(planned,a.m.Matcher([existing]))

    def test_wrong_property_schemes_are_not_used(self):
        self.assertEqual(a.ID_PROPERTIES,{'P2252':'nga-constituent','P2174':'moma-person','P2741':'tate-person'})

if __name__=='__main__':unittest.main()
