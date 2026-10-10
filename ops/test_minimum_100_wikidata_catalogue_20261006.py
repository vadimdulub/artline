"""Mutations of a preserved real entity exercise production-import rejection paths."""
import copy,gzip,importlib.util,json,tempfile,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('native',Path(__file__).with_name('minimum-100-wikidata-catalogue-20261006.py'))
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)


class NativeStatementGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc=n.c.load(n.ROOT/'captures/29ad6600ef987b309f1daee30818601667703637a3c725811cabcd36febb1640.json')
        raw=gzip.decompress((n.c.ROOT/cls.rc['body_path']).read_bytes())
        assert n.c.d.sha(raw)==cls.rc['sha256']
        cls.entity=json.loads(raw)['entities']['Q100278166']
        cls.museum=next(x['museum']for x in n.c.load(n.ROOT/'wikidata-catalogue-001/selected-new-object-ids.json')if x['qid']=='Q100278166')
        # This in-memory test label is never a catalogue record or source claim.
        cls.creators={n.w.value(x)['id']:{'labels':{'en':{'value':'Test creator authority label'}}}for x in n.w.active(cls.entity,'P170')}

    def parse(self,e):return n.fields(e,self.museum,self.creators,self.rc)

    def test_date_is_creation_date_and_unknown_media_stays_unknown(self):
        facts,reason=self.parse(self.entity);self.assertIsNone(reason)
        self.assertEqual((facts['first'],facts['last'],facts['date_display']),(1937,1937,'1937'))
        self.assertIsNone(facts['medium']);self.assertIsNone(facts['dimensions'])

    def test_no_invented_year(self):
        e=copy.deepcopy(self.entity);e['claims'].pop('P571')
        self.assertEqual(self.parse(e)[1],'creation_statement_requires_review')

    def test_after_cutoff_is_held(self):
        e=copy.deepcopy(self.entity);e['claims']['P571'][0]['mainsnak']['datavalue']['value']['time']='+1971-01-01T00:00:00Z'
        self.assertEqual(self.parse(e)[1],'creation_precision_or_cutoff_requires_review')

    def test_broad_century_is_held(self):
        e=copy.deepcopy(self.entity);e['claims']['P571'][0]['mainsnak']['datavalue']['value']['precision']=7
        self.assertEqual(self.parse(e)[1],'creation_precision_or_cutoff_requires_review')

    def test_ended_holding_cannot_be_current_collection(self):
        e=copy.deepcopy(self.entity);e['claims']['P195'][0]['qualifiers']={'P582':[]}
        self.assertEqual(self.parse(e)[1],'qualified_collection_requires_review')

    def test_part_is_not_imported_as_an_independent_whole(self):
        e=copy.deepcopy(self.entity);e['claims']['P361']=[{'rank':'normal'}]
        self.assertEqual(self.parse(e)[1],'part_or_ensemble_requires_review')

    def test_qualified_creator_is_not_promoted_to_definite(self):
        e=copy.deepcopy(self.entity);e['claims']['P170'][0]['qualifiers']={'P1480':[]}
        self.assertEqual(self.parse(e)[1],'creator_attribution_requires_review')

    def test_source_must_reference_the_same_museum(self):
        e=copy.deepcopy(self.entity);e['claims']['P195'][0]['mainsnak']['datavalue']['value']['id']='Q1'
        self.assertEqual(self.parse(e)[1],'museum_collection_identity_conflict')

    def test_binary_source_body_roundtrips_without_json_wrapping(self):
        with tempfile.TemporaryDirectory(prefix='artline-source-proof-',dir='/tmp')as folder:
            path=Path(folder)/'source.body.gz';raw=b'{"entities":{}}';compressed=gzip.compress(raw,mtime=0)
            n.save_bytes(path,compressed)
            self.assertEqual(gzip.decompress(path.read_bytes()),raw)
            with self.assertRaises(AssertionError):n.save_bytes(path,b'different bytes')

    def test_other_native_identifiers_are_used_for_duplicate_checks(self):
        e=copy.deepcopy(self.entity)
        e['claims']['P6002']=[{'rank':'normal','mainsnak':{'datavalue':{'value':'artist/exact-artwork'}}}]
        e['claims']['P1679']=[{'rank':'normal','mainsnak':{'datavalue':{'value':'specific-artwork-123'}}}]
        self.assertIn('https://www.wikiart.org/en/artist/exact-artwork',n.native_urls(e))
        self.assertIn('https://artuk.org/discover/artworks/specific-artwork-123',n.native_urls(e))
        e['claims']['P6002'][0]['mainsnak']['datavalue']['value']='artist-profile-only'
        self.assertNotIn('https://www.wikiart.org/en/artist-profile-only',n.native_urls(e))

    def test_capped_museum_index_continues_without_repeating_prior_ids(self):
        cursor,reason=n.next_cursor([dict(capped=True,selected_ids=['Q100','Q20','Q9'])])
        self.assertIsNone(reason);self.assertEqual(cursor,'Q9')
        query=n.index_query('Q301250',100,cursor)
        self.assertIn('FILTER(STR(?work) > "http://www.wikidata.org/entity/Q9")',query)
        self.assertIn('ORDER BY STR(?work) LIMIT 100',query)

    def test_exhausted_and_budgeted_source_pages_remain_explicitly_unresolved(self):
        self.assertEqual(n.next_cursor([dict(capped=False,selected_ids=['Q1'])]),(None,'source_index_exhausted'))
        self.assertEqual(n.next_cursor([dict(capped=True,selected_ids=['Q1'])]*5),(None,'five_bounded_metadata_pages_reviewed'))

    def test_cross_campaign_names_do_not_rewind_the_museum_cursor(self):
        old=n.ROOT
        try:
            with tempfile.TemporaryDirectory(prefix='artline-index-proof-',dir='/tmp')as folder:
                n.ROOT=Path(folder)
                for name,depth,ids in [('z-old',1,['Q10']),('a-new-priority',2,['Q20'])]:
                    n.c.save(n.ROOT/name/'index-evidence.json.gz',dict(evidence=[dict(museum={'id':'museum'},page_number=depth,receipt={'retrieved_at':'2026-10-07T00:00:00Z'},selected_ids=ids,capped=True)]))
                self.assertEqual(n.next_cursor(n.index_history()['museum']),('Q20',None))
        finally:n.ROOT=old


if __name__=='__main__':unittest.main()
