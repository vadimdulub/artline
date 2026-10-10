#!/usr/bin/env python3
"""Pin individually reviewed Städel metadata additions; preparation is read-only."""
import hashlib
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-staedel-20261006.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s);m=s.m

HOLD_GROUPS={
'1114':('existing_translated_title_requires_reconciliation','Surname-first creator review found Il Cristianesimo che introduce le arti in Germania, b38f5996, with no inventory/dimensions. Resolve same work, study or copy before adding.'),
'2059':('version_identity_requires_review','Additional Michau surname-first labels include Retour de la pêche, c16a1bb0, and generic animated landscapes. The native page lacks dimensions; further physical-object comparison is needed.'),
'166':('version_identity_requires_review','Additional Schalcken surname-first label found ritratto di pittore, b78fc8fb, and self-portrait69f2294c, with incomplete identities.'),
'sg114':('version_identity_requires_review','Additional full/reordered Scholderer name found Portrait of the Artist’s Wife, e7e38304, probably1872–1873 and no dimensions. Resolve the sitter/version before adding.'),
'2460':('version_identity_requires_review','Additional Ribot reordered-name pool contains Les Philosophes, db18a0fe, and kitchen scenes with incomplete identities. Resolve the Empty Bottle figure composition before adding.'),
'2436':('version_identity_requires_review','Additional reversed Baj label found Astratto, Senza titolo,2343a754, lacking dimensions and inventory. Retain Non uccidete i bambini for composition comparison.'),
'442':('version_identity_requires_review','The known large Giovane fumatore is a different format, but the newly found c76ce256 counterpart lacks dimensions and its exact physical identity is not reconciled. Retain both source leads.'),
'1981/1980':('version_identity_requires_review','Additional reordered Goya labels revealed the two wooden Cannibales panels,b6dd88ea/42b13db5. They have different recorded dimensions but related violent subjects; compare compositions and preserve the tentative native attribution before adding.'),
'sg1258':('source_date_conflict','Dachpfanne header says 1967 but narrative dates the rooftop-tile paintings to 1965; preserve the unresolved version/date relationship.'),
'sg465':('source_date_conflict','Ensor header says 1921 but inscription reads ENSOR 99. Retain both pending resolution.'),
'sg1197':('source_date_conflict','Vallotton header/narrative says 1900 but signature and reverse inscription give 1901.'),
'2077':('source_chronology_requires_review','Hodler 1909 header and narrative six-year-old Hector require chronology/version review; do not derive a replacement date from age.'),
'2472':('object_type_requires_review','Rivers Eliza is an assembled pencil/foil/paper/wood work. Preserve native painting classification as evidence pending object-type review.'),
'2492':('attribution_qualification_requires_review','Brandi native creator field is unqualified, while narrative says in all probability and offers several possible saints. Reconcile the qualified attribution before adding.'),
'944':('existing_translated_title_requires_reconciliation','The Lucca Madonna, 9587145b, is an existing same-title/creator lead; adding another record would risk duplication.'),
'1378':('existing_translated_title_requires_reconciliation','Compare Aertsen Market with Christ and the Woman Taken in Adultery, ede4927d, and 4c72f672 before a new record.'),
'1077':('existing_translated_title_requires_reconciliation','Veneto Flora, 77b209b6, and Portrait présumé de Lucrèce Borgia, 2cba0380, require same-work reconciliation with the native historical title.'),
'90':('version_identity_requires_review','Fabritius Naming of Saint John, 114edc35, lacks inventory and dimensions; source title/date differences do not distinguish objects.'),
'1050/1076/1223':('version_identity_requires_review','Brouwer creator pool includes Feeling, 79549b25, The Bitter Drunk, ee03fca2, and multiple drinkers without inventories. Compare the physical compositions before adding the operation/potion/drunken-peasant works.'),
'1559':('version_identity_requires_review','Segantini sunset landscape needs comparison with Plain when it gets dark, a30ea0c6, and the smaller Maloja composition, 59167ce0. The narrative distinguishes a smaller triptych version; do not decide solely by dates.'),
'sg404':('version_identity_requires_review','Rousseau park avenue requires comparison with Montsouris, f6585393, at a very similar 46 x 38 cm format, and Promeneurs dans un parc, cd1d1b71. Site-name differences alone do not settle identity.'),
'1350':('version_identity_requires_review','Sisley bank-of-Seine landscape requires physical-object comparison against the creator-scoped river-bank and autumn variants, including incomplete generic landscapes.'),
'2261':('version_identity_requires_review','Vallotton Blonde Nude remains a version lead among multiple standing and reclining nudes. Native inventory alone does not exclude differently titled existing records.'),
'1809':('version_identity_requires_review','Vuillard board-game scene needs composition comparison against generically titled interiors and family scenes in the creator pool.'),
'sg509':('version_identity_requires_review','Codde surname-first/name-variant review found Merry Company, 9a74131d, and Galant gezelschap, 6f84c2b7, with incomplete dimensions. Compare music-making versions.'),
'2334':('version_identity_requires_review','Fleischmann numbered composition needs comparison with unnumbered Composition, 425c7553, lacking inventory/dimensions. Different dates do not resolve identity.'),
'sg1240':('version_identity_requires_review','Fontana Attese has multiple slit-canvas versions, including a0b51ae4 and ed69e59c without dimensions or inventory. Preserve four cuts and 92 x 73 cm pending comparison.'),
'1126/590':('version_identity_requires_review','Van der Heyden country-road and Loenerslot scenes require comparison with A Country Home, b7b952af, An Imaginary View of Nijenrode Castle, 5b8a78b2, and other incompletely catalogued country views.'),
'1240':('version_identity_requires_review','Ruisdael dune landscape with fence needs comparison with Landscape with Wooden Fence and the other generic dune/woodland views, retaining native 44.3 x 36.2 cm and inventory1240.'),
'1167':('version_identity_requires_review','Dal Ponte creator pool contains the unidentified pair 4058dddc and dispersed panels; resolve their subjects and scope before adding this Madonna.'),
'783':('version_identity_requires_review','Hobbema forest entrance requires comparison with Le Chemin dans la forêt, e1e5575a, and other woodland roads with incomplete object identities.'),
'1825':('version_identity_requires_review','Dahl painted multiple Vesuvius eruptions. Compare the source 128 x 172 cm canvas with the existing Eruption of Vesuvius versions; event1820 and signature1826 are distinct evidence.'),
'1436':('version_identity_requires_review','Van Gogh Nuenen farmhouse requires comparison against translated cottage/farmhouse versions and their physical identities.'),
'2548/sg1247':('version_identity_requires_review','Ernst Fishbone Forest and Nature at Dawn need composition comparison with Forêt, 952fdde9, La grande forêt, 6c3e7ac5, and forest/bird variants. Generic titles do not establish distinct objects.'),
'2132':('version_identity_requires_review','Léger Fishermen needs comparison with the creator pool’s composition/figure paintings and titles such as Composition aux deux matelots. Several generic versions lack inventories.'),
'1112':('version_identity_requires_review','Ruysdael sailing boats needs comparison with lake/river and Russian/Dutch/French landscape variants with incomplete inventories and dimensions.'),
'2045':('version_identity_requires_review','Fantin-Latour flower still life requires comparison against repeated chrysanthemums and generic bouquets; native 1889 signature and 1952 bequest remain preserved.'),
'sg1213':('version_identity_requires_review','Matisse capuchin cress has no historical SG277 inventory collision, but generic flower/porcelain still lifes and nasturtium versions still need physical-object comparison.'),
'1628':('version_identity_requires_review','Hoppner girl with rabbit needs comparison against generic female/child portraits, including nearly matching standard canvas sizes.'),
'sg1253':('version_identity_requires_review','Tàpies white bed/cage work needs comparison with generic relief paintings, including Relief gris mat, b2f9489d, lacking physical-object metadata.'),
'sg1261':('version_identity_requires_review','Giacometti seated Annette needs comparison with generic Portrait, 58d4f904, and repeated sitter/nude versions.'),
'2440/2258':('version_identity_requires_review','Fruhtrunk name reversal revealed Sans Titre, 50ac7308, with no inventory or dimensions. Resolve the unclassified composition before adding either proposed abstraction.'),
'1071/1271':('version_identity_requires_review','Goyen Haarlem Sea and dune path have repeated broad river/seascape/dune compositions. Retain native inventories and signatures for further physical-object comparison.'),
'sg1227':('version_identity_requires_review','Schlemmer half-length profile needs comparison with Kopf, 7c9c1867, and other head compositions with unknown dimensions.'),
'2155':('version_identity_requires_review','Delacroix Hamlet/Horatio subject has several existing paintings and prints. Reconcile 1975.1.616 and the inventory-less French cemetery versions before addition.'),
'sg22':('version_identity_requires_review','Thoma hammock mother/child requires comparison with Mother and Child in a garden, 6fe896cb, lacking dimensions and inventory.'),
'1107':('version_identity_requires_review','Cuyp sheep pasture requires comparison with Panoramic Landscape with Shepherds, Sheep and a Town, 12392a5a, and other generic pastoral records.'),
'647':('version_identity_requires_review','Roos cattle ford needs comparison with Landscape with Cattle, 2cfe400d/379e14c8, and the unclassified Пейзаж, eb25f831.'),
'1354':('version_identity_requires_review','Spitzweg hermit requires comparison with LA LECTURE DU BREVIAIRE, LE SOIR, ec6db7fe, which lacks inventory/dimensions.'),
'2439/2438':('version_identity_requires_review','Nay Himmelsrichtung and Ostseedünen need further comparison with incomplete generic compositions and White Spring, 7183bb69. Do not establish different works by source dates alone.'),
'607':('version_identity_requires_review','Pynacker cemetery needs composition comparison with Italian Landscape with Ancient Tempietto and generic Italian landscapes.'),
'1499':('version_identity_requires_review','Corot Marino autumn view needs comparison with generic Italian landscapes; the source explicitly distinguishes a morning painting and preparatory drawing.'),
'sg172':('version_identity_requires_review','Liebermann Jewish Street study needs comparison with Vegetable market in Amsterdam, 1bf3b048, and the larger studio version mentioned by the native source.'),
'2550':('version_identity_requires_review','Kandinsky Kallmünz landscape needs comparison with the Russian-title summer landscapes, 7745f235/89a6aa3e, and other early views before addition.'),
'1849':('version_identity_requires_review','Poussin thunderstorm requires comparison with L’Orage, 26473be7, whose dimensions are missing. A separate 99 x132 cm Rouen storm record does not alone reconcile every existing entry.'),
'sg1128':('version_identity_requires_review','Heckel Holstein landscape and existing Schleswig DEP594, 893006c9, have closely similar dimensions and related geography; a date discrepancy alone cannot distinguish them.'),
'1484/1485':('version_identity_requires_review','Peruzzini monk landscapes require comparison with incomplete Rijksmuseum leads44f9f8ce/e0a20fb7, retaining reading/praying distinctions and independent inventories.'),
'sg458':('version_identity_requires_review','Cézanne rocky road landscape needs composition comparison against translated and generic landscape variants.'),
'838/952':('version_identity_requires_review','Fra Angelico and Rosso Madonna/Holy Family subjects have existing broadly titled versions without complete inventories; compare specific panels before adding.'),
'850':('version_identity_requires_review','Rogier Medici Madonna needs comparison with Madonna and Child, 76c4b71e, and the incompletely described Various Altarpieces, a9962524.'),
'sg1252':('version_identity_requires_review','Dubuffet Tapié Grand Duc needs comparison with Portrait de Michel Tapié C.90.1 and other portrait versions.'),
'1113':('version_identity_requires_review','Brueghel Latona lead SK-A-70, 476a931b, has nearly identical37 x56cm dimensions. Resolve composition/version rather than adding on translated-title differences.'),
'1821':('version_identity_requires_review','Friedrich rising fog needs comparison with Fog, c96e59d7, and mountain variants. Pinakothek8858 is a larger separately inventoried canvas but does not resolve the inventory-less Fog entry.'),
'1092':('version_identity_requires_review','Van der Neer nocturnal canal has many moonlit-waterway title variants with incomplete identities; retain source inventory1092 for composition comparison.'),
'977':('version_identity_requires_review','Savery Orpheus requires comparison with generic rocky/river animal landscapes and former Paradise subjects.'),
'1658':('version_identity_requires_review','Monticelli wall-painter scene needs comparison with Subject Composition61f9c604/742f7801, which have no physical metadata.'),
'1772':('version_identity_requires_review','Pater pastoral festivity needs comparison with Fête Galante69a6f3b4 and Fête Champêtre bdadaddd before a new record.'),
'1441':('version_identity_requires_review','Tiepolo Crotta family canvas requires review against the incompletely classified Four Decorative Scenes3250535e and narrative subject variants; preserve acquisition1908/1902 conflict.'),
'1680':('version_identity_requires_review','Morland peasants and hut needs comparison with Rustic Sceneace04453 and other country/inn scenes lacking full identities.'),
'1208':('version_identity_requires_review','Nattier Leerse portrait requires comparison with generic portraits of women and incomplete inventories; sitter search alone does not resolve them.'),
'1798':('version_identity_requires_review','Veit Bernus portrait requires comparison with Portrait of a Woman3a606e12, lacking inventory/dimensions and with an unverified date.'),
'sg41':('version_identity_requires_review','Trübner violet dress is larger than Auckland1957/11, but Dame mit schwarzem Halsband and other sitter versions still need composition review.'),
}
HOLDS={oid:value for ids,value in HOLD_GROUPS.items() for oid in ids.split('/')}
NOTES={
'sg176':'Renoir creator pools, reordered names and luncheon subjects were reviewed. Phillips object1637 is130.2 x175.6cm; Chicago1922.437 is55 x65.9cm; StädelSG176 is100.5 x81.3cm. These native inventories and formats distinguish the luncheon paintings. Other nearby outdoor portraits have different subjects/formats. Preserve1879 and the1910 acquisition separately.',
'1210':'Reordered Van Vliet label revealed another Oude Kerk interior,276abad6. It is82 x65cm oil on canvas, whereas Städel1210 is50.6 x59.7cm on oak. The support and portrait/landscape formats distinguish these repeated church views without relying on uncertain creation dates.',
'2214':'The Modersohn-Becker pool includes birch-trunk and Worpswede landscapes, named women and children, and a newly found girl in red. None identifies the native male figure lying under a flowering tree. Preserve the52 x74cm cardboard support,1903 and distinct2214 gift inventory.',
'1981':'Reviewed all84 creator-scoped painting/unclassified leads, including qualified and alias labels. None identifies this separately inventoried violence-against-two-women pine panel. War prints and the Maragato series are different compositions/supports. Preserve the literal question mark attribution and1941/1942 acquisition discrepancy.',
'1980':'The independently inventoried companion attack-on-a-woman pine panel was compared with the same Goya pool. Do not merge it with1981 or upgrade the tentative attribution. Preserve individual31.2 x40cm dimensions and source provenance.',
'sg1244':'Aquis submersus is a54 x43.8cm oil canvas. The generically titled Landscape22a31754 is11.1 x20.6cm oil on glass, a distinct object. The full59 painting/unclassified Ernst pool contains no corresponding native title/composition identity.',
'761':'The tentative Teniers the Elder label is kept literally, without linking the younger namesake. The broad family-name pool has no Birth of Adonis composition identity. Preserve ca1600–1605 and the native support.',
'2451':'The native narrative mentions two further Blind Man and Girl versions. The existing Hofer pool consists of other named portraits, The Letter and Man with a Melon, with different subjects and formats; no existing Blind Man version was found. Preserve this102 x90cm canvas, inventory2451 and1943.',
'498':'The Rembrandt pool includes Saul and David5990ce08, Mauritshuis621:130 x164.5cm oil on canvas. This native work is62 x50.1cm on oak, separately inventoried498. These physical identities distinguish the versions without relying on date differences.',
'2085':'Marc historical inventorySG292 has no existing artwork or identifier match. The nearby Siberian Dogs in the Snow1983.97.1 is80.5 x114cm with multiple dogs; Städel2085 is62.5 x105cm and one dog. Preserve the confiscation and explicit1961 reacquisition, separate from creation.',
'1149':'The complete36 Vermeer painting/unclassified pool and broad Geograph/Géographe searches contain no matching work. Other named compositions and native inventories are distinct. Preserve unknown dimensions and the signed1669 evidence.',
'1157':'The full Tischbein name-variant painting pool and broad Goethe search found other subjects/creators, no corresponding Campagna portrait. Keep source1787 and the inconsistent1887/1878 acquisition statements separately.',
'sg1274':'The twelve Richter painting/unclassified leads concern cityscapes, sea views, figures and portraits; no curtain identity was found. Broad German/English curtain searches were checked. Preserve this200 x275cm canvas and1967.',
'890':'The independently inventoried Job panel is a trimmed exterior altar wing,96 x51.5cm lime wood. The complete Dürer painting/unclassified pool contains other altarpieces and individual subjects, no Job/Jabach identity. Count this panel once; do not claim the entire dispersed retable.',
'879':'Both Meloni and Melone names were checked. Existing works concern Emmaus and Christ carrying the Cross; no Narcissus/Catherine version was found. Retain the source description of trimming and removed overpainting without inventing a second work.',
'1652':'Bruyn surname-first variant found only the distinct Déploration/Pietà lead. The native Nativity has named Clapis/Bonenberg donors and inscribed1516, with its own136.7 x152.7cm oak panel and inventory1652.',
'442':'Molenaer Giovane fumatore bebbbf33 is71 x54.3cm, whereas this smoking man and empty glass is29.2 x24.2cm. The remaining creator pool depicts different multiple-figure, musical or religious subjects. Preserve the questionable signature without inferring a creator profile.',
}

def main():
    source=s.RUN/'staedel-001-research.json.gz';research=m.load(source)
    assert len(research['records'])==180 and research['source_failures']==0
    working={};working_paths=sorted(s.RUN.glob('editorial-working-notes-*.json'))
    for p in working_paths:
        for ids,note in m.load(p)['notes'].items():
            for oid in ids.split('/'):working[oid]=note
    assert all(r['source_record_id'] in working for r in research['records'])
    comparisons={r['source_record_id']:r for r in m.load(s.RUN/'creator-title-comparison-leads-003.json')['records']}
    held=list(research['held']);records=[];reviews=[]
    for r in research['records']:
        oid=r['source_record_id']
        if oid in HOLDS:
            reason,note=HOLDS[oid];held.append(dict(record=r,reason=reason,editorial_note=note));continue
        raw=s.captured_body(dict(receipt=r['source_receipt'],body_path=r['body_path']))
        assert s.validate_record(r,raw)==r['facts']
        review=dict(source_record_id=oid,source_capture_sha256=r['source_receipt']['sha256'],
            reviewed_fields=['native_fields','narratives','unlabelled_properties','object_history','inscriptions','index_identity','creation','acquisition_credit','rights'],
            decision='approved_new_review_record',working_source_note=working[oid],
            final_identity_decision=NOTES.get(oid,'Native object, inventory and source identities were checked, together with creator-name variants, candidate title leads and the painting/unclassified creator pool. No corresponding identity or unresolved same-work lead was identified for this selection. Preserve literal source facts, anonymous/qualified creator labels and unknown fields; no artist link or display/publication inference.'),
            creator_comparison_pool_size=comparisons[oid]['pool_size'])
        r['raw_source_record']['editorial_review']=review;records.append(r);reviews.append(review)
    assert len(records)==98
    with m.connect() as db:
        assert not s.title_collisions(db,records)
        iid=research['museum']['id'];known,titles,inventories=s.existing_keys(db,iid)
        assert not known & {r['facts']['source_url'] for r in records}
        assert not any(s.inventory_keys(r['facts']['accession'])&inventories for r in records)
        assert not any(m.norm(r['facts']['title']) in titles for r in records)
    paths=[s.RUN/x for x in ['creator-identity-review-003.json','creator-title-comparison-leads-003.json','creator-name-discovery-001.json','subject-version-identity-leads-001.json','supplemental-identity-leads-003.json','qualified-creator-extra-leads-001.json','renoir-version-comparison-001.json']]+working_paths
    extra=s.RUN/'supplemental-identity-review-003.json'
    assert extra.exists();paths.append(extra)
    evidence=[dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    plan=dict(at=m.now(),records=records,held=held,research_source=str(source.relative_to(m.ROOT)),research_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),identity_evidence=evidence,
        editorial_reviews=reviews,before=research['before'],indexes=research['indexes'],policy='Individually selected official Städel paintings and separately inventoried painted panels. Review-only local metadata with native creator qualifications, creation statements, acquisition/ownership and rights evidence. Unresolved source conflicts and object versions held; no images, artist links, display claims or publication changes.')
    dest=m.RUN/'staedel-001-current-plan.json.gz';assert not dest.exists();m.save(dest,plan)
    m.save(s.RUN/'followup-queue-001.json',dict(at=plan['at'],held=held,resume_page=research['resume_page'],unprocessed_captured_rows=research['unprocessed_captured_rows'],next_page=research['next_page'],policy='Research evidence only. Recheck source and current physical-object identities before later additions. Continue after captured page4 unprocessed rows; current pass does not exhaust collection.'))
    print('Städel reviewed',len(records),'individual holds',len(HOLDS),'all held',len(held),'sha256',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)

if __name__=='__main__':main()
