"""Offline policy checks using preserved museum text; no database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-dulwich-identity-20261007.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i);w=i.w

class DulwichPolicies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review=w.review();cls.facts={r['facts']['source_id']:r['facts'] for r in cls.review['rows']}
    def test_every_selected_object_has_complete_extract_and_index_chain(self):
        self.assertEqual(len(self.facts),336)
        self.assertEqual(len(self.review['errors']),1)
        self.assertIn('batch-035',self.review['errors'][0]['source_reference']['path'])
        for r in self.review['rows']:
            if w.m.norm(r['facts']['title'])!=w.m.norm(r['index']['title']):self.assertIn('index/object title differs',r['facts']['source_issues'])
    def test_source_kind_does_not_claim_raw_http(self):
        for f in self.facts.values():
            self.assertIn('not original HTTP bytes',f['capture_kind'])
            self.assertIn('Source:',f['source_metadata'])
    def test_incomplete_index_is_rejected(self):
        p=next(p for p in w.pages(w.m.load(w.RUN/'web-index-extra-002.json.gz')['result']) if '?page=6' in p['url'])
        self.assertFalse(p['complete'])
        with self.assertRaises(AssertionError):w.index_rows(p)
    def test_failed_sibling_does_not_contaminate_successful_extract(self):
        pages=w.pages(w.m.load(w.RUN/'web-objects-001/batch-035.json.gz')['result'])
        self.assertEqual(len(pages),1);self.assertTrue(pages[0]['complete'])
        self.assertIn('hagar-in-the-desert',self.facts)
    def test_truncated_object_cannot_supply_facts(self):
        p=w.pages(w.m.load(w.RUN/'web-objects-001/batch-001.json.gz')['result'])[0];p['complete']=False
        with self.assertRaises(AssertionError):w.object_facts(p)
    def test_multi_by_attribution_preserves_title_and_qualifications(self):
        f=self.facts['head-of-a-woman']
        self.assertEqual(f['title'],'Head of a Woman');self.assertEqual(f['inventory'],'DPG380')
        self.assertEqual(f['creator_label'],'British (?) or Flemish School, after a print by Aegidius Sadeler II, after a painting by Parmigianino or Girolamo Bedoli')
    def test_by_inside_title_is_preserved(self):
        f=self.facts['nymphs-by-a-fountain'];self.assertEqual(f['title'],'Nymphs by a Fountain');self.assertEqual(f['creator_label'],'Sir Peter Lely')
    def test_jacob_sitter_and_pendant_are_not_invented_metadata(self):
        f=self.facts['jacob-de-witt'];self.assertIsNone(f['creator_label']);self.assertIsNone(f['inventory']);self.assertIsNone(f['date_display'])
        self.assertIn('DPG571',' '.join(f['narrative']));self.assertIsNotNone(w.creation(f['date_display'])['date_issue'])
    def test_unknown_index_creator_is_preserved(self):
        p=w.pages(w.m.load(w.RUN/'web-index-page-6-retry-001.json.gz')['result'])[0]
        f=next(r for r in w.index_rows(p) if r['title']=='Jacob de Witt');self.assertIsNone(f['creator_label'])
    def test_attribution_conflict_remains_visible(self):
        f=self.facts['james-vi-and-i'];self.assertEqual(f['creator_label'],'After John de Critz the Elder');self.assertEqual(f['detail_creator_label'],'Attributed to John de Critz the Elder');self.assertTrue(f['source_issues'])
    def test_index_sitter_title_changes_are_preserved(self):
        rows=[r for r in self.review['rows'] if 'index/object title differs' in r['facts']['source_issues']]
        self.assertEqual({r['facts']['inventory'] for r in rows},{'DPG573','DPG634','DPG570'})
        self.assertTrue(all(r['facts']['title'].startswith('called ') for r in rows))
    def test_creation_not_acquisition(self):
        f=self.facts['girl-at-a-window'];self.assertEqual(f['date_display'],'1645');self.assertEqual(f['acquisition'],'Bourgeois Bequest, 1811')
    def test_short_numeric_end_preserves_source_range(self):
        self.assertEqual(w.creation('c.1779-85'),dict(first=1779,last=1785,date_precision='circa_range',date_issue=None))
    def test_literal_circa_has_no_fabricated_window(self):
        self.assertEqual(w.creation('c.1500'),dict(first=1500,last=1500,date_precision='circa',date_issue=None))
    def test_before_retains_unknown_lower_and_exclusive_endpoint(self):
        self.assertEqual(w.creation('Before 1686'),dict(first=None,last=1686,date_precision='before',date_issue=None))
    def test_cutoff_cases(self):
        self.assertIsNone(w.creation('1970')['date_issue']);self.assertIsNone(w.creation('Before 1971')['date_issue'])
        for date in ['1971','c.1970','1969-1971','Before 1972','1970s','20th Century']:self.assertIsNotNone(w.creation(date)['date_issue'],date)
    def test_qualified_period_does_not_invent_subdivision(self):
        self.assertEqual(w.creation('Mid–17th Century'),dict(first=1600,last=1699,date_precision='century',date_issue=None))
        self.assertEqual(w.creation('Early 1650s'),dict(first=1650,last=1659,date_precision='decade',date_issue=None))
    def test_uncertain_and_multiple_phase_dates_stay_held(self):
        for date in ['c.1772, retouched 1785','Possibly 17th Century','1645/7 or 1648','c.1645/8','After 1670','17th Century?','c.1799-02']:
            self.assertIsNotNone(w.creation(date)['date_issue'],date)
    def test_contemporary_and_missing_date_sculptures_stay_held(self):
        for sid in ['bronze-oak-grove','walking-the-dog-i-ii-iii']:
            f=self.facts[sid];self.assertIsNotNone(w.creation(f['date_display'])['date_issue'])
    def test_short_surname_and_mononym_are_searched(self):
        self.assertIn('dou',i.search_terms(self.facts['a-woman-playing-a-clavichord']))
        self.assertTrue({'rembrandt','rijn'}<=set(i.search_terms(self.facts['girl-at-a-window'])))
    def test_multiple_creators_and_geographic_suffix_are_searched(self):
        f=next(f for f in self.facts.values() if f['inventory']=='DPG322');self.assertTrue({'seghers','quellinus'}<=set(i.search_terms(f)))
        f=next(f for f in self.facts.values() if f['inventory']=='DPG634');self.assertIn('smart',i.search_terms(f))
    def test_school_is_not_an_invented_person(self):
        self.assertEqual(i.search_terms(self.facts['the-judde-memorial']),[])
    def test_request_must_match_captured_source_call(self):
        x=w.m.load(w.RUN/'web-objects-001/batch-001.json.gz');p=w.pages(x['result'])[0]
        x=copy.deepcopy(x);x['requests'][0]['link_id']=99999
        with self.assertRaises(AssertionError):w.checked_index(p,x)

if __name__=='__main__':unittest.main()
