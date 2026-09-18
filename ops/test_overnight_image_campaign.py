"""Synthetic safety tests; never connect to any catalogue database."""
import copy,importlib.util,json,tempfile,unittest
from unittest import mock
from pathlib import Path

def module(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
campaign=module('night_campaign','overnight-image-campaign.py')
commons=module('night_commons','overnight-commons-images.py')
fng=module('night_fng','overnight-fng-images.py')
rijks=module('night_rijks','overnight-rijks-images.py')
saam=module('night_saam','overnight-saam-images.py')
nga=module('night_nga','overnight-nga-commons.py')
met_new=module('night_met_new','research-overnight-met-selection.py')
met_import=module('night_met_import','import-overnight-met-selection.py')

class SafetyTests(unittest.TestCase):
    def test_known_source_image_conflict_fails_closed(self):
        core=campaign.core;im={'provider':'synthetic','external_id':'1','source_image_url':'https://example.invalid/wrong.jpg'}
        with mock.patch.object(core,'KNOWN_SOURCE_IMAGE_CONFLICTS',{('synthetic','1','https://example.invalid/wrong.jpg')}):
            with self.assertRaisesRegex(ValueError,'different artwork'):core.validate_source_image_identity(im)
            core.validate_source_image_identity(dict(im,source_image_url='https://example.invalid/correct.jpg'))
    def test_new_met_duplicate_checks_cover_holding_and_source_aliases(self):
        c={'artwork_id':'new-work','slug':'new-work','artist_qid':'Q123','artist_slug':'synthetic-artist','accession_number':'A.1','title':'Synthetic work','external_id':'42','qid':None,'page':'https://www.metmuseum.org/art/collection/search/42'}
        state={'institution_id':'museum','artists':{'Q123':[{'id':'artist','slug':'synthetic-artist','status':'review'}]},'works':[],'identifiers':[],'redirects':[]}
        self.assertEqual(len(met_import.conflicts([c],state)[0]),1)
        old={'id':'old-work','current_institution_id':None,'museum_holding':True,'accession_number':'A.1','artist_ids':[],'title':'Different title'}
        self.assertIn('accession',met_import.conflicts([c],dict(state,works=[old]))[1][0]['reason'])
        identifier={'entity_id':'old-work','scheme':'european-met-the-met-object','external_id':'42','canonical_url':None}
        self.assertIn('identifier',met_import.conflicts([c],dict(state,identifiers=[identifier]))[1][0]['reason'])
        old.update(accession_number='B.2',artist_ids=['artist'],title='Synthetic work')
        self.assertIn('Same-artist',met_import.conflicts([c],dict(state,works=[old]))[1][0]['reason'])
        self.assertEqual(len(met_import.conflicts([c,dict(c,artwork_id='other-work',external_id='43')],state)[0]),1)

    def test_new_met_dates_preserve_uncertainty_and_reject_unknowns(self):
        base={'objectBeginDate':1845,'objectEndDate':1855,'objectDate':'ca.1850'}
        self.assertEqual(met_new.date_fields(base)['date_precision'],'circa_range')
        self.assertEqual(met_new.date_fields(dict(base,objectDate='19th century'))['date_precision'],'century')
        self.assertEqual(met_new.date_fields({'objectBeginDate':1850,'objectEndDate':1850,'objectDate':'April 24, 1850'})['date_precision'],'exact')
        self.assertEqual(met_new.date_fields({'objectBeginDate':1850,'objectEndDate':1850,'objectDate':'[1850]'})['date_precision'],'circa')
        for text in ('1850, later edition','1850 or slightly earlier','1850 (published 1980)'):
            with self.assertRaises(ValueError):met_new.date_fields({'objectBeginDate':1850,'objectEndDate':1850,'objectDate':text})
        for text in ('undated','before 1850','after 1850','1850'):
            with self.assertRaises(ValueError):met_new.date_fields(dict(base,objectDate=text))
        with self.assertRaisesRegex(ValueError,'lifespan'):
            met_new.date_fields(dict(base,objectDate='1845–1855',artistBeginDate='1845',artistEndDate='1855'))
    def test_hidden_wikidata_export_text_is_not_an_artwork_title(self):
        html='<div class="fn"><div lang="en"><i>Synthetic title<span class="noprint">Edit</span></i></div><div style="display: none;">label QS:Len,"Synthetic title"</div></div>'
        self.assertEqual(nga.visible_title_variants(html),{'synthetic title'})
        self.assertNotIn('wrong title',nga.visible_title_variants('<i>Correct title</i><div hidden>Wrong title</div>'))
    def test_download_cooldown_is_preserved_when_work_is_deferred(self):
        core=campaign.core;f=core.Fetcher(Path('/tmp/artline-synthetic-cache-unused'));f.defer_long_cooldowns=True
        response=mock.Mock(status_code=429,headers={'Retry-After':'300'})
        with mock.patch.object(f.session,'get',return_value=response),mock.patch.object(core,'provider_rate_slot') as rate,mock.patch.object(core.time,'sleep'):
            with self.assertRaises(core.SourceCooldown):f.get('https://upload.wikimedia.org/synthetic-image')
            rate.assert_any_call('upload.wikimedia.org',cooldown=300.0)
    def test_resume_uses_latest_explicit_checkpoint(self):
        with tempfile.TemporaryDirectory(prefix='artline-synthetic-resume-') as tmp:
            run=Path(tmp)
            events=[{'artwork_id':'synthetic-one','outcome':'failed'},
                    {'artwork_id':'synthetic-two','outcome':'complete'},
                    {'artwork_id':'synthetic-one','outcome':'retry_after_cloud_login_expiry'}]
            (run/'events.jsonl').write_text('\n'.join(json.dumps(x) for x in events)+'\n{interrupted')
            latest=campaign.core.latest_events(run)
            self.assertEqual(latest['synthetic-one']['outcome'],'retry_after_cloud_login_expiry')
            self.assertEqual(latest['synthetic-two']['outcome'],'complete')
    def test_missing_explicit_pdm_uri_fails_closed(self):
        page={'pageid':1,'imageinfo':[{'extmetadata':{'LicenseShortName':{'value':'Public domain'},'Copyrighted':{'value':'False'}}}]}
        with self.assertRaisesRegex(ValueError,'public-domain URI'):
            commons.rights_and_identity({}, {}, page, {})
    def test_approved_human_readable_uri(self):
        self.assertEqual(commons.canonical_licence_uri('http://creativecommons.org/publicdomain/zero/1.0/deed.en'),commons.CC0)
        self.assertEqual(commons.canonical_licence_uri('https://creativecommons.org/licenses/by-sa/4.0/legalcode'), 'https://creativecommons.org/licenses/by-sa/4.0/')
    def test_unapproved_uris_are_not_reclassified(self):
        for bad in ['https://evil.example/publicdomain/zero/1.0/','https://creativecommons.org/licenses/by-nc/4.0/','https://creativecommons.org/publicdomain/zero/1.0deed.en']:
            self.assertEqual(commons.canonical_licence_uri(bad),bad)
    def test_painting_scope_requires_source_type(self):
        c={'work_type':'painting','creation_year_start':1500,'creation_year_end':1510}
        good={'objectName':'Painting','objectBeginDate':1500,'objectEndDate':1505}
        self.assertEqual(campaign.fresh_scope('met',good,c)['source_year_end'],1505)
        for change in [{'objectName':'Print'},{'objectEndDate':1971},{'objectEndDate':None},{'objectBeginDate':1600,'objectEndDate':1600}]:
            with self.assertRaises(ValueError):campaign.fresh_scope('met',dict(good,**change),c)
    def test_existing_print_is_classified_separately(self):
        c={'work_type':'print','creation_year_start':1500,'creation_year_end':1510}
        self.assertEqual(campaign.fresh_scope('met',{'objectName':'Print','objectBeginDate':1500,'objectEndDate':1505},c)['source_classification'],'print ')
    def test_commons_structured_data_is_checked(self):
        snak={'rank':'normal','mainsnak':{'snaktype':'value','datavalue':{'value':{'id':'Q123'}}}}
        self.assertEqual(commons.ids({'statements':{'P275':[snak]}},'P275'),{'Q123'})
    def test_fng_identity_and_rights(self):
        c={'external_id':'10','title':'Synthetic painting','accession_number':'A 1','fng_people':['20'],'roles':['primary'],
          'creation_year_start':1850,'creation_year_end':1850,'date_precision':'exact'}
        o={'objectId':10,'responsibleOrganisation':'Kansallisgalleria / Ateneumin taidemuseo','owner':'Suomen valtio',
          'category':{'categoryId':'artwork'},'classifications':[{'en':'painting'}],'title':{'en':'Synthetic painting'},
          'inventoryNumber':'A 1','people':[{'id':20,'role':{'en':'Artist'},'attribution':None}],
          'yearFrom':1850,'multimedia':[{'license':'CC0','isRiaDisplayImage':True,'jpg':{'1000':'/media-assets/1/jpg/1000/30.jpg'}}]}
        self.assertTrue(fng.source_match(c,o)[1].startswith('https://kokoelma.kansallisgalleria.fi/'))
        variants=[{'objectId':11},{'owner':'Private owner'},{'yearFrom':1971},{'children':[11]},
          {'datePrefix':{'en':'at the latest'}},{'multimedia':[{'license':'CC BY-NC','isRiaDisplayImage':True}]},
          {'people':[{'id':21,'role':{'en':'Artist'}}]}]
        for change in variants:
            with self.assertRaises(ValueError):fng.source_match(c,dict(copy.deepcopy(o),**change))
        drawing=dict(c,work_type='drawing')
        with self.assertRaises(ValueError):fng.source_match(drawing,o)
        self.assertTrue(fng.source_match(drawing,dict(o,classifications=[{'en':'drawing'}])))
        generic_print=dict(c,work_type='print')
        with self.assertRaises(ValueError):fng.source_match(generic_print,dict(o,classifications=[{'en':'graphic arts'}]))
        self.assertTrue(fng.source_match(generic_print,dict(o,classifications=[{'en':'graphic arts'}],materials=[{'en':'monotype'}])))

    def test_rijks_exact_source_identity_and_metadata_terms(self):
        c={'external_id':'10','title':'Synthetic painting','accession_number':'SK-A-1','rijks_people':['20'],'roles':['primary'],'creation_year_start':1850,'creation_year_end':1850}
        o={'id':'https://id.rijksmuseum.nl/10','type':'HumanMadeObject','classified_as':[{'equivalent':[{'id':'http://vocab.getty.edu/aat/300033618'}]}],
          'identified_by':[{'type':'Name','content':'Synthetic painting'},{'type':'Identifier','content':'SK-A-1','classified_as':[{'id':'http://vocab.getty.edu/aat/300312355'}]}],
          'produced_by':{'part':[{'carried_out_by':[{'type':'Person','id':'https://id.rijksmuseum.nl/20'}]}],
            'timespan':{'begin_of_the_begin':'1850-01-01','end_of_the_end':'1850-12-31','identified_by':[{'type':'Name','content':'1850'}]}},
          'subject_of':[{'id':'https://data.rijksmuseum.nl/10','subject_to':[{'classified_as':[{'id':rijks.CC0}]}]}]}
        self.assertEqual(rijks.source_match(c,o)['source_year_end'],1850)
        for change in [{'id':'https://id.rijksmuseum.nl/11'},{'subject_of':[]},{'classified_as':[]}]:
            with self.assertRaises(ValueError):rijks.source_match(c,dict(copy.deepcopy(o),**change))
        wrong=copy.deepcopy(o);wrong['produced_by']['part'][0]['carried_out_by'][0]['id']='https://id.rijksmuseum.nl/21'
        with self.assertRaises(ValueError):rijks.source_match(c,wrong)
    def test_saam_media_cc0_is_required_separately(self):
        c={'external_id':'10','title':'Synthetic painting','accession_number':'A1','artist':'Example Painter','aliases':[],'roles':['primary'],'creation_year_start':1850,'creation_year_end':1850,'date_precision':'exact'}
        dnr={'record_link':'https://americanart.si.edu/collections/search/artwork/?id=10','data_source':'Smithsonian American Art Museum','metadata_usage':{'access':'CC0'},'title':{'content':'Synthetic painting'},
          'online_media':{'media':[{'type':'Images','usage':{'access':'CC0'},'idsId':'SAAM-A1','content':'https://ids.si.edu/ids/deliveryService?id=SAAM-A1'}]}}
        ft={}
        for name,label,value in [('objectType','Type','Painting'),('identifier','Object number','A1'),('name','Artist','Example Painter'),('date','Date','1850'),('objectRights','Restrictions & Rights','CC0'),('setName','See more items in','Smithsonian American Art Museum Collection')]:ft[name]=[{'label':label,'content':value}]
        o={'unitCode':'SAAM','content':{'descriptiveNonRepeating':dnr,'freetext':ft}}
        self.assertEqual(saam.source_match(c,o)[2]['source_year_end'],1850)
        for source_type,kind in [('Painting-Miniature','painting'),('Drawing','drawing'),('Graphic Arts-Print','print')]:
            variant=copy.deepcopy(o);variant['content']['freetext']['objectType'][0]['content']=source_type
            self.assertEqual(saam.source_match(dict(c,work_type=kind),variant)[2]['source_year_end'],1850)
            with self.assertRaises(ValueError):saam.source_match(dict(c,work_type='photography'),variant)
        for license in ['Unknown','CC BY-NC','']:
            wrong=copy.deepcopy(o);wrong['content']['descriptiveNonRepeating']['online_media']['media'][0]['usage']['access']=license
            with self.assertRaises(ValueError):saam.source_match(c,wrong)
        wrong=copy.deepcopy(o);wrong['content']['freetext']['objectRights'][0]['content']='Copyright retained'
        with self.assertRaises(ValueError):saam.source_match(c,wrong)

if __name__=='__main__':unittest.main()
