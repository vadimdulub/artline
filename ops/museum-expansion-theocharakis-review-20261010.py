"""Papaloukas physical-work reconciliation; research proposals, no database writes."""
import collections
import csv
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location('t', Path(__file__).with_name('museum-expansion-theocharakis-source-20261010.py'))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
m, RUN, q = t.m, t.RUN, t.q
PROOF = Path.home() / 'Library/Application Support/Artline/research-proofs/theocharakis-20261010'

# Pairing is an editorial conclusion from the inspected images, not an explicit
# recto/verso label supplied by the source. Never infer it from adjacent IDs alone.
NEW_SHEETS = [
    dict(primary=13, secondary=24, reason='Matching irregular lower edge and mirrored lower corner losses, equal dimensions and visible ghosting support a two-sided charcoal sheet.'),
    dict(primary=23, secondary=29, reason='Matching loose fibres and irregular top edge, matching bottom corner/fold features and faint reverse portrait visible through the paper support one two-sided sheet.'),
    dict(primary=31, secondary=39, reason='Distinctive brown spots at mirrored top corners and matching irregular bottom edge support one sheet bearing a layout on each side.'),
    dict(primary=36, secondary=49, reason='Mirrored lower-edge damage, staining and missing paper patches identify opposite sides of the same sheet; charcoal nude and pencil female figure remain separate side descriptions.'),
    dict(primary=89, secondary=55, reason='Matching irregular top edge, mirrored lower notch and matching stain/crease locations identify one sheet with an interior decoration study and floral motif.'),
    dict(primary=115, secondary=133, reason='Matching clipped corner and crease pattern after rotation, with related monument studies visible on each side, support one sheet.'),
    dict(primary=120, secondary=127, reason='The coarse board has matching mirrored edge damage and rounded top corner; coloured and pencil savings-bank studies are opposite sides of one board.'),
    dict(primary=153, secondary=163, reason='Mirrored Christ figures visibly show through the paper; matching irregular margins and reused printed journal paper conclusively identify a single two-sided sheet.')
]
EXISTING_SHEETS = [
    dict(candidate=16, existing=6, reason='Matching mirrored patterned staining and top-edge damage; different layouts on two sides of existing 111590.'),
    dict(candidate=28, existing=10, reason='Matching mirrored folded corners and paper edge contours; additional monumental-group studies on the other side of existing 111569.'),
    dict(candidate=45, existing=3, reason='Mirrored identical outlines and paper folds/corners match existing 111572; do not add the reverse-view record 111571 separately.'),
    dict(candidate=47, existing=11, reason='Identical mirrored large notch and torn edges, repair trace and visible ink showing through match existing 111576. Source 111575 is an additional side reference, not an extra sheet.')
]
HOLDS = [
    dict(numbers=[17], comparator_numbers=[5], reason='Pencil Monastery 111598 and oil Landscape 111599 share board dimensions and rounded contours. A possible opposite-side relationship cannot be resolved confidently from the images; do not add another physical board yet.'),
    dict(numbers=[18], comparator_numbers=[7], reason='Floral motifs/warrior 111595 and existing iconographic floor plan 111594 share dimensions and folding. Parent-sheet identity remains uncertain; existing dated record must not be silently redated from the undated candidate.'),
    dict(numbers=[109,138], comparator_numbers=[], reason='Adjacent studies 110802/110803 have equal dimensions, overlapping geometry and possible shared paper features. Separate sheets versus opposite sides remain unresolved.'),
    dict(numbers=[111,140], comparator_numbers=[], reason='Harvest 110807 and Studies 110806 have transposed equal dimensions and complex overlapping drawings. Original physical unit remains uncertain; do not count two independent sheets without further evidence.'),
    dict(numbers=[154,169], comparator_numbers=[], reason='Savings-bank drawing 111132 and Papyrus 111133 have equal dimensions and apparently similar support. Native pages provide no accession or side designation; relationship unresolved.'),
    dict(numbers=[158,172], comparator_numbers=[], reason='Two male-figure pages 111114/111115 share dimensions and near-identical pose with different background work. Separate studies, altered states or opposite sides cannot yet be distinguished securely.'),
    dict(numbers=[67,77], comparator_numbers=[], reason='Equestrian saint 111401 and torso with sword 111402 share dimensions and possible mirrored edge damage. Evidence suggests a shared sheet but is not strong enough to consolidate or count independently.')
]
DISTINCT_COMPARISONS = [
    dict(numbers=[51,65,79,92], reason='Related Archangel Michael studies have different widths, line treatments and secondary figures/annotations. Repeated iconography alone does not make them duplicates.'),
    dict(numbers=[52,78,94], reason='Same-size composition studies show different arrangement, modelling and additions. No unique matching reverse-side damage establishes a common sheet; retain distinct source records pending live identity checks.'),
    dict(numbers=[60,72], reason='Equal nominal size but markedly different cut-paper boundaries and different drawing geometry; retain separate studies.'),
    dict(numbers=[60,87], reason='Different paper proportions, boundary cuts and cloud/drawing construction establish different studies.'),
    dict(numbers=[61,75], reason='Related angel and geometric tracing have different paper dimensions, silhouettes and drawing details; not merely flipped views.'),
    dict(numbers=[88,95], reason='Different geometric constructions and paper/crease configurations; equal nominal dimensions are insufficient to merge.'),
    dict(numbers=[108,114,118,126,142], reason='Dolphin/medallion sheets differ in dimensions, support and arrangement. Multiple motifs on each sheet count once; depicted medallions are not separate holdings.'),
    dict(numbers=[121,122,134,137], reason='Related tracing-paper Saint Demetrius studies have different image sizes, cut edges, inscriptions and drawn arrangements. Shared outer dimensions do not justify merging.'),
    dict(numbers=[123,125], reason='Different support size, composition and colour placement in standing Saint Demetrius studies.'),
    dict(numbers=[145,147,107], reason='Carol-singer studies have distinct facial drawing, curtain lines, composition placement, colour and paper edges/dimensions. Keep three original studies.'),
    dict(numbers=[157,159,173], reason='Saint Demetrius studies show distinct colour construction, horse/anatomical lines, architectural details and torn-paper boundaries despite equal nominal size.'),
    dict(numbers=[156,170,171,175], reason='Horse/rider studies differ in dimensions, paper outline, drawing medium and details; retain individual source identities.'),
    dict(numbers=[59,71], reason='Distinct John and Virgin studies on differently oriented supports, with different edges and printed-paper positioning; common nominal dimensions do not establish a shared sheet.'),
    dict(numbers=[85,97], reason='John study and angel head have substantially different edge damage/staining and images; retain separate source identities.'),
    dict(numbers=[43,8], reason='Existing anatomical studies were compared. Same nominal format does not establish a shared sheet; no merge or metadata change is justified by this review.'),
    dict(numbers=[42,9], reason='Existing hand/leg study and nude were compared. Different composition and insufficient unique support evidence; no existing-record merge is performed.'),
    dict(numbers=[30,46], reason='Distinct unfinished figure group and archer compositions. Equal format alone does not establish a reverse-side identity; retain source records pending live checks.'),
    dict(numbers=[2,21], reason='Existing and proposed vestment drawings have different support dimensions and drapery arrangement; not duplicates merely because titles match.'),
    dict(numbers=[32,36], reason='Nude studies differ in size, medium, pose and support; retain distinct object identities.')
]


def ref(path):
    path = Path(path)
    return dict(path=str(path.relative_to(m.ROOT)) if path.is_relative_to(m.ROOT) else str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def parse_date(value):
    if value in ('χ.χ.', 'n.d.'):
        return dict(first=None, last=None, date_precision='unknown', date_scope='requires_editorial_review')
    match = re.fullmatch(r'(\d{4})(?:\s*-\s*(\d{4}))?', value)
    if match is None:
        raise ValueError('Unreviewed artwork-date syntax: '+value)
    first = int(match[1])
    last = int(match[2] or match[1])
    if first > last:
        raise ValueError('Reversed artwork-date interval')
    return dict(first=first, last=last, date_precision='year' if first == last else 'range',
                date_scope='eligible' if last <= 1970 else 'post_1970' if first > 1970 else 'requires_editorial_review')


def main():
    source = m.load(RUN/'selected-source-records-001.json.gz')['rows']
    native = {v['source_id']:v for v in m.load(RUN/'native-object-records-001.json.gz')['rows']}
    images = {v['source_id']:v for v in m.load(RUN/'visual-references-001.json')['rows']}
    assert len(source) == len(native) == len(images) == 180
    assert all(all(v['source_comparison'].values()) for v in native.values())
    held = {n:g for g in HOLDS for n in g['numbers']}
    secondary = {v['secondary']:v for v in NEW_SHEETS}
    primary = {v['primary']:v for v in NEW_SHEETS}
    existing_side = {v['candidate']:v for v in EXISTING_SHEETS}
    assert len(held) == 12 and len(secondary) == 8 and len(existing_side) == 4
    assert not (set(held)&set(secondary) or set(held)&set(existing_side) or set(secondary)&set(existing_side))
    rows = []
    for row in source:
        n = row['number'];f = row['fields'];original = native[row['source_id']]
        date = original['fields']['έτος'];parsed = parse_date(date)
        assert parsed['date_scope'] != 'post_1970'
        assert f['Δημιουργός'] == ['Σπύρος Παπαλουκάς (1892 - 1957)', 'Spyros Papaloukas (1892 - 1957)']
        medium = f['Υλικό'][-1]
        work_type = 'watercolor' if any(v in medium.lower() for v in ['watercolour', 'watercolor']) else 'painting' if f['Τύπος'] == ['Ζωγραφικά Έργα','Paintings'] else 'drawing'
        assert f['Τύπος'] in (['Ζωγραφικά Έργα','Paintings'], ['Σχέδια','Drawings'])
        decision = 'candidate_primary'
        note = 'Selected original-source work reviewed on the contact sheet; no specific physical-unit conflict identified. Live database identity remains unverified.'
        if row['role'] == 'historical_comparator':
            decision='existing_record';note='Historical delivery record retained unchanged; fresh production state is unavailable.'
        elif n in held:
            decision='hold_physical_unit';note=held[n]['reason']
        elif n in secondary:
            decision='same_sheet_secondary';note=secondary[n]['reason']
        elif n in existing_side:
            decision='existing_sheet_reference_only';note=existing_side[n]['reason']
        elif n in primary:
            note=primary[n]['reason']
        rows.append(dict(number=n,source_id=row['source_id'],source_url=row['source_url'],native_url=row['native_url'],
            source_titles=f['Τίτλος'],title=f['Τίτλος'][-1],creator_label=f['Δημιουργός'][0],creator_translations=f['Δημιουργός'],
            painter_id=None,creator_link_state='named_creator_supported_but_live_painter_id_unverified',
            inventory_literal=None,inventory_note='No museum accession is exposed. Page ID and image asset filename are source identifiers only.',
            date_display=f['Ημερομηνία δημιουργίας'][-1],native_date_literal=date,**parsed,work_type=work_type,
            medium_text=medium,medium_literals=f['Υλικό'],dimensions_text=f['Έκταση (μέγεθος ή διάρκεια)'][-1],
            dimensions_literals=f['Έκταση (μέγεθος ή διάρκεια)'],native_fields=original['fields'],
            source_fields=f,aggregator_enrichment=row['enrichment'],source_receipt=row['receipt'],native_receipt=original['receipt'],
            image_reference=dict(path=images[row['source_id']]['path'],sha256=images[row['source_id']]['sha256']),
            full_image_url=original['full_image_url'],rights_links=row['rights_links'],decision=decision,decision_reason=note,
            proposed_status='review',ready_to_apply=False,applied=False,current_display_verified=False,
            museum_confidence_editorial=.98,museum_confidence_basis='Native foundation artwork page plus explicit provider collection/holding label and institutional statement; editorial assessment, not a calibrated probability.',
            numeric_date_eligibility=parsed['date_scope']=='eligible'))
    by_number={v['number']:v for v in rows}
    units=[]
    for row in rows:
        if row['decision']!='candidate_primary':continue
        members=[row]
        if row['number']in primary:members.append(by_number[primary[row['number']]['secondary']])
        assert len({(v['first'],v['last'])for v in members})==1
        titles=list(dict.fromkeys(v['title']for v in members))
        mediums=list(dict.fromkeys(v['medium_text']for v in members))
        units.append(dict(primary_source_id=row['source_id'],primary_number=row['number'],source_ids=[v['source_id']for v in members],
            source_numbers=[v['number']for v in members],title=' / '.join(titles),
            description_note=('Two-sided physical sheet, consolidated by editorial image comparison; each side’s original metadata and source citation retained. Source does not label recto/verso.' if len(members)>1 else 'One source object. Multiple motifs, studies, views or depicted monuments do not become additional holdings.'),
            date_display=row['date_display'],first=row['first'],last=row['last'],date_precision=row['date_precision'],
            work_type=row['work_type'] if len({v['work_type']for v in members})==1 else 'unknown',medium_text='; '.join(mediums),
            dimensions_text=row['dimensions_text'],creator_label=row['creator_label'],painter_id=None,inventory_literal=None,
            proposed_status='review',ready_to_apply=False,applied=False,physical_units_counted=1,
            date_scope=row['date_scope'],current_display_verified=False,
            identity_state='editorial_source_unit_review_complete_live_production_duplicate_check_pending',
            rights_state='CC BY-SA 4.0 recorded. No production image upload in this pass; attachment still requires selected image identity and date-policy checks.'))
    counts=dict(collections.Counter(v['decision']for v in rows))
    assert counts==dict(existing_record=18,candidate_primary=138,same_sheet_secondary=8,existing_sheet_reference_only=4,hold_physical_unit=12),counts
    m.save(RUN/'physical-unit-review-001.json',dict(at=m.now(),new_two_sided_sheets=NEW_SHEETS,
        existing_sheet_references=EXISTING_SHEETS,holds=HOLDS,distinct_or_unmerged_comparisons=DISTINCT_COMPARISONS,
        inference_policy='Physical-sheet grouping is an editorial inference from inspected matching damage, folds, fibres or reverse-side show-through plus dimensions. Adjacent page IDs and equal dimensions alone do not establish identity. Ambiguous units are held. No existing records merged or mutated.',
        contact_sheets_reviewed=9,comparison_sheets_reviewed=31,
        visual_reference=ref(RUN/'visual-references-001.json'),comparison_references=[ref(RUN/('comparison-references-00'+str(n)+'.json'))for n in [1,2,3]],
        special_decisions=['Source 111578 excluded as photographic documentation before download.',
          'Source 111433 shows multiple strips/views in a single supplied image; count one source object, never separate quota items.',
          'Heraklion archaeology subjects are Papaloukas studies held by Theocharakis; depicted ancient objects are not new Theocharakis holdings.',
          'School/church/museum place names in titles are subjects or study destinations, not current holding assignments.',
          'Original studies using printed/reused paper retain Papaloukas source attribution; no separate attribution or new work for printed background references.',
          'Existing anatomical-study pairs compared; no confident evidence to merge either pair. Existing 18-record production count is not refreshed here.']))
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=rows,counts=counts,
        source_reference=ref(RUN/'selected-source-records-001.json.gz'),native_reference=ref(RUN/'native-object-records-001.json.gz'),
        physical_review_reference=ref(RUN/'physical-unit-review-001.json'),script_reference=ref(Path(__file__).resolve())))
    m.save(RUN/'candidate-physical-units-001.json.gz',dict(at=m.now(),institution_id=t.IID,rows=units,
        proposed_new_units=len(units),actual_added=0,numeric_date_candidates=sum(v['date_scope']=='eligible'for v in units),
        unknown_date_candidates=sum(v['date_scope']=='requires_editorial_review'for v in units),
        decisions_reference=ref(RUN/'editorial-source-decisions-001.json.gz'),
        mandatory_next_steps=['Fresh institution-scoped production rows, source IDs, citations and title/creator comparators',
          'Resolve the supported Papaloukas label against verified live painter identities; do not fabricate painter records',
          'Reconcile all source IDs of two-sided sheets against production before proposing a new physical work',
          'Verify prior protected campaign records; prepare exact-hash plan, successful backup, apply, readback and zero-write replay',
          'Do not rerun immutable writers or change historical dates/statuses/images while matching'] ))
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=['number','source_id','title','date_display','decision','decision_reason','source_url']);w.writeheader()
    for row in rows:w.writerow({k:row[k]for k in w.fieldnames})
    (RUN/'review-ledger-001.csv').open('x').write(out.getvalue())
    print(json.dumps(dict(counts=counts,proposed_physical_units=len(units),known_dates=sum(v['date_scope']=='eligible'for v in units),unknown_dates=sum(v['date_scope']=='requires_editorial_review'for v in units),actual_added=0)),flush=True)


if __name__=='__main__':main()
