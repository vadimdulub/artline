"""Preserve source evidence and count physical supports after selected visual review."""
import collections
import csv
import importlib.util
import io
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-zongolopoulos-paintings-comparisons-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN,PROOF=c.m,c.RUN,c.PROOF
IID=c.v.t.z.IID
DOUBLE={6,14,28,41,44,50,51,56,95,103,122,123,136,139,150,151}
COLLAGE={18,26,31,56,68,75,85}
HOLD={61}
DISTINCT=[
    dict(numbers=[6,44,50],reason='Different landscape arrangements: farmhouse and central tree; yellow house behind fence; broad field with distant windmill/buildings. These are not crops of one painting. All three describe reverse sides, each counted as one physical support.'),
    dict(numbers=[27,28,82,83,115,130],reason='Window scenes differ in orientation, window frames, curtains, balcony ironwork, vegetation and interior objects. Similar subjects do not establish duplicate objects. Source115 subject tags refer to a male torso, but its explicit room/window description agrees with the image; preserve the conflicting tags without turning them into another work.'),
    dict(numbers=[65,74],reason='Illustrated maps have different land/sea layouts, extent and placement of illustrations. Separate source objects, no claim that one is merely a colour version of the same digital image. Physical medium unrecorded.'),
    dict(numbers=[37,43],reason='Shared publication page108-2 is not an object identifier. Different geometric arrangements, painted edges and shapes support distinct canvases, without assigning either to a named artist.'),
    dict(numbers=[18,26,31],reason='Separate paper collage compositions. Source31 is one collage/pastel study containing multiple panels, not a set of separately counted works; motifs resembling the geometric sheets do not make the collage their original support.'),
    dict(numbers=[56,68,75,85],reason='Balsa collage studies differ in shape arrangement, orientation, edges and attached elements. Retain separate source identities; source56 is explicitly two-sided and counts once. No undocumented reverse-side association or material date inferred.'),
    dict(numbers=[33,41,46],reason='Chimney compositions differ in arrangement and supports. Count source41 once despite two-sided description. Source book/exhibition numbers are not dates.'),
    dict(numbers=[95],reason='The painting visibly contains repeated foot/sole forms, consistent with its description. The unsigned reverse is not a second candidate.'),
    dict(numbers=[131,132,133,134,135,140,144,145,146,147],reason='Geometric sheets have different line, circle and colour arrangements. Source132/133 and131/140 are related compositions but not duplicate photographs or alternate crops. Missing material fields remain unknown.'),
    dict(numbers=[97],previous_numbers=[103],reason='Current64368 and previous64417 are different Helen abstract paintings: brown diagonal construction with coloured top rectangles versus a dark vertical composition. Shared1960 evidence does not make them identical.'),
    dict(numbers=[52],previous_numbers=[3],reason='The star-like abstract composition differs from the existing64476 image in forms, background and arrangement. Preserve both sources and dates; no existing record is changed.'),
]

def main():
    sources=m.load(RUN/'selected-source-records-001.json.gz')['rows']
    visual=m.load(RUN/'visual-references-001.json');images={r['number']:r for r in visual['rows']}
    rows=[]
    for s in sources:
        n=s['number'];f=s['fields'];desc=f['Περιγραφή'];text=' | '.join(desc);lower=text.lower()
        assert not f.get('Ημερομηνία')
        assert f['Πηγή']==f['Εκδότης']==f['Πάροχος']==['Ίδρυμα Γεωργίου Ζογγολόπουλου']
        assert 'Κληροδότημα Γιώργου Ζογγολόπουλου'in desc
        inventory=[v.removeprefix('Inventory number ')for v in desc if v.startswith('Inventory number ')]
        assert len(inventory)==1
        kind='painting';basis='Museum-supplied broad painting type; medium unspecified unless preserved in source descriptions.'
        if n in COLLAGE or n in {65,74,116,131,145,146}:
            kind='unknown';basis='Collage/mixed media or insufficiently specific physical medium; preserve literal descriptions without inventing a controlled type.'
        elif n==1:kind='print';basis='Explicit lithograph description takes precedence over the broad painting category.'
        elif 'ακουαρέλα'in lower:kind='watercolor';basis='Explicit source watercolour description.'
        elif 'παστέλ'in lower and 'ακρυλικό'not in lower or n==71:kind='drawing';basis='Explicit source pastel or ink-on-paper description.'
        elif 'λάδι'in lower or 'ακρυλικ'in lower:kind='painting';basis='Explicit source oil or acrylic description.'
        first=last=1960 if n==97 else None
        date_note='No dedicated date field or secure physical creation date. Do not infer dates from style, artist lifespan, inventory, exhibition/page numbers or depicted place.'
        if n==97:date_note='Museum description explicitly transcribes E. ZOGG./1960 on an oil canvas. Record1960 as an inscribed year reported by the source, not an independently deciphered signature. ReverseNo14 is not a date.'
        if n==1:date_note='Museum description transcribes a1933 signature on lithograph17/20. Retain the inscription year and impression number; the printing date of this physical impression is not independently established. Numeric creation fields remain null.'
        label=f['Δημιουργός'][0];catalogue_label=label
        creator_state='source_explicit_live_painter_identity_pending'
        creator_note='Preserve the museum-supplied creator; no painter ID inferred from the institution or depicted subject.'
        if label=='Άγνωστος δημιουργός':creator_state='anonymous_source_label';creator_note='Anonymous museum collection object; do not assign George or Helen merely because the foundation holds it.'
        if n==28:creator_note+=' The reverse is described as probably by Helen; this does not establish her as creator of the front or whole support.'
        if n==50:
            creator_state='conflicting_creator_evidence_no_accepted_link'
            catalogue_label='Απόδοση αβέβαιη: Γιώργος Ζογγολόπουλος (πεδίο δημιουργού), Ε. Ζογγολόπουλος (υπογραφή κατά την περιγραφή)'
            creator_note='Museum creator field says George; description reports E. Zongolopoulos on one side. Preserve both claims and the source field, with qualified object-level display text; no accepted painter link.'
        if n==89:
            creator_state='qualified_source_attribution_no_accepted_link'
            catalogue_label='Αποδιδόμενο στην Ελένη Πασχαλίδου - Ζογγολοπούλου'
            creator_note='Museum field names Helen, but description specifies unsigned and from Helen folder. Preserve the evidential basis and use a qualified attribution pending live reconciliation.'
        decision='hold_source_image_conflict'if n in HOLD else'candidate_primary'
        reason='Description is Girl with an umbrella, oil on wood, but both catalogue and preservation previews show a geometric abstract composition. Hold this source object pending correction or object evidence; no image swap or creator inference.'if n in HOLD else'Distinct source-backed physical work after selected contact/comparison review; fresh institution/global source/title/creator checks still required.'
        row=dict(number=n,source_id=s['source_id'],source_url=s['source_url'],title=f['Τίτλος'][0],creator_label=label,
            catalogue_creator_label=catalogue_label,creator_link_state=creator_state,creator_note=creator_note,painter_id=None,
            first=first,last=last,date_display='1960 (inscribed year reported by source)'if n==97 else'Unknown',
            date_precision='year'if n==97 else'unknown',date_scope='eligible'if n==97 else'requires_editorial_review',date_note=date_note,
            inscription_year=1933 if n==1 else 1960 if n==97 else None,impression_number='17/20'if n==1 else None,
            work_type=kind,work_type_basis=basis,medium_text=None,dimensions_text=None,source_description=desc,
            inventory_source_literal=inventory[0],inventory_literal=None,
            inventory_note='Exported digit sequences appear doubled; retain literal source text, never halve it or substitute the page ID as an accession.',
            source_fields=f,aggregator_enrichment=s['enrichment'],source_receipt=s['receipt'],
            image_reference={k:images[n][k]for k in ['path','sha256']},rights_links=s['rights_links'],
            digital_image_rights=f['Δικαιώματα'],image_date_policy_passed=False,
            image_hold='Physical creation date unknown or later than1955; internal review images only. The specific Greek-source approval remains valid and NC/ND alone is not the hold reason.',
            two_sided_support=n in DOUBLE,reused_support=n==45,physical_units_counted=0 if n in HOLD else 1,
            decision=decision,decision_reason=reason,museum_confidence_editorial=.96,
            museum_confidence_basis='Explicit foundation provider/publisher/source and bequest description; editorial assessment, not a calibrated probability. No current display claim.',
            proposed_status='review',ready_to_apply=False,applied=False,current_display_verified=False)
        if n==44:row['side_note']='Descriptions disagree on child versus female portrait and side ordering. Preserve both accounts; one support, no invented third work.'
        if n==123:row['side_note']='Image shows the boats/landscape side identified in the description; fruit/jug reverse not counted separately.'
        if n==115:row['subject_note']='Museum description and image agree on room/window; conflicting male-torso subject tags remain source evidence only.'
        if n==90:row['inscription_note']='Small signature visible but no year securely deciphered; no date invented from thumbnail.'
        rows.append(row)
    units=[]
    keys=['title','creator_label','catalogue_creator_label','creator_link_state','creator_note','painter_id','first','last','date_display','date_precision','date_scope','date_note','inscription_year','impression_number','work_type','work_type_basis','medium_text','dimensions_text','inventory_source_literal','inventory_literal','two_sided_support','reused_support','physical_units_counted','proposed_status','ready_to_apply','applied','current_display_verified']
    for r in rows:
        if r['decision']=='candidate_primary':units.append(dict({k:r[k]for k in keys},primary_number=r['number'],primary_source_id=r['source_id'],source_ids=[r['source_id']],identity_state='editorial_source_review_complete_fresh_live_identity_pending'))
    assert len(rows)==151 and len(units)==150
    assert sum(r['first']is None for r in units)==149 and sum(r['two_sided_support']for r in units)==16
    assert sum(r['creator_label']=='Άγνωστος δημιουργός'for r in units)==37
    m.save(RUN/'physical-unit-review-001.json',dict(at=m.now(),contact_sheets_reviewed=8,focused_comparison_sheets_reviewed=10,preservation_previews_reviewed=5,
        distinct_comparisons=DISTINCT,held_numbers=sorted(HOLD),two_sided_numbers=sorted(DOUBLE),
        source_image_conflict='61/64218: Girl with an umbrella description versus geometric abstract image in both source presentations.',
        exact_duplicate_image_groups=visual['exact_duplicate_images'],
        visual_reference=c.ref(RUN/'visual-references-001.json'),comparison_reference=c.ref(RUN/'comparison-references-001.json'),prior_comparison_reference=c.ref(RUN/'prior-pictorial-comparison-001.json'),
        limits='One physical support per source candidate; no automatic aliasing, copy/edition expansion or guaranteed global novelty. Unknown dates remain in review. Public image previews do not establish provenance or dates by style.'))
    m.save(RUN/'editorial-source-decisions-001.json.gz',dict(at=m.now(),rows=rows,counts=dict(collections.Counter(r['decision']for r in rows)),
        source_reference=c.ref(RUN/'selected-source-records-001.json.gz'),physical_reference=c.ref(RUN/'physical-unit-review-001.json'),script_reference=c.ref(Path(__file__).resolve())))
    m.save(RUN/'candidate-physical-units-001.json.gz',dict(at=m.now(),institution_id=IID,rows=units,proposed_new_units=150,numeric_date_candidates=1,unknown_date_candidates=149,
        anonymous_creator_candidates=37,qualified_or_conflicting_named_candidates=2,actual_added=0,production_images_prepared=0,
        prior_candidates=49,combined_pending_candidates=199,combined_numeric_date_candidates=50,combined_unknown_date_candidates=149,
        decisions_reference=c.ref(RUN/'editorial-source-decisions-001.json.gz'),prior_candidate_reference=c.ref(c.v.t.OLD/'candidate-physical-units-001.json.gz'),
        mandatory_next_steps=['Restore production authentication; obtain fresh scoped rows and bounded global source/title/creator comparisons',
            'Preserve anonymous creators and qualified attributions; verify named painter links and doubled inventory export semantics',
            'Check reverse-side and existing sculpture duplicate flags before interpreting row counts as physical-work counts',
            'Exact-hash proposal, protected prior rows, successful backup, apply, readback and zero-write replay',
            'Retain unknown-date review status and require specific creation-date evidence before preparing further Greek-source public images']))
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=['number','source_id','title','creator_label','catalogue_creator_label','date_display','work_type','two_sided_support','decision','decision_reason','source_url']);w.writeheader()
    for r in rows:w.writerow({k:r[k]for k in w.fieldnames})
    (RUN/'review-ledger-001.csv').open('x').write(out.getvalue())
    print(dict(candidates=len(units),unknown_dates=149,types=dict(collections.Counter(r['work_type']for r in units)),combined_pending=199,actual_added=0))

if __name__=='__main__':main()
