"""Dated Theocharakis source proposals; preserves differences and makes no DB writes."""
import collections
import csv
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location('d', Path(__file__).with_name('museum-expansion-theocharakis-dated-source-20261010.py'))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
m, q, RUN = d.m, d.q, d.RUN
PROOF = Path.home() / 'Library/Application Support/Artline/research-proofs/theocharakis-dated-20261010'
IID = d.t.IID
MEDIUM_EQUIVALENTS = {
    ('Υδρόχρωμα σε χαρτί', 'Ακουαρέλα σε χαρτί'),
    ('Υδατοχρώματα σε χαρτί', 'Ακουαρέλα σε χαρτί'),
    ('Λάδι σε μουσαμά', 'Λάδι σε καμβά'),
    ('Μολύβι, κραγιόνια και υδροχρωμα σε διαφανές χαρτί', 'Μολύβι, κραγιόνια και ακουαρέλα σε διαφανές χαρτί'),
}
DISTINCT = [
    dict(numbers=[28,29], reason='Related nude tracings have different composition, paper proportions, staining and dimensions; 111795 is a landscape torso/legs study, 111796 includes the head and upper body.'),
    dict(numbers=[31,36,34], reason='A full oil painting, a gridded pencil study and a wide tracing are separate physical works. The cropped aggregator thumbnail of the painting omits the right side visible in its original asset.'),
    dict(numbers=[37,51], previous_numbers=[160], reason='Two Danae oil portraits differ in facial construction, hair, hand positions and paint treatment; their source catalogue references identify pages 55 and 54 respectively. The prior-wave pencil study 111110 is a smaller separate sheet, not a third painting or a repeated photograph.'),
    dict(numbers=[30,32,33], reason='Pear paintings have different arrangements, fruit count, modelling, backgrounds and dimensions. Source 103308 has a separate unresolved dimension/image-proportion inconsistency; do not rewrite its dimensions or attach its image from this review.'),
    dict(numbers=[40,41], reason='Crayon boat studies differ in viewpoint, line work, foreground, dimensions and paper contours; no unique matching support evidence establishes reverse sides.'),
    dict(numbers=[10,14,15,23,39], reason='Five self-portraits differ in medium, facial construction, pose, paper/canvas and size. Shared sitter and similar titles are not object identity.'),
    dict(numbers=[12,22,25], reason='Bust studies differ in drawing construction, medium, paper contours and dimensions; depicted sculpture is a subject, not an additional museum holding.'),
    dict(numbers=[27,35], reason='Gridded and faint outline fruit studies use different compositions, margins and dimensions; retain two source identities.'),
    dict(numbers=[13,24], reason='Hydra studies depict different buildings/viewpoints, use different media and have different dimensions. Both native creation intervals end in 1956, despite abbreviated index year 1955.'),
    dict(numbers=[2,3,9,16,19,20,21], reason='Hydra houses share a location but show distinct building arrangements, viewpoints, media and sizes on the reviewed contact sheet.'),
    dict(numbers=[42,43,44,45,46,47,48,49,50,52,53,54,55,56,57,58,59], reason='Paros landscapes, churches, sea views and boats show distinct compositions on the reviewed contact sheet. Matching titles, dates or dimensions alone do not establish duplicates.'),
]
HOLD_REASON = ('Source 111641 and 111796 show the same nude drawing, including identical brown stains and line details, in different photographs. '
    '111641 describes 22.5 x 32 cm pencil on paper, while 111796 describes 34 x 30.5 cm pencil on transparent paper. '
    'The latter fits the observed portrait-oriented sheet. Hold 111641 as a duplicate-image/metadata conflict; its true object or mistaken image is unresolved. '
    'Do not count it independently, consolidate its conflicting metadata into 111796, or infer that it belongs to the different 111795 tracing merely because their dimensions agree.')


def ref(path):
    path = Path(path)
    return dict(path=str(path.relative_to(m.ROOT)) if path.is_relative_to(m.ROOT) else str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def date_bounds(literal):
    match = re.fullmatch(r'(\d{4})(?:\s*-\s*(\d{4}))?', literal)
    assert match, literal
    first, last = int(match[1]), int(match[2] or match[1])
    assert first <= last <= 1970
    return first, last


def main():
    sources = m.load(RUN/'selected-source-records-001.json.gz')['rows']
    natives = {v['source_id']:v for v in m.load(RUN/'native-object-records-001.json.gz')['rows']}
    images = {v['source_id']:v for v in m.load(RUN/'visual-references-001.json')['rows']}
    previous = m.load(d.OLD/'selected-source-records-001.json.gz')['rows']
    assert len(sources) == len(natives) == len(images) == 60
    assert not ({v['source_id']for v in sources} & {v['source_id']for v in previous})
    rows = []; reconciliations = []
    for s in sources:
        n = natives[s['source_id']]; f = s['fields']; nf = n['fields']; number = s['number']
        assert n['source_comparison']['title'] and n['source_comparison']['dimensions']
        assert n['creators'] == ['Σπύρος Παπαλουκάς (1892 - 1957)']
        assert f['Δημιουργός'] in [
            ['Σπύρος Παπαλουκάς', 'Spyros Papaloukas'],
            ['Σπύρος Παπαλουκάς (1892 - 1957)', 'Spyros Papaloukas (1892 - 1957)']]
        notes = []
        if not n['source_comparison']['creator']:
            notes.append(dict(field='creator', decision='Same explicit personal name; native page additionally supplies life dates. Preserve both source labels; life dates are not creation dates.'))
        if not n['source_comparison']['medium']:
            assert (f['Υλικό'][0], nf['τεχνική']) in MEDIUM_EQUIVALENTS
            notes.append(dict(field='medium', decision='Reviewed equivalent Greek terminology for watercolour, canvas, or mixed pencil/crayon/watercolour. Preserve each literal phrase.'))
        first, last = date_bounds(nf['έτος'])
        if not n['source_comparison']['date']:
            assert (number, f['Ημερομηνία δημιουργίας'][0], nf['έτος']) in [
                (38, '1950', '1950 - 1955'), (51, '1948', '1948 - 1949')]
            notes.append(dict(field='date', decision='Use the broader explicit native object interval for a proposed new record. Preserve abbreviated aggregator date as evidence; no existing date changes.'))
        if notes:
            reconciliations.append(dict(number=number, source_id=s['source_id'], notes=notes,
                aggregator_fields=f, native_fields=nf, native_creators=n['creators']))
        # Classify physical technique, retaining the provider's broader collection category.
        technique = nf['τεχνική']
        kind = 'painting' if technique.startswith('Λάδι ') else 'watercolor' if technique == 'Ακουαρέλα σε χαρτί' else 'drawing'
        decision = 'hold_duplicate_image_metadata_conflict' if number == 26 else 'candidate_primary'
        note = HOLD_REASON if number == 26 else 'Source-backed physical artwork; contact sheet reviewed. Live production duplicate and painter identity checks remain pending.'
        if number == 28:
            note += ' Use the native portrait-sheet description; conflicting page 111641 is held separately and is not an additional work or accepted metadata alias.'
        image_note = 'Internal research reference only; no image attachment prepared.'
        if last > 1955:
            image_note += ' Creation interval ends after the museum-image production cutoff of 1955; artwork metadata remains eligible through 1970.'
        if number == 30:
            image_note += ' Native asset is landscape-oriented with two pears, while literal dimensions are 20 x 19 cm and title is singular. Preserve source metadata; production image held for further object/crop/dimension evidence.'
        if number == 26:
            image_note += ' Duplicate imagery with conflicting physical metadata; image and artwork addition held.'
        rows.append(dict(number=number, source_id=s['source_id'], source_url=s['source_url'], native_url=s['native_url'],
            title=f['Τίτλος'][-1], source_titles=f['Τίτλος'], creator_label=f['Δημιουργός'][0], creator_translations=f['Δημιουργός'],
            native_creator_labels=n['creators'], painter_id=None, creator_link_state='verified_source_name_live_painter_identity_pending',
            inventory_literal=None, inventory_note='Page IDs and image filenames remain source references; no accession exposed.',
            date_display=nf['έτος'], aggregator_date_literals=f['Ημερομηνία δημιουργίας'], index_date=s['index']['index_date'],
            first=first, last=last, date_precision='year' if first == last else 'range', date_scope='eligible',
            work_type=kind, provider_type_literals=f['Τύπος'], medium_text=f['Υλικό'][-1], medium_literals=f['Υλικό'],
            native_medium_literal=technique, dimensions_text=f['Έκταση (μέγεθος ή διάρκεια)'][-1],
            dimensions_literals=f['Έκταση (μέγεθος ή διάρκεια)'], source_fields=f, native_fields=nf,
            aggregator_enrichment=s['enrichment'], source_receipt=s['receipt'], native_receipt=n['receipt'],
            image_reference={k:images[s['source_id']][k] for k in ['path','sha256']}, full_image_url=n['full_image_url'],
            rights_links=s['rights_links'], image_note=image_note, image_date_policy_passed=last <= 1955,
            image_further_identity_evidence_required=number in [26,30], proposed_status='review',
            decision=decision, decision_reason=note, ready_to_apply=False, applied=False, current_display_verified=False,
            museum_confidence_editorial=.98,
            museum_confidence_basis='Native foundation object record and explicit foundation collection/holding label; editorial assessment, not a calibrated probability. Location in a title is the subject, not current display.'))
    assert len(reconciliations) == 40
    changed = collections.Counter(note['field']for row in reconciliations for note in row['notes'])
    assert changed == dict(creator=40, medium=26, date=2), changed
    units = []
    for row in rows:
        if row['decision'] != 'candidate_primary': continue
        unit = {k:row[k]for k in ['title','creator_label','painter_id','inventory_literal','date_display','first','last',
            'date_precision','date_scope','work_type','medium_text','dimensions_text','proposed_status','ready_to_apply','applied','current_display_verified']}
        unit.update(primary_source_id=row['source_id'], primary_number=row['number'], source_ids=[row['source_id']],
            source_numbers=[row['number']], physical_units_counted=1, image_note=row['image_note'],
            identity_state='editorial_source_review_complete_live_production_identity_pending')
        units.append(unit)
    assert len(units) == 59 and sum(v['last'] > 1955 for v in units) == 13
    m.save(RUN/'metadata-reconciliation-001.json.gz', dict(at=m.now(), rows=reconciliations, differing_fields=dict(changed),
        literal_fields_preserved=True, normalization_policy='Explicit name and medium equivalences are editorially reviewed. Prefer broader native creation intervals, never index abbreviations or artist life dates. No source literals overwritten.',
        source_reference=ref(RUN/'selected-source-records-001.json.gz'), native_reference=ref(RUN/'native-object-records-001.json.gz')))
    m.save(RUN/'physical-unit-review-001.json', dict(at=m.now(), contact_sheets_reviewed=3, focused_comparison_sheets_reviewed=10,
        holds=[dict(number=26, source_id='theocharakis/000163-111641', comparator_number=28, reason=HOLD_REASON)],
        distinct_comparisons=DISTINCT, production_image_identity_holds=[dict(number=30, reason=next(v['image_note']for v in rows if v['number']==30))],
        image_scope='60 source thumbnails and 26 selected native originals, including the previous-wave Danae study, are internal evidence only.',
        visual_reference=ref(RUN/'visual-references-001.json'), comparison_reference=ref(RUN/'comparison-references-001.json'),
        physical_identity_limit='Visual source reconciliation does not replace a live production duplicate check. Different bytes or URLs alone do not establish different artworks. No existing or prior-wave record changed.'))
    m.save(RUN/'editorial-source-decisions-001.json.gz', dict(at=m.now(), rows=rows,
        counts=dict(collections.Counter(v['decision']for v in rows)), physical_review_reference=ref(RUN/'physical-unit-review-001.json'),
        reconciliation_reference=ref(RUN/'metadata-reconciliation-001.json.gz'), script_reference=ref(Path(__file__).resolve())))
    m.save(RUN/'candidate-physical-units-001.json.gz', dict(at=m.now(), institution_id=IID, rows=units, proposed_new_units=59,
        numeric_date_candidates=59, unknown_date_candidates=0, actual_added=0, prior_wave_candidates=138,
        combined_pending_candidates=197, prior_candidates_reference=ref(d.OLD/'candidate-physical-units-001.json.gz'),
        decisions_reference=ref(RUN/'editorial-source-decisions-001.json.gz'),
        mandatory_next_steps=['Restore production authentication, obtain fresh scoped rows and global source/creator/title comparators',
            'Check all current and prior source aliases against production and resolve verified Papaloukas painter ID',
            'Prepare exact-hash write plan only after reconciliation; successful backup, apply, readback and zero-write replay',
            'Retain review status, historical values, image policy holds and protected earlier campaign records']))
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=['number','source_id','title','date_display','work_type','decision','decision_reason','source_url']);w.writeheader()
    for row in rows:w.writerow({k:row[k]for k in w.fieldnames})
    (RUN/'review-ledger-001.csv').open('x').write(out.getvalue())
    print(json.dumps(dict(proposed_physical_units=len(units),held_source_records=1,combined_pending=197,
        work_types=dict(collections.Counter(v['work_type']for v in units)),date_policy_passed=46,image_identity_hold_within_date_scope=1,actual_added=0)),flush=True)


if __name__ == '__main__': main()
