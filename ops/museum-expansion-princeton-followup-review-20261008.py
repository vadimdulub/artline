#!/usr/bin/env python3
"""Individual, source-backed decisions for the bounded Princeton follow-up."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('identity',Path(__file__).with_name('museum-expansion-princeton-followup-identity-20261008.py'));identity=importlib.util.module_from_spec(s);s.loader.exec_module(identity)
f=identity.f;m=f.m;RUN=f.RUN;IID=identity.IID;ref=f.ref;checked=identity.checked
CANDIDATES=RUN/'native-candidates-001.json.gz';IDENTITY=RUN/'native-identity-001.json.gz';CITATIONS=RUN/'identity-citations-001.json.gz'
NOTES={
1:'One1963 Alice Neel Irma Seitz canvas91.2×66cm, Richard Neel gift1977. No same sitter/object in the24-record creator scope; Lida Moser is another named sitter and68.6×50.8cm canvas.',
2:'One1945 Gallatin Wine Glass canvas76.2×50.7cm, gift of his nieces. Exact-title database works are Whistler etchings; the four-record Gallatin scope has no corresponding object.',
4:'One1913 Münter Mother of Kandinsky canvas45.2×38cm, Taplin memorial gift. Portrait of Wassily Kandinsky is another named sitter. Museum article independently identifies the1913 gift; no matching native identity in the25-record creator scope.',
5:'One1877 Nehrlich Selinunte temple view52×84.5cm, Mather Fund purchase from Galerie Kurt Meissner1978. Existing Nehrlich leads depict Gustav IV Adolf, not this Greek temple subject.',
6:'One seventeenth-century Circumcision canvas25.7×28×1cm, Mather gift1928. Preserve attributed to Salomon Koninck and native1629–1656 bounds; literal century independently establishes pre1971 scope. Exact-title records by Fra Angelico and Goltzius are different creators/versions.',
7:'One1894 Monet Meadow at Giverny canvas92×73cm, Dick bequest1954, native catalogue raisonné referenceW1368. Review includes French prairie/pré/printemps and English meadow/spring leads across the486-record creator scope. The1922–26 garden canvas, earlier spring scenes and pastel meadow are different physical works. Count this documented canvas only, not all four meadow paintings mentioned in the museum narrative.',
8:'One1958 Camille Hilaire Repetition canvas81×99.5cm, Adams gift. Broad Hilaire-name scope includes Degas and other unrelated creators; no corresponding Hilaire object or native identity. No artist authority inferred from surname overlap.',
11:'One circa1858 Hayter portrait of Amy Emily Sarah Fitzroy77×64cm, Forbes gift1993. No same named sitter/native identity in the166-record broad Hayter scope. Source frame36×31cm is smaller than stated painting and appears inconsistent; preserve the literal dimensions in source evidence and catalogue text without inventing corrected measurements.',
12:'One circa1830 Delacroix Dead Dog canvas41.5×87.5cm, McCormick Fund purchase1996. Review includes chien/dog/mort/dead subject leads across745 records; those depict horses, human deaths or other compositions. Source provenance identifies the1864 Delacroix sale and1996 museum purchase.',
16:'One1890 Clairin Le Carnage canvas110.2×150.2cm. Source records the1993 sale as bought in followed by Forbes gift to the museum; not an outgoing museum sale or present loan. No matching object in the26-record creator scope.',
17:'One1904 Ernest Lawson Morning Mist canvas50.8×63.8cm, Remington bequest2004. Exact-title works are by Flory, Eby, Wales and Nakamura; no Lawson counterpart in the62-record creator scope.',
18:'One circa1763–75 portrait of Mian Hadala Pal, image18.3×13.8cm, museum purchase2021. Preserve Attributed to Nainsukh of Basohli; also query the Nainsukh mononym, with no existing creator/work counterpart found. The sitter reign1673–78 in the title is not the creation date. Prior auction Rajasthan-school/nineteenth-century label remains provenance evidence, not silently substituted for the current qualified attribution.',
19:'One1875 Hoffbauer Petit-Pont watercolor16.5×24.5cm, purchased2019 from Alain Cambon. The historical event year884 belongs to the title, not creation. Other Paris panoramas show different places/events; no corresponding native object.',
20:'One1944 James Edward Davis Light Reflection watercolor53.1×35.4cm, artist giftx1952-79. Separate from the two1947 watercolor-dye sheetsx1952-77 andx1952-78; native date, physical measurements and accession differ.',
21:'One1878 Charles Wable Algerian Palace perspective watercolor15.8×29.2cm, museum purchase2019 from Alain Cambon. No creator/title/native counterpart; retain the historical exhibition title without an inferred current venue.',
22:'One1970 Ralph Rosenborg Autumn Night watercolor31×39.5cm, gift of Princeton Gallery of Fine Art. The literal and numeric1970 creation fields agree and are within scope. Earlier American Landscape works are differently titled1936 woodcuts and1941 etchings.',
23:'One1861 Charles Herbert Moore Lilies of the Valley watercolor20.9×10.8cm, Mather gift. Exact-title Milne work is oil on board; the broad Moore scope includes other creators and no corresponding object.',
24:'One1941 Kienbusch Two Ducks—Stonington watercolor59.3×46cm, Beal giftx1962-44. Separate portrait-oriented sheet from the landscape-oriented Decoy Ducks47×61.2cm,x1978-73. Count each accession once, not each duck.',
25:'One1956 Paul Jenkins Untitled watercolor40.7×56.6cm, anonymous gift. None of the1438 exact-title results overlaps the19-record Jenkins creator scope; no corresponding native ID or inventory. Unrelated Jenkins-name records do not establish an artist link.',
26:'One1942 James Edward Davis Path of Motion—Rhumba Plus watercolor45.6×30.3cm, artist gift. No matching object in the creator/title/native scope; retain the title as a single sheet.',
27:'One1883 Daingerfield Harlequin watercolor over graphite42×29cm, Platt bequest. Exact-title works are by Picasso, Derain, Cézanne, Amen, Vasarely and Zerbe; the five-record Daingerfield scope has no counterpart.',
28:'One1969 Lois Dodd One cow watercolor29.2×30.8cm, acquired directly from the artist and gifted2019. Distinct source accession and composition from Group of cows1966,28.2×30.5cm.',
29:'One1941 Kienbusch Decoy Ducks watercolor,image47×61.2cm, Beal giftx1978-73. Source inscription records studio selection before framing in1953; this does not replace creation1941. Different sheet orientation/measurements/accession from Two Ducksx1962-44.',
31:'One1920 R. W. Bauhan Église Saint Martin watercolor over graphite62.4×45.7cm, gift of the School of Architecture. Native campuscollections=false and museum Prints and Drawings catalogue/credit establish the recipient collection; a donor department is not itself a campus holding. No matching existing creator/title/native object.',
33:'One1944 Salcia Bahnc Woman’s Head red chalk and watercolor45×35.6cm, Rogerson gift. Source type remains drawing because medium begins red chalk; no forced watercolor type. Same-title results are by different creators and physical versions.',
34:'One1823 John Frederick Lewis Tiger watercolor/white gouache over graphite24.1×29.7cm, Platt bequest. Full Lewis-specific title review and additional animal vocabulary show no corresponding Lewis object. Exact Tiger results are by Barye, Detmold, Marc, Delacroix and other creators.',
35:'One James Edward Davis B+O Express watercolor50.5×37.8cm, artist gift. Preserve the complete1939–1959 source creation range; neither choose a midpoint nor count it as multiple works. No corresponding creator/title/native object.',
36:'One1926 James Edward Davis Seated Female Nude watercolor38×28.7cm, artist gift. The17 exact-title hits have other creators; no matching Davis object.',
37:'One1882 Xanthus Smith Tree Trunks and Mushrooms watercolor32.1×21.7cm, Feld gift. The broad573-record Smith scope has no corresponding title/native identity; surname overlap does not create artist links.',
38:'One1913 Walkowitz Spiral of Colors watercolor29.6×20.1cm, artist gift1947. No corresponding object in the34-record creator scope; source rights labels retained without any image use.',
39:'One1890 La Farge Waimea watercolor/gouache,image11×22cm and larger20.2×27.2cm support, Hamill gift. Keep the location/date/time title verbatim and count one sheet. No corresponding Hawaiian view in the42-record creator scope.',
40:'One1944 Andrew Wyeth Maine Woods watercolor/graphite54.5×75.9cm, American Academy of Arts and Letters gift. Same-title Hartley work is a74.9cm-square oil canvas by another creator; Wyeth Door Step is another architectural subject.',
41:'One1931 Alfeo Faggi Ballet Dancer watercolor50.5×35.5cm, McVitty gift. Exact-title Pinto etching has a different creator/medium; no Faggi counterpart.',
42:'One1906 Walkowitz Windmill watercolor over graphite36.2×28.5cm, artist gift1947. Same-title Jacque work is an etching by another creator; no Walkowitz counterpart.',
43:'One1916 Demuth Trees, No.2 watercolor over graphite21.2×27.6cm, Mather gift. Number2 is a title designation, not two objects. Existing Fish Series Nos.1–4 depict another subject and have separate physical identities.',
44:'One1907 Walkowitz Still Life with Fruit watercolor12.6×20.2cm, artist gift1947. None of44 same-title records corresponds to the34-record Walkowitz creator scope; no native/inventory duplicate.',
45:'One separately accessioned1947 Davis Light Reflection watercolor-dye sheetx1952-77,native9136,51×35.8cm. Native catalogue distinguishes it fromx1952-78,native9137, with separate primary reproduction inventoryINV31967 versusINV31966. Equal title/date/size do not merge these individually catalogued sheets; no assembly or recto/verso grouping is stated. Metadata image references are evidence only; no image downloaded.',
46:'One Davis Jersey Fall watercolor37.8×50.5cm, artist gift. Preserve literal1947–1958 creation range. Stuart Davis New Jersey Landscape is a1935–43 lithograph by another creator, not this sheet.',
48:'One1938 Davis Daffodils watercolor/lithographic crayon50.8×76.3cm, artist gift. Lithographic crayon describes the drawing medium and does not make this an editioned print. Exact-title Logsdail/Creffield records have other creators.',
49:'One1788 Farington Rosslyn Castle watercolor/graphite, image31.1×44.8cm, Josten gift. The same-year Falls of the Clyde is a differently located ink/wash drawing35.9×53cm. Retain source sheet/mount dimensions separately in literal text.',
50:'One1928 Reginald Marsh Ship and Scows watercolor over graphite35.3×50.6cm, Ramsay gift1997. Native provenance follows Rehn gallery and1995 auction to donor. No corresponding physical work in the913-record broad creator scope.',
52:'One circa1897 Anshutz Horse and Boat watercolor26.4×33.2cm, Milberg gift purchase from James Graham & Sons. Preserve native1892–1902 approximation. Existing Anshutz farmer/harvesting, genre and gown subjects have no corresponding object/native identity.',
55:'One circa1820–30 William Jong portrait watercolor/graphite9.9×7.9cm, Balken gift. Unknown American stays an object-level qualified label; the named sitter is not promoted to artist. Closest William Grant/James Ward results depict other named sitters and are large oil canvases.',
56:'One1830 Deborah Smith Taber portrait of Mehitable Eddy Taber49.5×38cm, Balken gift. The sole broad Taber lead is Eileen Taber’s1956 Monks woodcut, a different creator and subject.',
57:'One1928 Davis Lower Manhattan watercolor35.4×50.8cm, artist gift. Same-title works are John Marin’s different-sized watercolor and George Ault’s lithograph; no Davis counterpart.',
58:'One1938 Davis Concorde—Night black-crayon/watercolor50.7×76.3cm, artist gift. Keep drawing type for the mixed medium; Henry William Banks Davis Approaching Night is another artist and oil canvas.',
59:'One1950 John Marin Quoddy Head watercolor over graphite22.4×30.4cm, James Edward Davis gift honoring Egbert. Additional Quoddy/head/coast/Maine title checks preserve the broader comparison pool. Other named coastal works are distinct locations/compositions; no corresponding Quoddy native/title object.',
60:'One1966 Lois Dodd Group of cows watercolor28.2×30.5cm, artist gift2019. Acquired directly from the artist; different accession/date/composition from One cow1969. Count the drawing once, not represented animals.',
61:'One1968 Willi Hartung Cat and Bird watercolor/gouache35.4×39.5cm, artist gift. Paul Klee’s exact-title work is oil/ink on mounted canvas38.1×53.2cm. Hans Hartung is a different creator; no authority conflation.',
62:'One separately accessioned1947 Davis Light Reflection watercolor-dye sheetx1952-78,native9137,51×35.8cm. Companion catalogue recordx1952-77,native9136 has a different accession and primary reproduction inventory. Count one physical sheet for this accession; source does not identify a shared assembly or reverse. Keep both source signatures and image-reference strings without downloading images.'
}
HOLDS={
3:'Bridge on the Touques has an existing Le pont à Trouville lead54fe1d21-c505-4fe0-93ed-f16a8e35ae75 with incomplete physical metadata. Title translation and location overlap require fuller object comparison; do not decide from source1891 alone.',
9:'Keil Seated Girl with Wreaths and existing Girl Teasing a Boy have near dimensions and overlapping seventeenth-century dates. Resolve the depicted composition/version before treating them as separate canvases.',
10:'Unknown British man in a blue coat, formerly Reynolds, has no named sitter. Preserve former attribution and source1752, but retain the generic portrait for fuller identity review.',
13:'Boudin Beach at Trouville is physically distinct from documented small panels, but existing7a640bad-8c80-4524-a52d-0e2476d1c73a and other incomplete Trouville beach leads remain unresolved. Source1865 versus an unverified1890s date is insufficient by itself.',
14:'Literal1964–71 and native1964–1971 span the creation cutoff. Do not truncate to1964 or silently classify the object as eligible.',
15:'Literal n.d. explicitly means undated. Numeric1600–1900 classification does not establish an actual object creation range. Preserve unknown date and former van Streeck attribution without adding an eligible record.',
30:'Dehner Untitled1952,40×51.8cm, is close in size to existing1951 gouache/graphite39.7×52.1cm and shares a generic title with other incomplete versions. Resolve physical composition/provenance before addition; one-year difference alone is not identity evidence.',
32:'Circle-of-Varley Farmhouse has an incomplete1835 Landscape creator lead; broad attribution and generic subject leave same-object uncertainty. Preserve the qualified attribution for further research.',
47:'Hunt Bird’s Nest and Blossom has an existing Bird’s nest with sprays of apple blossoms leadbbe7ea05-198a-5b17-9a23-5eb5a0d09a0f without physical metadata. Date ranges meet at1850; resolve version before addition.',
51:'Indian Court Official has an explicit2021 transfer from the Albright-Knox collection, but previous accession is absent and the generic portrait may exist under another title. Preserve the documented new holding as research evidence and reconcile former-collection object identity before adding.',
53:'Grohs Lofoten1967 has existing same-year Lofoten Landscape and Untitled watercolor leads with close overall measurements. Different catalogue accessions and widths require a fuller composition/provenance check rather than automatic duplication.',
54:'Ruskin Snow Capped Alps circa1845–49 has an existing Mountain Landscape, Macugnaga1845 leadf5bf5e0e-a1ed-5f40-b1a7-28fdd595444a without physical metadata. The small native sheet could be a titled version of this subject; preserve unresolved identity.'
}
def extra_protected_ids():return sorted({v['id'] for r in m.load(RUN/'additional-title-context-001.json.gz')['results'] for v in r['rows']})
def build():
    x=m.load(CANDIDATES);ix=m.load(IDENTITY);cx=m.load(CITATIONS)
    for dep in x['dependencies']+[x['parser_reference'],ix['query_reference']]+ix['query_references']:checked(dep)
    assert ix['candidate_reference']==ref(CANDIDATES) and cx['identity_reference']==ref(IDENTITY)
    validation=m.load(RUN/'identity-recomputed-001.json');checked(validation['validator_reference'])
    assert validation['candidate_reference']==ref(CANDIDATES) and validation['identity_reference']==ref(IDENTITY) and validation['comparisons_recomputed_equal'] and validation['rows']==62
    assert validation['query_references']==[ix['query_reference']]+ix['query_references'] and ix['params']==identity.params_for(x['rows'])
    context=m.load(RUN/'additional-title-context-001.json.gz');assert context['identity_reference']==ref(IDENTITY);checked(context['query_reference'])
    assert len(x['rows'])==62 and set(NOTES).isdisjoint(HOLDS) and set(NOTES)|set(HOLDS)==set(range(1,63));out=[]
    for row,cmp in zip(x['rows'],ix['comparisons']):
        assert row==f.parse(checked(row['source_reference']));n=row['number'];v=copy.deepcopy(row['facts'])
        if n in HOLDS:out.append(dict(row,state='editorial_hold',basis=HOLDS[n],comparison=cmp));continue
        assert v['date_issue'] is None and v['date_display'].casefold() not in ['n.d.','undated','date unknown'] and v['date_precision']!='after'
        assert v['first']<=v['last']<=1970 and v['inventory'] and v['credit_line'] and v['creator_label']
        assert not any(flag in row['review_flags'] for flag in ['campus_collection_requires_review','university_portrait_inventory','inventory_or_credit_requires_review','holding_or_custody_requires_review'])
        assert not cmp['untitled_creator_hits'] and not any(cmp[k] for k in ['native_scheme_hits','native_url_hits','source_hits']) and not any(a['relevant'] for a in cmp['inventory_hits'])
        basis='Native object '+v['source_id']+', inventory '+v['inventory']+': '+NOTES[n]
        out.append(dict(row,facts=v,state='approved_review_only_addition',existing_artwork_id=None,confidence=.90,basis=basis,comparison=cmp,derived_fields=dict(object_form=None,basis='No explicit icon or other derived form in this selection'),limitation='Editorial confidence in physical object identity and documented museum connection, not a calibrated probability. Preserve qualified/cultural creators, source rights, literal dates and unknowns. New records remain review. No new painter authority, image attachment, publication, current-display, legal-title or physical-custody claim.'))
    return out
def main():
    dest=RUN/'editorial-reviewed-001.json.gz';assert not dest.exists();rows=build()
    paths=[CANDIDATES,IDENTITY,CITATIONS,RUN/'identity-recomputed-001.json',RUN/'additional-title-context-001.json.gz',RUN/'version-web-001.json',f.d.PRIOR/'campus-collection-context-001.json']
    m.save(dest,dict(at=m.now(),reviewer_reference=ref(Path(__file__).resolve()),decisions=rows,supplement_references=[ref(p) for p in sorted(paths)],policy='Individual review decisions. No quota-based date or identity inference; uncertain physical versions retained. Source labels unchanged; no images or production writes.'))
    print(json.dumps(dict(approved=len(NOTES),held=len(HOLDS))),flush=True)
if __name__=='__main__':main()
