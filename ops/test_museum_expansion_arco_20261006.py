"""Offline tests against preserved primary metadata; no database connections."""
import copy
import gzip
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('arco',Path(__file__).with_name('museum-expansion-arco-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class ArcoPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=a.m.load(a.RUN/'probe.json');cls.scope=p['scope']
        cls.uri='https://w3id.org/arco/resource/HistoricOrArtisticProperty/1100034601'
        cls.triples=[r for r in p['graphs']['rows'] if r['root']==cls.uri]
        for path in (a.RUN/'pages').glob('*.json'):
            record=a.m.load(path)
            if record['receipt']['url'].endswith('/1100034601'):
                cls.fields=a.fields(gzip.decompress((a.m.ROOT/record['body_path']).read_bytes()));break

    def test_object_specific_metadata_and_missing_inventory(self):
        f,why=a.facts(self.triples,self.uri,self.scope,self.fields)
        self.assertIsNone(why);self.assertEqual((f['first'],f['last']),(1835,1835))
        self.assertEqual(f['creator_label'],'Bonarelli Godeardo (1806/ 1895)')
        self.assertIsNone(f['accession']);self.assertIn('Ancona',self.fields['INDIRIZZO'])

    def test_uncertain_cross_cutoff_and_reversed_dates_held(self):
        self.assertEqual(a.numeric_date('1960 - 1970'),(1960,1970,'range'))
        for date in ['post 1900 - 1900','1900 (?) - 1900','1960 - 1980','1835 - 1834','sec. XIX','']:
            with self.subTest(date=date):self.assertIsNone(a.numeric_date(date))

    def test_source_circa_qualifiers_and_finite_open_bounds_are_preserved(self):
        self.assertEqual(a.numeric_date('ca 1600-ca 1610'),(1600,1610,'circa_range'))
        self.assertEqual(a.numeric_date('1600 ca - 1610 ca'),(1600,1610,'circa_range'))
        self.assertEqual(a.numeric_date('ca 1870 - 1870'),(1870,1870,'circa'))
        self.assertEqual(a.numeric_date('post 1900-ante 1902'),(1900,1902,'range'))
        self.assertEqual(a.numeric_date('1900 post - 1902 ante'),(1900,1902,'range'))
        self.assertEqual(a.numeric_date('1850'),(1850,1850,'exact'))
        for raw in ['post 1900-ante ','post 1900-ante 1900','ca 1970-1970','ca 1960-ca 1980','ca 1800 (?) - ca 1850']:
            with self.subTest(raw=raw):self.assertIsNone(a.numeric_date(raw))

    def test_museum_uri_alone_does_not_prove_same_city(self):
        scope=copy.deepcopy(self.scope);scope['authority']['catalogue_city']='Roma (RM)'
        self.assertEqual(a.graph_check(self.triples,self.uri,scope),'catalogue_city_conflict')

    def test_publication_date_cannot_replace_object_date(self):
        f=dict(self.fields,date='2006 - 2006')
        self.assertEqual(a.facts(self.triples,self.uri,self.scope,f)[1],'object_creation_qualification_or_cutoff_review')

    def test_different_source_identity_held(self):
        f=dict(self.fields);f['CODICE DI CATALOGO NAZIONALE']='another-work'
        self.assertEqual(a.facts(self.triples,self.uri,self.scope,f)[1],'html_graph_catalogue_identifier_conflict')

    def test_multiple_creation_phases_held(self):
        rows=self.triples+[dict(root=self.uri,s=self.uri,p=a.CD+'hasDating',o='https://example.test/second-date')]
        self.assertEqual(a.graph_check(rows,self.uri,self.scope),'multiple_creation_phases_require_review')

    def test_component_is_not_counted_as_another_whole_work(self):
        rows=self.triples+[dict(root=self.uri,s=self.uri,p=a.CORE+'isPartOf',o='https://example.test/whole')]
        self.assertEqual(a.graph_check(rows,self.uri,self.scope),'component_or_ensemble_requires_review')

    def test_shared_date_labels_cannot_override_object_date(self):
        rows=self.triples+[dict(root=self.uri,s='https://w3id.org/arco/resource/TimeInterval/1835-1835',p=a.LABEL,o='post 1835 (?)')]
        f,why=a.facts(rows,self.uri,self.scope,self.fields)
        self.assertIsNone(why);self.assertEqual(f['date_display'],'1835 - 1835')

    def test_linked_nodes_remain_scoped_to_their_object(self):
        roots=[dict(root='A',s='A',p=a.CD+'hasInventorySituation',o='invA'),dict(root='B',s='B',p=a.CD+'hasInventorySituation',o='invB')]
        children=[dict(s='invA',p=a.CD+'inventoryIdentifier',o='100'),dict(s='invB',p=a.CD+'inventoryIdentifier',o='200')]
        rows=a.join_graph_components(roots,children)
        self.assertEqual([r['o'] for r in rows if r['root']=='A' and r['p']==a.CD+'inventoryIdentifier'],['100'])
        self.assertEqual([r['o'] for r in rows if r['root']=='B' and r['p']==a.CD+'inventoryIdentifier'],['200'])

    def test_exact_subject_captures_preserve_object_location_links(self):
        uri=self.uri;location='https://w3id.org/arco/resource/TimeIndexedTypedLocation/1100034601-current'
        def component(subject,role):
            return dict(subject=subject,role=role,receipt={'request_form':{'query':a.subject_query(subject)}})
        parts=[(component(uri,'object_subject'),[dict(p=a.LOC+'hasTimeIndexedTypedLocation',o=location)]),
               (component(location,'linked_subject'),[dict(p=a.LOC+'hasLocationType',o=a.LOC+'CurrentPhysicalLocation')])]
        rows=a.join_subject_components(parts)
        self.assertEqual(rows[1],dict(root=uri,s=location,p=a.LOC+'hasLocationType',o=a.LOC+'CurrentPhysicalLocation'))
        tampered=copy.deepcopy(parts);tampered[1][0]['subject']=uri+'-other'
        with self.assertRaises(AssertionError):a.join_subject_components(tampered)

    def test_unlinked_subject_and_truncated_subject_response_are_rejected(self):
        other='https://w3id.org/arco/resource/InventorySituation/unrelated'
        def component(subject,role):
            return dict(subject=subject,role=role,receipt={'request_form':{'query':a.subject_query(subject)}})
        root=component(self.uri,'object_subject')
        with self.assertRaises(AssertionError):
            a.join_subject_components([(root,[dict(p=a.DC+'date',o='1835')]),
                (component(other,'linked_subject'),[dict(p=a.CD+'inventoryIdentifier',o='100')])])
        with self.assertRaises(AssertionError):a.join_subject_components([(root,[dict(p=a.DC+'date',o='1835')]*500)])

    def test_official_title_plus_subject_uses_same_object_fields(self):
        result=a.m.load(a.RUN/'rechecks/continuation-06/museums/arco-museum-3b3ed18c4cc4239dc480.json.gz')
        uri='https://w3id.org/arco/resource/HistoricOrArtisticProperty/1100141638'
        item=next(r for r in result['held'] if r.get('uri')==uri)
        scope=next(s for s in a.scopes() if s['museum']['slug']==result['museum']['slug'])
        triples=[]
        for path in (a.RUN/'graph-bundles-v2').glob('*.json.gz'):
            rows=a.m.load(path)['rows']
            triples=[r for r in rows if r['root']==uri]
            if triples:break
        self.assertTrue(triples)
        facts,reason=a.facts(triples,uri,scope,item['object_fields'])
        self.assertIsNone(reason)
        self.assertEqual(facts['title'],"Contadino su asinello. contadino in groppa all'asino")
        altered=dict(item['object_fields'],title='Contadino su asinello. different subject')
        self.assertEqual(a.facts(triples,uri,scope,altered)[1],'html_graph_title_conflict')


if __name__=='__main__':unittest.main()
