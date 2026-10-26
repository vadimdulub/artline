"""Record an explicitly completed human/model image inspection, never infer it.

Run only after opening every specified contact sheet with the image viewer.
Special decisions are manually supplied by the reviewer. No catalogue writes.
"""
import argparse
import collections
import json
from pathlib import Path
import exhibitions_common as c

E = c.ROOT / 'docs/research/catalogue-deduplication-20261026'


def record(manifest, batch, first, last, special):
    index = c.load(Path(manifest))
    assert 1 <= first <= last <= len(index['sheets'])
    decisions = []
    for number in range(first, last + 1):
        sheet = index['sheets'][number - 1]
        assert c.sha(Path(sheet['path']).read_bytes()) == sheet['sha256']
        for offset, obj in enumerate(sheet['candidates']):
            position = (number - 1) * 9 + offset + 1
            state, reason = special.get(str(position), [
                'primary_view_approved',
                'Actually inspected in the labelled sheet. Visible subject agrees with the exact object title; the supplied composition is visible. Source frame, condition and photographic perspective retained.'])
            records = [c.load(p) for p in (E / 'image-preparation').glob(obj['native_id'] + '-*.json')]
            records = [r for r in records if r['candidate'] == obj['candidate'] and r['state'] == 'prepared_pending_visual_review']
            assert len(records) == 1
            prepared = records[0]
            assert c.sha(Path(prepared['path']).read_bytes()) == prepared['sha256']
            decisions.append(dict(obj, manifest_position=position, decision=state, basis=reason,
                                  image_sha256=prepared['sha256'], image_path=prepared['path'],
                                  contact_sheet=sheet['path'], contact_sheet_sha256=sheet['sha256'],
                                  source_credit_preserved=prepared['credit'], visual_review_at=c.now()))
    value = dict(at=c.now(), actually_viewed_candidates=len(decisions), decisions=decisions,
                 manifest=str(manifest), sheets_actually_viewed=list(range(first, last + 1)),
                 counts=dict(collections.Counter(r['decision'] for r in decisions)),
                 uploads=0, fresh_production_preflight_still_required=True,
                 rights_not_inferred_from_metadata_licence=True)
    c.save(E / ('actual-image-review-' + batch + '.json'), value)
    print(json.dumps(dict(reviewed=len(decisions), counts=value['counts'])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--batch', required=True)
    parser.add_argument('--first-sheet', type=int, required=True)
    parser.add_argument('--last-sheet', type=int, required=True)
    parser.add_argument('--special', default='{}')
    args = parser.parse_args()
    record(args.manifest, args.batch, args.first_sheet, args.last_sheet, json.loads(args.special))
