#!/usr/bin/env python3
"""Pin 148 individually reviewed Auckland additions; preparation is read-only."""
import hashlib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('u',Path(__file__).with_name('museum-expansion-auckland-20261006.py'))
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)
m=u.m

HOLDS={
 '284':('source_date_conflict','Lindauer Hōri Ngākapa Te Whanaunga: native creation field says 1878, while the narrative explicitly dates this portrait and exhibition to 1874. Preserve both pending resolution.'),
 '16592':('source_date_conflict','Kauw Johanna Katharina Steiger: native creation field says 1643, while the narrative explicitly dates the portrait at age two to 1645.'),
 '76':('version_identity_requires_review','Netscher Girl arranging flowers needs comparison with the generically titled 1683 Portrait of a Lady, 9d611326-088a-494d-a98f-cb9f8f869d86, which has no inventory or dimensions, and the separately inventoried Detroit Young Woman with a Garland. Retain native inventory 1887/1/23 and its 1883 gift credit.'),
 '2978':('version_identity_requires_review','Ricci rocky landscape needs physical-object comparison with A mountainous landscape, 3eb62924-d52a-4b9c-8265-b6c90abc34a6, and the natural-arch/waterfall landscapes with incomplete identities. Preserve Auckland 1961/14/2 and 635 x 482 mm; date differences alone do not separate objects.'),
 '11517':('version_identity_requires_review','Hondecoeter bird gathering U/113 needs comparison with broadly titled bird and park compositions lacking inventories. Preserve the circa 1660–1690 range and 1013 x 1073 mm dimensions; a differently translated title is not a new identity.'),
 '120':('version_identity_requires_review','Collier Vanitas needs comparison with 02167829-a54a-4762-a8c9-351867f0bed0 and 1bc47075-1bbf-42b3-b5d9-73ebbaba048c. Their unverified dates and missing catalogue inventories do not establish different objects. Preserve native 1699 and 1887/1/8.'),
 '3295':('version_identity_requires_review','Sickert Baccarat, Dieppe requires comparison with Baccarat – the Fur Cape, eaeaa697-d705-456f-8317-9ceb8b947699, Tate N05089. Both are dated 1920; different recorded heights and title wording require a composition-level check.'),
 '3499':('version_identity_requires_review','Sickert A Cup of Tea requires comparison with the window portraits, including 0e510ca0-15b5-41f0-b251-55d309707c9a with the same 508 x 406 mm dimensions, and 7c1afad5-1446-42fc-a4db-312bce96446c without inventory or dimensions. Do not decide identity by date differences.'),
 '16128':('version_identity_requires_review','Bonnard Bowl of Apples has a distinct native 2023 gift inventory, but broadly titled still lifes, including Nature morte jaune et rouge, 59e8e104, need further physical-object comparison. The larger fruit-dish works can be separated by dimensions; missing dimensions on other leads remain unresolved.'),
 '16122':('version_identity_requires_review','Matisse Spanish Woman belongs to a repeated-sitter series. The Met confirms its separate 1975.1.193, 1923, 47 x 35.6 cm record, but other Spanish-woman and generic portrait leads still require composition/version comparison with Auckland 2023/6/7.'),
 '14898':('version_identity_requires_review','Picasso Woman in a hairnet has no exact title match. However Portrait de Marie-Thérèse, 7d26fc69-7aec-457d-ad9f-ec854c1ccfa2, MP167, has the same 46 x 38 cm dimensions and other generic portraits need comparison. Preserve the 1938 source date and 2023 gift; do not infer a new object from the differing title/date.'),
 '14890':('version_identity_requires_review','Cézanne Road/Old Wall requires comparison with ROUTE DE VILLAGE, AUVERS, 3317ae0f, whose reported 46 x 55.5 cm dimensions are close to Auckland 463 x 556 mm. Distinguish the compositions before adding; source creation dates alone are insufficient.'),
 '16124':('version_identity_requires_review','Braque The Cup has no exact translated-title match, but Le verre, ed95ad87-2e1e-40ed-9f8d-722cabdabe08, lacks inventory/dimensions and needs comparison. Preserve Auckland 240 x 330 mm, 1912 and 2023/6/9. The circular Soda and larger Bottle of Marc are distinguishable but do not resolve every glass/cup lead.'),
 '14895':('version_identity_requires_review','Léger Pistons requires comparison with Les disques, adc418f8-a24e-47c9-a5e2-4349c1a9a817, and Contrastes de formes, 0e7f69d2-5173-452c-9729-d07751e47446, both carrying unverified 1918 dates and no dimensions. Preserve the Auckland canvas and 2023 gift evidence.'),
 '2985':('version_identity_requires_review','Coccorante Roman ruins requires comparison with the inventory-less French ruins/nocturne records 8b10e098-e0ec-4321-a88b-3576fc41387f and 1150ed0b-8f17-4ad1-b46f-af2ac5527487. Detroit 37.1801 is much smaller; that alone does not resolve the other leads.'),
 '3189':('version_identity_requires_review','Rosa Landscape with a Rock needs composition comparison with generically titled and untranslated landscapes in the creator-scoped pool. Preserve native 1964/24, 200 x 438 mm and mid-seventeenth-century wording; do not create a duplicate merely because the title differs.'),
 '5754':('version_identity_requires_review','Hodgkins Berries and Laurel is one of several works with the same vase. Creator-scoped still-life/landscape records including The Croft and The Sitting Room have incomplete inventories/dimensions. Retain the native circa 1930 and January 1931 exhibition evidence for a composition-level comparison.'),
 '3120':('version_identity_requires_review','Hodgkins Lancashire Family needs comparison with the inventory-less Family After Dinner, 9cf936b0-c792-5447-9dcd-60372626f2c1. Different dates and title wording alone are insufficient to resolve the physical-object identity.'),
}

NOTES={
 '15692':'The creator-scoped pool contains no 1939 composition identity. Nearby works include a 1937 painting and differently sized 1938–1942 gouache and 1943 painting. The native object/title, 560 x 711 mm canvas and 2023/8/5 gift identity support this addition. Retain Thanksgiving Foundation gift wording, separate from earlier loan history.',
 '16129':'Creator-scoped painting titles and cow/Rouen translations were inspected. The separate Italian Normandy cows-at-watering-place landscape is 80 x 64 cm; the Auckland hillside canvas is 56 x 46 cm, with its own narrative, native identity and 2023/6/14 gift. Preserve 1884 creation and the source dateline of 2024 separately.',
 '16130':'The creator-scoped pool and broader Masochistic Instrument title search reveal no matching object. Nearby surrealist works have different named compositions, formats and native inventories; the 1934 desert miniature is 18.1 x 14.1 cm. Preserve Auckland 621 x 477 x 21 mm, circa 1934, the melting-violin narrative and 2023/6/15 gift.',
 '628':'The native object consistently identifies accession 1930/18/1, 1447 x 902 mm, dated 1905 and gifted by Moss Davis in 1930. Its narrative mentions another version; this does not contradict the selected object creation field. Neither creator-scoped rows nor the broad Lamia search found an existing identity. Preserve the narrative literally; do not substitute a date from another version.',
 '1088':'Goldie sitter aliases Kapekape and Ahinata, the full title and creator-name variants were checked without a corresponding record. Retain the native 1939 portrait and its literal title and sitter narrative.',
 '244':'Goldie Wharekauri/Tahuna title and sitter variants were checked. The Tahuna landscape result by Patrick Hayman is unrelated. Preserve the 1910 portrait, exact inventory and differing historic/title tribal wording as source evidence.',
 '11852':'Harata/Rewiri/Tarapata and creator variants were checked; broad Harata matches concern the Mahabharata and different objects. Retain this individually inventoried Goldie portrait.',
 '3024':'Both current Ficherelli and historical Furini creator leads and broad Antiochus/Stratonica titles were reviewed. Other matching subjects carry different creators/object identities; neither creator pool contains this composition. Retain the native circa 1638, current attribution and old attribution history.',
 '9669':'The painting is an independently inventoried study for The Coming Storm, not the larger finished canvas mentioned in the source. Creator and broad title checks found other artists’ Coming Storm works only. Retain M1921/1/12 and the literal circa 1910 date.',
 '768':'The Sartorius-family scoped pool and broad Eclipse search found no corresponding horse portrait; the Mulready result is an anatomical study, not this oil canvas. Retain Captain O’Kelly title, 1780 creation and 1933/1/2.',
 '95':'The Wilkie pool and broad Ceres/Proserpine subjects revealed no matching Wilkie object. The 1803 student painting and its 1887 gift remain distinct from the narrative’s 1869 purchase by the donor.',
 '2851':'The extra Marie Conlan sitter search found no existing identity. The existing May Smith still life is a different subject. Retain 1941 creation and 1958 acquisition separately.',
 '39337':'The Pabst sitter search found no existing object; native creator and title checks are also clear. Retain circa 1906 and the 2024 gift without turning later biographical events into creation dates.',
 '344':'Erueti Tamaikōhā, Tamaikoha and Ariari sitter aliases found no existing identity. Retain the native title and the narrative’s Eru Tamaikoha Te Ariari wording separately.',
 '9663':'The full Bramley pool and shortened Kingdom of Heaven search found no matching funeral painting. Results by De Morgan and Gaultier have distinct subjects/creators. Retain 1891 creation and Mackelvie permanent-loan collection evidence.',
 '9722':'Neither the Gainsborough pool nor Lavington/Exeter subject queries returned this portrait. Other Exeter sitters are named differently and have other creator identities. Retain circa 1760, M1960/1 and the museum’s literal dimensions.',
 '9173':'The Henry Moore pools include both marine-painter works and sculptor namesakes. None identifies this 1880 voyage scene; the broader Last Voyage results are unrelated subjects/creators. Keep the native creator label without linking an artist profile.',
 '2768':'The Dahl pool contains named sitters other than George I. Broad George I results are explicitly after Kneller or other subjects. Preserve the circa 1714 native Dahl portrait and its separate 1957/12/1 inventory.',
 '2841':'O’Conor generic landscapes were compared by their physical formats: the recorded supports differ from Auckland’s 489 x 609 mm canvas, including the tall Glade and larger Yellow Landscape. Retain La ferme and circa 1892; no exact-title identity was found.',
 '9730':'Wakatipu/Earnslaw subject queries found no current record; the creator pool contains other named locations. Preserve 1877–1879 creation, earlier 1876 sketching and later 1971 Mackelvie acquisition independently.',
 '11062':'The Nash painting pool and Bleached Objects search found no matching composition. Nearby surreal landscapes have different titles, formats and source identities; preserve the 1934 native canvas, M1994/7 and 620 x 747 mm dimensions.',
 '8972':'Both Andrea Michieli and Andrea Vicentino names and broader Joseph/brothers translations were checked; results concern other creators or scenes. Retain the literal repeated known-as label, M1882/2/1 and late-sixteenth-century wording with enclosing century bounds.',
}


def main():
    source=u.RUN/'auckland-001-research.json.gz';research=m.load(source)
    working={};working_paths=sorted(u.RUN.glob('editorial-working-notes-*.json'))
    for p in working_paths:
        for ids,note in m.load(p)['notes'].items():
            for oid in ids.split('/'):working[oid]=note
    assert len(research['records'])==168 and not research['source_failures']
    assert all(r['source_record_id'] in working for r in research['records'])
    held=list(research['held']);records=[];reviews=[]
    comparisons={r['source_record_id']:r for r in m.load(u.RUN/'creator-title-comparison-leads-001.json')['records']}
    for r in research['records']:
        oid=r['source_record_id']
        if oid in HOLDS:
            reason,note=HOLDS[oid];held.append(dict(record=r,reason=reason,editorial_note=note));continue
        if len(records)>=148:
            held.append(dict(record=r,reason='outside_selected_200_target',editorial_note='Native candidate retained beyond the selected 148 additions. No import approval; recheck current identities before later use.'));continue
        raw=u.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
        assert u.validate_record(r,raw)==r['facts']
        review=dict(source_record_id=oid,source_capture_sha256=r['source_receipt']['sha256'],
            reviewed_fields=['rendered_fields','creator_names_and_roles','native_attributes','brief_description','blocks','index_identity','acquisition_credit','copyright'],
            decision='approved_new_review_record',working_source_note=working[oid],
            final_identity_decision=NOTES.get(oid,'The native whole-canvas identity, source and inventory checks, creator/title comparison leads and relevant additional subject searches were reviewed. No corresponding current catalogue identity or unresolved version conflict was identified for this selection. Preserve literal metadata and uncertainty; no artist profile, display or publication inferred.'),
            creator_comparison_pool_size=comparisons[oid]['pool_size'])
        r['raw_source_record']['editorial_review']=review;records.append(r);reviews.append(review)
    assert len(records)==148 and research['before']['eligible']+len(records)==200
    assert len(HOLDS)==18 and not set(HOLDS)&{r['source_record_id'] for r in records}
    with m.connect() as db:
        assert not u.title_collisions(db,records)
        known,titles,inventories=u.existing_keys(db,research['museum']['id'])
        assert not any(r['source_record_id'] in known or m.norm(r['facts']['title']) in titles or u.inventory_keys(r['facts']['accession'])&inventories for r in records)
    paths=[u.RUN/p for p in ['auckland-001-identity-before.json','creator-identity-review-001.json','additional-creator-name-leads-001.json',
        'supplemental-creator-artworks-001.json','creator-title-comparison-leads-001.json','subject-version-identity-leads-001.json',
        'additional-subject-identity-leads-001.json','permanent-trust-holdings-context.json']]+working_paths
    evidence=[dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    plan=dict(at=m.now(),records=records,held=held,research_source=str(source.relative_to(m.ROOT)),research_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        identity_evidence=evidence,editorial_reviews=reviews,before=research['before'],indexes=research['indexes'],
        policy='148 selected official Auckland oil paintings. Literal creation dates, creator labels, acquisition and trust-ownership qualifications and rights evidence retained. Review-only local metadata additions; no images, artist links, display claims or publication changes.')
    dest=m.RUN/'auckland-001-current-plan.json.gz';m.save(dest,plan)
    m.save(u.RUN/'followup-queue-001.json',dict(at=plan['at'],held=held,resume_page=research['resume_page'],unprocessed_captured_rows=research['unprocessed_captured_rows'],next_page=research['next_page'],
        policy='Held and unselected candidates remain research evidence. Unprocessed index rows are not approved. Recheck source and existing identities before any subsequent addition.'))
    print('Auckland reviewed',len(records),'held',len(held),'sha256',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)


if __name__=='__main__':main()
