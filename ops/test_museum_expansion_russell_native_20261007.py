"""Offline physical identity, date and review safeguards; no database fixtures."""
import copy
import importlib.util
import unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-russell-native-apply-20261007.py'))
a=importlib.util.module_from_spec(s);s.loader.exec_module(a);n=a.n;w=a.w


class RussellNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=a.records();cls.rows={r['source_id']:r for r in a.m.load(a.CANDIDATES)['rows']};cls.review=a.m.load(a.REVIEW);cls.plan,cls.digest=a.validate_plan()

    def record(self,key):return next(r for r in self.records if r['facts']['source_id']==key)

    def test_all_selected_sources_are_distinct_and_accounted(self):
        self.assertEqual(68,len(self.records));self.assertEqual(68,len({w.compact(r['facts']['inventory']) for r in self.records}))
        self.assertEqual(140,len(self.review['decisions']));self.assertEqual(16,sum(r['state']=='hold_identity_or_source' for r in self.review['decisions']))

    def test_unknown_or_biographical_dates_rejected(self):
        for raw in ['', 'after 1834', 'late 1800s-early 1900s', 'early 1900s', '1971', '1969-1971','about 1970']:
            with self.subTest(raw=raw),self.assertRaises(AssertionError):n.creation(raw)
        native=copy.deepcopy(self.record('king-leopold')['native']);native['parsed']['title']='A Sitter (1810-1880)';native['parsed']['caption_lines'][0]='A Sitter (1810-1880)'
        with self.assertRaises(AssertionError):n.source_facts(native)

    def test_bounded_creation_and_literal_qualifiers(self):
        self.assertEqual((1800,1899,'range'),n.creation('late 19th Century'))
        self.assertEqual((1920,1929,'range'),n.creation('1920s'))
        self.assertEqual((1810,1840,'circa_range'),n.creation('about 1810-1840'))

    def test_memories_uses_physical_bronze_cast_date(self):
        r=self.record('memories');f=r['facts'];self.assertEqual((1947,1947),(f['first'],f['last']));self.assertIn('1917',f['date_display']);self.assertIn('posthumous',f['creator_label'])
        native=copy.deepcopy(r['native']);native['parsed']['narrative']=native['parsed']['narrative'].replace('1947','1977')
        with self.assertRaises(AssertionError):a.facts(native,self.rows['memories'],r['decision'])

    def test_studio_attribution_and_explicit_material_preserved(self):
        r=self.record('pereat');self.assertEqual('Studio of Orazio Andreoni',r['facts']['creator_label']);self.assertEqual('Plaster',r['facts']['medium']);self.assertIn('pedestal',r['decision']['identity_note'])

    def test_copy_sculptor_not_invented(self):
        r=self.record('king-leopold');self.assertEqual('Unknown artist, after Peter Turnerelli',r['facts']['creator_label']);self.assertEqual('late 1800s',r['facts']['date_display']);self.assertNotEqual(1817,r['facts']['first'])

    def test_prototype_and_copy_date_conflicts_held(self):
        held={r['source_id'] for r in self.review['decisions'] if r['state']=='hold_identity_or_source'}
        self.assertTrue({'venus','voltaire','amazon-taming-a-horse','christmas-morning-1866'}<=held)

    def test_shared_inventory_across_undated_page_also_held(self):
        rows=self.rows
        self.assertEqual('hold_source',rows['lady-with-a-mantilla']['state']);self.assertIn('the-reception',rows['lady-with-a-mantilla']['shared_inventory_sources'])
        self.assertEqual('hold_source',rows['morning']['state']);self.assertEqual('hold_source',rows['night']['state'])

    def test_existing_identities_not_added_again(self):
        chosen={r['facts']['source_id'] for r in self.records}
        self.assertFalse(chosen&{'a-lions-head','aurora-triumphans','heavenly-stairs','midsummer','landscape-with-bridge','if-one-could-have-that-little-head-of-hers'})

    def test_study_and_replica_physical_distinctions(self):
        self.assertIn('preparatory sketch',self.record('gypsy-horse-drovers')['decision']['identity_note'])
        self.assertEqual('Plaster',self.record('daedalus-and-icarus')['facts']['medium'])
        self.assertIn('1860 original',self.record('flood-in-the-highlands')['decision']['identity_note'])

    def test_separate_trilogy_canvases_no_extra_aggregate(self):
        rows=[self.record(k) for k in ['in-the-wilderness','jephthahs-vow','the-martyr']]
        self.assertEqual(3,len({r['facts']['inventory'] for r in rows}));self.assertTrue(all('trilogy' in r['decision']['identity_note'] or 'three-painting' in r['decision']['identity_note'] for r in rows))

    def test_title_events_are_not_creation_years(self):
        self.assertEqual(1873,self.record('the-moorish-proselytes-of-archbishop-ximenes-granada-1500')['facts']['first'])
        self.assertEqual(1890,self.record('how-the-danes-came-up-the-channel-a-thousand-years-ago')['facts']['first'])

    def test_rejected_old_url_leads_do_not_merge_different_objects(self):
        for key in ['on-the-cornish-coast','the-bathers','the-bathers-2']:a.legacy_url_check(self.record(key),self.plan['before'])
        r=self.record('the-bathers');before=copy.deepcopy(self.plan['before']);c=next(c for c in before['citations'] if c['source_url']==r['facts']['source_url']);c['field_name']='accepted_metadata'
        with self.assertRaises(AssertionError):a.legacy_url_check(r,before)

    def test_bathers_remain_three_distinct_objects(self):
        self.assertEqual({'SC24','SC42'},{self.record(k)['facts']['inventory'] for k in ['the-bathers','the-bathers-2']})
        self.assertTrue(any(x['accession_number']=='BORGM 01696' for x in self.plan['before']['artworks']))

    def test_native_caption_or_creator_tampering_rejected(self):
        r=self.record('ethel')
        for idx,value in [(0,'Ethel, 1971'),(1,'Another artist')]:
            native=copy.deepcopy(r['native']);native['parsed']['caption_lines'][idx]=value
            with self.assertRaises(AssertionError):a.facts(native,self.rows['ethel'],r['decision'])

    def test_qualified_creator_cannot_be_promoted(self):
        r=self.record('pereat');d=copy.deepcopy(r['decision']);d['facts']['creator_label']='Orazio Andreoni'
        with self.assertRaises(AssertionError):a.facts(r['native'],self.rows['pereat'],d)

    def test_missing_dimensions_and_unknown_types_retained(self):
        self.assertTrue(all(r['facts']['dimensions'] is None for r in self.records));self.assertEqual(5,sum(r['facts']['work_type']=='unknown' for r in self.records));self.assertEqual('unknown',self.record('table-lamp')['facts']['work_type'])

    def test_new_artwork_metadata_validation_rejects_images_or_publication(self):
        r=self.record('ethel');f=r['facts'];art={k:None for k in self.plan['before']['artworks'][0]}
        art.update(id=r['artwork_id'],slug=r['slug'],title=f['title'],normalized_title=a.m.norm(f['title']),date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['date_precision'],work_type=f['work_type'],medium_text=f['medium'],dimensions_text=None,accession_number=f['inventory'],status='review',research_candidate=True,unlinked_creator_label=f['creator_label'],current_institution_id=a.IID,created_by=a.m.ACTOR,updated_by=a.m.ACTOR)
        a.assert_new(art,r)
        for key,value in [('primary_media_id','image'),('published_at','now'),('status','published'),('creation_year_start',1971),('dimensions_text','invented')]:
            changed=dict(art);changed[key]=value
            with self.assertRaises(AssertionError):a.assert_new(changed,r)


if __name__=='__main__':unittest.main()
