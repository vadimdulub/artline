#!/usr/bin/env python3
"""Pin individually reviewed Goulandris additions and unresolved version leads."""
import copy
import hashlib
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('g',Path(__file__).with_name('museum-expansion-goulandris-20261006.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
m=g.m

HOLDS={
 'fautrier-jean-composition':'Compare the Italian Petit construction en bleu: near-identical paper format, different reported medium/date. The 1958 inscription alone does not resolve the identity.',
 'helion-jean-blue-composition':'Native inscription identifies no. 166, begun Paris May 1938 and finished Virginia December 1938. Generic existing Composition records lack physical details; compare before adding.',
 'picasso-pablo-painter-and-model-in-an-armchair':'Met 1988.1101.2 has the same first state and sheet format. Goulandris describes added ink and gouache and approximately five impressions; establish the specific impression independently.',
 'poliakoff-serge-untitled':'The complete eighteen-row creator pool contains generic compositions with missing details and two near-identical formats; reconcile versions before adding.',
 'maurice-de-vlaminck-still-life':'Orsay RF 1973 27 has essentially the same canvas format. Signature placement and dated provenance differ, but need object-version confirmation rather than relying on the conflicting dates.',
 'hadjikyriakos-ghika-nikos-paris-roofs':'Existing Paris Roofs II (1952), under Nicolas Ghika, may be this work. Preserve both titles and compare before any duplicate or holding change.',
 'picasso-pablo-young-man-with-bouquet':'Header and narrative select 1905 but the reported verso inscription says 1904 or 5. Retain the unresolved source date statements for explicit reconciliation.',
 'braque-georges-athena':'Resolve the specific impression against Dieppe and NGA versions; the printing/publishing note is undated and must not silently inherit a design date.',
 'giorgio-de-chirico-portrait-of-a-man':'The medium field says watercolour and gouache on paper, while the narrative calls it a tiny oil painting. Preserve the source conflict.',
 'giacometti-alberto-portrait-1':'The model is only presumably Diego. Existing generic Portrait and Diego records require comparison; do not convert the tentative sitter identification into certainty.',
 'giacometti-alberto-interior-with-trunk-and-basket-of-wood':'Met Interior at Stampa has a near-identical graphite sheet format. Compare the specific furniture and inscription before adding.',
 'helion-jean-equilibrium':'Two existing Equilibrium records have 1933–1934/1934 dates and missing physical details; reconcile this signed 1933 watercolor before adding.',
 'maillol-aristide-reclining-nude':'Cleveland 1958.390 has no dimensions, inscription or edition information in its current API record. Resolve whether it is a different impression from the 1948 Flammarion copy.',
 'christo-packed-coast-project-for-australia-near-sydney':'Retain the explicit joint creator label and unknown type. Existing Packed Coast, Project for Little Bay is a collage of nearly the same dimensions; the abbreviated medium descriptions do not establish distinct versions.',
 'matisse-henri-the-nightmare-of-the-white-elephant-jazz':'Goulandris copy 172/250 and Chicago 1948.80.7 have separate provenance chains, but Chicago supplies no edition number. Resolve the specific copy before creating a second physical-object record.',
 'matisse-henri-the-cow-boy-jazz':'Goulandris copy 172/250 and Chicago 1948.80.17 have separate provenance chains, but Chicago supplies no edition number. Resolve the specific copy before creating a second physical-object record.',
 'bouzianis-george-self-portrait':'Existing Portrait of a man (1915) has no physical metadata. Preserve the circa-1945 self-portrait as a version-comparison lead rather than infer difference solely from dates.',
 'bouzianis-george-portrait-of-the-painter-vas-hadjis':'The native verso identifies Chatzis, distinct from the named Waldmuller portrait, but the existing generic Portrait of a man lacks physical details. Compare it before adding.',
}

NOTES={
 'vincent-van-gogh-olive-picking':'The native narrative explicitly distinguishes this in-situ canvas from two studio versions. The Met catalogue independently describes its Women Picking Olives as the third, most resolved version. Retain the Goulandris 73.5 × 92.5 cm version and historical provenance; do not change the Met record.',
 'vincent-van-gogh-les-alyscamps':'One vertical 92 × 73 cm canvas. The narrative distinguishes four Alyscamps paintings and describes this view with the industrial building; it is not a collective record for the series.',
 'gauguin-paul-still-life-with-grapefruits':'Retain the source alternative 1901 or 1902 and illegible signature date. The narrative’s favored 1901 does not erase the stated uncertainty; historical Apples and Flowers title remains in the evidence.',
 'el-greco-the-holy-face':'The narrative identifies this 51 × 66 cm canvas as autograph and distinguishes workshop versions. The Early 1580s label remains literal; index bounds cover the stated decade without inventing an early-decade endpoint.',
 'henri-de-toulouse-lautrec-woman-in-monsieur-forests-garden':'The narrative explicitly describes multiple versions of Honorine. This oil on board, 60.7 × 55 cm, differs from the existing 55.6 × 46.4 cm oil on canvas; retain the distinct support and dimensions.',
 'giacometti-alberto-portrait-of-yanaihara':'The source describes repeated sittings and multiple canvases. This signed 1960, 92 × 72.6 cm canvas differs in format from the existing 1956 Isaku Yanaihara canvas, 81.3 × 65.1 cm.',
 'lichtenstein-roy-sunrise':'One physical enamel-on-steel work from an edition of five. Native painting-category membership and the narrative’s hand-applied enamel support this classification. Do not create five records or turn the verso 3208 into a museum inventory.',
 'baselitz-georg-three-stripes-two-cows':'Three compositional stripes on one canvas count once. The narrative confirms the 1967 work and does not describe three separately inventoried panels.',
 'derain-andre-still-life':'All five same-creator exact-title records have substantially larger physical formats. Retain this 20 × 31 cm canvas and its circa 1948–1950 interval, independently of those other still lifes.',
 'derain-andre-nude':'The 23 × 14.5 cm canvas laid on cradled panel differs in support and portrait orientation from the existing 43.5 × 58.1 cm canvas. Circa dating remains explicit.',
 'fautrier-jean-head-of-hostage-no-17':'The source explicitly explains that Hostages were painted in 1942–1944 and several signed in 1945. Preserve the 1944 creation field and reported F.45 signature as separate phases; no silent date correction.',
 'hundertwasser-ninety-nine-heads':'A single mixed-technique oil work on hard fibre board. Archive no.134 is an artist catalogue reference, not a museum accession; retain its photo affix as part of the stated medium.',
 'nicholson-ben-1967-green-quoit':'The native narrative identifies the relief as painting and explains the carved panel. The one physical 123.5 × 121.5 cm work counts once; the prehistoric monument inspiration is not a creation date.',
 'soulages-pierre-painting-august-13-1959':'Native title and verso inscription agree on 13 August 1959 and portrait format 162 × 114 cm. Current French record 00M11011260 independently gives landscape format 114 × 162 cm and 16 December 1959; these are distinct dated canvases.',
 'caniaris-vlassis-untitled':'No same-creator lead was found. The two anonymous exact-title leads are an intaglio and a lithograph, distinct from this 89.5 × 79 cm mixed-media canvas.',
 'bouzianis-george-portrait-of-a-woman':'The 1944 female portrait differs in subject from both retained same-creator leads, Portrait of a man and the named painter Waldmuller. Keep the source 120 × 90.5 cm canvas and full donor evidence.',
 'samaras-lucas-untitled':'Preserve this dated physical object as a real review record with unknown type and all acrylic/plaster/fabric/canvas/feather materials. No same-creator lead was found; anonymous Untitled paper prints differ in medium and form.',
 'stamos-theodoros-archaic-landscape':'The titled verso inscription and no.939 identify this 61 × 51 cm oil on isorel. Related landscape leads have different physical supports/formats; no.939 remains an inscription rather than an invented museum inventory.',
 'chagall-marc-untitled-for-elise-and-basil':'The explicit dated 1969 dedication to Elise and Basil identifies this 28.5 × 21 cm work. Keep mixed media on paper and unknown type; the dedication and native donated-by-artist provenance do not create artist authority links.',
 'braque-georges-flight-1':'Goulandris impression 31/100 is distinct from Dieppe 973.20.39 / 4841(MD), whose current official inscription field explicitly identifies an artist’s proof with studio stamp. Count this numbered sheet once.',
 'braque-georges-violet-head':'Goulandris impression 2/75 is distinct from Dieppe 973.20.29 / 4831(MD), explicitly inscribed H.C. / Hors Commerce and studio-stamped. The reference to Large Illustrated Albums is the catalogue context of this individual lithograph.',
 'braque-georges-the-sign':'Goulandris impression 26/30 differs from Dieppe 972.21.23 / 4688(MD), explicitly an artist’s proof with studio stamp. Preserve the numbered impression and both image/sheet dimensions.',
 'braque-georges-thistle':'Use the explicit 1955 printing/publication for this numbered lithograph. The earlier watercolor and sketchbook discussion concern its source design, not this physical impression.',
 'forain-jean-louis-dancer':'The expanded dancer/ballet title search found oils and printed/drawn scenes with different media and formats. This 35.8 × 29 cm pastel on grey paper depicts a lone dancer; retain its circa 1900 date.',
 'giacometti-alberto-interior':'The 1947 pencil drawing depicts the Paris studio furniture. It differs from the existing oil-on-canvas Interior and from the smaller Stampa/Annette graphite sheets in the retained creator pool.',
 'miro-joan-composition':'This 1965 hors-commerce etching/aquatint on BFK Rive, 28.5 × 22.5 cm, differs in medium or sheet/plate format from each same-creator exact-title lead. The anonymous Composition is a substantially larger screenprint.',
 'modigliani-amedeo-cariatide':'This pencil-and-gouache sheet laid on canvas, 63.7 × 40 cm, differs from the Chicago watercolor (53.7 × 41 cm primary support) and Italian black-pencil drawing (42 × 26 cm primary support). Do not compare frame/mount dimensions as though they were the drawing.',
 'picasso-pablo-the-painter-and-his-model':'Native recto and verso dates agree on 21 May 1970. The narrative distinguishes five drawings from that day and this embraced-model composition. Existing same-title leads have other formats/media; this 19 × 12 cm ink sheet remains a distinct selected work.',
 'picasso-pablo-profile-of-woman-jacqueline':'This is the documented 1970 offset poster heightened in red pencil and dedicated to Goulandris on 1 April 1970. The narrative’s general linocut discussion concerns the source design; preserve the exact medium and both creation phases.',
 'picasso-pablo-jacqueline-with-hair-loose':'Use the documented 1958–1959 edition date, retaining printed 1957 and 1958 inscriptions. Image 56 × 44 cm and the second-state numbered 36/50 impression distinguish it from the 1949 Corsage sheets with image about 64.9 × 49.5 cm. Preserve the native translated title despite the URL wording.',
 'picasso-pablo-bathers':'The signed 23 April 1921 pencil sheet is 16.2 × 22.1 cm. Existing same-title leads are differently sized paper works or 1932 etchings; their depicted bathers do not make them this sheet.',
}


def reference(path):
    return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def prepare():
    research_path=g.RUN/'goulandris-004-research.json.gz';research=m.load(research_path)
    comparison_path=g.RUN/'creator-title-comparison-leads-004.json';comparisons={r['source_record_id']:r for r in m.load(comparison_path)['records']}
    collision_path=g.RUN/'exact-title-identity-evidence-003.json';collisions=m.load(collision_path)['rows']
    evidence=[reference(p) for p in [research_path,comparison_path,g.RUN/'creator-identity-review-004.json',collision_path,g.RUN/'supplemental-primary-captures-001.json',g.RUN/'supplemental-primary-captures-002.json']]
    source_records={r['source_record_id']:r for r in research['records']}
    assert set(HOLDS)<=source_records.keys() and set(NOTES)<=source_records.keys()
    decisions=[];approved=[];held=copy.deepcopy(research['held'])
    for oid,r in source_records.items():
        f=r['facts'];parsed=r['raw_source_record']['native_fields'];comparison=comparisons[oid]
        if oid in HOLDS:
            decisions.append(dict(source_record_id=oid,decision='hold',note=HOLDS[oid],facts=f))
            held.append(dict(record=r,reason='editorial_identity_or_source_review',editorial_note=HOLDS[oid],creator_comparison=comparison));continue
        note=NOTES.get(oid,'Native title, creator, creation statement, physical medium and dimensions agree. The retained English/original-title and creator-scoped comparison leads do not establish the same physical object. Preserve unknown fields and the literal source attribution.')
        if oid.startswith('henri-de-toulouse-lautrec-') and oid.removeprefix('henri-de-toulouse-lautrec-') in g.LAUTREC_1948:
            note='One individually catalogued leaf of the posthumous Gründ edition printed by Mourlot and Thiry in 1948, copy 448/750 on superior Vélin. The original 1890s designs/impressions are distinct from this documented edition. Preserve design date, printing date, sheet format and copy number together. The parent Twelve Lithographs album is excluded so these twelve leaves are not counted twice.'
        elif oid.startswith('maillol-aristide-'):
            note='One individually catalogued composition from the posthumous Flammarion edition printed by Draeger in 1948, copy 945/1000 on Marais paper. Preserve that physical printing date and edition statement, distinct from original drawings and other subjects. Do not invent an accession from the copy fraction or count the parent edition again.'
        selected=copy.deepcopy(r)
        decision=dict(source_record_id=oid,decision='approve_review_record',note=note,facts=f,
            creator_pool_size=comparison['pool_size'],comparison_lead_ids=[v['id'] for v in comparison['leads']],
            exact_title_comparison_ids=[v['id'] for v in g.matching_title_rows(collisions,r)])
        decisions.append(decision)
        selected['raw_source_record']['title_identity_review']=dict(evidence_path=str(collision_path.relative_to(m.ROOT)),evidence_sha256=reference(collision_path)['sha256'],existing_ids=decision['exact_title_comparison_ids'])
        selected['raw_source_record']['editorial_review']=decision
        approved.append(selected)
    assert len(approved)==95 and len(held)==28
    manifest=g.RUN/'editorial-review-001.json'
    m.save(manifest,dict(at=m.now(),decisions=decisions,evidence=evidence,approved=95,held_candidates=18,
        policy='Review-only physical objects. Exact-title collisions require creator, medium, version and edition comparison. Heuristic ranking is a lead aid, not automatic identity approval. No existing metadata, artists, images or publication changes.'))
    for r in approved:r['raw_source_record']['editorial_manifest']=reference(manifest)
    with m.connect() as db:
        known,titles=g.existing_keys(db,research['museum']['id'])
        assert not known&{r['source_record_id'] for r in approved}
        assert not any(g.title_keys(r)&titles for r in approved)
        g.check_title_identities(db,approved)
    plan=dict(at=m.now(),records=approved,held=held,editorial_manifest=reference(manifest),
        policy='95 selected pre-1971 additions, retained in review; two unknown object types, no fabricated accessions or artist links. 123 distinct index identities reconciled as 95 additions and 28 documented holds/existing identities. No images or display claims.')
    dest=m.RUN/'goulandris-001-current-plan.json.gz';m.save(dest,plan)
    m.save(g.RUN/'followup-queue-002.json',dict(at=m.now(),distinct_index_identities=123,approved_additions=95,held=held,remaining_target='Five existing records plus 95 additions reaches 100 eligible-date linked records; 200 still requires further source research.',editorial_manifest=reference(manifest)))
    print('Pinned',len(approved),'review additions;',len(held),'held/existing;',reference(dest)['sha256'],flush=True)


if __name__=='__main__':prepare()
