"""Offline source-integrity, multilingual and duplicate-scope regressions."""
import copy
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-armenia-apply-20261007.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);s=a.s;m=a.m

class ArmeniaCaptions(unittest.TestCase):
    def capture(self,n):return m.load(s.RUN/'sarian-object-captures-001'/f'{n:03}.json')

    def test_all_captures_reproduce_fields(self):
        for n in range(1,42):
            with self.subTest(n=n):
                d=self.capture(n)
                self.assertEqual(s.captions(s.body(d['capture'])),([s.clean(x) for x in d['title_fields']],[s.clean(x) for x in d['detail_fields']]))
                self.assertLessEqual(s.fields(d,n)['last'],1970)

    def test_disputed_support_not_guessed(self):
        for n in [12,14,16]:
            f=s.fields(self.capture(n),n);self.assertIsNone(f['medium']);self.assertEqual(f['work_type'],'painting')

    def test_ink_watercolor_conflict_keeps_unknown_type(self):
        f=s.fields(self.capture(34),34)
        self.assertIsNone(f['medium']);self.assertEqual(f['work_type'],'unknown');self.assertEqual(f['first'],1937)

    def test_actual_illustration_ink_is_drawing(self):
        self.assertEqual(s.fields(self.capture(30),30)['work_type'],'drawing')

    def test_actual_stage_design_is_not_print_boilerplate(self):
        d=self.capture(38);self.assertIn(b'Serigraph',s.body(d['capture']))
        f=s.fields(d,38);self.assertEqual(f['work_type'],'painting');self.assertEqual(f['medium'],'Gouache on paper')

    def test_date_disagreement_rejected(self):
        d=self.capture(1);d['title_fields'][1]=d['title_fields'][1].replace('1905','1906')
        with self.assertRaises(AssertionError):s.fields(d,1)

    def test_after_cutoff_rejected(self):
        d=self.capture(1);d['title_fields']=[x.replace('1905','1971') for x in d['title_fields']]
        with self.assertRaises(AssertionError):s.fields(d,1)

    def test_mismatched_dimensions_rejected(self):
        d=self.capture(1);d['detail_fields'][2]=d['detail_fields'][2].replace('106 x 88','107 x 88')
        with self.assertRaises(AssertionError):s.fields(d,1)

    def test_wrong_holding_rejected(self):
        d=self.capture(1);d['detail_fields'][2]=d['detail_fields'][2].replace('National Gallery of Armenia','Sarian House Museum')
        with self.assertRaises(AssertionError):s.fields(d,1)

    def test_partial_caption_set_rejected(self):
        with self.assertRaises(AssertionError):s.captions(b'<span class="category-options">MARTIROS SARIAN 1905</span>')

    def test_capture_hash_required(self):
        d=self.capture(1);d['capture']['receipt']['sha256']='0'*64
        with self.assertRaises(AssertionError):s.body(d['capture'])

    def test_plan_exact_selection(self):
        plan,digest=a.validate_plan();self.assertEqual(len(plan['records']),36)
        self.assertEqual(len(plan['held']),5)
        self.assertEqual({r['raw_source_record']['queue_number'] for r in plan['records']},set(range(1,42))-{2,7,8,13,14})

    def test_duplicate_object_page_rejected(self):
        plan=m.load(a.PLAN);plan['records'][-1]=copy.deepcopy(plan['records'][0])
        with self.assertRaises(AssertionError):a.validate(plan)

    def test_invented_medium_rejected(self):
        plan=m.load(a.PLAN);r=next(r for r in plan['records'] if r['raw_source_record']['queue_number']==12);r['facts']['medium']='Tempera on canvas'
        with self.assertRaises(AssertionError):a.validate(plan)

    def test_changed_evidence_reference_rejected(self):
        plan=m.load(a.PLAN);plan['evidence'][0]['sha256']='0'*64
        with self.assertRaises(AssertionError):a.validate(plan)

if __name__=='__main__':unittest.main()
