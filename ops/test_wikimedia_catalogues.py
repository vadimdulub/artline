"""Safety counterexamples for real-catalogue import planning. No database use."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('apply_wiki',Path(__file__).with_name('apply-wikimedia-catalogues.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def time_snak(year,precision=9):
    return {'snaktype':'value','datavalue':{'value':{'time':f'+{year:04d}-00-00T00:00:00Z','precision':precision,'before':0,'after':0}}}

def entity(year,precision=9,qualifiers=None):
    return {'claims':{'P571':[{'rank':'normal','mainsnak':time_snak(year,precision),'qualifiers':qualifiers or {}}]}}

class GuardTests(unittest.TestCase):
    def test_century_is_not_promoted_to_exact_year(self):
        self.assertEqual(m.r.date(entity(1600,7))['precision'],'unknown')
    def test_explicit_range_survives_coarse_main_date(self):
        d=m.r.date(entity(1600,7,{'P1319':[time_snak(1550)],'P1326':[time_snak(1608)]}))
        self.assertEqual((d['first'],d['last'],d['precision']),(1550,1608,'range'))
    def test_cross_cutoff_range_not_image_eligible(self):
        d=m.r.date(entity(1970,9,{'P1319':[time_snak(1968)],'P1326':[time_snak(1972)]}))
        self.assertFalse(d['eligible'])
    def test_ambiguous_alternative_dates_not_invented_range(self):
        e=entity(1850);e['claims']['P571']+=entity(1870)['claims']['P571']
        self.assertEqual(m.r.date(e)['precision'],'unknown')
    def test_unsupported_qualifier_requires_review(self):
        self.assertEqual(m.r.date(entity(1880,9,{'P1480':[{'datavalue':{'value':{'id':'Q_not_circa'}}}]}))['precision'],'unknown')
    def test_transliterated_accession_collision_is_detectable(self):
        self.assertEqual(m.accession_key('ΒΧΜ 01544'),m.accession_key('BXM 01544'))
        self.assertNotEqual(m.accession_key('ΒΧΜ 01544'),m.accession_key('ΒΧΜ 01545'))
    def test_accession_disagreement_is_not_new_duplicate(self):
        record={'creator_qid':'Q123','creator_entity':{'labels':{'en':{'value':'Painter One'}}},'titles':['Tribute to the Eucharist'],'entity':{'claims':{'P217':[{'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':'BXM 01544'}}}]}}}
        row={'id':'old','title':'The Hospitality of Abraham','alternate_title':None,'accession_number':'ΒΧΜ 01544','creator_qids':[],'creator_names':[]}
        existing,reason=m.choose_existing(record,[row])
        self.assertIsNone(existing);self.assertEqual(reason,'accession_has_conflicting_title_and_creator')

if __name__=='__main__':unittest.main()
