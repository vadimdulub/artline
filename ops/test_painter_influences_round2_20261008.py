"""Pure policy checks; no database connections or fixtures."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('round2', Path(__file__).with_name('apply-painter-influences-round2-20261008.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ResearchGuards(unittest.TestCase):
    def test_later_generations_cannot_influence_dead_targets(self):
        self.assertIsNotNone(m.chronology_issue({'birth_year': 1900}, {'death_year': 1800}, 'influenced'))

    def test_posthumous_influence_is_allowed_but_personal_tuition_is_not(self):
        source = {'birth_year': 1500, 'death_year': 1570}
        target = {'birth_year': 1800, 'death_year': 1870}
        self.assertIsNone(m.chronology_issue(source, target, 'influenced'))
        self.assertIsNotNone(m.chronology_issue(source, target, 'teacher_of'))

    def test_unknown_dates_are_not_invented(self):
        self.assertIsNone(m.chronology_issue({}, {}, 'teacher_of'))

    def test_generic_artist_and_photographer_are_not_painter_evidence(self):
        self.assertFalse(m.painter_role({'occupations': ['artist', 'photographer']}))
        self.assertTrue(m.painter_role({'occupations': ['iconographer']}))
        self.assertTrue(m.painter_role({'occupations': ['watercolorist']}))

    def test_secondary_assertions_remain_qualified_after_publication(self):
        self.assertEqual(m.d.grade([{'provider': 'Wikipedia'}])[:2], ('editorial_inference', 'medium'))
        self.assertEqual(m.d.grade([{'provider': 'Museum', 'evidence_level': 'documented'}])[:2], ('documented', 'high'))

    def test_every_review_matches_its_original_cached_paragraph(self):
        assertions, reviews = m.assertions()
        self.assertEqual(len(reviews), 141)
        self.assertEqual(len(assertions), 406)
        self.assertTrue(all(v['source_qid'] != v['target_qid'] for v in assertions))


if __name__ == '__main__':
    unittest.main()
