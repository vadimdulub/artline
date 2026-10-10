#!/usr/bin/env python3
"""Pin forty reviewed Irish additions toward the 200 eligible-date target."""
import hashlib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('ireland',Path(__file__).with_name('museum-expansion-ireland-20261006.py'))
i=importlib.util.module_from_spec(spec);spec.loader.exec_module(i)
m=i.m

HOLDS={
    '6950':('version_identity_requires_review','Compare Dirck Stoop hunting party 07c9ab46-454b-55d1-9c40-39a95e63d7fc, Rijksmuseum SK-A-395, 1649. The new 1640s period includes that year; resolve the physical versions before addition.'),
    '6961':('version_identity_requires_review','Canaletto painted many versions of Saint Mark’s Square. The 287 creator-scoped leads include translated titles and unlocated works; a date difference alone does not prove distinct identity.'),
    '7047':('date_and_version_identity_requires_review','The source dates this circa 1765 but lists 1761 and 1765 exhibitions. Existing Yale B1975.4.1237 (d2f3c897-1c51-5229-8367-cb3b764e5cbd) is Falstaff Inspecting the Recruits, 1761–1765. Resolve the version and source chronology.'),
    '7086':('existing_creator_sitter_identity','Existing 4b5cf458-f47d-5833-96bc-a29dd6405ff4 is Lawrence’s John Jeffreys Pratt, dated 1802, under a shorter title. Preserve it and hold the overlapping native portrait for reconciliation.'),
    '7150':('source_date_inscription_conflict','Native Date says 1797; the Signed field transcribes 1796 on the reverse. Preserve both and resolve the discrepancy before adding.'),
    '7337':('version_identity_requires_review','Compare the 45 de Hooch creator-scoped records, including translated interiors and a woman with two men. Board-game and guardroom subjects need composition/version reconciliation.'),
    '7359':('version_identity_requires_review','The Dusart subject may overlap Peasants outside an Inn, KMSsp667 (4102ddd9-5142-4d68-ac54-d4a1bc7f8588), or other translated genre scenes. Retain the signed 1692 NGI facts as a lead.'),
    '7376':('version_identity_requires_review','Existing Claesz Breakfast Piece 38f010c8-3784-444d-afd2-d380a6ec81cd lacks inventory/holding and has an unverified 1640–1649 date. Compare versions rather than treating the new 1637 date as proof of difference.'),
    '7524':('version_identity_requires_review','The additional David III Rijckaert spelling search found Kroscene KMSsp281 and Et bondegilde KMSsp282. Reconcile the farmhouse/inn compositions before creating a possible translated-title overlap.'),
    '8103':('sitter_version_identity_requires_review','Native title explicitly identifies Benjamin Hoadly the physician/playwright (1706–1757). Existing Hogarth Tate N02736 names the bishop; other portraits are attributed to Sarah Hoadly. Preserve this promising distinct-sitter lead for source-backed version comparison.'),
    '8113':('source_date_creator_chronology_requires_review','Native circa 1772 date follows the stated Jacob Ennis death in 1771. Circa may accommodate this, but preserve the discrepancy for editorial date/attribution review rather than making an automatic decision.'),
    '8515':('version_identity_requires_review','Existing Duyster Interior Guardroom, Soldiers off Duty, 32ab609a-0ba0-590e-b9ba-f7eacb19697a, has no inventory or holding and a 1635 date. Compare the composition against native signed 1632 NGI.436.'),
    '8859':('existing_creator_subject_identity','Existing 32f71f7c-38b6-5161-9a03-bc5168027b35 is Dirck Hals’s Woman sewing by Candlelight, 1633, already linked to Ireland without inventory. The initial article does not establish a different work; no duplicate added.'),
}

NOTES={
    '6918':'Lady Raleigh is a different sitter and NGI.282 inventory from the existing Sir Walter Raleigh, NGI.281. Preserve the unknown English creator; the sitter’s lifespan is not the creation interval.',
    '6929':'One 1590 oil portrait on panel, NGI.283. The separate Thomas Wright 1829 Robert Devereux record is retained as a different creator/date source lead; no artist identity is inferred from the sitter name.',
    '7025':'The 236 x 145 cm NGI.292 canvas has its own circa 1799–1800 date and acquisition. The existing Gilbert Stuart Baron FitzGibbon portrait is another artist’s 1789 work, Cleveland 1919.910.',
    '7035':'Retain the signed 1746 Hudson portrait and full literal source. The label’s general statement that Hudson employed Joseph van Aken for drapery is preserved in evidence, without inventing an object-specific contribution or upgrading attribution.',
    '7119':'One NGI.302 portrait of Thomas Moore’s father. Other John Moore records name a novelist/physician or an archbishop, not this source-identified sitter. Preserve the unknown Irish creator and full nineteenth-century period.',
    '7128':'One separately inventoried NGI.303 portrait of Anastasia Moore, companion to NGI.302 but not the same panel. Preserve the unknown artist and broad century.',
    '7206':'Preserve Attributed to Thomas Hickey. William Hickey with a sculpted bust is not the existing two-person Burke/Fox conversation painting NGI.258; the 1819 William Thomas double-sitter portrait is also a separate source identity.',
    '7217':'The source explicitly calls NGI.311 an autograph replica of the monumental Hampton Court painting. Count this 139 x 122 cm canvas once, retaining circa 1701; 1697 is the depicted return from Ryswick.',
    '7228':'Creation remains circa 1874–1876. The sitter’s 1877 death, 1883 exhibitions and 1884 gift are separate events and do not replace that native date.',
    '7678':'Count one separately inventoried surviving wood-panel fragment, NGI.354, not the whole dismembered retablo. Preserve fragment in the medium and the complete creator label including and Companion. The saint’s lifetime is subject history, not creation.',
    '7737':'Two represented scenes occur on one 98.3 x 67 cm oak panel with one NGI.360 inventory. Count a single artwork and retain the named anonymous-master label without creating an artist biography.',
    '7874':'Preserve the signed 1766 Cotes portrait. The biography mentions his employment of drapery painter Peter Toms but does not expressly assign a contribution to this object; preserve that prose without inventing a second attribution.',
    '7885':'Retain the native eighteenth-century date and incomplete dimension string 69 cm. Do not infer a second measurement or use Wheatley’s lifespan as creation bounds.',
    '7906':'One oil sketch on paper laid on canvas, NGI.376, from the artist’s bedroom window toward Harnham Ridge. The label independently describes the summer following his wife’s 1828 death, consistent with 1829. Salisbury cathedral views and Old Sarum landscape leads are distinct depicted locations.',
    '7958':'One Romney canvas with Titania, Puck and the changeling, NGI.381, 1793. Earlier Emma Hamilton sittings and marriage are biographical context; other catalogue Titania entries identify different artists and compositions.',
    '8083':'One separately inventoried oil sketch, NGI.396. Sketch status is explicit; it is not counted as the eventual banquet painting or as the depicted event itself. Acquisition before 1898 remains separate from creation in 1783.',
    '8133':'Retain the explicit seventeenth-century period and unknown English artist. Joseph Addison’s lifespan in the title is sitter identification, not the artwork’s creation range.',
    '8263':'Preserve After Anthony van Dyck and the full seventeenth-century period. This copy NGI.413 is not upgraded to an autograph work. The existing Leygebe portrait names the third Earl (1672–1739), a different sitter.',
    '8482':'Retain Isaac de Jouderville and 1631–1635. The Signed field explicitly marks G Dou as false; that inscription does not authorize changing the creator. The existing Jouderville young-woman portrait identifies a different subject.',
    '8560':'One signed 1769 oil canvas NGI.440, depicting John Camillus Hone. The separate Nathaniel Hone artist record was inspected; its wife portrait, adult male miniature and Conjuror sketch are different works. The 1775 solo exhibition is not creation.',
}


def main():
    source=i.RUN/'ireland-002-research.json.gz';research=m.load(source)
    records=[];held=list(research['held']);reviews=[]
    for r in research['records']:
        oid=r['source_record_id']
        if oid in HOLDS:
            reason,note=HOLDS[oid];held.append(dict(record=r,reason=reason,editorial_note=note));continue
        if len(records)>=40:
            held.append(dict(record=r,reason='outside_selected_200_target',editorial_note='Retained candidate beyond the forty-work target. No import approval inferred; recheck current identity evidence before any later use.'));continue
        raw=i.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
        assert i.validate_record(r,raw)==r['facts']
        review=dict(source_record_id=oid,source_capture_sha256=r['source_receipt']['sha256'],
            reviewed_fields=['Title','Date','Credit Line','Object number','Medium','Dimensions','Signed','Inscription','Description','Label Text','Provenance'],
            decision='approved_new_review_record',note=NOTES.get(oid,'Native individual inventory, acquisition credit and creation field agree. Creator/sitter identity searches found no corresponding catalogue work. Retain unknown fields and literal source labels without adding artist links or display claims.'))
        r['raw_source_record']['editorial_review']=review;reviews.append(review);records.append(r)
    assert len(records)==40 and research['before']['eligible']+len(records)==200
    with m.connect() as db:
        assert not i.title_collisions(db,records)
        known,titles,inventories=i.existing_keys(db,research['museum']['id'])
        assert not any(r['source_record_id'] in known or m.norm(r['facts']['title']) in titles or i.inventory_keys(r['facts']['accession'])&inventories for r in records)
    paths=['identity-before-002.json','creator-identity-review-002.json','sitter-and-creator-variants-002.json']
    evidence=[dict(path=str((i.RUN/p).relative_to(m.ROOT)),sha256=hashlib.sha256((i.RUN/p).read_bytes()).hexdigest()) for p in paths]
    plan=dict(at=m.now(),records=records,held=held,research_source=str(source.relative_to(m.ROOT)),research_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        identity_evidence=evidence,editorial_reviews=reviews,before=research['before'],indexes=research['indexes'],
        policy='Forty individually reviewed native paintings toward 200 eligible-date works. Retain full source labels, copies, unknown creators and fragment context. No images, display assertions, publication or existing-record metadata changes.')
    path=m.RUN/'ireland-002-current-plan.json.gz';m.save(path,plan)
    m.save(i.RUN/'followup-queue-002.json',dict(at=plan['at'],held=held,previous_queue='followup-queue-001.json',next_index=research['next_index'],
        scope='Second-pass unresolved identities and seven candidates beyond the selected target. Older queue remains unchanged.'))
    print('Reviewed Ireland plan',len(records),'held',len(held),'sha256',hashlib.sha256(path.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':main()
