"""Offline guard tests. No database connection or catalogue fixtures."""
import copy,importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
s=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('cesi-delivery-20261010.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
m=d.m
class GuardTests(unittest.TestCase):
    def test_duplicate_relationship_aborts_before_insertion(self):
        db=Mock();db.execute.return_value.fetchall.return_value=[{'id':'existing'}]
        r=dict(target_artist_id='student',source_artist_id='teacher',relationship_type='teacher_of',source_label='Teacher')
        with self.assertRaises(AssertionError):d.assert_no_relation(db,r)
        db.execute.return_value.fetchall.return_value=[]
        d.assert_no_relation(db,r)
    def test_api_title_check_handles_quotes_and_nested_values(self):
        self.assertIn('A "quoted" title',set(d.json_strings({'data':[{'title':'A "quoted" title'}]})))
    def test_unknown_and_conflicting_dates_stay_unknown(self):
        for value in ['',None,'unknown','1590-1580','1965-1975','active 1556-1629','17th century']:
            self.assertIsNone(m.dateparse(value))
        self.assertEqual(m.dateparse('c.1590–1599')['precision'],'circa_range')
        self.assertEqual(m.dateparse('1955')['last'],1955)
    def test_real_local_write_is_rejected_before_connecting(self):
        with patch.object(m.psycopg,'connect') as connect:
            with self.assertRaises(AssertionError):m.connect(write=True,local=True)
            connect.assert_not_called()
    def test_ambiguous_source_rows_and_repeated_weak_titles_are_excluded(self):
        with tempfile.TemporaryDirectory(prefix='artline-identity-') as directory:
            root=Path(directory)
            m.save(root/'indexes/a.json.gz',dict(artist_id='a',works=[dict(title='Same'),dict(title='Same'),dict(title='Distinct')]))
            def row(aid,title,confidence=.94):return dict(artwork_id=aid,title=title,artist_id='a',provider='wikiart',state='existing',identity_confidence=confidence)
            rows=[row('x','Distinct'),row('x','Distinct'),row('y','Same'),row('z','Same',.99),row('ok','Distinct')]
            with patch.object(m,'RUN',root),patch.object(m,'all_rows',return_value=rows):
                self.assertEqual([r['artwork_id'] for r in m.safe_rows()],['z','ok'])
    def test_visual_hold_cannot_be_overridden_by_generic_acceptance(self):
        with tempfile.TemporaryDirectory(prefix='artline-visual-') as directory:
            root=Path(directory)
            for name,decision in [('a','hold'),('z','accept')]:m.save(root/'visual-review'/(name+'.json'),dict(decisions=[dict(artwork_id='a',sha256='abc',decision=decision)]))
            with patch.object(m,'RUN',root):self.assertEqual(d.visual()['a']['decision'],'hold')
    def test_unrelated_existing_metadata_and_images_cannot_change(self):
        before=dict(artwork=dict(id='a',title='Original',status='review',primary_media_id='original-image',current_institution_id='museum',creation_year_start=1600),creators=[dict(artist_id='p')],attachments=[dict(media_id='original-image')],holdings=[dict(institution_id='museum')])
        plan=dict(rows=[dict(artwork_id='a',state='existing',image=None,add_holding=False,before=before)],supplements=[])
        d.validate_after(plan,{'a':copy.deepcopy(before)})
        for key,value in [('primary_media_id','replacement'),('status','published'),('creation_year_start',1700),('title','Changed')]:
            after=copy.deepcopy(before);after['artwork'][key]=value
            with self.assertRaises(AssertionError):d.validate_after(plan,{'a':after})
    def test_original_associations_cannot_be_removed(self):
        before=dict(artwork=dict(id='a',title='Original'),creators=[dict(artist_id='p')],attachments=[dict(media_id='original-image')],holdings=[dict(institution_id='museum')])
        plan=dict(rows=[dict(artwork_id='a',state='existing',image=None,add_holding=False,before=before)],supplements=[])
        for key in ['creators','attachments','holdings']:
            after=copy.deepcopy(before);after[key]=[]
            with self.assertRaises(AssertionError):d.validate_after(plan,{'a':after})
if __name__=='__main__':unittest.main()
