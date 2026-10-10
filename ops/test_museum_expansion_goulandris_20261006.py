"""Offline checks against retained real museum pages; no database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('g',Path(__file__).with_name('museum-expansion-goulandris-20261006.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


class GoulandrisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=g.m.load(g.m.RUN/'goulandris-001-current-plan.json.gz')
        cls.records={r['source_record_id']:r for r in cls.plan['records']}

    def test_approved_real_capture_roundtrip(self):
        self.assertEqual(len(self.records),95)
        for r in self.records.values():
            raw=g.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
            self.assertEqual(g.validate_record(r,raw),r['facts'])

    def test_physical_printing_dates_and_design_dates_remain_distinct(self):
        leaves=[r for oid,r in self.records.items() if oid.startswith('henri-de-toulouse-lautrec-') and oid.removeprefix('henri-de-toulouse-lautrec-') in g.LAUTREC_1948]
        self.assertEqual(len(leaves),12)
        for r in leaves:
            self.assertEqual((r['facts']['first'],r['facts']['last']),(1948,1948))
            self.assertNotEqual(r['raw_source_record']['native_fields']['date'],'1948')
            self.assertIn('448/750',r['facts']['medium'])
        self.assertNotIn('henri-de-toulouse-lautrec-lithographs',self.records)

    def test_multiple_medium_nodes_retain_edition_note(self):
        r=self.records['braque-georges-thistle'];p=r['raw_source_record']['native_fields']
        self.assertTrue(p['medium'].startswith('Coloured lithograph'))
        self.assertEqual(len(p['medium_notes']),1)
        self.assertEqual(r['facts']['date_display'],'1955')
        changed=copy.deepcopy(p);changed['medium_notes']=[]
        self.assertEqual(g.facts(changed,r['raw_source_record']['index_record'],r['raw_source_record']['types'])[1],'reviewed_print_edition_statement_missing')

    def test_later_edition_cannot_borrow_early_design_date(self):
        r=self.records['braque-georges-thistle'];p=copy.deepcopy(r['raw_source_record']['native_fields'])
        p['medium_notes']=['Reprinted in 1980']
        self.assertEqual(g.facts(p,r['raw_source_record']['index_record'],r['raw_source_record']['types'])[1],'later_printing_or_edition_requires_review')

    def test_known_dated_mixed_material_works_keep_unknown_type(self):
        unknown=[r for r in self.records.values() if r['facts']['work_type']=='unknown']
        self.assertEqual({r['source_record_id'] for r in unknown},{'samaras-lucas-untitled','chagall-marc-untitled-for-elise-and-basil'})
        self.assertIn('feathers',self.records['samaras-lucas-untitled']['facts']['medium'])

    def test_source_conflicts_and_possible_copies_are_held(self):
        held={h.get('record',{}).get('source_record_id',h.get('index',{}).get('source_id')) for h in self.plan['held']}
        for oid in ['christo-packed-coast-project-for-australia-near-sydney','giorgio-de-chirico-portrait-of-a-man','picasso-pablo-young-man-with-bouquet','hadjikyriakos-ghika-nikos-paris-roofs','matisse-henri-the-cow-boy-jazz']:
            self.assertIn(oid,held);self.assertNotIn(oid,self.records)

    def test_dates_do_not_invent_cutoff_eligibility(self):
        self.assertEqual(g.creation_date('Early 1580s'),(1580,1589,'range'))
        self.assertEqual(g.creation_date('1901 or 1902'),(1901,1902,'range'))
        self.assertEqual(g.creation_date('28 November 1970'),(1970,1970,'exact'))
        for value in ['','1971','1969-1971','Circa 1970','1932 for drawings, 1953 for album','1970s']:
            self.assertIsNone(g.creation_date(value),value)

    def test_codes_and_copy_numbers_are_not_accessions(self):
        self.assertTrue(all(r['facts']['accession'] is None for r in self.records.values()))
        self.assertIn('31/100',self.records['braque-georges-flight-1']['facts']['medium'])

    def test_translated_titles_are_identity_keys(self):
        r=self.records['braque-georges-the-sign']
        self.assertIn(g.m.norm('Le Signe'),g.title_keys(r))
        self.assertIn(g.m.norm('The Sign'),g.title_keys(r))

    def test_changed_exact_title_identity_stops_apply(self):
        r=self.records['derain-andre-still-life'];review=r['raw_source_record']['title_identity_review']
        rows=g.m.load(g.m.ROOT/review['evidence_path'])['rows']
        with patch.object(g,'title_collision_rows',return_value=rows):g.check_title_identities(None,[r])
        changed=copy.deepcopy(rows)
        row=next(v for v in changed if v['id'] in review['existing_ids']);row['medium_text']='Changed physical support'
        with patch.object(g,'title_collision_rows',return_value=changed):
            with self.assertRaisesRegex(AssertionError,'New or changed'):g.check_title_identities(None,[r])

    def test_editorial_decision_cannot_be_changed(self):
        r=copy.deepcopy(self.records['samaras-lucas-untitled'])
        r['raw_source_record']['editorial_review']['decision']='hold'
        raw=g.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
        with self.assertRaises(AssertionError):g.validate_record(r,raw)


if __name__=='__main__':unittest.main()
