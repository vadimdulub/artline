"""Pure checks for identity/custody decisions; never connect to a database."""
import copy
import importlib.util
from pathlib import Path
import unittest


def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(filename))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


t=module('t','research-artwork-location-tate-current-20261005e.py')
d=module('d','refine-artwork-location-deposit-recipients-20261005e.py')
im=module('im','research-museum-image-sources-20261005e.py')
guides=module('guides','write-museum-guides-20261005.py')


class TateChecks(unittest.TestCase):
    def setUp(self):
        self.old=next(v for v in t.selected()if v['object_evidence']['accession_number']=='A00702')
        self.obj=t.r.load(t.r.RUN/'tate-current-objects-20261005e/A00702.json.gz')['data']['items'][0]

    def test_exact_current_match(self):
        self.assertEqual(t.decide(self.old,self.obj),[])

    def test_different_accession_never_matches(self):
        self.obj['acno']='A00703';self.assertEqual(t.decide(self.old,self.obj),['accession_identity_conflict'])

    def test_loan_and_joint_collection_require_review(self):
        self.obj['isLoanedOut']=True;self.obj['collection']='ARTIST ROOMS'
        self.assertIn('currently_marked_loaned_out',t.decide(self.old,self.obj))
        self.assertIn('joint_or_other_collection_requires_review',t.decide(self.old,self.obj))

    def test_title_attribution_and_date_changes_survive(self):
        self.obj['title']='Different painting';self.obj['contributors'][0]['role_display']='after';self.obj['dateText']='1840'
        self.assertEqual(set(t.decide(self.old,self.obj)),{'title_requires_reconciliation','qualified_or_multiple_creator_relationships','source_date_wording_changed'})


class DepositChecks(unittest.TestCase):
    def setUp(self):
        cs=d.r.load(d.r.RUN/'primary-plans/deposit-recipients-20261005e.json.gz')['claims']
        self.c=next(v for v in cs if v['object_evidence']['current_object_record']['Code_Museofile']=='M5025')
        self.obj=copy.deepcopy(self.c['object_evidence']['current_object_record'])
        self.reg=d.r.load(d.r.RUN/'museofile-current-20261005b.json.gz')['rows']
        self.authority=next(v for v in self.reg if v['Identifiant']=='M5025')

    def test_armee_recipient_is_explicit(self):
        result=d.decision(self.obj,self.authority,self.reg)
        self.assertEqual(result['basis'],'unique_armee_recipient_name_with_explicit_paris_conservation_place')
        self.assertTrue(result['ownership_is_not_inferred'])

    def test_duplicate_authority_or_different_location_rejected(self):
        self.assertIsNone(d.decision(self.obj,self.authority,self.reg+[self.authority]))
        self.obj['Localisation']='Versailles;Questure du Sénat'
        self.assertIsNone(d.decision(self.obj,self.authority,self.reg))

    def test_private_owner_does_not_become_museum_owner(self):
        self.obj['Statut_juridique']='propriété privée'
        result=d.decision(self.obj,self.authority,self.reg)
        self.assertEqual(result['original_legal_status'],'propriété privée')
        self.assertTrue(result['ownership_is_not_inferred'])

    def test_restitution_usufruct_missing_or_qualified_work_rejected(self):
        for key,value in [('Statut_juridique','donation sous réserve usufruit'),('MANQUANT','oui'),('Auteur','atelier de David'),('Lieu_de_depot','dépôt;musée de l’Armée;retour')]:
            with self.subTest(key=key):
                obj={**self.obj,key:value};self.assertIsNone(d.decision(obj,self.authority,self.reg))


class ImageSourceChecks(unittest.TestCase):
    def test_known_broken_asset_uses_evidenced_source_instead(self):
        work={'id':'work1','source_url':'https://example.test/object/1','identifiers':[],
            'media':{'id':'broken','storage_kind':'local','storage_path':'/assets/broken.jpg'}}
        sources={im.canonical(work['source_url']):{'kind':'direct_catalogue_image','image_url':'https://example.test/image.jpg'}}
        guides.UNAVAILABLE_MEDIA={'broken'}
        try:
            kind,obj=guides.image_match(work,sources,{})
            self.assertEqual(kind,'direct_catalogue_image');self.assertEqual(obj['image_url'],'https://example.test/image.jpg')
            self.assertEqual(guides.image_match(work,{},{}),('image_research_pending',None))
        finally:guides.UNAVAILABLE_MEDIA=set()

    def test_known_url_aliases_only(self):
        self.assertEqual(im.canonical('https://www.pop.culture.gouv.fr/notice/joconde/123/'),im.canonical('https://pop.culture.gouv.fr/notice/joconde/123'))
        self.assertEqual(im.canonical('https://collections.louvre.fr/en/ark%3A/53355/cl010061984.json'),im.canonical('https://collections.louvre.fr/ark:/53355/cl010061984'))
        self.assertNotEqual(im.canonical('https://x.test/123'),im.canonical('https://x.test/124'))
        self.assertIsNone(im.canonical('javascript:alert(1)'))

    def test_direct_image_wins_without_overriding_rights(self):
        index={};rc={'retrieved_at':'2026-10-05T10:00:00Z'}
        im.add(index,'https://x.test/1',rc,'direct_catalogue_image','https://x.test/1.jpg',rights='restricted')
        im.add(index,'https://x.test/1',{'retrieved_at':'2026-10-06T10:00:00Z'},'catalogue_reports_image')
        obj=next(iter(index.values()));self.assertEqual(obj['kind'],'direct_catalogue_image');self.assertEqual(obj['source_rights'],'restricted')
        self.assertTrue(obj['no_image_downloaded'])


if __name__=='__main__':unittest.main()
