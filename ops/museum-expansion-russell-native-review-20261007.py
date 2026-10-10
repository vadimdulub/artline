#!/usr/bin/env python3
"""Record individually reviewed native Russell-Cotes additions; no database writes."""
import copy
import importlib.util
import collections
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-russell-native-research-20261007.py'))
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m;w=n.w;RUN=n.RUN
HOLDS={
'a-lions-head':'Existing Heywood Hardy A Lion’s Head, 1878, d7e7a728-987f-5ebd-ac34-928f41096d8f; reconcile instead of duplicating.',
'aurora-triumphans':'Existing Evelyn De Morgan Aurora Triumphans / Dawn, 1886, 7a67604d-ad6b-5286-a284-e81989e2e210. Native caption de Moran is inconsistent with its own narrative. Reconcile existing identity.',
'heavenly-stairs':'Existing Arthur Hughes exact-title identity 7244aad1-f07a-575f-9713-df40f65e4dd5, dated 1888 rather than native circa1887. Resolve holding without duplicate.',
'if-one-could-have-that-little-head-of-hers':'Existing Fortescue-Brickdale identity 0ca49350-9da5-53f6-919b-1ea1a58e13fa, imported1910 versus native1900–1909/exhibited1909. Reconcile existing identity.',
'midsummer':'Existing Albert Moore 1887 identity 7feb438b-ba18-5a05-8d4f-18049b9d7af1; reconcile holding rather than add.',
'landscape-with-bridge':'Existing same-title Corot identity 3f8ee41e-b2d4-435a-a553-a13d89bb650c with conflicting date. Native attribution is explicitly tentative and signature is not authorship proof; retain for reconciliation.',
'amazon-taming-a-horse':'Caption circa1843 conflicts with narrative placing development of Parian ware around1845 and Minton production1846–1910. Prototype versus manufacture date remains unresolved.',
'christmas-morning-1866':'Caption creation1898 conflicts with narrative saying rough sea was painted in the summer after December1865. Depicted shipwreck and title1866 are not a resolution of this creation conflict.',
'clytie':'Native SC8 conflicts with the captured Gallery I PDF listing SC8 for Calvi Summer. Resolve inventory before adding.',
'summer-2':'Native SC6 differs from captured Gallery I PDF SC8. Resolve conflict also involving Clytie before adding.',
'female-figure':'Caption names Benjamin Spence; narrative gives Edgar George Papworth Jnr. Unresolved object attribution despite clear1866 caption.',
'repose':'Existing Géza Vastagh Repose (Lion and Lioness), inventory1987.233, circa1900, and A Siesta need physical-version comparison against native BORGM02169,1899.',
'piazza-san-marco':'Pritchett’s existing Piazzetta and Salute/Piazzetta views have uncertain dates and need physical comparison against the native Doge’s Palace composition BORGM01758.',
'study-for-reclining-nude':'Etty creator pool includes generic Italian/French nude records with overlapping dates; resolve physical composition and version before adding this broadly dated study.',
'venus':'Caption circa1820 is also the stated date of the Leeds Hope Venus prototype. Actual manufacture date of this copy is not established.',
'voltaire':'Caption1781 does not establish the production date of this explicitly Barbedienne-foundry copy after Houdon. Hold casting chronology.',
}
NOTES={
'a-breezy-day-cornwall':'Native biography identifies David James as Joseph Donahue; both names were searched. Other Cornwall views in the creator pool have different titles/dates. Preserve source name David James; no artist profile changes.',
'a-shady-retreat':'1834 is the object caption date; Creswick’s biographical dates and later book illustration activity are not used for creation.',
'a-tempting-bait':'The source distinguishes the original painting exhibited1906 and sold to this museum1936 from Bovril promotional reproductions. Count the oil canvas once.',
'an-autumn-morning':'The Aumonier oil depicts plough horses; it is distinct from the separately inventoried Trevor An Autumn Morning/Anacapri1883 and Aumonier’s other sourced landscapes.',
'anno-domini':'Native Anno Domini / Flight into Egypt is the gigantic canvas exhibited1883, BORGM01344. The biblical event is not its creation date.',
'autumn-morning':'The Trevor Anacapri canvas BORGM02118,1883 is distinct from Aumonier’s An Autumn Morning BORGM00170,1900. Native heading is retained; fuller location title remains in caption evidence.',
'cherubs':'Native heading and narrative say Cherubs; the caption begins with truncated “rubs”. Same object page, inventoried oil panel and1899 date identify the work; preserve the caption typo in evidence.',
'coastal-scene':'Native narrative identifies William Raymond Dommersen as distinct from his father Pieter Cornelis. The1889 oil panel BORGM1995.42.1 is retained with its own inventory.',
'crater-of-kilanea':'Native date1883, oil board and BORGM00786 distinguish this nocturnal crater from the1880–1881 flowing-lava painting BORGM00785. The historical1908 title and spelling variants remain evidence.',
'daedalus-and-icarus':'SC83 is the1895 plaster preparatory model. Native source explicitly distinguishes it from the final bronze in Bristol; do not assign Bristol’s physical bronze to Russell-Cotes.',
'ethel':'Native Ethel Warwick portrait,1898,BORGM00894, purchased1917, is the oil painting rather than a reproduction or the sitter’s later stage history. Godward’s existing14-work pool was reviewed.',
'flood-in-the-highlands':'Native explicitly identifies this1864 Landseer replica as distinct from the1860 original in Aberdeen. The depicted1829 flood is not the creation date.',
'george-bernard-shaw':'SC90 is Kathleen Scott’s circa1933 bronze bust. The sitter’s1856–1950 lifespan and repeated sittings do not date this cast; retain the explicit object caption.',
'girl-knitting':'The1874 Gérard oil panel BORGM00880 is identified by native maker, medium and inventory; unrelated same-title works are different creator identities.',
'glen-sannox-isle-of-arran':'Native caption1882; the source explicitly says it is unknown whether this Murray painting was commissioned. Preserve that uncertainty and do not infer commissioning.',
'griselda':'Native1874 creation and marble are explicit. The medieval story is subject evidence; do not use Boccaccio’s dates. Type remains unknown where the saved object text does not explicitly classify this particular object.',
'gypsy-horse-drovers':'Native explicitly distinguishes this canvas BORGM01178 from its preparatory sketch on a wooden paint-box lid. Existing BORGM01174/.V records are not this canvas. Preserve native1894 and existing-study1895 discrepancy without editing older records.',
'harvest-time':'Retain literal about1810–1840 as a circa range; no midpoint or biographical year is invented.',
'how-the-danes-came-up-the-channel-a-thousand-years-ago':'1890 is creation; AD877 is the depicted event. Native narrative records a joint gift by Bone and his daughter.',
'in-the-wilderness':'One separately inventoried canvas BORGM01346 in Long’s three-painting Jephthah sequence,1885–1886. No additional trilogy aggregate is created.',
'jephthahs-vow':'Native explicitly calls this the first painting of the trilogy, BORGM01349. It is not a whole-series duplicate of BORGM01346 and01347.1885–1886 is creation; the1886 exhibition corroborates chronology.',
'judith':'Native BORGM01244 is Landelle’s1895 canvas depicting Judith with a sword; the biblical story is not a production date. Creator-scoped French titles were compared.',
'king-leopold':'One late19th-century marble copy, T1.3.2001.20, of the1817 Turnerelli original in the Royal Collection. Unknown actual sculptor is preserved; do not upgrade to Turnerelli or count the counterpart Charlotte bust on this record.',
'la-sirene-or-the-siren':'Retain object date1879 and literal Charles Landelle label. Native caption1821 versus narrative1812 birth discrepancy is not resolved as artist metadata.',
'landscape-autumn-blue-and-gold':'BORGM01587,1894 is distinct from Murray’s1882 Glen Sannox. Native text leaves its commission status unknown.',
'landscape':'Native explicit about1860–1870 describes the work, independently of Thors’s stated1863–1900 activity. Keep the circa range and original creator wording.',
'lewis-waller-as-monsieur-beaucaire':'Native1903 portrait and1915 purchase are distinct from the play’s1902 first performance and Waller’s lifespan. Count the portrait only.',
'lion-hunt':'SC15 is the Millet bronze sculpture, not a same-title painting or print. Literal late1800s is bounded conservatively by1800–1899, without inventing a late-century cutoff.',
'love-betrayed':'BORGM02039a is a circa1880 watercolor on paper mounted on board. Preserve the alphabetic inventory suffix and distinguish this bridge/cupid subject from Stanhope’s Love and the Maiden.',
'melusine':'Native SC28 marble is dated1841–1845 and described as carved for a Bavarian bath. Preserve historical intended setting without claiming current custody there; the museum object page identifies this collection object.',
'memories':'SC85 is the1947 bronze cast made after damage to the earlier1917 marble. The source explicitly dates the cast. Preserve1917 prototype/exhibition,1937 gift context and replacement Victoria Cross history; do not represent the bronze as a1917 cast or invent its caster.',
'miranda':'Native1869 marble SC26 has very little known history. Retain tentative identification with Shakespeare’s Miranda as source narrative, not a fabricated provenance.',
'monte-carlo-and-monaco-from-cap-martin':'Native circa1910 creation is independent of Holst’s1896 move to Bournemouth and1934 death. Both Lauritz/Laurits search forms were checked.',
'on-the-cornish-coast':'Native John Brett1880 canvas BORGM00357 differs from existing Charles L. Saunders On the Cornish Coast BORGM01936. The old native-URL citation is explicitly an unresolved title lead, not an accepted identity; preserve it unchanged and add this distinct Brett object.',
'painter-and-model':'Native1953 oil painting BORGM01522 shows Minton with Norman Bowler. Existing Minton1953 Portuguese Cannon is a different subject; biographies do not supply the object date.',
'pereat':'Native SC51 is a plaster version made by Andreoni’s studio in Rome, distinct from the marble/bronze original at Wadsworth. Preserve the studio qualification. The lost pedestal was replaced from the other version; its replacement date is unknown and no separate pedestal artwork is counted.',
'phryne-3':'Native1902 marble Sc27 is the object date and inventory. The subject’s circa328BC lifetime is not its creation date.',
'psyche-at-the-throne-of-venus':'Native1883 Hale canvas BORGM00967 is distinct from other military scenes by Hale; source medium typo “Oil in canvas” remains literal.',
'rising-tide-coast-of-scilly':'Native1885 is creation and1967 is the donation. David James/Joseph Donahue names were both checked; no artist biography is changed.',
'river-of-lava-issuing-from-mauna-loa-hawaii':'BORGM00785,1880–1881 is distinct from Furneaux’s1883 nocturnal crater BORGM00786. The1885 purchase is not its creation date.',
'river-with-barges-and-a-windmill':'Native caption Jan ver der Linde differs from narrative Jan van der Linde; preserve both, search the corrected form for duplicates, and create no artist link. Date remains about1880–1890.',
'saint-francis-of-assisi':'SC126 stone sculpture1930–1940; its possible use as a holy-water stoup remains tentative. The saint’s life and canonisation dates are subject context only.',
'scene-in-rotterdam':'Native1869 oil canvas BORGM00697 is by Pieter Dommershuijzen, distinct from the separately inventoried1889 William Raymond Dommersen coastal panel.',
'sir-merton-russell-cotes-1835-1921':'SC4 is Gazzeri’s circa1898 marble bust; caption Ernesto Gazzer and narrative Ernesto Gazzeri are retained. Existing same-sitter painting BORGM01358 is another creator/medium/inventory. No birth/death dates of the sitter are used for creation.',
'study-of-a-highland-cow':'Native1915 study on board BORGM2001.18 remains a separate physical study from Hurt’s larger cattle paintings; its possible purpose is tentative.',
'sunlight-nude':'Native1920s retained as1920–1929, not a guessed year. Model’s identification with Hilda is tentative and not an artist/subject metadata addition.',
'table-lamp':'One nineteenth-century electrical table lamp with unknown attribution and literal spelter medium. The1998 donation is not its manufacture date; its three branches are not three artworks. Physical type remains unknown rather than inventing a category.',
'the-annunciation':'Native object-specific1892 oil-on-fabric-on-board caption is retained. The broad biographical statement about Solomon’s inability to afford oils is not treated as a new technical examination or an invented different object date.',
'the-bathers-2':'SC42 is Andreoni’s marble mother-and-child sculpture, distinct from Stephens SC24 and Palmer’s1925 painting BORGM01696. Prior citation on the Palmer record explicitly says identity was unresolved; preserve that audit lead unchanged.',
'the-bathers':'SC24 is Stephens’s1878 marble mother-and-child sculpture, distinct from Andreoni SC42 and Palmer’s painting BORGM01696. Its alternate title One More Step and In We Go remains source evidence. Old URL citation was an unresolved false-title lead.',
'the-chosen-five':'One Long1885 canvas BORGM01348 depicts five models; the title is not a five-object quantity. Ancient Zeuxis and Helen are subject context.',
'the-cowl-maketh-not-the-monk':'Retain header1889 and narrative winter/spring1888–1889 production as evidence. Alternate title The Habit Does Not Make the Monk was checked against the53-work Watts pool.',
'the-dancing-faun':'SC14 is the1901–1904 iron sculpture by the named foundry. A base was recast after2005 vandalism; this is restoration of the earlier sculpture, not a second newly created faun. The old base is not separately counted.',
'the-death-journey-of-the-lily-maid-of-astolat':'BORGM00578 is one original1911 watercolor/pen/ink illustration, not a printed book or all16 illustrations. Preserve the physical drawing medium.',
'the-lands-end-cornwall':'Native1880 small oil canvas BORGM00356 is distinct from Brett’s other1880 Cornish canvas BORGM00357 and Tate’s much larger Britannia’s Realm. Source alternate Black East Wind and inscription Black Coast remain evidence.',
'the-love-message':'One1876 marble statue SC61, exhibited that year. The artist’s other cathedral statues mentioned in the biography are not counted.',
'the-martyr':'One separately inventoried canvas BORGM01347, final painting in the Jephthah trilogy. No additional whole-series record is created.',
'the-messenger':'SC25 is MacDonald’s1833 marble girl with carrier pigeon, distinct from generic same-title paintings in the catalogue.',
'the-moorish-proselytes-of-archbishop-ximenes-granada-1500':'Native1873 is creation. The title’s1500 and narrative1492 are historical events, not artwork dates.',
'the-new-model':'Native1883 canvas BORGM01990 by Dominik Skutezky; Skutecký spelling is preserved in narrative and searched, with no artist-profile mutation.',
'the-princes-sleeping-in-the-tower':'One1862 marble group SC80 depicts two princes; count one sculpture. Their1483 imprisonment and1674 remains discovery are subject context. Native Augusta Freeman / Horatia Augusta Latilla names are retained.',
'the-schiava-slave':'One19th-century marble SC50. Preserve the uncertain original title The Greek Slave and Girolamo/Gerolamo Oldofredi Tadini spellings.1921 is the gift year, not a fabricated creation date.',
'the-submission-of-emperor-barbarossa-to-pope-alexander-the-third':'Native1867 creation is independent of depicted1177 event and ruler’s dates. Preserve caption Soloman Hart alongside narrative Solomon Hart; no artist link is invented.',
'the-thames-embankment-london':'Native1882 is the object date.1878 electrification describes the depicted street and is not substituted as creation.',
'venetian-scene':'Native about1860–1870 range is retained. Henry Selous/Slous variants were checked; historical Grand Tours and illustrated-Shakespeare dates do not replace creation.',
'venetian-water-carrier':'Native1890 oil canvas BORGM00014; Eugene von/de Blaas name variants are checked. Same-title works by other creators do not establish identity.',
'venus-verticordia':'Native oil canvas BORGM01897,1864–1868 is distinct from the existing pencil Study for Venus Verticordia1946.345. Face repainting describes a state of the same canvas, not a separate artwork or a second version to add.',
'winter':'SC7,1872 is a separately inventoried Calvi marble bust, companion to Summer. Summer/Clytie inventory ambiguity does not alter this consistently identified SC7; the pair is not counted again as an aggregate.',
}


def reviewed_facts(row):
    f=copy.deepcopy(row['facts']);slug=row['source_id'];text=row['parsed']['narrative']
    if slug=='memories':
        assert 'cast in bronze in 1947' in text
        f.update(date_display='1947 (bronze cast; original marble 1917)',first=1947,last=1947,date_precision='exact',creator_label='Thomas Shaw Wilson (posthumous bronze cast)')
    if slug=='pereat':
        assert 'plaster version was made by Andreoni’s studio' in text
        f.update(creator_label='Studio of Orazio Andreoni',medium='Plaster',work_type='sculpture')
    if slug=='king-leopold':
        assert 'copy of the 1817 original by Peter Turnerelli' in text
        f.update(creator_label='Unknown artist, after Peter Turnerelli')
    return f


def main():
    rows=m.load(RUN/'native-candidates-002.json.gz')['rows'];comps={r['source_id']:r for r in m.load(RUN/'native-comparisons-002.json.gz')['records']};decisions=[]
    for row in rows:
        slug=row['source_id'];state=row['state'];decision=dict(source_id=slug,source_reference=row['source_reference'],state=state,reason=row.get('reason'))
        if state=='candidate':
            if slug in HOLDS:decision.update(state='hold_identity_or_source',reason=HOLDS[slug])
            else:
                assert slug in NOTES,slug;c=comps[slug];assert not c['inventory_hits']
                assert not c['source_hits'] or slug in ['on-the-cornish-coast','the-bathers','the-bathers-2']
                decision.update(state='approved_review_only_addition',reason=None,facts=reviewed_facts(row),confidence=0.95,identity_note=NOTES[slug],comparison=c,limitation='Editorial confidence, not a calibrated probability. Native collection membership does not assert legal ownership, present custody or current display. Original caption, narrative, source rights, date/creator discrepancies and unknown dimensions are retained; no artist profiles, links or images are created.')
        decisions.append(decision)
    selected=[r for r in decisions if r['state']=='approved_review_only_addition'];assert len(selected)==68
    m.save(RUN/'native-editorial-001.json.gz',dict(at=m.now(),decisions=decisions,selected_source_ids=[r['source_id'] for r in selected],counts=dict(collections.Counter(r['state'] for r in decisions)),source_review='All84 candidate narratives read individually; full140 capture accounting retained. Earlier86-candidate snapshot corrected the sitter-date and shared-inventory parsing issues before any mutation. Source scope and creator lookup were expanded for literal accented names and source variants.',policy='68 selected native additions. Keep unknown and studio/copy labels, original source evidence, physical casting date, distinct studies/replicas and separately inventoried canvases. Preserve all older catalogue records.'))
    print('Selected',len(selected),collections.Counter(r['facts']['work_type'] for r in selected))


if __name__=='__main__':main()
