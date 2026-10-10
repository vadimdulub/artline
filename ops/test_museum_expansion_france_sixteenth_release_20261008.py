"""Offline selection and identity safeguards; no catalogue fixtures or DB writes."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-sixteenth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
t=r.module('t','museum-expansion-france-sixteenth-comparison-triage-20261008.py')
class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=r.m.load(r.CANDIDATES)['rows'];cls.by={v['number']:v for v in cls.rows};cls.triage=r.m.load(r.RUN/'comparison-triage-001.json.gz')
    def test_unresolved_not_approved(self):
        self.assertEqual(len(r.NOTES),121);self.assertEqual(sum(n>=511 for n in r.NOTES),119);self.assertFalse(set(r.NOTES)&set(r.HOLDS));self.assertFalse(set(r.NOTES)&set(r.n.DEFERRED_ECOUEN))
    def test_delivered_wave70_not_selected_again(self):
        old=r.m.load(r.i.prior.REVIEW)['decisions'];ids={v['source_id'] for v in old if v['state']=='approved_review_only_addition'}
        self.assertFalse(ids&{v['source_id'] for v in self.rows});self.assertEqual(len(self.rows),359)
    def test_comparison_basis_required(self):
        saved=r.n.FOLLOWUP.pop(542)
        try:
            with self.assertRaisesRegex(AssertionError,'missing individual comparison basis'):r.coverage(self.rows,self.triage)
        finally:r.n.FOLLOWUP[542]=saved
    def test_historical_inventory_conflict_stays_open(self):
        for n in [584,586]:self.assertIn(n,r.HOLDS);self.assertNotIn(n,r.NOTES);self.assertIn('22278',r.HOLDS[n])
    def test_creator_roles_preserved_from_native(self):
        native=next(v for v in r.m.load(r.i.OLD/'paris-object-context-checked-001.json.gz')['rows'] if v['number']==488)
        v=copy.deepcopy(self.by[488]['facts']);before=copy.deepcopy(v['source_fields']);r.derive_creator(v,488,native)
        self.assertEqual(v['source_fields'],before);self.assertIn('copie d’après',v['creator_label']);self.assertIn('anciennement attribué',v['creator_label']);self.assertIn('Ecole française',v['creator_label'])
    def test_dates_not_sitter_or_acquisition_dates(self):
        for n in r.NOTES:
            f=self.by[n]['facts'];self.assertIsNone(f['date_issue']);self.assertLessEqual(f['first'],f['last']);self.assertLessEqual(f['last'],1970)
        self.assertEqual(self.by[594]['facts']['date_display'],'16e siècle');self.assertEqual(self.by[488]['facts']['date_display'],'18e siècle')
    def test_inventory_signal_prevents_triage_exclusion(self):
        a=self.by[542]['facts']['source_fields'];b=self.by[488]['facts']['source_fields']
        self.assertIsNotNone(t.reason(a,b));self.assertIsNone(t.reason(a,b,identity_signal=True))
    def test_mixed_materials_not_forced_into_family(self):
        self.assertIsNone(t.family({'Domaine':'sculpture','Materiaux_techniques':'cire;bois'}));self.assertIsNone(t.family({'Domaine':'dessin','Materiaux_techniques':'papier;collage;encre'}))
    def test_one_object_per_inventory_and_group(self):
        selected=[self.by[n] for n in r.NOTES];self.assertEqual(len(selected),len({(v['institution_id'],v['facts']['inventory']) for v in selected}));r.batch_review(self.rows)
        for n in [519,580,581,610,611,632]:self.assertNotIn(n,r.NOTES)
if __name__=='__main__':unittest.main()
