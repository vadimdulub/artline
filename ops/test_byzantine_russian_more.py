import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('more',Path(__file__).with_name('byzantine-russian-more.py'))
more=importlib.util.module_from_spec(spec);spec.loader.exec_module(more)


class SourceIdentityTests(unittest.TestCase):
    def test_cover_dates_do_not_become_icon_dates(self):
        self.assertEqual(more.russian_date('1840-е годы. Оклад - 1845 год'),(None,None,'unknown'))
        self.assertEqual(more.russian_date('В окладе. 1704'),(1704,1704,'exact'))

    def test_unicode_centuries_and_locations(self):
        self.assertEqual(more.russian_date('Холуй. Первая половина ΧΙV века'),(1301,1350,'range'))

    def test_uncertain_and_restored_dates_remain_unknown(self):
        for literal in ('probably 1861','16th century with later renovation','18th century or possibly early 20th century'):
            self.assertEqual(more.english_date(literal),(None,None,'unknown'))

    def test_catalogue_field_values_stay_separate_from_labels(self):
        raw=b'<div><div><p class="stk-block-text__text"><strong>Credit Line</strong></p></div><div><p class="stk-block-text__text">On loan from a collector</p></div><div><p class="stk-block-text__text"><strong>Medium</strong></p></div><div><p class="stk-block-text__text">Egg tempera on wood</p></div></div>'
        fields=more.icon_museum_fields(raw)
        self.assertEqual(fields,{'Credit Line':'On loan from a collector','Medium':'Egg tempera on wood'})


if __name__=='__main__':unittest.main()
