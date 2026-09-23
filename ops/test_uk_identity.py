import importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('uk',Path(__file__).with_name('uk-painters-20260920.py'))
u=importlib.util.module_from_spec(s);s.loader.exec_module(u)

def claim(value):return {'mainsnak':{'snaktype':'value','datavalue':{'value':value}},'rank':'normal'}

class IdentityTests(unittest.TestCase):
    def test_missing_life_dates_do_not_prove_name_identity(self):
        self.assertFalse(u.compatible_name_identity({'record':{},'identifiers':[]},{},1846,1917))

    def test_activity_before_birth_rejects_namesake(self):
        existing={'record':{'birth_year':1846,'timeline_basis':'activity','timeline_start_year':1623,'timeline_end_year':1623},'identifiers':[]}
        self.assertFalse(u.compatible_name_identity(existing,{},1846,1917))

    def test_conflicting_native_identity_overrides_shared_dates(self):
        existing={'record':{'birth_year':1685},'identifiers':[{'scheme':'nga-constituent','external_id':'33636'}]}
        self.assertFalse(u.compatible_name_identity(existing,{'claims':{'P2252':[claim('6011')]}},1685,1748))

    def test_compatible_positive_life_date_match(self):
        self.assertTrue(u.compatible_name_identity({'record':{'birth_year':1754,'active_start_year':1786},'identifiers':[]},{},1754,1825))

    def test_activity_bounds_remain_activity_without_invented_life_dates(self):
        def date(year):return claim({'time':f'+{year}-00-00T00:00:00Z','precision':9,'before':0,'after':0,'calendarmodel':'http://www.wikidata.org/entity/Q1985727'})
        actual=u.source_activity({'claims':{'P2031':[date(1764)],'P2032':[date(1777)]}})
        self.assertEqual((actual['timeline_basis'],actual['active_start_year'],actual['active_end_year']),('activity',1764,1777))
        self.assertNotIn('birth_year',actual)

if __name__=='__main__':unittest.main()
