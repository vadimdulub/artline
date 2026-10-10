"""Physical-object and source-version decisions; pending proposals, never DB writes."""
import collections
import csv
import hashlib
import importlib.util
import io
import json
import re
from pathlib import Path

spec=importlib.util.spec_from_file_location('z',Path(__file__).with_name('museum-expansion-zongolopoulos-source-20261010.py'))
z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
m,q,RUN,IID=z.m,z.q,z.RUN,z.IID
PROOF=Path.home()/'Library/Application Support/Artline/research-proofs/zongolopoulos-20261010'
PRIMARY=set(range(7,21))|{21,28,29,30,31,32,36,44,48,53,54,58,60,61,62,63,64,65,66,67,68,80,93,97,99,103,106,107,108,110,122,125,126,127,128}
HOLDS=[
    dict(numbers=[22,23,24,25,26,27],comparators=[21],reason='Alexander: repeated photographs, multiple views and a golden-colour rendering do not establish seven separate originals or casts. Several pages explicitly say first model; retain one supported candidate and hold the others without merging their different exported inventory strings.'),
    dict(numbers=[35,46,47,49,50],comparators=[33,34],reason='Reclining nude: identical image bytes also occur on two existing records. Separate casts versus repeated views are unproven. No new copy or existing merge is justified; the explicitly described plaster model 48 is distinct.'),
    dict(numbers=[37,38,39,41,43,45],comparators=[36],reason='Poseidon: six identical photographs and an opposite-side view of the wire sculpture on a marked acrylic mount. Exported inventory strings differ, but separate objects are unverified. Retain only primary36 in this proposal.'),
    dict(numbers=[40,42],comparators=[44],reason='Mother Cyprus: identical images and another view of the same composition. Further object/edition evidence is needed before counting additional casts.'),
    dict(numbers=[51,52,69,70,71,72,73,74,75,76,77,78,79],comparators=[53,54],reason='Poet: repeated photos, colour/gilding differences and an umbrella variant are unresolved states or casts. Some source text itself describes a more yellow rendering. Keep the structurally distinct sheet-form and solid-form sculptures53/54; do not count every photographic page or infer that a removable umbrella establishes another physical work. Record79 explicitly says trial cast/gilded?, which remains uncertain.'),
    dict(numbers=[55,56,57,59],comparators=[58],reason='Goat model: duplicate and differently angled photographs of the same model composition. No independently identifiable cast or dimensions; hold additional physical units.'),
    dict(numbers=[81,82,83,84,85,86,87,88,89,90,91,92],comparators=[80,93],reason='Prometheus: source mentions multiples and maquettes, but contains five pairs of identical photographs plus mounting/colour variations. Retain one solid-form and one distinct open-wire maquette. Further cast/version evidence is needed for the other records; different exported inventory strings alone are insufficient.'),
    dict(numbers=[96],comparators=[94,95],reason='Horse: already represented by two historical records with similar photographs. Source notes 1999 gilding and 2-3 pieces; those are not proof that this page describes an additional independently dated 1959 cast. No historical creation year is rewritten.'),
    dict(numbers=[100,101,102],comparators=[97],reason='Tall composition with small figure: repeated views of matching construction and explicit source text saying same as No33. Retain a single candidate; exact relationship of the different export identifiers remains unresolved. Price notes are retained as evidence, not catalogue valuations.'),
    dict(numbers=[98],comparators=[99],reason='Zalongo monument maquette: cropped and fuller views share the 1:10 model description and composition. Keep the fuller-view source99 as one candidate; neither the monument itself nor each figure becomes another holding.'),
    dict(numbers=[105],comparators=[104,109],reason='Cyclopean: similar views and finishes overlap historical records. No secure proof of an additional physical version. Preserve both existing records and their differing date evidence pending live review.'),
    dict(numbers=[117,118,119,120,121],comparators=[111,112,113,114,116],reason='Olive: shared photographs overlap several historical records. A nine-piece edition statement supports a series, not assignment of every page to a distinct cast or its casting date. Hold the proposed additional copies; retain existing records unchanged.'),
    dict(numbers=[123,124],comparators=[126],reason='Thessaloniki Fair maquette: identical image pair and a different view of matching construction, base and label. No independent copy established. Distinct fabricated model122 remains separate from126.'),
]
DISTINCT=[
    dict(numbers=[4,5,6,7,8,9,10],reason='Mantinea architectural sheets have distinct elevations, plans, sections and perspective arrangements. Count the four new physical sheets once each; a sheet containing several views is one work. Mantinea is the depicted project, not its holding institution.'),
    dict(numbers=[29,30,31,32],reason='Four framed Zalongo design drawings have different arrangements/view labels and separate literal frame dimensions. Do not use frame measurements as artwork dimensions.'),
    dict(numbers=[18,36],reason='The1953 Poseidon initial maquette is a solid human figure; the1955 version uses open radial wire construction. These are visibly different physical models, not alternate photographs.'),
    dict(numbers=[33,34,48],reason='The source explicitly identifies48 as a plaster model, also visible as a damaged light-coloured support, distinct from the dark reclining nude in historical records.'),
    dict(numbers=[53,54],reason='The Poet candidates differ in base, leg/body construction and broad sheet-form versus solid-form structure. Material composition and dimensions remain unknown unless explicitly supplied.'),
    dict(numbers=[60,61,62,63],reason='The abstract rectangular sculpture and three Z studies have different internal plate/bar layouts and supports; source additionally distinguishes model and trial for62/63. Retain each original source identity.'),
    dict(numbers=[28,68],reason='Dialogue variants have different planar/curved figures and supporting frameworks. Source68 also records fabrication by the artist with Leonidas Gkikas; preserve this contributor note without inventing an accepted co-creator link.'),
    dict(numbers=[80,93],reason='Solid-form and open-wire Prometheus maquettes have clearly different construction and composition, unlike the repeated photographs within each family.'),
    dict(numbers=[110,111,112,113,114,116,125],reason='New110 has a different folded-sheet layout from the historical Olive casting group. New125 is explicitly a glued/joined rather than cast maquette, with visibly different construction. Preserve that qualification; no inference of new copies from colour alone.'),
    dict(numbers=[122,126],reason='Two Thessaloniki Fair maquettes differ in plate construction, thickness and base. The source describes122 as a model of the17-metre public sculpture; the full monument is not a new foundation holding.'),
    dict(numbers=[13,16,17,19,20,103,127,128],reason='Eight works are explicitly by Helen Paschalidou-Zongolopoulou, not George. Distinct pictorial compositions and source records support separate works; original Untitled labels retained alongside descriptive subject text.'),
]


def ref(p):
    p=Path(p)
    return dict(path=str(p.relative_to(m.ROOT))if p.is_relative_to(m.ROOT)else str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def dates(value):
    match=re.fullmatch(r'(\d{4})(?:\s*/\s*(\d{4}))?',value);assert match,value
    start=int(match[1]);end=int(match[2]or match[1]);assert start<=end<=1970
    return start,end


def main():
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    visual=m.load(RUN/'visual-references-001.json');images={v['source_id']:v for v in visual['rows']}
    holds={n:g for g in HOLDS for n in g['numbers']}
    assert len(PRIMARY)==49 and len(holds)==61 and not PRIMARY&holds.keys()
    rows=[]
    for source in sources:
        number=source['number'];f=source['fields'];description=f['Περιγραφή'];start,end=dates(f['Ημερομηνία'][0])
        inventory=[v.removeprefix('Inventory number ')for v in description if v.startswith('Inventory number ')]
        assert len(inventory)==1
        assert f['Πηγή']==f['Εκδότης']==f['Πάροχος']==['Ίδρυμα Γεωργίου Ζογγολόπουλου']
        assert 'Κληροδότημα Γιώργου Ζογγολόπουλου'in description
        state='existing_record'if source['role']=='existing_comparator'else'candidate_primary'if number in PRIMARY else'hold_physical_identity'
        assert state=='existing_record'or number in PRIMARY or number in holds
        kind={'Γλυπτό':'sculpture','Ζωγραφικό έργο':'painting','Σχέδιο':'drawing'}[f['Τύπος'][0]]
        medium=None
        if number==13:kind='drawing';medium='παστέλ σε χαρτί'
        if number in [16,17,19,20]:kind='watercolor';medium='ακουαρέλα'
        if number in [103,128]:medium='λάδι σε μουσαμά'
        if number==48:medium='γύψος'
        decision_reason=holds[number]['reason']if number in holds else'Historical record unchanged; live identity and current count unavailable.'if state=='existing_record'else'Source-backed physical work selected after contact-sheet and relevant comparison review; fresh global and institution-scoped production identity checks remain pending.'
        row=dict(number=number,source_id=source['source_id'],source_url=source['source_url'],
            title=f['Τίτλος'][0],creator_label=f['Δημιουργός'][0],painter_id=None,
            creator_link_state='explicit_source_creator_live_identity_pending',date_display=f['Ημερομηνία'][0],
            first=start,last=end,date_precision='year'if start==end else'range',date_scope='eligible',
            work_type=kind,medium_text=medium,dimensions_text=None,source_description=description,
            inventory_source_literal=inventory[0],inventory_literal=None,
            inventory_note='Preserve the exact exported Inventory number text. Every value appears to repeat a digit sequence, but no verified native accession is available; never silently halve or replace it with a page ID.',
            source_fields=f,aggregator_enrichment=source['enrichment'],source_receipt=source['receipt'],
            image_reference={k:images[source['source_id']][k]for k in ['path','sha256']},rights_links=source['rights_links'],
            image_date_policy_passed=end<=1955,decision=state,decision_reason=decision_reason,
            museum_confidence_editorial=.96,museum_confidence_basis='Explicit foundation publisher/provider/source and bequest description, supported by foundation collection profile. Editorial assessment, not a calibrated probability. Holdings do not prove current display.',
            physical_identity_limit='Shared images may be illustrative of a series; no automatic merge or edition-size expansion. A held row may eventually prove a distinct work.',
            proposed_status='review',ready_to_apply=False,applied=False,current_display_verified=False)
        if number==68:row['contributor_note']='Source states that the artist and Leonidas Gkikas constructed the work; main creator field is George Zongolopoulos.'
        if number in [29,30,31,32]:row['dimension_note']='Dimensions in the description are explicitly for the frame; retain them in source evidence only.'
        if number in [94,95,96]:row['date_note']='1999 is gilding evidence, not a replacement creation year. Source1959 is retained; physical edition identity remains under review.'
        if number==115:row['image_note']='Existing-source thumbnail is partially grey/unusable and shows an architectural setting; do not prepare or attach it. No existing image or metadata altered.'
        rows.append(row)
    assert len(rows)==128
    units=[]
    for row in rows:
        if row['decision']!='candidate_primary':continue
        unit={k:row[k]for k in ['title','creator_label','painter_id','date_display','first','last','date_precision','date_scope','work_type','medium_text','dimensions_text','inventory_source_literal','inventory_literal','proposed_status','ready_to_apply','applied','current_display_verified']}
        unit.update(primary_number=row['number'],primary_source_id=row['source_id'],source_ids=[row['source_id']],
            physical_units_counted=1,identity_state='editorial_source_review_complete_fresh_live_identity_pending')
        units.append(unit)
    counts=dict(collections.Counter(v['decision']for v in rows))
    assert counts==dict(existing_record=18,candidate_primary=49,hold_physical_identity=61)
    assert sum(v['last']<=1955 for v in units)==19
    assert sum(v['creator_label'].startswith('Ελένη')for v in units)==8
    m.save(RUN/'physical-unit-review-001.json',dict(at=m.now(),contact_sheets_reviewed=7,focused_comparison_sheets_reviewed=11,
        holds=HOLDS,distinct_comparisons=DISTINCT,exact_duplicate_image_groups=visual['exact_duplicate_images'],
        inference_policy='Retain a bounded set of distinguishable source objects. Hold ambiguous additional records rather than force merges or treat every exported inventory string as another physical cast. No secondary source citations are automatically attached to primaries.',
        existing_record_audit_flags=[dict(numbers=[33,34],reason='Identical source photograph; casts versus duplicate catalogue records unresolved.'),
            dict(numbers=[111,114],reason='Identical source photograph; nine-piece series label does not resolve these individual records.'),
            dict(numbers=[94,95],reason='Similar horse photographs and shared1999 gilding note require physical-version review.'),
            dict(numbers=[104,109],reason='Related Cyclopean composition and differing source dates require version review; no automatic merge.'),
            dict(numbers=[115],reason='Source thumbnail is incomplete/unusable. Preserve historical record without image attachment.')],
        visual_reference=ref(RUN/'visual-references-001.json'),comparison_reference=ref(RUN/'comparison-references-001.json')))
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=rows,counts=counts,
        source_reference=ref(RUN/'selected-source-records-001.json.gz'),physical_review_reference=ref(RUN/'physical-unit-review-001.json'),
        image_policy_reference=ref(RUN/'image-policy-review-001.json'),script_reference=ref(Path(__file__).resolve())))
    m.save(RUN/'candidate-physical-units-001.json.gz',dict(at=m.now(),institution_id=IID,rows=units,
        proposed_new_units=49,numeric_date_candidates=49,unknown_date_candidates=0,actual_added=0,
        decisions_reference=ref(RUN/'editorial-source-decisions-001.json.gz'),
        mandatory_next_steps=['Restore production authentication and obtain fresh scoped rows and global source/title/creator identity comparisons',
            'Resolve George and Helen creator identities using verified painter records; do not fabricate painter links',
            'Audit repeated photographs among historical records before treating their count as distinct physical artworks',
            'Reconcile literal inventory strings without silently halving repeated digits',
            'Exact-hash plan, protected prior records, successful backup, apply, readback and zero-write replay']))
    out=io.StringIO(newline='');writer=csv.DictWriter(out,fieldnames=['number','source_id','title','creator_label','date_display','work_type','inventory_source_literal','decision','decision_reason','source_url']);writer.writeheader()
    for row in rows:writer.writerow({k:row[k]for k in writer.fieldnames})
    (RUN/'review-ledger-001.csv').open('x').write(out.getvalue())
    print(json.dumps(dict(counts=counts,types=dict(collections.Counter(v['work_type']for v in units)),image_date_candidates=19,actual_added=0)),flush=True)


if __name__=='__main__':main()
