import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('nordic1000',Path(__file__).with_name('nordic-1000-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

class SourceEligibility(unittest.TestCase):
    def setUp(self):
        self.museum=dict(qid='Q1132918',id='museum-id',country='NO')
        self.no={'_id':'12','_source':{'NmId':'NG.M.123','MetaData':{'CataloguingLevel':['Enkeltobjekt'],'ObjectName':['Maleri'],'Owner':[{'FullName':'Nasjonalmuseet for kunst, arkitektur og design'}],'ObjectNumber':['NG.M.123'],'Production':[{'PerRole':'Kunstner','LevelCertainty':'sikker','PersonRef':42,'PersonRefMetaData':{'FullName':'Source Creator'},'DateFrom':'1901','DateTo':'1901'}],'Labeldate':['1901'],'ObjectTitle':[{'Title':'Original title','Alternatives':[{'Title':'English title','Lang':'ENG'}]}]}}}
        self.smk={'object_number':'KMS1','id':'1_object','number_of_parts':1,'object_names':[{'name':'Painting'}],'production':[{'creator_forename':'Source','creator_surname':'Creator','creator_lref':'42_person'}],'production_date':[{'start':'1901-01-01','end':'1901-12-31','period':'1901'}],'production_dates_notes':['Værkdatering'],'titles':[{'title':'Museum title','language':'engelsk'}],'frontend_url':'https://open.smk.dk/artwork/image/KMS1'}
    def test_native_translation_retains_object_identity(self):
        row,why=r.norwegian_fields(self.no,self.museum,{})
        self.assertIsNone(why);self.assertEqual(row['title'],'English title');self.assertIn('Original title',row['title_aliases']);self.assertEqual(row['first'],1901)
    def test_native_earliest_year_is_not_exact(self):
        self.no['_source']['MetaData']['Labeldate']=['Tidligst 1901']
        self.assertIsNone(r.norwegian_fields(self.no,self.museum,{})[0])
    def test_native_undated_label_does_not_use_hidden_range(self):
        self.no['_source']['MetaData']['Labeldate']=['Uten år']
        self.assertIsNone(r.norwegian_fields(self.no,self.museum,{})[0])
    def test_qualified_author_does_not_become_primary(self):
        self.no['_source']['MetaData']['Production'][0]['LevelCertainty']='tilskrevet'
        self.assertIsNone(r.norwegian_fields(self.no,self.museum,{})[0])
    def test_verso_is_not_inserted_as_whole_object(self):
        self.no['_source']['NmId']='NG.M.123VERSO'
        self.assertIsNone(r.norwegian_fields(self.no,self.museum,{})[0])
    def test_part_is_not_inserted_as_single_work(self):
        self.no['_source']['NmId']='NG.M.123-002'
        self.assertIsNone(r.norwegian_fields(self.no,self.museum,{})[0])
    def test_outside_owner_is_not_museum_holding(self):
        self.no['_source']['MetaData']['Owner'][0]['FullName']='Private lender'
        self.assertIsNone(r.norwegian_fields(self.no,self.museum,{})[0])
    def test_smk_deposit_needs_custody_review(self):
        self.smk['object_number']='DEP1'
        self.assertIsNone(r.smk_fields(self.smk,self.museum,{})[0])
    def test_career_proxy_does_not_become_creation_range(self):
        self.smk['production'][0].update(creator_date_of_birth='1700-01-01',creator_date_of_death='1779-01-01')
        self.smk['production_date'][0].update(start='1715-01-01',end='1779-12-31',period='1715-1779')
        self.assertIsNone(r.smk_fields(self.smk,self.museum,{})[0])
    def test_circa_1970_requires_cutoff_review(self):
        self.smk['production_date'][0].update(start='1970-01-01',end='1970-12-31',period='ca. 1970')
        self.assertIsNone(r.smk_fields(self.smk,self.museum,{})[0])
    def test_explicit_1970_is_allowed(self):
        self.smk['production_date'][0].update(start='1970-01-01',end='1970-12-31',period='1970')
        self.assertEqual(r.smk_fields(self.smk,self.museum,{})[0]['first'],1970)
    def test_post_cutoff_is_held(self):
        self.smk['production_date'][0].update(start='1971-01-01',end='1971-12-31',period='1971')
        self.assertIsNone(r.smk_fields(self.smk,self.museum,{})[0])
    def test_numeric_ids_are_scoped_by_provider(self):
        row,_=r.norwegian_fields(self.no,self.museum,{});row['artist_ids']=[]
        c=dict(external=[dict(entity_id='other',scheme='another-museum',external_id='12',canonical_url='https://example.org/12')],citations=[],artworks=[],creators=[])
        self.assertIsNone(r.collision_reason(row,c)[0])
        c['external'][0]['scheme']='nasjonalmuseet-object'
        self.assertEqual(r.collision_reason(row,c)[0],'Existing exact source identity')

if __name__=='__main__':unittest.main()
