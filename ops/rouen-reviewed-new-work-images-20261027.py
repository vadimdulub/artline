"""Finite reviewed-image delivery for the 624 verified new Rouen objects."""
import argparse
import collections
import importlib.util
from pathlib import Path
import exhibitions_common as c

s = importlib.util.spec_from_file_location('delivery', Path(__file__).with_name('rouen-reviewed-image-delivery-20261027.py'))
d = importlib.util.module_from_spec(s)
s.loader.exec_module(d)
d.OP = 'rouen-reviewed-new-work-images-20261027'
d.E = d.m.E / 'native-images'
d.B = Path.home() / 'Library/Application Support/Artline/backups' / d.OP
d.PREP = d.D / 'rouen-new-work-reviewed-image-preparation-20261027.json.gz'
d.SELECTION = d.D / 'rouen-new-work-image-research-selection-20261027.json.gz'


def prepare():
    root = d.m.E.parent
    reviewed = []
    for number in range(14, 31):
        reviewed.extend(c.load(root / ('actual-image-review-%03d.json' % number))['decisions'])
    # Reopened individually before planning: the second photograph is the back.
    corrections = [dict(native_id='07290022199', candidate=1, decision='back_detail',
                        basis='Individually reopened after the sheet review: reverse canvas, stretcher and inventory marks; no primary assignment.',
                        image_sha256=c.sha(Path(next(r['image_path'] for r in reviewed if r['native_id']=='07290022199' and r['candidate']==1)).read_bytes()))]
    for correction in corrections:
        rows = [r for r in reviewed if (r['native_id'], r['candidate']) == (correction['native_id'], correction['candidate'])]
        assert len(rows) == 1 and rows[0]['image_sha256'] == correction['image_sha256']
        rows[0].update(correction)
    assert len(reviewed) == 450
    assert len({(r['native_id'], r['candidate']) for r in reviewed}) == 450
    selected = {r['native_id']: r for r in c.load(d.SELECTION)['selected']}
    approved = collections.defaultdict(list)
    for review in reviewed:
        assert review['native_id'] in selected
        if review['decision'] == 'primary_view_approved':
            approved[review['native_id']].append(review)
    images = []
    for native, reviews in sorted(approved.items()):
        # Alternate/back/context photos have explicit separate review decisions.
        assert len(reviews) == 1, ('Multiple approved primaries require explicit reconciliation', native)
        review = reviews[0]
        candidates = [c.load(p) for p in (root / 'image-preparation').glob(native + '-*.json')]
        candidates = [r for r in candidates if r.get('candidate') == review['candidate'] and r.get('state') == 'prepared_pending_visual_review']
        assert len(candidates) == 1
        image = dict(candidates[0], visual_review=review,
                     provisional_media_id=d.m.uid('new-rouen-image/' + native),
                     provisional_storage_path='/assets/artworks/imported/rouen-collection-20261027/' + native + '.jpg')
        assert image['artwork_id'] == selected[native]['artwork_id']
        d.checked_image(image)
        images.append(image)
    hashes = collections.Counter(r['sha256'] for r in images)
    assert all(n == 1 for n in hashes.values()), 'Shared primary photos require individual identity review'
    gaps = [dict(native_id=n, artwork_id=r['artwork_id'], decisions=[v for v in reviewed if v['native_id'] == n])
            for n, r in selected.items() if n not in approved]
    value = dict(at=c.now(), operation=d.OP, images=images, held=gaps,
                 actual_views_reviewed=450, distinct_new_works_with_candidates=len(selected),
                 decision_counts=dict(collections.Counter(r['decision'] for r in reviewed)),
                 metadata_licence_not_reused_as_image_licence=True, new_images_uploaded=0)
    c.save(d.PREP, value)
    c.save(d.E / 'individual-review-corrections.json', dict(at=c.now(), corrections=corrections,
                                                          original_sheet_receipts_retained=True, before_any_upload_or_database_write=True))
    c.save(d.E / 'preparation-receipt.json', dict(at=c.now(), path=str(d.PREP), sha256=c.sha(d.PREP.read_bytes()),
                                                approved_primary_images=len(images), held_candidate_works=len(gaps),
                                                actual_views_reviewed=450, decision_counts=value['decision_counts']))
    print('Prepared', len(images), 'actually reviewed new-work primaries;', len(gaps), 'candidate works held.', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('phase', choices=['prepare', 'plan', 'upload', 'apply', 'verify'])
    phase = p.parse_args().phase
    prepare() if phase == 'prepare' else getattr(d, phase)()
