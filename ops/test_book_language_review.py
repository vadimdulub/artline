import unittest
from book_language_review import parse_field,wikipedia_language,claim_language_ids

ALIASES={'english':'Q1860','french':'Q150','german':'Q188','russian':'Q7737','arabic':'Q13955'}
def capture(text,q='Q1'):
    return {'page':{'title':'A book','pageid':1,'pageprops':{'wikibase_item':q},'revisions':[{'revid':10,'slots':{'main':{'content':text}}}]}}
class LanguageEvidenceTests(unittest.TestCase):
    def test_language_of_website_and_original_title_are_not_composition_evidence(self):
        result=wikipedia_language(capture('{{Infobox book|orig_lang_code=de|title=Das Buch}}'),'Q1',ALIASES)
        self.assertEqual(result['state'],'missing_language_field')
    def test_explicit_field_with_reference(self):
        result=wikipedia_language(capture('{{Infobox book|language=[[German language|German]]<ref>{{cite book|language=English}}</ref>}}'),'Q1',ALIASES)
        self.assertEqual(result['languages'],['Q188'])
    def test_genuine_multilingual_field_preserved(self):
        result=parse_field('{{ubl|[[Russian language|Russian]]|French}}',ALIASES)
        self.assertEqual(result['languages'],['Q150','Q7737']);self.assertFalse(result['unresolved'])
    def test_qualified_partial_language_requires_review(self):
        result=wikipedia_language(capture('{{Infobox book|language=Russian, with some French}}'),'Q1',ALIASES)
        self.assertEqual(result['state'],'qualified_or_unmapped_language');self.assertEqual(result['languages'],[])
    def test_original_and_translated_are_not_blindly_combined(self):
        result=parse_field('Arabic (original)<br>English (translation)',ALIASES)
        self.assertEqual(result['languages'],[]);self.assertTrue(result['unresolved'])
    def test_redirect_to_another_work_rejected(self):
        result=wikipedia_language(capture('{{Infobox book|language=English}}','Q2'),'Q1',ALIASES)
        self.assertEqual(result['state'],'page_identity_mismatch')
    def test_multiple_edition_infoboxes_held(self):
        result=wikipedia_language(capture('{{Infobox book|language=English}}\n{{Infobox book|language=French}}'),'Q1',ALIASES)
        self.assertEqual(result['state'],'conflicting_infobox_languages')
    def test_claim_ranks(self):
        def claim(q,rank):return {'rank':rank,'mainsnak':{'snaktype':'value','datavalue':{'value':{'id':q}}}}
        self.assertEqual(claim_language_ids({'claims':{'P407':[claim('Q150','normal'),claim('Q188','preferred'),claim('Q1860','deprecated')]}}),['Q188'])

if __name__=='__main__':unittest.main()
