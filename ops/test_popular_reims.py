"""Synthetic tests only: exact Reims photo rights, accession and rendition boundaries."""
import importlib.util
import io
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
s=importlib.util.spec_from_file_location('reims',Path(__file__).with_name('popular-reims-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit-overnight-local-images.py'));audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
PAGE=m.HOST+'/oeuvre/synthetic-painting'
HTML=f'''<div class="oeuvre-fiche-partielle"><h1>Synthetic painting</h1>
<section class="informations-creation"><span class="auteur">Example Painter</span></section>
<section class="informations-generales"><a class="musee" href="fr/musees/musee-des-beaux-arts/">Musée des Beaux-Arts</a> (inv. 123.4.5)</section></div>
<div class="oeuvre-fiche-image"><a class="oeuvre-image-1" data-src="local/cache-vignettes/L1024xH800/abc-def.jpg?123"><img src="local/cache-vignettes/L1024xH800/abc-def.jpg?123"><span class="oeuvre-credits">Domaine public Photo : Example Photographer</span></a></div>
<div id="fiche-complete"><dl><dt>Titre</dt><dd>Synthetic painting</dd></dl><dl><dt>peintre</dt><dd><a><strong>Example Painter</strong></a><a href="?ZoneCreation-EpoqueDatation=synthetic">1800</a></dd></dl>
<dl><dt>Domaine</dt><dd>peinture</dd></dl><dl><dt>Libellé</dt><dd>Oil on canvas</dd></dl><dl><dt>Numéro d'inventaire</dt><dd>123.4.5</dd></dl></div>
<div id="telecharger"><button class="image-hd-card" data-oeuvre="123.4.5" data-numinventaire="(inv. 123.4.5)" data-droits="Example Photographer" data-musee="Musée des Beaux-Arts" data-oeuvreauteur="Painter Example" data-oeuvretitre="Synthetic painting" data-image="IMG/base/multimedia-hd/MBA/123.4.5.P.01.jpg" data-vignette="local/cache-vignettes/L128xH160/123.4.5.P.01-abc12.jpg?123" data-notice="synthetic"><img src="local/cache-vignettes/L160xH200/123.4.5.P.01-def34.jpg?456"></button><p class="licence-ouverte"><a href="{m.LICENSE}">CC BY</a></p></div>'''

class ReimsRights(unittest.TestCase):
 def parse(self,html=HTML):return m.parse_object(html,PAGE)
 def test_explicit_exact_photo_and_ported_license(self):
  o=self.parse();self.assertEqual(o['licence_uri'],m.LICENSE);self.assertEqual(o['photographer'],'Example Photographer');self.assertTrue(audit.allowed(m.LICENSE))
 def test_nc_or_nd_not_approved(self):
  for x in ('by-nc','by-nd','by-nc-sa'):
   uri=m.LICENSE.replace('/by/', '/'+x+'/');self.assertFalse(audit.allowed(uri))
   with self.assertRaises(ValueError):self.parse(HTML.replace(m.LICENSE,uri))
 def test_unknown_jurisdiction_not_silently_accepted(self):self.assertFalse(audit.allowed(m.LICENSE.replace('/fr/','/invalid/')))
 def test_another_hd_accession_rejected(self):
  with self.assertRaisesRegex(ValueError,'accession'):self.parse(HTML.replace('MBA/123.4.5.P','MBA/987.6.5.P'))
 def test_wrong_preview_view_rejected(self):
  with self.assertRaisesRegex(ValueError,'preview'):self.parse(HTML.replace('L160xH200/123.4.5.P.01','L160xH200/123.4.5.P.02'))
 def test_different_photographer_rejected(self):
  with self.assertRaisesRegex(ValueError,'credit'):self.parse(HTML.replace('data-droits="Example Photographer"','data-droits="Other Photographer"'))
 def test_explicit_nc_restriction_rejected(self):
  with self.assertRaises(ValueError):self.parse(HTML.replace('Domaine public Photo','Non-commercial Photo'))
 def test_download_extra_restriction_rejected(self):
  with self.assertRaises(ValueError):self.parse(HTML.replace('CC BY</a>','CC BY</a> non-commercial only'))
 def test_metadata_license_does_not_clear_photo(self):
  with self.assertRaises(ValueError):self.parse(HTML.replace('licence-ouverte','metadata-license'))
 def test_missing_download_is_held(self):
  with self.assertRaises(ValueError):self.parse(HTML.replace('image-hd-card','unlicensed-card'))
 def test_other_host_is_held(self):
  with self.assertRaises(ValueError):self.parse(HTML.replace('local/cache-vignettes/L1024','https://example.com/local/cache-vignettes/L1024'))
 def test_photo_classification_rejected(self):
  with self.assertRaises(ValueError):self.parse(HTML.replace('<dd>peinture</dd>','<dd>photographie</dd>'))
 def test_old_spaced_filename_retains_exact_identity(self):
  o=self.parse(HTML.replace('123.4.5.P.01','123.4.5.P (1)'));self.assertIn('P (1)',o['licensed_hd_url'])
 def test_explicit_date_range_with_html_whitespace(self):
  html=HTML.replace('>1800</a>', '>entre 1850</a><a href="?ZoneCreation-EpoqueDatation=second">et \n\t1860</a>')
  o=self.parse(html);self.assertEqual((o['year_start'],o['year_end']),(1850,1860))
 def test_movement_does_not_become_date(self):
  html=HTML.replace('>1800</a>', '>1800</a><a href="?ZoneCreation-EpoqueDatation=movement">Orientalisme</a>')
  self.assertEqual(self.parse(html)['year_start'],1800)
 def test_metadata_only_parse_never_claims_image_rights(self):
  o=m.parse_object(HTML.replace('image-hd-card','unlicensed'),PAGE,media_rights=False)
  self.assertNotIn('licence_uri',o);self.assertNotIn('image_url',o)

class Renditions(unittest.TestCase):
 def picture(self):
  a=Image.new('RGB',(800,600),'white');d=ImageDraw.Draw(a);d.rectangle((10,60,330,500),fill='blue');d.ellipse((370,100,650,400),fill='orange');return a
 def data(self,a):
  b=io.BytesIO();a.save(b,'JPEG');return b.getvalue()
 def test_same_photo_resized_matches(self):
  a=self.picture();b=a.resize((160,120));self.assertTrue(m.compare_renditions(self.data(a),self.data(b))['verified'])
 def test_other_picture_does_not_match(self):
  with self.assertRaises(ValueError):m.compare_renditions(self.data(self.picture()),self.data(Image.new('RGB',(160,120),'green')))
 def test_crop_does_not_match(self):
  a=self.picture()
  with self.assertRaises(ValueError):m.compare_renditions(self.data(a),self.data(a.crop((300,0,800,600))))

if __name__=='__main__':unittest.main()
