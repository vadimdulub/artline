import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('nordic2k',Path(__file__).with_name('nordic-2000-20261008.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

class ContinuationChecks(unittest.TestCase):
    def setUp(self):
        self.mu=dict(qid='Q671384',id='museum',country='DK')
        self.obj=dict(id='11_object',object_number='KKS11',number_of_parts=1,object_names=[dict(name='Drawing')],production=[dict(creator_forename='Source',creator_surname='Creator',creator_lref='42_person')],production_date=[dict(start='1890-01-01',end='1890-12-31',period='1890')],production_dates_notes=['Værkdatering'],titles=[dict(title='Tree study',language='engelsk')],frontend_url='https://open.smk.dk/artwork/image/KKS11')
    def test_new_target_does_not_change_date_floor(self):
        self.assertEqual(r.b.TARGET,2000)
        row,why=r.graphic_fields(self.obj,self.mu,{})
        self.assertIsNone(why);self.assertEqual(row['first'],1890)
    def test_drawing_identity_and_raw_evidence_preserved(self):
        before=copy.deepcopy(self.obj);row,why=r.graphic_fields(self.obj,self.mu,{})
        self.assertEqual(self.obj,before);self.assertEqual(row['source_evidence'],before)
        self.assertEqual(row['external_id'],'KKS11');self.assertEqual(row['accession'],'KKS11');self.assertEqual(row['work_type'],'drawing');self.assertEqual(row['source_url'],before['frontend_url'])
        self.assertEqual(row['key'],'european-smk-statens-museum-for-kunst-object/KKS11')
    def test_deposit_drawing_is_held(self):
        self.obj['object_number']='DEP11'
        self.assertIsNone(r.graphic_fields(self.obj,self.mu,{})[0])
    def test_qualification_is_not_removed(self):
        self.obj['production'][0]['creator_qualifier']='attributed to'
        self.assertIsNone(r.graphic_fields(self.obj,self.mu,{})[0])
    def test_multiple_authors_not_flattened(self):
        self.obj['production'].append(dict(creator='Other Artist'))
        self.assertIsNone(r.graphic_fields(self.obj,self.mu,{})[0])
    def test_unknown_date_not_invented(self):
        self.obj['production_date']=[]
        self.assertIsNone(r.graphic_fields(self.obj,self.mu,{})[0])
    def test_post_1970_drawing_held(self):
        self.obj['production_date'][0].update(start='1971-01-01',end='1971-12-31',period='1971')
        self.assertIsNone(r.graphic_fields(self.obj,self.mu,{})[0])
    def test_name_is_used_only_to_hold_possible_existing_version(self):
        row,_=r.graphic_fields(self.obj,self.mu,{});row['artist_ids']=[]
        candidates=dict(external=[],citations=[],artworks=[dict(id='existing',title='Tree study',alternate_title=None,accession_number=None,current_institution_id=None,unlinked_creator_label=None)],creators=[dict(artwork_id='existing',artist_id='known',creator_name='Source Creator')])
        reason,ids=r.b.collision_reason(row,candidates)
        self.assertEqual(ids,['existing']);self.assertIn('Possible existing',reason);self.assertEqual(row['artist_ids'],[])
    def test_provider_scoped_numeric_ids(self):
        row,_=r.graphic_fields(self.obj,self.mu,{});row['artist_ids']=[]
        candidates=dict(external=[dict(entity_id='unrelated',scheme='other-source',external_id='KKS11',canonical_url=None)],citations=[],artworks=[],creators=[])
        self.assertIsNone(r.b.collision_reason(row,candidates)[0])
    def test_inventory_collection_qualifier_preserves_object_identity(self):
        claim=dict(mainsnak=dict(datavalue=dict(value='NM 1288')),qualifiers=dict(P195=[dict(datavalue=dict(value=dict(id='Q842858')))]))
        entity=dict(claims=dict(P217=[claim]));before=copy.deepcopy(entity)
        self.assertEqual(r.collection_inventories(entity,'Q842858'),['NM 1288'])
        self.assertEqual(entity,before)
    def test_other_collection_and_extra_inventory_qualifiers_are_held(self):
        claim=dict(mainsnak=dict(datavalue=dict(value='NM 1288')),qualifiers=dict(P195=[dict(datavalue=dict(value=dict(id='Q842858')))]))
        entity=dict(claims=dict(P217=[claim]))
        self.assertEqual(r.collection_inventories(entity,'Q671384'),[])
        claim['qualifiers']['P580']=[dict(datavalue=dict(value='1850'))]
        self.assertEqual(r.collection_inventories(entity,'Q842858'),[])
    def test_impossible_creation_date_is_held_without_substitution(self):
        row=dict(creator_qids=['Q1'],first=186,last=186)
        creators=dict(Q1=dict(entity=dict(claims=dict(P569=[dict(mainsnak=dict(datavalue=dict(value=dict(time='+1818-01-01T00:00:00Z',precision=9))))]))))
        before=copy.deepcopy(row)
        self.assertIn('held without substituting',r.creator_date_conflict(row,creators))
        self.assertEqual(row,before)
    def test_unknown_lifetime_does_not_supply_creation_year(self):
        row=dict(creator_qids=['Q1'],first=1890,last=1890);before=copy.deepcopy(row)
        self.assertIsNone(r.creator_date_conflict(row,{}));self.assertEqual(row,before)
    def test_verso_drawing_is_held_as_side_identity(self):
        self.obj['object_number']='KKS11 verso'
        row,why=r.graphic_fields(self.obj,self.mu,{})
        self.assertIsNone(row);self.assertIn('Sheet-side',why)
    def test_sheet_family_holds_both_sides_and_existing_side_variant(self):
        rows=[dict(key=key,source_scheme='european-smk-statens-museum-for-kunst-object',institution_id='museum',accession=key) for key in ['KKS11','KKS11 verso','KKS12','KKS13']]
        baseline=dict(works=[dict(current_institution_id='museum',accession_number='KKS12 recto')])
        self.assertEqual(r.ambiguous_sheet_keys(rows,baseline),{'KKS11','KKS11 verso','KKS12'})

if __name__=='__main__':unittest.main()
