#!/usr/bin/env python3
"""Pin the individually reviewed first Irish painting selection, without writes."""
import hashlib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('ireland',Path(__file__).with_name('museum-expansion-ireland-20261006.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
m=i.m

HOLDS={
    '3156':('creator_scoped_version_overlap','Compare existing Anguissola artwork ec296bcc-db3e-577a-99a4-7ad928ea9169: Alessandro Farnese under another title and a 1562 date. Do not create an overlapping portrait.'),
    '4706':('creator_scoped_version_overlap','Compare existing Hals Fisher Boy bb59bc2b-cfeb-5bb8-bb90-47f3041d3503, dated 1630–1632. New native inventory cannot by itself establish a different physical work.'),
    '7314':('creator_scoped_version_overlap','Compare existing Ostade Peasants Drinking and Making Music in a Barn aa868493-391d-548e-b72f-f905a5b80600; the changed English title and circa date need version reconciliation.'),
    '8121':('native_creation_narrative_conflict','This is explicitly a later partial copy after the Boston work, but the native header says first quarter of the sixteenth century while the label says this copy belonged to a prominent collection in the fifteenth century. Retain both and hold the new record.'),
    '10779':('native_creation_precision_requires_review','The header gives 1599. Both description and label call the inscription a terminus ante quem. Preserve the explicit year and qualification for precision review.'),
    '6186':('native_creation_narrative_conflict','Header gives 1782; the label describes the sitter wearing the insignia of an order established in 1783. Possible later alteration or catalogue discrepancy requires review.'),
    '6217':('native_creation_provenance_conflict','Header and signature give 1856, but provenance lists a sale in April 1855. Preserve the evidence and resolve the chronology before adding.'),
    '6897':('qualified_contributor_requires_review','The object credits Wijnants, while the description ascribes its figures to Johannes Lingelbach. Preserve the contributor qualification for a reviewed creator-label decision.'),
}

NOTES={
    '6113':'One separately inventoried Katherina Knoblauch panel. Her husband Friedrich Rohrbach is the Chicago companion, not this sitter; the coat of arms on the reverse is not another imported artwork.',
    '6427':'Heinrich Knoblauch is a different sitter and panel from Katherina and her husband Friedrich. The museum explicitly says Heinrich and Katherina are not companion pieces.',
    '8881':'The historical 1854 deposit was to the Irish Institution for the future National Gallery. The present credit calls it Presented and the current label explicitly identifies it as the first Dutch work acquired by the Gallery; no present incoming loan is inferred.',
    '7418':'NGI.33 is 61 x 44 cm, acquired in 1869. London NG176 is 165 x 106 cm, acquired in 1840; the existing Metropolitan Museum record is a small drawing. Distinct inventories, media and dimensions establish separate works despite similar titles.',
    '11764':'NGI.95 is the 109 x 246 cm canvas retained by Cardinal Polignac. Its description distinguishes the version sent to the king. Chicago 1933.914 is a 26.8 x 45 cm painting dated 1729, not this 1731 canvas.',
    '11797':'The catalogue distinguishes this Granacci painting from later repetitions and copies. Preserve its own circa 1494 date and NGI.98 inventory.',
    '2046':'A seventeenth-century copper-panel copy after Guido Reni. Preserve After in the creator label; the 1630 plague is historical subject/prototype context, not an exact creation year for this copy.',
    '2621':'A historical loan in 1875 is followed by an explicit presentation in 1891 in both provenance and credit. The 1779 event and 1779–1780 creation interval remain distinct.',
    '3379':'One complete canvas, NGI.181, depicting the view above Augustus Bridge. The companion view below the bridge has the separate inventory NGI.182.',
    '3490':'One complete companion canvas, NGI.182, depicting the view below Augustus Bridge. Its shared sale lot with NGI.181 does not make them the same physical artwork.',
    '5644':'Creation remains circa 1854; 1170 is the depicted marriage, and 1855/1879 are provenance events. The 1854 exhibition also supports the creation context.',
    '6426':'Count one separately inventoried detached predella panel, NGI.242, not the complete San Marco altarpiece. The existing Healing of Palladia panel has a different subject and NGA inventory 1952.5.3. The third-century martyrdom is not the creation date.',
    '6464':'Retain the explicit 1642 creation date and the Monogrammist IS label. The separately supplied floruit 1645–1658 is not a birth/death boundary and does not authorize inventing an artist profile or changing the work date.',
    '6841':'One separately inventoried painted study after a live model, NGI.275, 96.7 x 47.7 cm. It is described as preparation for Saint Sebastian; the existing Viennese Study for a thief is a different subject and inventory.',
    '6852':'Preserve Studio of Willem van de Velde II. A studio work dated 1700–1710 need not end at the named master’s death in 1707; do not upgrade the attribution to the master himself.',
    '4045':'A posthumous sitter portrait dated circa 1820; the sitter’s death in 1799 does not replace the creation date.',
}


def main():
    source=i.RUN/'ireland-001-research.json.gz';research=m.load(source)
    with m.connect() as db:collisions=i.title_collisions(db,research['records'])
    keys={m.norm(v[k]) for v in collisions for k in ['title','alternate_title'] if v[k]}
    held=list(research['held']);records=[];reviews=[]
    for record in research['records']:
        oid=record['source_record_id'];title=record['facts']['title']
        if m.norm(title) in keys:
            matches=[v for v in collisions if any(v[k] and m.norm(v[k])==m.norm(title) for k in ['title','alternate_title'])]
            held.append(dict(record=record,reason='catalogue_title_identity_requires_review',existing=matches));continue
        if oid in HOLDS:
            reason,note=HOLDS[oid];held.append(dict(record=record,reason=reason,editorial_note=note));continue
        raw=i.captured_body(dict(receipt=record['source_receipt'],body_path=record['body_path']))
        assert i.validate_record(record,raw)==record['facts']
        review=dict(source_record_id=oid,source_capture_sha256=record['source_receipt']['sha256'],
            reviewed_fields=['Title','Date','Credit Line','Object number','Medium','Dimensions','Signed','Inscription','Description','Label Text','Provenance'],
            decision='approved_new_review_record',note=NOTES.get(oid,'Native acquisition credit, individual inventory, creation field and catalogue narrative agree. Preserve the full source creator label and unknown fields; subject, acquisition and artist-life dates are not creation dates.'))
        record['raw_source_record']['editorial_review']=review;records.append(record);reviews.append(review)
    assert len(records)==92
    evidence_paths=['identity-before-001.json','ireland-001-title-collisions.json','creator-identity-review-001.json',
        'creator-alias-identity-review-001.json','unlinked-creator-identity-review-001.json',
        'selected-version-comparisons-001.json','selected-version-comparisons-002.json',
        'ireland-wikiart-versions-001.json','ireland-artic-versions-001.json','ireland-london-versions-001.json']
    evidence=[dict(path=str((i.RUN/p).relative_to(m.ROOT)),sha256=hashlib.sha256((i.RUN/p).read_bytes()).hexdigest()) for p in evidence_paths]
    plan=dict(at=m.now(),records=records,held=held,research_source=str(source.relative_to(m.ROOT)),research_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        identity_evidence=evidence,editorial_reviews=reviews,before=research['before'],indexes=research['indexes'],
        policy='Native painting index plus individually reviewed object pages and acquisition credits. Review-only additions. Unknown and qualified creators remain literal object labels. No images, display assertions, publication or existing metadata changes.')
    path=m.RUN/'ireland-001-current-plan.json.gz';m.save(path,plan)
    m.save(i.RUN/'followup-queue-001.json',dict(at=plan['at'],held=held,next_index=research['next_index'],policy='Unresolved duplicate, version, date and loan candidates; no approval inferred from index presence.'))
    print('Reviewed Ireland plan',len(records),'held',len(held),'sha256',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':main()
