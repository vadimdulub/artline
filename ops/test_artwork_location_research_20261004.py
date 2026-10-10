"""Pure identity checks only. Never connects to a catalogue or creates fixtures."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('primary', Path(__file__).with_name('research-artwork-location-primary-20261004.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
spec2 = importlib.util.spec_from_file_location('secondary', Path(__file__).with_name('research-artwork-location-secondary-20261004.py'))
s = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(s)
spec3 = importlib.util.spec_from_file_location('leads', Path(__file__).with_name('apply-artwork-location-leads-20261005.py'))
l = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(l)
spec4 = importlib.util.spec_from_file_location('vam', Path(__file__).with_name('research-artwork-location-vam-20261005b.py'))
v = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(v)
spec5 = importlib.util.spec_from_file_location('arco_plan', Path(__file__).with_name('research-artwork-location-arco-plan-20261005b.py'))
ap = importlib.util.module_from_spec(spec5)
spec5.loader.exec_module(ap)
spec6 = importlib.util.spec_from_file_location('marseille', Path(__file__).with_name('research-artwork-location-marseille-20261005b.py'))
m = importlib.util.module_from_spec(spec6)
spec6.loader.exec_module(m)
spec7 = importlib.util.spec_from_file_location('rijks_refine', Path(__file__).with_name('refine-artwork-location-rijks-20261005b.py'))
rr = importlib.util.module_from_spec(spec7)
spec7.loader.exec_module(rr)
spec8 = importlib.util.spec_from_file_location('ycba', Path(__file__).with_name('research-artwork-location-ycba-20261005b.py'))
y = importlib.util.module_from_spec(spec8)
spec8.loader.exec_module(y)
spec9 = importlib.util.spec_from_file_location('storage', Path(__file__).with_name('refine-artwork-location-arco-storage-20261005c.py'))
st = importlib.util.module_from_spec(spec9)
spec9.loader.exec_module(st)
spec10 = importlib.util.spec_from_file_location('hunterian', Path(__file__).with_name('research-artwork-location-hunterian-20261005c.py'))
hu = importlib.util.module_from_spec(spec10)
spec10.loader.exec_module(hu)
spec11 = importlib.util.spec_from_file_location('allocation', Path(__file__).with_name('refine-artwork-location-joconde-allocation-20261005c.py'))
al = importlib.util.module_from_spec(spec11)
spec11.loader.exec_module(al)
spec12 = importlib.util.spec_from_file_location('louvre', Path(__file__).with_name('research-artwork-location-louvre-20261005c.py'))
lv = importlib.util.module_from_spec(spec12)
spec12.loader.exec_module(lv)
spec13 = importlib.util.spec_from_file_location('municipal', Path(__file__).with_name('research-artwork-location-bristol-glasgow-20261005c.py'))
mu = importlib.util.module_from_spec(spec13)
spec13.loader.exec_module(mu)
spec14 = importlib.util.spec_from_file_location('mds', Path(__file__).with_name('research-artwork-location-mds-20261005c.py'))
md = importlib.util.module_from_spec(spec14)
spec14.loader.exec_module(md)
spec15 = importlib.util.spec_from_file_location('rmg', Path(__file__).with_name('research-artwork-location-rmg-auckland-20261005c.py'))
rg = importlib.util.module_from_spec(spec15)
spec15.loader.exec_module(rg)
spec16 = importlib.util.spec_from_file_location('undated', Path(__file__).with_name('refine-artwork-location-undated-identities-20261005c.py'))
ud = importlib.util.module_from_spec(spec16)
spec16.loader.exec_module(ud)


class UndatedMuseumIdentityTests(unittest.TestCase):
    def test_mds_empty_display_date_does_not_hide_other_date_fields(self):
        c = {'scheme': 'mds-object', 'object_evidence': {'museum_supplied_record': {'fields': {'Object number': ['123'], 'Date - earliest / single': ['2000']}}, 'date_reconciliation': {'primary_dates': []}}}
        self.assertEqual(ud.source(c), ('123', ['2000']))

    def setUp(self):
        self.row = {'artwork': {'status': 'review', 'date_display': 'Creation date under review', 'creation_year_start': None, 'creation_year_end': None, 'accession_number': 'B1970.3.1'}, 'identifiers': [{'scheme': 'wikidata', 'external_id': 'Q123'}]}
        self.claim = {'scheme': 'ycba-object', 'review_state': 'review', 'object_evidence': {'qualifications': ['source_date_wording_changed'], 'current_lido_record': {'inventory': 'B1970.3.1', 'dates': ['undated'], 'object_wikidata': ['https://www.wikidata.org/wiki/Q123']}}}

    def test_exact_undated_holding_keeps_date_and_artwork_review(self):
        before = copy.deepcopy(self.row)
        proof = ud.undated_identity(self.row, self.claim)
        self.assertTrue(proof['artwork_publication_remains_review'])
        self.assertTrue(proof['eligibility_not_determined'])
        self.assertEqual(before, self.row)

    def test_undated_does_not_override_a_conflicting_known_date(self):
        self.claim['object_evidence']['current_lido_record']['dates'] = ['1830']
        self.assertIsNone(ud.undated_identity(self.row, self.claim))

    def test_undated_requires_inventory_reverse_identity_and_unqualified_creator(self):
        for field, value in [('inventory', 'B1970.3.2'), ('object_wikidata', ['https://www.wikidata.org/wiki/Q456'])]:
            c = copy.deepcopy(self.claim)
            c['object_evidence']['current_lido_record'][field] = value
            self.assertIsNone(ud.undated_identity(self.row, c))
        self.claim['object_evidence']['qualifications'].append('creator_relationship_qualified')
        self.assertIsNone(ud.undated_identity(self.row, self.claim))


class MuseumSuppliedRecordTests(unittest.TestCase):
    def authority(self):
        def statement(value):
            return {'rank': 'normal', 'mainsnak': {'snaktype': 'value', 'datavalue': {'value': {'time': value}}}}
        return {'claims': {'P569': [statement('+1910-01-01T00:00:00Z')], 'P570': [statement('+2007-01-01T00:00:00Z')]}}

    def test_appended_lifespan_requires_matching_authority_years(self):
        self.assertIn('Gilbert, Stephen', md.creator_names(['Gilbert, Stephen 1910-2007'], self.authority()))
        self.assertNotIn('Gilbert, Stephen', md.creator_names(['Gilbert, Stephen 1911-2007'], self.authority()))
        self.assertNotIn('Gilbert, Stephen', md.creator_names(['Gilbert, Stephen 1910-2007'], {}))

    def test_json_encoded_titles_do_not_strip_uncertainty(self):
        self.assertEqual(md.literal_titles(['["Horses and Dog in a Landscape"]']), ['Horses and Dog in a Landscape'])
        self.assertEqual(md.literal_titles(['[Possibly a portrait]']), ['[Possibly a portrait]'])

    def test_appended_production_date_must_match_explicit_date_field(self):
        self.assertEqual(md.title_key('Alice (1919)', ['1919']), md.title_key('Alice', ['1919']))
        self.assertNotEqual(md.title_key('Alice (1918)', ['1919']), md.title_key('Alice', ['1919']))
        self.assertNotEqual(md.title_key('Alice (possibly 1919)', ['1919']), md.title_key('Alice', ['1919']))

    def test_creator_honors_do_not_remove_attribution_qualifications(self):
        self.assertEqual(md.creator_label('Cooke, Edward William (RA, FRS, FSA)'), 'Cooke, Edward William')
        self.assertIn('attributed', md.creator_label('Cooke, Edward William (attributed to)'))
        self.assertIn('Gilbert, Stephen', md.creator_names(['Gilbert, Stephen (Sir) 1910-2007'], self.authority()))

    def test_empty_production_fields_do_not_hide_explicit_creation_fields(self):
        self.assertEqual(md.production_fields({'Object production date': [''], 'Associated date': ['1932'], 'Date - association': ['Creation']})[1], ['1932'])

    def test_creation_association_does_not_use_a_sitter_or_acquisition_date(self):
        f = {'Associated person': ['Named artist'], "Person's association": ['Creation'], 'Associated date': ['1932'], 'Date - association': ['Creation']}
        self.assertEqual(md.production_fields(f)[:2], (['Named artist'], ['1932']))
        f["Person's association"] = ['sitter']
        f['Date - association'] = ['acquisition']
        self.assertEqual(md.production_fields(f)[:2], ([], []))

    def test_artist_lifespan_conflict_is_not_hidden_by_name_normalization(self):
        self.assertTrue(md.lifespan_conflict(['Gilbert, Stephen (1911-2007) (artist)'], self.authority()))
        self.assertFalse(md.lifespan_conflict(['Gilbert, Stephen 1910-2007 (artist)'], self.authority()))
        self.assertFalse(md.lifespan_conflict(['Gilbert, Stephen active 1930-1970 (artist)'], self.authority()))

    def test_rmg_inventory_is_from_object_details_not_navigation(self):
        raw = b'<h1>Selected painting</h1><table><tr><th>ID:</th><td>WRONG</td></tr></table><div class="collections-table"><table><tr><th>ID:</th><td>BHC4147</td></tr><tr><th>Creator:</th><td>Named artist</td></tr></table></div>'
        self.assertEqual(rg.parse('rmg', raw, 'https://example.org/1')['fields']['ID'], ['BHC4147'])

    def test_auckland_missing_accession_is_not_a_verified_object_page(self):
        with self.assertRaises(AssertionError):
            rg.parse('auckland', b'<h1>Search results</h1>', 'https://example.org')


class DateNotationTests(unittest.TestCase):
    def test_circa_notation_preserves_uncertainty(self):
        for source in ['ca. 1830', 'circa 1830', 'c.1830']:
            self.assertTrue(mu.dn.equivalent('c. 1830', source))
        self.assertFalse(mu.dn.equivalent('1830', 'circa 1830'))

    def test_explicit_ranges_keep_both_endpoints(self):
        self.assertTrue(mu.dn.equivalent('1811–1813', '1811 to 1813'))
        self.assertTrue(mu.dn.equivalent('1811–1813', 'between 1811 and 1813'))
        self.assertFalse(mu.dn.equivalent('1859–1879', 'between 1859 and 1861'))

    def test_unknown_qualified_and_post_cutoff_dates_do_not_resolve(self):
        for value in ['', 'undated', 'Creation date under review', 'after 1830', 'possibly 1830', '1830?', '1960–1980', '1980']:
            self.assertFalse(mu.dn.equivalent(value, value))

    def test_same_year_range_is_explicit_not_an_inferred_date(self):
        self.assertTrue(mu.dn.equivalent('1830', '1830-1830'))
        self.assertFalse(mu.dn.equivalent('1830', '1829-1830'))
        self.assertFalse(mu.dn.equivalent('1830', 'circa 1830-1830'))


class MunicipalCatalogueTests(unittest.TestCase):
    def test_bristol_declared_utf8_keeps_accented_names(self):
        raw = '<meta charset="utf-8"><p><label>Object Number</label>: K12</p><p><label>Artist</label>: MÜLLER, Rosa</p><p><label>Title</label>: Fête</p>'.encode()
        obj = mu.parse_object('bristol', raw, 'https://example.org/12')
        self.assertEqual(obj['makers'], ['MÜLLER, Rosa'])
        self.assertEqual(obj['fields']['Title'], ['Fête'])

    def test_mixed_legacy_pound_byte_does_not_corrupt_utf8_names(self):
        self.assertEqual(mu.bristol_text('MÜLLER '.encode() + b'\xa350'), 'MÜLLER £50')

    def test_bristol_current_location_reads_row_without_inventing_display(self):
        raw = b'<p><label>Object Number</label>: K12</p><div class="row"><div><div><h3>Current Location</h3></div><p>On loan</p></div></div>'
        self.assertEqual(mu.parse_object('bristol', raw, 'https://example.org/12')['fields']['Current Location'], ['On loan'])
        self.assertNotIn('Current Location', mu.parse_object('bristol', b'<p><label>Object Number</label>: K12</p><div class="row"><h3>Current Location</h3></div>', 'https://example.org/12')['fields'])

    def test_glasgow_unrelated_untitled_search_hit_does_not_abort_or_match_partial_id(self):
        obj = mu.parse_object('glasgow', b'<dl><dt>ID Number</dt><dd>PP.1981.8.446-447</dd></dl>', 'https://example.org/1')
        self.assertNotIn('Title', obj['fields'])
        self.assertNotEqual(p.acckey('447'), p.acckey(obj['fields']['ID Number'][0]))

    def test_portrait_prefix_does_not_remove_sitter_identity(self):
        self.assertEqual(mu.title_key('Portrait of John Watkins of Bristol', []), mu.title_key('John Watkins of Bristol', []))
        self.assertNotEqual(mu.title_key('Portrait of an Unknown Lady', []), mu.title_key('Portrait of a Lady', []))


class AdministrativeAllocationTests(unittest.TestCase):
    def candidate(self, allocation="affectation;Musée d'Orsay", location="Paris ; musée d'Orsay"):
        return {'Lieu_de_depot': allocation, 'Localisation': location,
                'Nom_officiel_musee': "musée d'Orsay", 'Ville': 'Paris',
                'Code_Museofile': 'M5060', 'Auteur': 'Named Painter',
                'Statut_juridique': "propriété de l'Etat;donation"}

    def test_same_museum_administrative_allocation_is_not_a_loan(self):
        self.assertIsNone(al.allocation_check(self.candidate()))

    def test_old_allocation_to_a_different_museum_does_not_confirm_current_holding(self):
        self.assertIsNotNone(al.allocation_check(self.candidate('attribution;musée du Louvre département des Peintures')))

    def test_current_location_outside_registered_museum_is_not_accepted(self):
        self.assertIsNotNone(al.allocation_check(self.candidate(location='Roubaix ; La Piscine')))

    def test_loan_and_uncertain_allocation_remain_review(self):
        for value in ["dépôt;Musée d'Orsay", "affectation (?);Musée d'Orsay", "attribution;dépôt;Musée d'Orsay"]:
            self.assertIsNotNone(al.allocation_check(self.candidate(value)))

    def test_matching_destination_does_not_override_missing_status(self):
        o = self.candidate()
        o['MANQUANT'] = 'oui'
        self.assertIsNotNone(al.allocation_check(o))

    def test_final_title_stop_does_not_change_internal_content(self):
        self.assertEqual(lv.title_variants('Le Pont.', True), lv.title_variants('Le Pont', True))
        self.assertNotEqual(lv.title_variants('Composition IV.', True), lv.title_variants('Composition VI', True))


class ItalianStorageTests(unittest.TestCase):
    def check(self, spec, rights='proprietà Stato', description='', other=''):
        return st.storage_only([rights], [description], [spec], [other])

    def test_internal_storage_coordinates(self):
        for value in ['deposito', 'deposito, soffittone, sala 3, carrello 2 dx', 'II piano/ deposito 0', 'Deposito (AA), rastrelliera 21, lato B']:
            self.assertTrue(self.check(value), value)

    def test_external_deposits_stay_review(self):
        for value in ['in deposito presso la Prefettura di Bergamo', 'deposito esterno', 'deposito (119), attualmente presso ufficio sindaco', 'deposito, fondo Privata Spettanza']:
            self.assertFalse(self.check(value), value)

    def test_legal_or_narrative_qualification_is_not_room(self):
        self.assertFalse(self.check('deposito', rights='proprietà privata'))
        self.assertFalse(self.check('deposito', rights='detenzione Stato'))
        self.assertFalse(self.check('deposito', description='restituito al proprietario'))
        self.assertFalse(self.check('deposito', other='prestito temporaneo'))
        self.assertFalse(st.storage_only([], [], ['deposito'], []))


class CurrentMuseumFormatTests(unittest.TestCase):
    def test_catalogue_outer_quotes_do_not_change_title(self):
        self.assertEqual(hu.unquote_title('"The Window"'), 'The Window')
        self.assertEqual(hu.unquote_title('“The Window”'), 'The Window')
        self.assertEqual(hu.unquote_title('Study for "The Window"'), 'Study for "The Window"')
        self.assertEqual(hu.unquote_title('"The Window'), '"The Window')

    def test_louvre_language_and_escaped_ark_are_same_object(self):
        urls = l.d.canonical_urls('https://collections.louvre.fr/en/ark:/53355/cl010066443.json')
        self.assertIn('https://collections.louvre.fr/ark%3A/53355/cl010066443', urls)
        self.assertNotIn('https://collections.louvre.fr/ark:/53355/cl010066444', urls)

    def test_met_legacy_identifier_shares_duplicate_family(self):
        self.assertEqual(l.d.scheme_family('european-met-the-met-object'), l.d.scheme_family('met-object'))


class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.index = p.Index.__new__(p.Index)
        self.row = {'artwork': {'title': 'A Landscape', 'alternate_title': None, 'accession_number': 'A 1.2', 'unlinked_creator_label': None}, 'artists': [{'name': 'Jane Painter'}], 'identifiers': [{'scheme': 'museum-object', 'external_id': '17'}], 'supplied': None}

    def match(self, **kw):
        args = {'row': self.row, 'scheme': 'museum-object', 'oid': '17', 'titles': ['A Landscape'], 'artists': ['Painter, Jane'], 'accession': 'A 1.2', 'dates': ['1901']}
        args.update(kw)
        return self.index.match(**args)

    def test_exact_native_id_still_requires_title(self):
        self.assertEqual(self.match(titles=['Another Landscape']), 'title_mismatch')

    def test_exact_native_id_still_requires_artist(self):
        self.assertEqual(self.match(artists=['Another Painter']), 'creator_mismatch')

    def test_inventory_conflict_is_held(self):
        self.assertEqual(self.match(accession='A 1.3'), 'inventory_mismatch')

    def test_complete_native_identity(self):
        self.assertTrue(self.match().startswith('existing_exact_'))

    def test_supplied_only_date_must_match(self):
        self.row['identifiers'] = []
        self.row['supplied'] = [['Jane Painter', 'A Landscape', '1900', 'Museum', 'Country', 'false']]
        self.assertEqual(self.match(), 'supplied_date_wording_mismatch')

    def test_supplied_unknown_is_not_assigned_a_date(self):
        self.row['identifiers'] = []
        self.row['supplied'] = [['Jane Painter', 'A Landscape', '', 'Museum', 'Country', 'false']]
        before = copy.deepcopy(self.row)
        self.assertEqual(self.match(), 'supplied_date_wording_mismatch')
        self.assertEqual(before, self.row)

    def test_supplied_exact_date_and_identity(self):
        self.row['identifiers'] = []
        self.row['supplied'] = [['Jane Painter', 'A Landscape', '1901', 'Museum', 'Country', 'false']]
        self.assertTrue(self.match().startswith('unique_exact_'))

    def test_wikidata_ended_holding_is_excluded(self):
        e = {'claims': {'P195': [{'rank': 'normal', 'qualifiers': {'P582': []}}, {'rank': 'normal'}]}}
        self.assertEqual(s.current_statements(e, 'P195'), [{'rank': 'normal'}])

    def test_wikidata_deprecated_holding_is_excluded(self):
        self.assertEqual(s.current_statements({'claims': {'P195': [{'rank': 'deprecated'}]}}, 'P195'), [])

    def test_preferred_current_statement_wins(self):
        e = {'claims': {'P195': [{'rank': 'normal'}, {'rank': 'preferred'}]}}
        self.assertEqual(s.current_statements(e, 'P195'), [{'rank': 'preferred'}])


class ReviewCitationTests(unittest.TestCase):
    def setUp(self):
        self.lead = {'artwork_id': 'local-row', 'target_ids': {'local': 'local-row', 'production': 'production-row'}, 'review_state': 'review', 'provider': 'example', 'external_id': '123', 'source_url': 'https://example.org/object/123', 'source_receipt': {'retrieved_at': '2026-10-05T00:00:00Z'}, 'reported_location': 'Unresolved museum', 'requires_duplicate_reconciliation': True}

    def test_production_uses_mapped_identity_and_preserves_lead(self):
        before = copy.deepcopy(self.lead)
        result = l.record(self.lead, 'production', 'pinned-hash')
        self.assertEqual(result['entity_id'], 'production-row')
        self.assertEqual(before, self.lead)
        import json
        evidence = json.loads(result['evidence_note'])
        self.assertEqual(evidence['review_state'], 'review')
        self.assertTrue(evidence['requires_duplicate_reconciliation'])
        self.assertNotIn('target_ids', evidence)

    def test_accepted_claim_cannot_enter_review_citation_writer(self):
        self.lead['review_state'] = 'accepted'
        with self.assertRaises(AssertionError):
            l.record(self.lead, 'production', 'pinned-hash')

    def test_source_and_target_separate_citation_identities(self):
        local = l.record(self.lead, 'local', 'pinned-hash')['id']
        production = l.record(self.lead, 'production', 'pinned-hash')['id']
        self.assertNotEqual(local, production)
        self.lead['source_url'] = 'https://example.org/object/124'
        self.assertNotEqual(local, l.record(self.lead, 'local', 'pinned-hash')['id'])

    def test_legacy_schemes_share_physical_object_duplicate_checks(self):
        for legacy, current in [('european-popular-ng-aliases-object', 'ng-object'), ('european-tate-object', 'tate-object'), ('european-rijks-object', 'rijks-object'), ('european-vam-object', 'vam-object')]:
            with self.subTest(legacy=legacy):
                self.assertEqual(l.d.scheme_family(legacy), l.d.scheme_family(current))


class MuseumCustodyTests(unittest.TestCase):
    def candidate(self, site, kind):
        return {'claim_type': 'holding', 'object_evidence': {'artistMakerPerson': [], 'creditLine': '', 'objectHistory': '', 'current_location_observation': {'site': site, 'type': kind, 'onDisplay': kind == 'display'}}}

    def test_outgoing_loan_with_no_site_stays_review(self):
        c = v.qualify(self.candidate('', 'display - loan'))
        self.assertEqual(c['review_state'], 'review')

    def test_storage_authority_does_not_create_display_claim(self):
        c = v.qualify(self.candidate('ES', 'storage'), {'status': 200})
        self.assertNotIn('review_state', c)
        self.assertEqual(c['claim_type'], 'holding')
        self.assertFalse(c['object_evidence']['current_location_observation']['onDisplay'])

    def test_storage_branch_requires_authority_evidence(self):
        with self.assertRaises(AssertionError):
            v.qualify(self.candidate('ES', 'storage'))

    def test_qualified_attribution_is_not_promoted(self):
        c = self.candidate('VA', 'storage')
        c['object_evidence']['artistMakerPerson'] = [{'note': 'attributed to'}]
        self.assertEqual(v.qualify(c)['review_state'], 'review')


class ItalianInstitutionTests(unittest.TestCase):
    def test_same_generic_museum_name_in_different_city_is_not_merged(self):
        records = [{'institution': {'id': 'milan', 'name': "Galleria d'Arte Moderna", 'slug': 'milan-gallery'}, 'place': {'name': 'Milan'}}]
        institution, _, issue = ap.resolve_institution({"Galleria d'Arte Moderna"}, 'Firenze (FI)', records, 'source-museum')
        self.assertIsNone(issue)
        self.assertNotEqual(institution['id'], 'milan')
        self.assertEqual(institution['status'], 'review')

    def test_missing_geography_does_not_authorize_a_same_name_merge(self):
        records = [{'institution': {'id': 'unknown-city', 'name': 'Museo Diocesano', 'slug': 'diocesan-museum'}, 'place': None}]
        institution, _, issue = ap.resolve_institution({'Museo Diocesano'}, 'Venezia (VE)', records, 'source-museum')
        self.assertIsNone(institution)
        self.assertEqual(issue, 'existing_institution_geography_requires_review')

    def test_milan_and_milano_are_the_same_city_for_identity_comparison(self):
        self.assertEqual(ap.citykey('Milan'), ap.citykey('Milano (MI)'))
        self.assertNotEqual(ap.citykey('Milano (MI)'), ap.citykey('Firenze (FI)'))

    def test_italian_catalogue_domain_change_preserves_duplicate_detection(self):
        aliases = l.d.canonical_urls('https://catalogo.cultura.gov.it/detail/HistoricOrArtisticProperty/0800675920')
        self.assertIn('https://catalogo.beniculturali.it/detail/HistoricOrArtisticProperty/0800675920', aliases)
        self.assertFalse(any('lombardiabeniculturali' in u for u in aliases))

    def test_regional_mirror_does_not_bypass_lombardia_duplicate_detection(self):
        aliases = l.d.canonical_urls('https://catalogo.cultura.gov.it/detail/Lombardia/HistoricOrArtisticProperty/B0050-00056_R03')
        self.assertIn('https://www.lombardiabeniculturali.it/opere-arte/schede/b0050-00056/', aliases)


class RenumberedObjectTests(unittest.TestCase):
    def test_marseille_documented_ba_prefix_matches_numbered_inventory(self):
        self.assertTrue(m.inventory_keys('BA 791') & m.inventory_keys('791'))
        self.assertFalse(m.inventory_keys('BA 791') & m.inventory_keys('792'))

    def test_other_department_prefixes_are_not_stripped(self):
        self.assertFalse(m.inventory_keys('D 791') & m.inventory_keys('791'))
        self.assertFalse(m.inventory_keys('BA 791 bis') & m.inventory_keys('791'))

    def test_renumbered_notice_keeps_old_url_in_duplicate_checks(self):
        urls = l.d.claim_urls({'source_url': 'https://pop.culture.gouv.fr/notice/joconde/09130010278', 'duplicate_source_urls': ['https://pop.culture.gouv.fr/notice/joconde/000PE012345']})
        self.assertIn('https://www.pop.culture.gouv.fr/notice/joconde/000PE012345', urls)


class RijksCurrentMakerTests(unittest.TestCase):
    def test_rejected_former_maker_does_not_replace_current_maker(self):
        obj = {'assigned_by': [{'assigned_property': 'part_of', 'assigned': [{'referred_to_by': [{'content': 'Earlier Painter [rejected attribution]'}]}]}], 'part': [{'carried_out_by': [{'notation': [{'@value': 'Current Painter'}]}]}]}
        before = copy.deepcopy(obj)
        makers, _ = rr.current_production(obj, '123')
        self.assertEqual(makers, ['Current Painter'])
        self.assertEqual(obj, before)

    def test_current_uncertain_attribution_stays_review(self):
        obj = {'part': [{'carried_out_by': [{'notation': [{'@value': 'Painter'}]}], 'referred_to_by': [{'content': 'Painter [attributed to]'}]}]}
        with self.assertRaises(AssertionError):
            rr.current_production(obj, '123')

    def test_unrejected_alternative_is_not_silently_ignored(self):
        obj = {'assigned_by': [{'assigned_property': 'part_of', 'assigned': [{'referred_to_by': [{'content': 'Alternative Painter'}]}]}], 'part': [{'carried_out_by': [{'notation': [{'@value': 'Current Painter'}]}]}]}
        with self.assertRaises(AssertionError):
            rr.current_production(obj, '123')


class YaleArtistAuthorityTests(unittest.TestCase):
    def test_name_variant_requires_the_same_primary_artist_identifier(self):
        row = {'artists': [{'id': 'local-artist', 'name': 'James Faed'}]}
        actors = [{'names': ['James Faed Sr.'], 'identifiers': ['https://www.wikidata.org/wiki/Q6133733'], 'qualifiers': []}]
        names, proofs = y.maker_names(row, actors, {'local-artist': {'Q6133733'}})
        self.assertIn('James Faed', names)
        self.assertEqual(proofs[0]['shared_wikidata_ids'], ['Q6133733'])
        self.assertEqual(actors[0]['names'], ['James Faed Sr.'])

    def test_different_artist_identifier_does_not_authorize_name_alias(self):
        row = {'artists': [{'id': 'local-artist', 'name': 'James Faed'}]}
        actors = [{'names': ['John Faed'], 'identifiers': ['https://www.wikidata.org/wiki/Q955520'], 'qualifiers': ['after']}]
        names, proofs = y.maker_names(row, actors, {'local-artist': {'Q6133733'}})
        self.assertNotIn('James Faed', names)
        self.assertFalse(proofs)


if __name__ == '__main__':
    unittest.main()
