# Archaeological Museum of Kilkis — continued review, 10 October 2026

**26 researched candidates await live database identity checks. Six further leads are held. No artworks or images were added in this pass.** The last dated production register showed 18 catalogue works and zero numerically date-eligible works on 9 October; authentication failure prevented a fresh count. These research totals do not increase that register.

- [All 32 object decisions](review-ledger-001.csv)
- [Detailed editorial evidence](editorial-decisions-001.json.gz)
- [Image and physical-object review](visual-assessment-001.json)
- [Scholarly catalogue reconciliation](publication-object-review-001.json)
- [Remaining research and upload requirements](remaining-research-001.json)

The review builds on the [15 earlier candidates](../kilkis-20261010/README.md). Fourteen further objects were selected from the [official collection](https://www.efa-kilkis.gr/artworks/) and its SearchCulture index: a funerary relief, six vessels, two coins including a coin reused as a pendant, one additional pendant and four pieces of jewellery. Each selected object has an individual native record and aggregator record captured. Of the 65 indexed objects, 18 were in the historical delivery, 29 have now received selected-object review, and 18 remain unselected. This is not a complete artwork census.

The [publisher’s catalogue](https://universitystudiopress.gr/item/glypta-romaikon-xronon--051223), *Γλυπτά ρωμαϊκών χρόνων. Ευρήματα στον νομό Κιλκίς* by Eleni Papagianni (University Studio Press, 2025, ISBN 978-960-12-2678-1), reports 87 sculptures held at the museum. Its public seven-page excerpt contains four complete entries and the beginning of a fifth. Accession 201 is the existing Apollo candidate and accession 11 the existing female-statuette candidate, identified as Aphrodite in this publication. Accessions 331 and 2046 provide two additional torso candidates with qualified Late Hellenistic dates. Entry 134 is truncated and remains held. The full catalogue and inventory crosswalk remain an evidence gap; the figure 87 is not a count of new additions.

The 26 candidates comprise 24 native records and two additional complete scholarly entries. They retain unknown numerical creation bounds and unknown creators. Original historical periods, qualified identifications, source materials and original accession spellings remain explicit. Discovery dates in 1960, 1967, 1972 and 1994 are not creation dates. The book author and artists mentioned as comparisons are not assigned as sculptors. Vessels, coins and jewellery use the existing `unknown` work-type value, with their actual object types retained in source metadata; they are not mislabeled as paintings or sculptures.

Six leads remain held:

- Bed-decoration fragments 1594 and 1595 may relate to existing 1593; separate fragment numbers do not establish independent artworks.
- Half-grape-cluster fragments 5859 and 5862 share an excavation trench and may join or share a parent object. Different thicknesses do not resolve that question.
- Accession ΑΕΜΚ3 describes a headless nude statue, while both its aggregator thumbnail and native photograph show a headed clothed male. Existing accession 2 has the reciprocal mismatch: a clothed description and a headless nude thumbnail. A possible image swap is an inference requiring accession-linked evidence; neither record was swapped, merged or changed.
- Scholarly entry 134 is incomplete in the public excerpt.

Figurines 4460 and existing 4461 remain distinct: the original record expressly describes the latter as a smaller related object. Joined fragments, the kothon and its lid, the pendant made from a coin, multiple vessel scenes and multiple photographic views each count as one object.

Thirty-three selected thumbnails and one native image were inspected internally; their files and rendered PDF proof pages reside under `~/Library/Application Support/Artline/research-proofs/kilkis-20261010/`. Native image labels are CC BY-NC-ND 4. Generic site/footer licenses are separate evidence. No public image use or attachment is claimed. Holdings are documented separately from current display.

Cloud token refresh still requires `gcloud auth login`. Before applying any records, refresh the museum-scoped production baseline, identifiers and citations, reconcile aliases and object versions across production, protect prior campaign records, prepare an exact-hash plan and obtain a successful backup. The earlier [105 Kazantzakis candidates](../kazantzakis-more-20261009/README.md) also remain unapplied. The last successful production phase remains 920 new works plus one museum link across seven museums. The real local catalogue was not modified.

The scholarly Morrylos article returned HTTP 403 and remains on an access hold. No alternate access route was attempted. Further source research can continue at other museums while authentication, missing catalogue pages and object-identity gaps are unresolved. Kilkis has not yet reached the 100–200 target.
