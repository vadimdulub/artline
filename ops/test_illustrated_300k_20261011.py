"""Offline safety boundaries for selected image enrichment; no DB fixtures."""
import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import requests
s=importlib.util.spec_from_file_location('images',Path(__file__).with_name('illustrated-300k-20261011.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
class ImageSelection(unittest.TestCase):
 def test_obstructed_source_band_requires_visual_review(self):
  from PIL import Image,ImageDraw
  im=Image.new('RGB',(400,600),'#ddddcc');ImageDraw.Draw(im).rectangle((0,400,399,599),fill='black')
  self.assertEqual(a.opaque_edge_bands(im),['bottom'])
  intact=Image.new('RGB',(400,600),'#ddddcc');ImageDraw.Draw(intact).rectangle((0,590,399,599),fill='black')
  self.assertEqual(a.opaque_edge_bands(intact),[])
 def row(self):
  return dict(artwork_id='test-object',native_id='123',provider='rijks',title='Painting',creator_label='Named maker',accession_number='SK-A-1',last=1800,image=dict(image_url='https://iiif.micr.io/AbCd/full/!1200,1200/0/default.jpg'),raw=dict(source_images=['https://iiif.micr.io/AbCd/full/max/0/default.jpg'],rights=['http://creativecommons.org/publicdomain/mark/1.0/'],page_receipt=dict(sha256='a'*64)))
 def test_exact_primary_frame_and_date_scope(self):
  r=self.row();im=a.native_image('rijks',r)
  self.assertIn('/full/!1200,1200/',im['image_url']);self.assertIsNone(a.native_image('rijks',dict(r,last=1956)))
  self.assertIsNone(a.native_image('rijks',dict(r,accession_number='RP-P-123 (VERSO)')))
 def test_ambiguous_images_and_wrong_hosts_are_held(self):
  r=self.row();r['raw']['source_images'].append('https://iiif.micr.io/Other/full/max/0/default.jpg');self.assertIsNone(a.native_image('rijks',r))
  r=self.row();r['raw']['source_images']=['https://unrelated.example/AbCd/full/max/0/default.jpg'];self.assertIsNone(a.native_image('rijks',r))
  r=self.row();r['raw']['rights']=[];self.assertIsNone(a.native_image('rijks',r))
 def test_nga_primary_image_must_depict_same_native_object(self):
  r=dict(self.row(),images=[dict(openaccess='1',viewtype='primary',depictstmsobjectid='999',iiifurl='https://api.nga.gov/iiif/id')])
  self.assertIsNone(a.native_image('nga',r))
 def test_visual_review_cannot_be_skipped_or_retargeted(self):
  with tempfile.TemporaryDirectory(prefix='artline-image-unit-') as temp,patch.object(a,'RUN',Path(temp)):
   f=a.folder('rijks-000');audit=dict(sample_ids=['a'],prepared_images=[dict(artwork_id='a',sha256='one')],identity_holds={})
   a.saved(f/'quality-audit.json',audit);a.saved(f/'visual-review.json',dict(batch_quality_decision='accept',decisions=[]))
   with self.assertRaises(AssertionError):a.accepted('rijks-000')
   (f/'visual-review.json').unlink();a.saved(f/'visual-review.json',dict(batch_quality_decision='accept',decisions=[dict(artwork_id='a',sha256='another',decision='accept')]))
   with self.assertRaises(AssertionError):a.accepted('rijks-000')
 def test_provider_hold_prevents_any_request(self):
  with tempfile.TemporaryDirectory(prefix='artline-image-unit-') as temp,patch.object(a,'RUN',Path(temp)/'run'),patch.object(a,'ORIG',Path(temp)/'originals'),patch.object(a,'session') as session:
   a.saved(a.RUN/'access-holds/iiif.micr.io.json',dict(status=403))
   r=a.prepare_one(self.row(),'rijks-000');self.assertEqual(r['state'],'held');session.assert_not_called()
 def test_transaction_layout_preserves_interrupted_boundaries(self):
  with tempfile.TemporaryDirectory(prefix='artline-image-unit-') as temp,patch.object(a,'RUN',Path(temp)/'run'),patch.object(a,'BACKUP',Path(temp)/'backup'):
   images=[dict(artwork_id=str(j)) for j in range(601)]
   for batch in ['rijks-000','rijks-001']:a.saved(a.folder(batch)/'visual-review.json',dict(decisions=[]))
   self.assertEqual([len(g) for g in a.transaction_groups('rijks-000',images)],[500,101])
   a.saved(a.BACKUP/'rijks-001/before-000.json.gz',{})
   self.assertEqual([len(g) for g in a.transaction_groups('rijks-001',images)],[100]*6+[1])
   with self.assertRaises(AssertionError):list(a.transaction_groups('rijks-000',images[::-1]))
 def test_denied_response_is_recorded_and_not_retried(self):
  class Denied:
   status_code=403;headers={}
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def raise_for_status(self):raise requests.HTTPError('403 denied')
  with tempfile.TemporaryDirectory(prefix='artline-image-unit-') as temp,patch.object(a,'RUN',Path(temp)/'run'),patch.object(a,'ORIG',Path(temp)/'originals'),patch.object(a,'provider_slot'),patch.object(a,'session') as session:
   session.return_value.get.return_value=Denied();r=a.prepare_one(self.row(),'rijks-000')
   self.assertEqual(r['state'],'held');self.assertEqual(session.return_value.get.call_count,1);self.assertEqual(a.m.load(a.RUN/'access-holds/iiif.micr.io.json')['status'],403)
if __name__=='__main__':unittest.main()
