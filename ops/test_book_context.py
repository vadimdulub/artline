import unittest
from book_context import excerpt,overview,LICENSE

class ContextTests(unittest.TestCase):
    def test_wrong_work_redirect_is_not_a_biography(self):
        value,state=overview({'page':{'pageprops':{'wikibase_item':'Q2'}}},'Q1','creator')
        self.assertIsNone(value);self.assertEqual(state,'page_identity_mismatch')
    def test_preserves_complete_sentences_and_paragraphs(self):
        text='The book examines memory and responsibility.\nIts narrator returns home after a long absence.'
        self.assertEqual(excerpt(text,'book'),text.splitlines())
    def test_does_not_cut_an_unfinished_claim(self):
        first='A short complete sentence.'
        self.assertEqual(excerpt(first+' '+('word '*230)+'.','book'),[first])
    def test_retains_source_revision_and_license(self):
        capture={'page':{'title':'Example','pageprops':{'wikibase_item':'Q1'},'revisions':[{'revid':99}],'extract':'This work follows a family across several generations. Its story examines memory, inheritance and responsibility.'}}
        value,state=overview(capture,'Q1','book')
        self.assertEqual(state,'sourced_introduction');self.assertTrue(value['sourceUrl'].endswith('oldid=99'));self.assertEqual(value['licenseUrl'],LICENSE)
    def test_no_invented_context_for_missing_source(self):
        self.assertEqual(overview({'page':{'pageprops':{'wikibase_item':'Q1'}}},'Q1','book')[1],'insufficient_introductory_text')

if __name__=='__main__':unittest.main()
