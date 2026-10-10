"""Evidence-backed Kilkis research decisions; no database connection or writes."""
import collections
import csv
import hashlib
import importlib.util
import io
from pathlib import Path

spec = importlib.util.spec_from_file_location('m', Path(__file__).with_name('museum-expansion-20261006.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
RUN = m.RUN / 'native/kilkis-review-20261010'
OLD = m.RUN / 'native/kilkis-20261010'
PROOF = Path.home() / 'Library/Application Support/Artline/research-proofs/kilkis-20261010'
IID = '4f3ac99d-d622-591d-8885-ac14362fbb50'


def ref(path):
    path = Path(path)
    return dict(path=str(path.relative_to(m.ROOT)) if path.is_relative_to(m.ROOT) else str(path),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def new_text(path, text):
    with Path(path).open('x') as stream:
        stream.write(text)


OBSERVATIONS = {
    1: 'Model horse, rider and wheels form one accessioned toy/model; do not split the attached components.',
    2: 'Headless long-robed statue agrees with the Apollo 201 entry and plates 1–2 of the scholarly excerpt. Multiple plate views depict one statue.',
    3: 'Separate sculpted head with facial hair agrees with the short native description; no named sitter or sculptor inferred.',
    4: 'Broad schematic clay bust differs from the elongated and broken 1404 bust. Retain the native Byzantine period.',
    5: 'Elongated schematic bust with broken lower/side portions differs from 1400; retain the source’s possibly male identification and Byzantine period.',
    6: 'Separate hand-shaped bone fragment, but original parent bed/decoration remains unresolved against 1593 and 1595. Hold independent artwork counting.',
    7: 'Headless draped statuette differs from 201 and 477. Accession 11 is identified as Aphrodite in the scholarly catalogue; its proposed Eros support remains hypothetical.',
    8: '4460 and existing 4461 are different accessioned figurines. The existing description explicitly calls 4461 smaller; visible bases and coloration differ. Two rejoined pieces of 4460 count as one figurine.',
    9: 'Headless enveloping draped female statue matches the Herculanean-type title and differs from statuette 11 and headed statue 1.',
    10: 'Carved half-head fragment differs visually from the hand fragments, but the parent bed/decoration is unresolved. Do not count three independent artworks merely from three fragment accessions.',
    11: 'One dancing bronze figure with raised right arm and short tunic matches the Lar entry. No separate artwork for attributes or base fittings.',
    12: 'Headless clothed standing statue agrees with accession 4 description; distinct from the headed/clothed image attached to accession 3 and nude image attached to accession 2.',
    13: 'One half-grape-cluster fragment has a left-projecting upper edge. Same excavation trench and complementary half-cluster descriptions as 5862; no confirmed join or distinct parent. Hold.',
    14: 'Other half-grape-cluster fragment has a right-projecting upper edge. Thickness differs from 5859, but that does not prove independent parent artwork. Hold.',
    15: 'Confirmed contradiction: native title/description say headless nude male with cloak/tree support, while both the aggregator thumbnail and native image show a headed clothed male. Existing accession 2 has the reciprocal mismatch (clothed description, headless nude thumbnail). Possible swapped images are an inference; no swap, merge or identity reassignment performed.',
    16: 'One broken funerary relief with a large upper figure, smaller figures and inscription. Relief qualifies as sculpture despite inscription-oriented source classification; missing parts are not new objects.',
    17: 'One red-figure pelike. The illustrated Amazon/griffin scene and the reverse scene belong to the same vessel; rejoined pieces count once.',
    18: 'One metal kantharos with large spiral-ended handles. Native description records six rejoined fragments, not six works.',
    19: 'One black-glazed kantharos with ribbed lower body and folded handle ends; distinct silhouette from 4174.',
    20: 'Lidded clay kothon shown together; vessel and lid remain one accessioned work.',
    21: 'Black-glazed ribbed vessel with broken/missing handles. Preserve the question mark in the kantharos identification.',
    22: 'Single oinochoe with one handle; no decorative scene invented from the plain surface.',
    23: 'Silver coin inside gold suspension mount, as described. Reuse as a pendant and both coin faces do not create multiple catalogue objects.',
    24: 'Single silver coin. Obverse and reverse descriptions remain views of one drachma; the native Abydos mint statement is not a named creator assignment.',
    25: 'One gold pendant with a standing figure. Source identifies Fortuna; resemblance to third-century coins does not independently date manufacture of this pendant.',
    26: 'Single open bronze bracelet with rectangular section.',
    27: 'One arched bronze fibula with coiled ends; missing needle and fastening remain parts of this object.',
    28: 'One bronze ring with spiral bezel; do not count the paired spiral elements separately.',
    29: 'One long bent bronze pin with conical head; bending is recorded by the source and does not imply two objects.'
}
HOLD_REASONS = {6: 'unresolved_parent_furnishing', 10: 'unresolved_parent_furnishing',
                13: 'unresolved_fragment_join_or_parent', 14: 'unresolved_fragment_join_or_parent',
                15: 'source_image_metadata_contradiction'}


def main():
    old = m.load(OLD / 'candidate-facts-001.json.gz')
    more = m.load(RUN / 'decorative-candidate-facts-001.json.gz')
    native = old['rows'] + more['rows']
    assert len(native) == 29 and {r['number'] for r in native} == set(range(1, 30))
    assert len({r['source_id'] for r in native}) == 29
    visual = m.load(RUN / 'visual-references-001.json')
    assert len(visual['rows']) == 33 and all(v['available'] for v in visual['rows'])
    assert all(r['first'] is None and r['last'] is None and r['creator_label'] is None for r in native)

    with (m.ROOT / 'docs/research/greek-museums-20261008/delivery.csv').open(encoding='utf-8-sig') as stream:
        historical = [r for r in csv.DictReader(stream) if r['museum_id'] == IID]
    assert len(historical) == 18
    assert not ({r['source_id'] for r in native} & {r['source_id'] for r in historical})
    m.save(RUN / 'historical-identity-comparison-001.json', dict(
        at=m.now(), historical_rows=historical, selected_native_source_ids=[r['source_id'] for r in native],
        matching_historical_source_ids=[], live_production_identity_checked=False,
        limitation='Historical 18-object delivery only. Source-ID absence does not prove absence under translated titles, accession aliases, another institution, or a later import. Fresh scoped production rows/identifiers/citations are mandatory.',
        source_reference=ref(m.ROOT / 'docs/research/greek-museums-20261008/delivery.csv')))

    book_url = 'https://sitestatic.shopster.gr/6150c0d864787b561e67912f/051223_de.pdf'
    entries = [
        dict(catalogue_number='01', accession='201', existing_candidate_number=2,
             title='Άγαλμα Απόλλωνα κιθαρωδού', pages=[31, 32, 33], complete_entry=True,
             period='Late Hellenistic', period_qualified=False, discovery='Mikro Dasos, November 1972',
             material='White fine-grained marble with knots', dimensions='Preserved height 121 cm; plinth height 4 cm',
             note='Comparison with Euphranor’s Apollo Patroos does not establish a creator attribution. Plates 1–2 show this same statue.'),
        dict(catalogue_number='02', accession='11', existing_candidate_number=7,
             title='Αγαλμάτιο Αφροδίτης', pages=[33, 34], complete_entry=True,
             period='Late Hellenistic', period_qualified=False, discovery='Chorygion, December 1960',
             material='White fine-grained marble with grey veins', dimensions='Preserved height 51 cm',
             note='Aphrodite identification is the scholarly author’s determination; an associated Eros is a hypothesis, not another verified holding.'),
        dict(catalogue_number='03', accession='331', existing_candidate_number=None,
             title='Τμήμα γυμνού ανδρικού κορμού', pages=[34], complete_entry=True,
             period='Possibly Late Hellenistic', period_qualified=True, discovery=None,
             material='White marble, probably fine-grained', dimensions='Preserved height 36 cm',
             note='Possible Apollo or Dionysus identification remains unresolved. Full catalogue entry is present; its plate 5 is outside the public excerpt.'),
        dict(catalogue_number='04', accession='2046', existing_candidate_number=None,
             title='Τμήμα γυμνού ανδρικού κορμού', pages=[34, 35], complete_entry=True,
             period='Possibly Late Hellenistic', period_qualified=True, discovery='Europos acropolis, 19 September 1994',
             material='Off-white, relatively coarse-grained marble', dimensions='Preserved height 36 cm',
             note='Interpretation and dating are uncertain. Warrior, Heracles, satyr and centaur comparisons are not firm subject or creator assignments. Plate 5 is unavailable.'),
        dict(catalogue_number='05', accession='134', existing_candidate_number=None,
             title='Τμήμα άνω κορμού αγάλματος Ασκληπιού', pages=[35], complete_entry=False,
             period=None, period_qualified=True, discovery='Metallikon, 1967',
             material='White, relatively fine-grained marble', dimensions='Preserved height 36 cm',
             note='Entry cuts off mid-sentence and continues beyond the excerpt. Dating and the complete identification argument have not been read. Hold pending complete entry; plate 6 unavailable.')]
    for entry in entries:
        entry.update(source_url=book_url, artwork_creator=None, numeric_creation_start=None,
                     numeric_creation_end=None, source_role='scholarly_collection_catalogue',
                     current_display_verified=False, applied=False)
    m.save(RUN / 'publication-object-review-001.json', dict(
        at=m.now(), title='Γλυπτά ρωμαϊκών χρόνων. Ευρήματα στον νομό Κιλκίς', author='Ελένη Παπαγιάννη',
        publisher='University Studio Press', publication_year=2025, isbn='978-960-12-2678-1',
        publisher_url='https://universitystudiopress.gr/item/glypta-romaikon-xronon--051223',
        publisher_reference=ref(RUN / 'publisher-reconciliation-001.json.gz'),
        excerpt_reference=ref(RUN / 'catalogue-excerpt-capture-001.json'),
        contents_reference=ref(RUN / 'catalogue-contents-capture-001.json'),
        publisher_reported_sculptures=87, entries=entries,
        visual_review='All seven excerpt pages previously inspected; contents page visually checked in this review. Printed pages 31–35 contain four complete entries and the beginning of a fifth; plates 1–2 are views of entry 01.',
        coverage_gap='The full 87-entry catalogue, inventory crosswalk on printed page 113 and plates from page 119 are not available in the public excerpt. Do not create 87 placeholders or count overlap as new works.',
        date_policy='Discovery years 1972/1960/1994/1967 and publication year 2025 are not artwork creation years. Roman-period book scope includes Late Hellenistic works; retain each object’s qualified dating. Book author is not artwork creator.'))

    visual_rows = [dict(number=n, observation=OBSERVATIONS[n], decision=HOLD_REASONS.get(n, 'passes_selected_physical_unit_review')) for n in range(1, 30)]
    m.save(RUN / 'visual-assessment-001.json', dict(
        at=m.now(), rows=visual_rows, reference=ref(RUN / 'visual-references-001.json'),
        additional_native_image=ref(RUN / 'native-3-image-capture-001.json'),
        contact_sheets_reviewed=2, individual_refs_reopened=['6', '10', 'C1593', '13', '14', '15', 'native-3'],
        comparator_observations={
            'C1593': 'Intertwined hands carved on a bone fragment; parent bed relationship to 1594/1595 unresolved.',
            'C4461': 'Smaller related clay figurine, distinguished from 4460 by explicit source comparison and visual details.',
            'C1': 'Headed draped female statue, consistent with its source and distinct from the selected headless figures.',
            'C2': 'Headless nude male thumbnail contradicts the source’s clothed male description. Together with accession 3 mismatch this suggests a possible image swap, but accession-linked photographic evidence is needed before correcting either record.'},
        existing_records_modified=False, rights_decision='Native item labels are CC BY-NC-ND 4; generic site footer licenses are separate evidence. Internal references only. No production image attachment or permission inferred.'))

    decisions = []
    for source in native:
        n = source['number']
        row = dict(source)
        row.update(lead_key=source['source_id'], decision='hold' if n in HOLD_REASONS else 'candidate_pending_live_identity',
                   decision_reason=HOLD_REASONS.get(n, 'selected_physical_unit_review_passed'),
                   visual_observation=OBSERVATIONS[n], work_type='sculpture' if n <= 16 else 'unknown',
                   object_form=None, proposed_status='review', ready_to_apply=False,
                   new_production_record=False, image_attachment_authorized=False,
                   current_display_verified=False, numeric_date_eligibility=False,
                   date_review='Native historical period retained literally. It supports an ancient/Byzantine context, but no exact interval is invented and the record remains in review with unknown numeric dates.',
                   museum_confidence_editorial=0.95,
                   museum_confidence_basis='Official Kilkis collection membership, native accessioned object page and SearchCulture institutional provenance; editorial judgment, not calibrated probability.')
        if n in (2, 7):
            row['additional_publication_entry'] = entries[0 if n == 2 else 1]
        decisions.append(row)
    for entry in entries[2:]:
        decisions.append(dict(
            lead_key='kilkis-isbn9789601226781-inventory-' + entry['accession'], number='book-' + entry['catalogue_number'],
            title=entry['title'], inventory_literal=entry['accession'], source_url=book_url,
            native_url=None, source_id=None, decision='candidate_pending_live_identity' if entry['complete_entry'] else 'hold',
            decision_reason='complete_scholarly_entry_qualified_date' if entry['complete_entry'] else 'truncated_catalogue_entry',
            date_display=entry['period'], first=None, last=None, date_precision='unknown', creator_label=None,
            work_type='sculpture', object_form=None, medium_text=entry['material'], dimensions_text=entry['dimensions'],
            source_entry=entry, source_reference=ref(RUN / 'publication-object-review-001.json'),
            proposed_status='review', ready_to_apply=False, new_production_record=False,
            numeric_date_eligibility=False, current_display_verified=False, image_attachment_authorized=False,
            museum_confidence_editorial=0.95,
            museum_confidence_basis='Publisher explicitly identifies this as the Kilkis Museum sculpture collection; individual entries cite the museum inventory and accession. Holdings only, not display; editorial judgment.',
            identity_requirement='Compare accession, subject, material and dimensions against live production and full museum objects; fragment is not known to join another accession. No image of this entry is supplied in the excerpt.'))
    assert len(decisions) == 32 and sum(v['decision'] == 'hold' for v in decisions) == 6
    assert sum(v['decision'] == 'candidate_pending_live_identity' for v in decisions) == 26
    m.save(RUN / 'editorial-decisions-001.json.gz', dict(
        at=m.now(), institution_id=IID, rows=decisions, actual_added=0, candidates_pending_live_identity=26, held_leads=6,
        source_references=[ref(OLD / 'candidate-facts-001.json.gz'), ref(RUN / 'decorative-candidate-facts-001.json.gz'), ref(RUN / 'publication-object-review-001.json')],
        visual_reference=ref(RUN / 'visual-assessment-001.json'), historical_reference=ref(RUN / 'historical-identity-comparison-001.json'),
        script_reference=ref(Path(__file__).resolve()),
        mandatory_before_apply=['Fresh institution-scoped production baseline and object/citation/identifier reconciliation',
                                'Protect all prior campaign records; reconcile translated titles and accession aliases',
                                'Review any new conflicts without silently modifying these pinned facts',
                                'Prepare bounded exact-hash plan, successful backup, apply, verify and zero-write replay'],
        policy='Research candidates only. No fresh DB identity check, execution plan, backup, production addition, image attachment or new numerically eligible count is claimed.'))
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=['lead_key', 'number', 'inventory_literal', 'title', 'date_display', 'decision', 'decision_reason', 'source_url', 'ready_to_apply'])
    writer.writeheader()
    for row in decisions:
        writer.writerow({k: row.get(k) for k in writer.fieldnames})
    new_text(RUN / 'review-ledger-001.csv', output.getvalue())

    selected_ids = {v['source_id'] for v in native}
    index = m.load(OLD / 'selected-index-leads-001.json.gz')
    remaining = [r for page in index['pages'] for r in page['cards']
                 if r['state'] == 'other_index_record' and r['url'].split('/aggregator/edm/')[1] not in selected_ids]
    assert len(remaining) == 18
    m.save(RUN / 'remaining-research-001.json', dict(
        at=m.now(), institution_id=IID, goal_complete=False, actual_added=0,
        last_observed_catalogue_count=18, last_observed_dateeligible_count=0, last_count_date='2026-10-09', fresh_counts=False,
        selected_native_objects=29, additional_book_leads=3, source_objects_reviewed=32,
        candidate_count=26, held_count=6, live_duplicate_check_pending=True,
        source_index_objects=65, historical_index_objects=18, remaining_unselected_index_cards=remaining,
        native_periods=dict(collections.Counter(v['date_display'] for v in native)),
        public_reference_images=0, internal_reference_images=34, full_catalogue_count_claimed=False,
        next_steps=['Restore Google Cloud authentication; run fresh scoped identity queries before deciding any additions',
                    'Resolve accession 2/3 image contradictions through accession-linked museum or scholarly photographic evidence',
                    'Find parent furnishing/fragment join evidence for 1593–1595 and 5859/5862',
                    'Find a legitimate complete catalogue source or further primary publications; public excerpt provides only five entries',
                    'Read the continuation of catalogue entry 05 before accepting inventory 134',
                    'Continue other museums while source/auth gaps remain; directory or publication totals are not imported artwork totals'],
        provider_holds_reference=ref(RUN / 'source-access-holds-001.json'),
        pending_kazantzakis_reference=ref(m.RUN / 'native/kazantzakis-more-20261009/pending-delivery-001.json'),
        decisions_reference=ref(RUN / 'editorial-decisions-001.json.gz')))
    print(dict(reviewed=32, native=29, additional_book_leads=3, pending_identity=26, holds=6, actual_added=0), flush=True)


if __name__ == '__main__':
    main()
