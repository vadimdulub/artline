"""Offline release safeguards; no database connections or catalogue fixtures."""
import copy, importlib.util, unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('museum-expansion-france-fifteenth-review-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=r.m.load(r.CANDIDATES)['rows'];cls.old=r.m.load(r.RUN/'native-identity-001.json.gz')['comparisons'];cls.new=r.m.load(r.IDENTITY)['comparisons']
    def test_unresolved_never_released(self):
        self.assertFalse(set(r.NOTES)&set(r.PENDING));self.assertFalse(set(r.NOTES)&set(r.HOLDS));self.assertEqual(len(r.NOTES),291);self.assertLessEqual(max(r.NOTES),360)
    def test_suppressed_generic_comparison_guard(self):
        saved=r.GENERIC.pop(212)
        try:
            with self.assertRaisesRegex(AssertionError,'unreviewed initial generic'):r.coverage(self.rows,self.old,self.new)
        finally:r.GENERIC[212]=saved
    def test_supplemental_comparison_guard(self):
        n=next(n for n in r.NOTES if n in r.notes['SUPPLEMENTAL_REVIEW']);saved=r.notes['SUPPLEMENTAL_REVIEW'].pop(n)
        try:
            with self.assertRaisesRegex(AssertionError,'unreviewed supplemental'):r.coverage(self.rows,self.old,self.new)
        finally:r.notes['SUPPLEMENTAL_REVIEW'][n]=saved
    def test_copy_maker_is_not_prototype(self):
        v=copy.deepcopy(self.rows[219]['facts']);original=copy.deepcopy(v['source_fields']);change=r.derive_creator(v,220)
        self.assertEqual(v['source_fields'],original);self.assertIn('Hans Sebald',v['creator_label']);self.assertIn('copie d’après BEHAM Barthel',v['creator_label']);self.assertEqual(change['original'],original['Auteur'])
    def test_attribution_retains_other_roles(self):
        for n in [276,277,278]:
            v=copy.deepcopy(self.rows[n-1]['facts']);old=copy.deepcopy(v['source_fields']);r.derive_creator(v,n)
            self.assertEqual(v['source_fields'],old);self.assertIn('attribué à',v['creator_label']);self.assertIn('Bruegel Pieter',v['creator_label']);self.assertEqual('Cock Hieronymus' in old['Auteur'],'Cock Hieronymus' in v['creator_label'])
    def test_same_sheet_and_ambiguous_impressions_held(self):
        for n in [6,21,87,90,117,118,128,131,139,156,199,288,355]:self.assertIn(n,r.HOLDS);self.assertNotIn(n,r.NOTES)
    def test_selected_dates_and_unknown_lower_bounds(self):
        before=[]
        for row in self.rows:
            if row['number'] not in r.NOTES:continue
            f=row['facts']
            if f['date_precision']=='before':self.assertIsNone(f['first']);self.assertLessEqual(f['last'],1971);before.append(row['number'])
            else:self.assertLessEqual(f['first'],f['last']);self.assertLessEqual(f['last'],1970)
        self.assertTrue(before)
    def test_shared_historic_inventory_has_physical_basis(self):
        review=r.batch_review(self.rows)
        shared=[g for g in review['groups'] if g['kind']=='inventory_groups' and len(g['selected'])>1]
        self.assertEqual([g['selected'] for g in shared],[[158,159]])
        self.assertNotEqual(self.rows[157]['facts']['inventory'],self.rows[158]['facts']['inventory']);self.assertIn('aquarelle',r.NOTES[159])
    def test_coverage_all_candidates_without_claiming_all_resolved(self):
        out=r.coverage(self.rows,self.old,self.new);self.assertEqual(len(out),650)
        self.assertTrue(out[457]['supplemental_review_needed']);self.assertFalse(out[457]['selected']);self.assertIsNone(out[457]['supplemental_basis'])
if __name__=='__main__':unittest.main()
