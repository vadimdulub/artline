"""Offline preservation checks for the production enrichment transaction."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('delivery',Path(__file__).with_name('source-index-deliver-20261009.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)


def fixture(image=False):
    a=dict(id='work',title='Original',medium_text=None,dimensions_text='Original dimensions',accession_number='A1',
        primary_media_id=None,status='review',creation_year_start=None,creation_year_end=None,date_precision='unknown',
        date_display='Unknown',current_institution_id='museum',revision=7,updated_at='before',updated_by='other')
    before=dict(id='work',artwork=a,creators=[dict(artist_id='artist',attribution_role='attributed_to')],
        attachments=[dict(media_id='old-alternate',sort_order=1,view_label='Reverse')])
    im=dict(media_id='new-image',view_label='Decorated reverse of mirror') if image else None
    claim=dict(artwork_id='work',updates=dict(medium_text='Bronze'),image=im)
    plan=dict(claims=[claim],preimages={'work':before})
    after=copy.deepcopy(before)
    after['artwork'].update(medium_text='Bronze',revision=8,updated_at='after',updated_by=d.ACTOR)
    if im:
        after['artwork']['primary_media_id']='new-image'
        after['attachments'].append(dict(media_id='new-image',sort_order=0,view_label=im['view_label']))
    return plan,{'work':after}


class PreservationTests(unittest.TestCase):
    def test_only_pinned_missing_metadata_changes_pass(self):
        p,a=fixture();d.validate_after(p,a)

    def test_new_image_and_prior_attachment_pass(self):
        p,a=fixture(True);d.validate_after(p,a)

    def test_date_changes_are_rejected(self):
        p,a=fixture();a['work']['artwork']['creation_year_start']=1885
        with self.assertRaises(AssertionError):d.validate_after(p,a)

    def test_publication_changes_are_rejected(self):
        p,a=fixture();a['work']['artwork']['status']='published'
        with self.assertRaises(AssertionError):d.validate_after(p,a)

    def test_holding_changes_are_rejected(self):
        p,a=fixture();a['work']['artwork']['current_institution_id']='different-museum'
        with self.assertRaises(AssertionError):d.validate_after(p,a)

    def test_attribution_changes_are_rejected(self):
        p,a=fixture();a['work']['creators'][0]['attribution_role']='primary'
        with self.assertRaises(AssertionError):d.validate_after(p,a)

    def test_existing_image_attachment_changes_are_rejected(self):
        p,a=fixture(True);a['work']['attachments'][0]['view_label']='Changed'
        with self.assertRaises(AssertionError):d.validate_after(p,a)

    def test_wrong_new_primary_image_is_rejected(self):
        p,a=fixture(True);a['work']['artwork']['primary_media_id']='different'
        with self.assertRaises(AssertionError):d.validate_after(p,a)

    def test_reviewed_image_view_label_is_required(self):
        p,a=fixture(True);a['work']['attachments'][1]['view_label']='Front'
        with self.assertRaises(AssertionError):d.validate_after(p,a)

    def test_unplanned_metadata_overwrite_is_rejected(self):
        p,a=fixture();a['work']['artwork']['dimensions_text']='New dimensions'
        with self.assertRaises(AssertionError):d.validate_after(p,a)


if __name__=='__main__':unittest.main()
