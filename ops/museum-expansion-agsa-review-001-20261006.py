#!/usr/bin/env python3
"""Pin 131 individually reviewed AGSA additions; preparation does not write DB."""
import hashlib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('agsa',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m

HOLDS={
 '30102':('source_date_inscription_conflict','Nolan Albert Tucker: header and caption give 1945, while the signature transcription says Oct 41. Preserve both dates and resolve the conflict.'),
 '75120':('classification_requires_review','Appointment card for Worth, London: ink and pencil on card in decorative arts, although the native category says Painting. Resolve object classification before a painting import.'),
 '65901':('compound_object_requires_review','Artist’s paint box with landscape: determine the scope of the separately painted panel and assembled paint-box object before counting this as one painting.'),
 '68905':('classification_requires_review','Buddhist manuscript parabaik: native Painting category describes an entire manuscript/book object. Retain the lead for object-scope and classification review.'),
 '23780':('existing_creator_subject_identity','Existing d5caae0e-326c-5647-a373-3f47d8ea5620 is Esaias van de Velde’s 1622 landscape with travellers crossing a bridge, under the same title without its final phrase. Do not create an overlapping record.'),
 '24282':('existing_creator_subject_identity','Existing ac97b683-c3fc-515e-a123-fdcc64b70068 is Glover’s 1835 view of his house and garden, with Tasmania appended to the title. Preserve it for holding/inventory reconciliation.'),
 '24797':('version_identity_requires_review','Compare existing Claesz Still Life, 1643, 616e35f8-b8a6-4448-b357-fc6bf558f362, and other crab/breakfast compositions. Missing existing inventory and changed title do not establish a different physical work.'),
 '23807':('version_identity_requires_review','Wright painted many Vesuvius versions. Existing b465d227-ce97-5397-adc6-2ef57fb2fcf4 has an unresolved date and no inventory; compare its composition and source before adding AGSA 20083P15.'),
 '24970':('version_identity_requires_review','Existing 88e7667e-3ef9-559f-9a9a-57b928900e09 is Atomic Image, 1952, inventory 0662, with no accepted museum holding. Its Wikidata source could not be fetched (HTTP 403). The earlier editorial note identifying Wolverhampton was not verified and is withdrawn. Compare physical-object identity with AGSA Atomic landscape, 1957, 0.1785 before addition; different titles and dates alone are insufficient.'),
 '26641':('version_identity_requires_review','Guardi’s broadly titled architectural capriccio needs comparison against the 135 creator-scoped works, including translated capricci. Preserve AGSA 993P19, its wood support and 19 x 15.2 cm dimensions as version evidence.'),
 '27533':('version_identity_requires_review','Existing bb69350f-eefc-4ce3-8b72-1ac6e472288c is a Pulzone Cardinal Ferdinand de’ Medici portrait with an unverified eighteenth-century date. Resolve original/copy identity before adding the 1580 AGSA canvas.'),
 '26788':('historical_attribution_identity_requires_review','The Van Dyck married couple was formerly a Cornelius de Vos portrait of Frans Snyders and his wife at Detroit. Reconcile historical attribution/title identities; retain the native 1993 gift credit and 1994 acquisition narrative discrepancy.'),
 '24260':('version_identity_requires_review','Retain and studio in the Van de Velde label. Compare the small-vessel/inlet composition against existing shore and harbour pictures, including broadly titled translations, before addition.'),
 '23973':('version_identity_requires_review','Catherine Fenn is only a tentative sitter identification. Compare existing Cornelius Johnson unknown-lady portraits before treating the changed sitter title and 1623 source date as a distinct identity.'),
 '23904':('version_identity_requires_review','Claude’s capriccio is described as the first Liber Veritatis entry. Distinguish the painting from Roman Forum prints and translated or generically titled landscape records before adding it.'),
}

NOTES={
 '24206':'The native 1891 canvas and its narrative agree. The depicted stampede is explicitly a constructed scene, not a dated witnessed event. Existing Roberts Artist’s Camp and Queenscliff boat records are different subjects; broader breakaway/title searches found no corresponding artwork.',
 '24149':'Preserve John Russell’s source dates 1858–1930 and the 1891 artwork date. The catalogue narrative describes his Antibes visit in 1890–1891. No identity is inferred with the earlier British artist of the same name.',
 '23882':'The signed 1888 Conder painting is a new catalogue identity. Creator-scoped works and the broader Mentone title search found no corresponding artwork; the 1981 centenary grant is acquisition context.',
 '24143':'One small Japanese oil painting on wood with its original frame. The 1887–88 range is explicit shorthand; 1975 is acquisition. Existing Menpes Sabot Shop and Paris Shop Front records describe prints and other locations.',
 '25295':'Retain attributed to Gerrit Dou and the verso DT monogram exactly. Neither the inscription nor a related old-man subject upgrades the attribution.',
 '25649':'Retain Cambridge Michaelmas 1969, AGSA 752P2. Existing Cambridge Green is Tate T01109, 1968, with a different title and source identity; equal canvas dimensions do not make them the same work.',
 '26527':'Preserve the museum’s current Caroline Matilda Sotheron identification and circa 1808 date. The source explains the former Lucy Sotheron identification. Searches of both names and the Lawrence catalogue found no corresponding record; the John Wright miniature mentioned in the text is a separate work.',
}


def main():
    source=a.RUN/'agsa-001-research.json.gz';research=m.load(source)
    notes=dict(NOTES)
    working_paths=sorted(a.RUN.glob('editorial-working-notes-*.json'))
    for p in working_paths:
        for ids,note in m.load(p).get('notes',{}).items():
            for oid in ids.split('/'):
                if oid not in notes:notes[oid]=note
    held=list(research['held']);records=[];reviews=[]
    for r in research['records']:
        oid=r['source_record_id']
        if oid in HOLDS:
            reason,note=HOLDS[oid];held.append(dict(record=r,reason=reason,editorial_note=note));continue
        if len(records)>=131:
            held.append(dict(record=r,reason='outside_selected_200_target',editorial_note='Candidate retained beyond the 131-work selection. No import approval inferred; recheck current catalogue identity before later use.'));continue
        raw=a.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
        assert a.validate_record(r,raw)==r['facts']
        review=dict(source_record_id=oid,source_capture_sha256=r['source_receipt']['sha256'],
            reviewed_fields=['header_parts','creation_and_medium','creator_names','fields','narratives','image_captions'],
            decision='approved_new_review_record',note=notes.get(oid,'Individual native accession, acquisition credit, creator label and creation field agree. Native narrative, inscriptions, captions and creator/title identity leads were reviewed. Preserve source uncertainties and unknown fields; no artist profiles, display claims or publication inferred.'))
        r['raw_source_record']['editorial_review']=review;records.append(r);reviews.append(review)
    assert len(records)==131 and research['before']['eligible']+len(records)==200
    assert not set(HOLDS)&{r['source_record_id'] for r in records}
    with m.connect() as db:
        assert not a.title_collisions(db,records)
        known,titles,inventories=a.existing_keys(db,research['museum']['id'])
        assert not any(r['source_record_id'] in known or m.norm(r['facts']['title']) in titles or a.inventory_keys(r['facts']['accession'])&inventories for r in records)
    paths=[a.RUN/p for p in ['agsa-001-identity-before.json','creator-identity-review-001.json','additional-creator-name-leads-001.json',
        'creator-title-comparison-leads-001.json','subject-version-identity-leads-001.json']]+working_paths
    evidence=[dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    plan=dict(at=m.now(),records=records,held=held,research_source=str(source.relative_to(m.ROOT)),research_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        identity_evidence=evidence,editorial_reviews=reviews,before=research['before'],indexes=research['indexes'],
        policy='131 selected official AGSA paintings including watercolours and bark paintings. Full source dates, creator/cultural labels, attributions and rights evidence retained. Review-only metadata additions; no images, artist links, display claims or publication changes.')
    prior=m.RUN/'agsa-001-initial-review-plan.json.gz'
    if prior.exists():
        plan['review_revision']=dict(supersedes=str(prior.relative_to(m.ROOT)),sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
            reason='Hold Bowen pending same-object identity review and withdraw unverified foreign holding in its earlier editorial note. Select reviewed James Cant 35758 instead. Correct an unrelated holding-note typo; preserve the complete initial unapplied plan.')
    p=m.RUN/'agsa-001-current-plan.json.gz';m.save(p,plan)
    m.save(a.RUN/'followup-queue-001.json',dict(at=plan['at'],held=held,resume_index=research['resume_index'],unprocessed_captured_rows=research['unprocessed_captured_rows'],next_index=research['next_index'],
        policy='Held and unselected candidates remain research evidence. The unused captured rows are not reviewed or approved.'))
    print('AGSA reviewed',len(records),'held',len(held),'sha256',hashlib.sha256(p.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':main()
