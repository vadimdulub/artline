"""Offline invariants for source-qualified metadata and preservation of existing works."""
import copy
import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-larissa-apply-20261010.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class Larissa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.news,cls.holds=a.records();cls.by={v['facts']['number']:v for v in cls.news+cls.holds}
        initial=a.m.load(a.RUN/'production-initial-scope-001.json.gz')['snapshot'];focus=a.m.load(a.RUN/'focused-comparators-001.json.gz')['snapshot'];cls.before={}
        for key in initial:
            combined=initial[key]+focus[key]
            unique={__import__('json').dumps(v,sort_keys=True):v for v in combined};cls.before[key]=list(unique.values())
        cls.images=a.image_records(cls.before);cls.plan=dict(records=cls.news,holdings=cls.holds,images=cls.images)
    def baseline_after(self):
        out=copy.deepcopy(self.before);holds={v['artwork_id'] for v in self.holds};primary={x['artwork_id']:x['media_id'] for x in self.images if x['set_primary']}
        for v in out['artworks']:
            if v['id'] in holds:v['current_institution_id']=a.c.IID;v['updated_at']='synthetic change'
            if v['id'] in primary:v.update(primary_media_id=primary[v['id']],revision=v['revision']+1,updated_at='synthetic change',updated_by=a.m.ACTOR)
        return out
    def test_reuses_three_actual_identities(self):
        self.assertEqual((len(self.news),len(self.holds)),(184,3));self.assertEqual({v['facts']['number'] for v in self.holds},{25,56,191})
        self.assertFalse(set(v['artwork_id'] for v in self.news)&set(v['artwork_id'] for v in self.holds))
    def test_album_is_one_record_twelve_identifiers(self):
        album=self.by[176];self.assertEqual(len(album['facts']['source_ids']),12);self.assertEqual(len({x['artwork_id'] for x in self.images if x['primary_number']==176}),1)
        self.assertEqual(sum(len(x['facts']['source_ids']) for x in self.news),195)
    def test_no_invented_numeric_bounds(self):
        unknown={30,32,39,51,54,80,102};self.assertEqual({x['facts']['number'] for x in self.news if x['facts']['first'] is None},unknown)
        for n in unknown:self.assertIsNone(self.by[n]['facts']['last']);self.assertEqual(self.by[n]['facts']['date_precision'],'unknown')
    def test_conflicts_remain_visible(self):
        for n in [51,54,102]:self.assertIn('Conflicting source dates:',self.by[n]['facts']['date_display']);self.assertIn(' / ',self.by[n]['facts']['date_display'])
    def test_date_cutoff_checks_creation(self):
        self.assertTrue(all(x['facts']['first'] is None or x['facts']['first']<=x['facts']['last']<=1970 for x in self.news))
        self.assertEqual(self.by[168]['facts']['last'],1960);self.assertFalse(any(x['number']==168 for x in self.images))
    def test_no_image_for_open_after_date(self):self.assertFalse(any(x['number']==32 for x in self.images))
    def test_explicit_watercolour_types(self):
        selected=[x for x in self.news if x['facts']['work_type']=='watercolor'];self.assertEqual(len(selected),17)
        for x in selected:
            f=x['facts']['source_facts'];self.assertTrue(f['native_category']=='Υδατογραφία' or (f['native_technique']or'').startswith('Υδατογραφία'))
    def test_unknown_creator_initials_preserved(self):self.assertEqual(self.by[193]['facts']['creator_label'],'L.C.');self.assertIsNone(self.by[193]['facts']['source_facts']['painter_id'])
    def test_exact_https_source_evidence(self):
        for im in self.images:self.assertTrue(im['verified_https_source_image_url'].startswith('https://'));self.assertEqual(im['https_source_receipt']['sha256'],im['original_reference']['sha256']);self.assertLessEqual(im['bytes'],100000)
    def test_old_primaries_never_replaced(self):
        before={x['id']:x for x in self.before['artworks']}
        for im in self.images:
            if before.get(im['artwork_id'],{}).get('primary_media_id'):self.assertFalse(im['set_primary'])
        self.assertEqual(sum(x['set_primary'] for x in self.images),181)
    def test_expected_existing_changes_accepted(self):a.verify_existing(self.before,self.baseline_after(),self.plan,'offline')
    def test_rejects_date_rewrite_on_link(self):
        after=self.baseline_after();v=next(x for x in after['artworks'] if x['id']==a.r.LINKS[56]);v['creation_year_start']=1925
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_publishing_on_link(self):
        after=self.baseline_after();v=next(x for x in after['artworks'] if x['id']==a.r.LINKS[191]);v['status']='published'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_old_primary_replacement(self):
        after=self.baseline_after();v=next(x for x in after['artworks'] if x['id']==a.r.LINKS[25]);v['primary_media_id']='unrelated'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_creator_loss(self):
        after=self.baseline_after();after['artists']=after['artists'][1:]
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_rights_evidence_loss(self):
        after=self.baseline_after();after['media_rights_evidence']=after['media_rights_evidence'][1:]
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')
    def test_rejects_institution_mutation(self):
        after=self.baseline_after();after['museums'][0]['name']='Changed'
        with self.assertRaises(AssertionError):a.verify_existing(self.before,after,self.plan,'offline')

if __name__=='__main__':unittest.main(verbosity=2)
