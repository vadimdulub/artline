"""Offline source-policy regressions; never connect to a catalogue or use fixtures."""
import importlib.util
import hashlib
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('campaign',Path(__file__).with_name('museum-expansion-20261006.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class SourcePolicy(unittest.TestCase):
    def record(self,**changes):
        row=dict(Titre='Study',Numero_inventaire='INV 1',Reference='REF1',Millesime_de_creation='1860',
          Periode_de_creation='19e siècle',Auteur='Named painter',Domaine='peinture',Denomination='tableau',
          Materiaux_techniques='huile sur toile',Ville='Town',Nom_officiel_musee='Museum',
          Localisation='Town ; Museum',Statut_juridique='propriété de la commune',Lieu_de_depot=None)
        row.update(changes);return row

    def test_source_year_and_nullable_fields(self):
        facts,why=m.joconde_facts(self.record());self.assertIsNone(why);self.assertEqual(facts['year'],1860)

    def test_unknown_date_is_not_manufactured(self):
        for date in [None,'','vers 1860','1860;1870','1960-1980']:
            with self.subTest(date=date):self.assertIsNone(m.joconde_facts(self.record(Millesime_de_creation=date))[0])

    def test_cutoff(self):
        self.assertIsNotNone(m.joconde_facts(self.record(Millesime_de_creation='1970',Periode_de_creation='20e siècle'))[0])
        self.assertIsNone(m.joconde_facts(self.record(Millesime_de_creation='1971',Periode_de_creation='20e siècle'))[0])

    def test_conflicting_creation_fields(self):
        self.assertIsNone(m.joconde_facts(self.record(Periode_de_creation='18e siècle'))[0])
        self.assertIsNone(m.joconde_facts(self.record(Auteur='Painter (1700-1790)'))[0])

    def test_deposit_missing_and_custody_conflicts(self):
        for changes in [dict(Lieu_de_depot='Town;Museum'),dict(MANQUANT='oui'),dict(MANQUANT_COM='lost'),
                        dict(Localisation='Other Town ; Museum'),dict(Statut_juridique="propriété de l'Etat;dépôt")]:
            with self.subTest(changes=changes):self.assertIsNone(m.joconde_facts(self.record(**changes))[0])

    def test_multipart_and_mixed_media(self):
        for changes in [dict(Denomination='tableau;ensemble'),dict(Materiaux_techniques='collage et assemblage'),dict(Denomination='sculpture')]:
            with self.subTest(changes=changes):self.assertIsNone(m.joconde_facts(self.record(**changes))[0])

    def test_creator_qualifier_stays_literal(self):
        raw='Painter (atelier de)';f,_=m.joconde_facts(self.record(Auteur=raw));self.assertEqual(f['creator_label'],raw)
        f,_=m.joconde_facts(self.record(Auteur=None));self.assertIsNone(f['creator_label'])

    def test_icon_conservative_date_ranges(self):
        self.assertEqual(m.icon_date('19th century'),(1801,1900,'century'))
        self.assertEqual(m.icon_date('first half 20th century'),(1901,1950,'range'))
        self.assertEqual(m.icon_date('1860–1870'),(1860,1870,'range'))
        self.assertEqual(m.icon_date('c. 1860'),(1860,1860,'circa'))
        for raw in ['20th century','late 20th century','1950–1980','restored 1800','17th and 19th century','1900 or 1800','']:
            with self.subTest(raw=raw):self.assertEqual(m.icon_date(raw),(None,None,'unknown'))

    def test_french_source_periods(self):
        self.assertEqual(m.french_period('19e siècle'),(1801,1900,'century'))
        self.assertEqual(m.french_period('1ère moitié 20e siècle'),(1901,1950,'range'))
        self.assertEqual(m.french_period('2e quart 19e siècle'),(1826,1850,'range'))
        for raw in ['19e siècle (?)','20e siècle','3e quart 20e siècle','19e siècle;20e siècle','vers 19e siècle','']:
            with self.subTest(raw=raw):self.assertEqual(m.french_period(raw),(None,None,'unknown'))

    def test_period_does_not_override_explicit_date(self):
        row=self.record(Periode_de_creation='19e siècle')
        self.assertIsNone(m.joconde_period_facts(row)[0])
        row['Millesime_de_creation']=None
        facts,reason=m.joconde_period_facts(row)
        self.assertIsNone(reason);self.assertEqual((facts['first'],facts['last']),(1801,1900))

    def athens_body(self,oid):
        url='https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id='+oid
        return (m.RUN/'athens/captures'/(hashlib.sha256(url.encode()).hexdigest()+'.body')).read_bytes()

    def test_athens_real_source_keeps_unknown_creator_and_material(self):
        self.assertIsNone(m.athens_facts('81',self.athens_body('81'))['creator_label'])
        self.assertIsNone(m.athens_facts('26',self.athens_body('26'))['medium'])

    def test_athens_creation_anchor_cannot_be_replaced_with_other_date(self):
        body=self.athens_body('81').replace(b'Copper engraving, 1819.',b'Acquired in 1819.')
        with self.assertRaises(AssertionError):m.athens_facts('81',body)

    def test_athens_inventory_letter_and_zero_variants(self):
        self.assertEqual(m.athens_inventory('ΒΧΜ 01590'),m.athens_inventory('BXM 1590'))
        self.assertNotEqual(m.athens_inventory('ΒΧΜ 01590'),m.athens_inventory('ΒΧΜ 01591'))

    def test_explicit_numeric_range_preserves_source_bounds(self):
        row=self.record(Millesime_de_creation='1860-1867')
        f,reason=m.joconde_range_facts(row)
        self.assertIsNone(reason)
        self.assertEqual((f['first'],f['last'],f['date_precision'],f['date_display']),(1860,1867,'range','1860-1867'))

    def test_range_conflicts_and_multiple_dates_are_held(self):
        for raw in ['1970-1973','1867-1860','1860;1867','1860-1867 vers','1860-1867?']:
            with self.subTest(raw=raw):self.assertIsNone(m.joconde_range_facts(self.record(Millesime_de_creation=raw))[0])
        self.assertIsNone(m.joconde_range_facts(self.record(Millesime_de_creation='1860-1867',Periode_de_creation='18e siècle'))[0])

    def test_circa_uses_publisher_period_instead_of_invented_tolerance(self):
        f,reason=m.joconde_circa_facts(self.record(Millesime_de_creation='1910 vers',Periode_de_creation='1er quart 20e siècle'))
        self.assertIsNone(reason)
        self.assertEqual((f['first'],f['last'],f['date_precision'],f['date_display']),(1901,1925,'circa_range','1910 vers'))

    def test_circa_missing_cross_cutoff_or_conflicting_period_is_held(self):
        for raw,period in [('1970 vers','20e siècle'),('1880 vers',''),('1880 vers','18e siècle'),('1880 vers?','19e siècle'),('vers 1880','19e siècle (?)')]:
            with self.subTest(raw=raw,period=period):self.assertIsNone(m.joconde_circa_facts(self.record(Millesime_de_creation=raw,Periode_de_creation=period))[0])
        self.assertIsNone(m.joconde_circa_facts(self.record(Millesime_de_creation='1910 vers',Periode_de_creation='1ère moitié 20e siècle',Auteur='Creator (1930-1970)'))[0])

    def test_new_date_routes_keep_custody_and_object_guards(self):
        for parser,date in [(m.joconde_range_facts,'1860-1867'),(m.joconde_circa_facts,'1860 vers'),(m.joconde_before_facts,'1860 avant')]:
            for change in [dict(Lieu_de_depot='Other Museum'),dict(MANQUANT='yes'),dict(Denomination='tableau;ensemble')]:
                with self.subTest(parser=parser.__name__,change=change):self.assertIsNone(parser(self.record(Millesime_de_creation=date,**change))[0])

    def test_french_before_retains_unknown_lower_and_exclusive_upper(self):
        for raw in ['1860 avant','avant 1860']:
            f,reason=m.joconde_before_facts(self.record(Millesime_de_creation=raw,Auteur='Painter (1810-1870)'))
            self.assertIsNone(reason)
            self.assertEqual((f['first'],f['last'],f['date_precision'],f['date_display']),(None,1860,'before',raw))

    def test_french_before_1971_entails_creation_cutoff(self):
        f,reason=m.joconde_before_facts(self.record(Millesime_de_creation='1971 avant',Periode_de_creation='20e siècle'))
        self.assertIsNone(reason);self.assertEqual(f['last'],1971)
        self.assertIsNone(m.joconde_before_facts(self.record(Millesime_de_creation='1972 avant'))[0])

    def test_french_before_qualified_multiple_and_contradictory_dates_held(self):
        for raw in ['1860 avant?','vers 1860 avant','1850;1860 avant','1860 après']:
            with self.subTest(raw=raw):self.assertIsNone(m.joconde_before_facts(self.record(Millesime_de_creation=raw))[0])
        for change in [dict(Periode_de_creation='4e quart 19e siècle'),dict(Periode_de_creation='20e siècle'),dict(Periode_de_creation='19e siècle;20e siècle'),dict(Auteur='Painter (1860-1900)')]:
            with self.subTest(change=change):self.assertIsNone(m.joconde_before_facts(self.record(Millesime_de_creation='1860 avant',**change))[0])

    def test_sculpture_requires_explicit_form_and_domain(self):
        row=self.record(Denomination='buste',Domaine='sculpture',Materiaux_techniques='bronze (fonte)')
        f,reason=m.joconde_sculpture_facts(row)
        self.assertIsNone(reason);self.assertEqual(f['work_type'],'sculpture');self.assertEqual(f['year'],1860)
        for change in [dict(Denomination='statue;ensemble'),dict(Domaine='archéologie'),dict(Denomination='tête'),dict(Denomination='tableau')]:
            with self.subTest(change=change):self.assertIsNone(m.joconde_sculpture_facts(dict(row,**change))[0])

    def test_sculpture_version_and_component_date_ambiguity_held(self):
        row=self.record(Denomination='statue',Domaine='sculpture',Materiaux_techniques='plâtre')
        for change in [dict(Titre='Fragment de statue'),dict(Historique='Moulage réalisé en 1980'),dict(Historique='Fonte posthume de 1980'),dict(Millesime_de_creation='1860;1980'),dict(Millesime_de_creation='1972')]:
            with self.subTest(change=change):self.assertIsNone(m.joconde_sculpture_facts(dict(row,**change))[0])

    def test_sculpture_anonymous_and_qualified_creator_labels_preserved(self):
        for creator in ['anonyme','Named creator (atelier de)',None]:
            row=self.record(Denomination='statuette',Domaine='sculpture',Materiaux_techniques='bois polychrome',Auteur=creator,Millesime_de_creation='',Periode_de_creation='1er quart 16e siècle')
            f,reason=m.joconde_sculpture_facts(row)
            self.assertIsNone(reason);self.assertEqual(f['creator_label'],creator);self.assertEqual((f['first'],f['last']),(1501,1525))

    def test_sculpture_routes_keep_date_and_custody_safeguards(self):
        row=self.record(Denomination='bas-relief',Domaine='sculpture',Materiaux_techniques='pierre')
        for raw in ['1860','1860-1867','1860 vers','1860 avant','']:
            with self.subTest(raw=raw):
                f,reason=m.joconde_sculpture_facts(dict(row,Millesime_de_creation=raw));self.assertIsNone(reason)
                self.assertEqual(f['work_type'],'sculpture')
                self.assertIsNone(m.joconde_sculpture_facts(dict(row,Millesime_de_creation=raw,Lieu_de_depot='Other Museum'))[0])

    def test_captured_sculpture_first_edition_is_not_the_cast_date(self):
        plan=m.load(m.RUN/'joconde-sculpture-current-plan.json.gz')
        row=next(r['raw_source_record'] for r in plan['records'] if r['source_record_id']=='00660000036')
        self.assertIn('première édition',row['Historique'])
        self.assertEqual(m.joconde_sculpture_facts(row)[1],'sculpture_component_or_version_requires_review')

    def test_captured_sculpture_description_cannot_hide_different_version(self):
        plan=m.load(m.RUN/'joconde-sculpture-current-plan.json.gz')
        row=next(r['raw_source_record'] for r in plan['records'] if r['source_record_id']=='02470001089')
        self.assertIn('Moulage',row['Description'])
        self.assertEqual(m.joconde_sculpture_facts(row)[1],'sculpture_component_or_version_requires_review')


if __name__=='__main__':unittest.main()
