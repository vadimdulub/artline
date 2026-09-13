"""Offline checks for identity and image rights on donated museum files."""
import html
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('recovery', Path(__file__).with_name('recover-met-commons-images.py'))
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class CommonsRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {'external_id':'123', 'title':'An Artwork', 'artist':'A Painter'}
        self.xml = '''<row><Object_ID>123</Object_ID><Link_Resource>http://www.metmuseum.org/art/collection/search/123</Link_Resource>
          <Title>An Artwork</Title><Artist_Display_Name>A Painter</Artist_Display_Name>
          <Is_Public_Domain>True</Is_Public_Domain><Rights_and_Reproduction/>
          <Object_Begin_Date>1800</Object_Begin_Date><Object_End_Date>1810</Object_End_Date>
          <Image_Url>http://images.metmuseum.org/CRDImages/ep/original/example.jpg</Image_Url>
          <Filename>An Artwork MET example</Filename></row>'''

    def response(self, xml=None):
        return {'query':{'pages':{'1':{'ns':6, 'title':'File:An Artwork MET example.jpg',
          'revisions':[{'revid':42, 'slots':{'main':{'*':'<metadata_raw>' + html.escape(xml or self.xml) + '</metadata_raw>'}}}],
          'imageinfo':[{'url':'https://upload.wikimedia.org/wikipedia/commons/a/ab/example.jpg',
            'descriptionurl':'https://commons.wikimedia.org/wiki/File:An_Artwork_MET_example.jpg',
            'mime':'image/jpeg','size':1000,'sha1':'example', 'extmetadata':{
              'License':{'value':'cc0'},'LicenseShortName':{'value':'CC0'},
              'LicenseUrl':{'value':'http://creativecommons.org/publicdomain/zero/1.0/deed.en'}}}]}}}}

    def test_exact_donated_object_and_current_file_cc0_are_accepted(self):
        image = recovery.identity_and_rights(self.candidate, self.response())
        self.assertEqual(image['donor_object_id'], '123')
        self.assertEqual(image['rights_status'], 'cc0')
        self.assertEqual(image['donor_creation_end'], 1810)

    def test_metadata_identity_title_and_creation_conflicts_are_rejected(self):
        for before, after in [('>123<','>124<'),('/search/123','/search/1234'),
                              ('>An Artwork<','>Another Artwork<'),('>1810<','>1971<'),
                              ('>An Artwork MET example<','>Other MET file<'),
                              ('<Is_Public_Domain>True','<Is_Public_Domain>False')]:
            with self.subTest(before=before), self.assertRaises(ValueError):
                recovery.identity_and_rights(self.candidate,self.response(self.xml.replace(before,after)))

    def test_file_license_and_restrictions_are_required_even_with_open_museum_metadata(self):
        for key, value in [('License','cc-by-sa-4.0'),('LicenseUrl','https://example.org'),
                           ('Restrictions','Permission required')]:
            response = self.response()
            response['query']['pages']['1']['imageinfo'][0]['extmetadata'][key] = {'value':value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                recovery.identity_and_rights(self.candidate,response)


if __name__ == '__main__':
    unittest.main()
