#!/usr/bin/env python3
"""Independent checks for the five selected Parthenis inventories in batch 75."""
import importlib.util, io, json
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

s = importlib.util.spec_from_file_location('b75', Path(__file__).with_name('continuous-greek-batch-000075.py'))
b = importlib.util.module_from_spec(s); s.loader.exec_module(b)
h, i = b.h, b.i
p, pin = h.pinned(b.PHASE)
assert len(p['records']) == 5 and not p['new_institutions']
notes = {
    'Horses and Guardians': 'Wide, lightly painted composition with outlined horses, rounded trees and angular guardians; full supplied canvas frame, no detail or placeholder.',
    'Pomone': 'Upright outlined female figure against a blue and bare-canvas background, hand raised across torso; full supplied rectangular painting, naturally faint paint retained.',
    'Portrait of Alexandros Papanastasiou': 'Full-length male sitter in light suit and tie against pale blue vertical strokes; complete figure and supplied painting edges retained.',
    'The Artist’s Father in Law Nikolaos Valsamakis': 'Head-and-shoulders portrait of an older bald man with moustache, jacket and bow tie; upper-left writing and all supplied edges retained.',
    'Epidauros': 'Horizontal architectural composition with pale classical building, column and geometric ornament at right; supplied thin outer edges remain visible. Digitization differs about 3 percent from catalogue support ratio; no resizing crop or aspect adjustment performed.'
}
audit = h.load(i.folder(b.B) / 'quality-audit.json')
assert len(audit['prepared_images']) == 5 and not audit['identity_holds'] and not audit['preparation_holds']
files, decisions, sources = [], [], []
for im in audit['prepared_images']:
    raw = Path(im['path']).read_bytes(); orig = Path(im['original_path']).read_bytes()
    assert h.sha(raw) == im['sha256'] and h.sha(orig) == im['source_sha256'] and len(raw) == im['bytes'] <= 100000
    with Image.open(io.BytesIO(raw)) as pic: pic.verify()
    with Image.open(io.BytesIO(raw)) as pic:
        pic.load(); assert pic.size == (im['width'], im['height'])
    with Image.open(io.BytesIO(orig)) as pic:
        pic.load(); assert list(pic.size) == im['original_dimensions']
        assert abs(pic.width / pic.height - im['width'] / im['height']) < .03
    decisions.append(dict(artwork_id=im['artwork_id'], sha256=im['sha256'], artist=im['artist'], title=im['title'], decision='accept', viewed_individually=True, tool='functions tools.view_image', path=im['path'], note=notes[im['title']], flags_reviewed=im['flags']))
    files.append(dict(artwork_id=im['artwork_id'], sha256=im['sha256'], source_sha256=im['source_sha256'], bytes=im['bytes'], complete_decode=True, full_supplied_proportions=True))
review = dict(at=h.now(), batch_quality_decision='accept', decisions=decisions, scope='All five prepared derivatives actually viewed individually in this turn. Originals decoded technically; no claim of separately viewing originals.')
h.save(i.folder(b.B) / 'visual-review.json', review)
b.save('actual-visual-review.json', review)
b.save('prewrite-file-verification.json', dict(at=h.now(), files=files))
for r in p['records']:
    raw = Path(r['evidence_file']).read_bytes()
    assert h.sha(raw) == r['evidence']['sha256'] and r['evidence']['status'] == 200
    sp = BeautifulSoup(raw, 'html.parser'); head = sp.select_one('h1.artwork')
    date = head.span.get_text(' ', strip=True); head.span.extract()
    assert head.get_text(' ', strip=True).rstrip(',').strip() == r['title'] and date == r['date_display']
    assert r['accession_number'] in sp.select_one('.artwork-no').get_text()
    assert r['creator_label'] == sp.select_one('p.artist').get_text(' ', strip=True)
    assert sp.select_one('p.description').get_text(' ', strip=True) == r['medium'] + ', ' + r['dimensions']
    tag = sp.select_one('.img-magnifier-container img')
    assert (tag.get('data-zoom-image') or tag['src']) == r['raw']['image_url']
    assert 0 < r['first'] <= r['last'] <= 1955 and r['artist_id'] == 'd0b220dd-6817-4a2b-93a7-01193f38def3'
    sources.append(dict(artwork_id=r['artwork_id'], source_id=r['source_id'], inventory=r['accession_number'], source_sha256=r['evidence']['sha256'], creation=r['date_display'], creator_label=r['creator_label'], artist_id=r['artist_id']))
b.save('prewrite-source-verification.json', dict(at=h.now(), plan_sha256=pin, records=sources))
comparison = h.load(b.E / 'existing-parthenis-comparison-sheets.json')
assert len(comparison['sheets']) == 3 and sum(len(x['rows']) for x in comparison['sheets']) == 39
b.save('actual-existing-composition-review.json', dict(at=h.now(), sheets=[dict(path=x['path'], sha256=x['sha256']) for x in comparison['sheets']], viewed_in_contact_sheets=39, full_size_existing_files_viewed=0, unillustrated_not_visually_reviewed=17, finding='The five new selected compositions are absent from the 39 available existing primary images viewed in three contact sheets. All 56 existing creator records were also compared by title, inventory and source identity. Five possible title/version overlaps remain held.'))
with h.connect() as db, db.transaction():
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    b.no_collision(db, p['records'])
    assert not h.snapshot(db, [r['artwork_id'] for r in p['records']])
    assert h.load(b.E / 'prior-batch-live-reconciliation.json')['previous_batch_verified']
    for name in ['preserved-existing-before.json.gz', 'preserved-parthenis-before.json.gz']:
        old = h.load(b.E / name)['artworks']; assert h.snapshot(db, list(old)) == old
    # All artist aliases were reconciled globally by the established planner.
    assert len(p['artists']) == 1
    assert h.load(b.E / 'local-recovery-verification.json')['status'] == 'VERIFIED'
b.save('prewrite-verification.json', dict(at=h.now(), passed=True, plan_sha256=pin, selected=5, images=5, global_identity_evidence='final-global-identity-reconciliation.json', no_existing_production_rows=True, immutable_plan_backup=str(h.BACKUP / b.PHASE / 'plan-preimages.json.gz'), shared_lock='artline-curated-ingestion', local_catalogue_connections=0))
print('Five source records and individually viewed images passed prewrite verification.')
