# Acropolis Museum — production expansion, 9 October 2026

Added **116 production review artworks**, taking the museum from **25 to 141 catalogue works** and from **24 to 135 date-eligible works**. The museum now exceeds the 100-work minimum. It still needs 59 catalogue additions, or 65 date-eligible additions, to reach 200. The real local database remains unchanged at zero Acropolis records. The all-museum objective remains active.

- [Delivered artworks](added-production-artworks-001.csv)
- [All 179 discovery decisions](all-source-decisions-001.csv)
- [Museum register with observation timestamps](production-institution-register-001.csv)
- [Verification and remaining research](delivery-001.json)

The museum's [official collection index](https://www.theacropolismuseum.gr/en/explore-collections?field_exhibit_category_value=Sculpture&items_per_page=90) reports 256 sculptures. Two index pages yielded 180 rows and 179 unique URLs; one repeated boundary URL was retained as evidence and deduplicated. We reviewed 120 selected individual object pages, including 22 Greek narratives where the English description was incomplete. Nine existing objects were recognized by native URL; 50 discoveries remain deferred. A follow-up index page yielded [76 further discovery leads](next-source-discovery-001.csv), ready for individual review. Across three pages there are 255 unique URLs against 256 reported results; the one-record difference remains tracked, and directory discovery does not establish object coverage.

Four entries remain held: Telemachos' reconstructed stele, the male head combining an Athens fragment with a cast of a Rodin Museum fragment, the Athena head associated with torso/foot components, and the Lyon Kore assembly containing a cast of the upper body held in France. Surviving ancient fragments can be genuine artworks; assembled parts count together, and uncertain parent records are not invented. Dog head Acr.525 must be reconciled with the deferred body Acr.550 before further additions. Separate dog Acr.143 is a different animal. Dancer slabs EAM259 and EAM260 remain separate supports with a possible common base noted, without adding a hypothetical complete base.

The surviving objects control dates. Roman copies retain their Roman dates rather than the dates of their Greek models. BC ranges use negative years without year zero; century qualifiers remain literal, with conservative full-century bounds. Five open after dates remain outside automatic date-eligible counts. Dedicator names are not converted into sculptors. Rampin Master, Leochares and workshop attributions keep their qualifications, without new artist authority links.

The identity review checked 950 existing source/title/inventory/creator comparators and 730 supplementary subject matches. Existing 1911 watercolours of several Korai are depictions of the ancient sculptures and remain separate artworks at their recorded museum. Cleveland's Kore head and Alexander head and Chicago's Egyptian calf-bearer relief are distinct physical objects. Inventory namespaces are preserved: Acr.1329 and EAM1329 are different reliefs. Existing metadata and links were not rewritten.

Fourteen offline boundary tests passed. A successful Cloud SQL backup preceded the atomic write and readback, followed by a zero-write replay. All 26 protected existing records and 435 previous production additions were preserved; supplementary comparison snapshots were checked before the transaction. No images, publication changes or current-display claims were added.

The selected production phase totals **551 additions across five museums**; historical local totals remain separate. Only the Acropolis register row was refreshed. Other museum counts retain their previous audit timestamps. Continue toward 200 here and through the remaining nationwide and all-museum registers.
