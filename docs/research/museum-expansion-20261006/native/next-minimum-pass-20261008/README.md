# Five French museums — minimum 100 reached

Added **111 source-backed artwork records to the local review catalogue**. All five museums now exceed 100 eligible linked records. The preferred 200-work target remains ahead. Existing records, images, painter links and publication states remain unchanged. No current-display claim was added.

| Museum | Added | Linked records | Eligible records |
| --- | ---: | ---: | ---: |
| Nevers — Faïence Frédéric Blandin | 26 | 91 → 117 | 90 → 116 |
| Nancy — Beaux-Arts | 28 | 94 → 122 | 85 → 113 |
| Remiremont — Charles de Bruyères | 25 | 89 → 114 | 87 → 112 |
| Lisieux — Art et Histoire | 13 | 97 → 110 | 95 → 108 |
| Ornans — Gustave Courbet | 19 | 85 → 104 | 84 → 103 |

The [applied plan](five-museums-additions-001-plan.json.gz) has SHA-256 `10bb15ddb41cc61612b6de691e16cc70e3109f7f89442289677320672ae0de5e`. [Database readback](five-museums-additions-001-applied.json) verifies every new field, native identifier, citation and accepted collection holding. It preserves 2,672 scoped existing records and all 6,428 prior campaign objects and their associated rows. Replay made zero writes. Backups and logs are in the Artline Library directories.

A verified local Joconde snapshot provided 8,244 rows in the five museum scopes, including 7,789 source IDs not already catalogued. The [bounded selection](selected-metadata-queue-001.json) chose 176 records and retained 7,613 as held or outside this pass. Five selected-ID requests to the [official national-catalogue tabular API](https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/) returned all 176 records with HTTP 200. Complete current response bodies and receipts are retained in [capture evidence](capture-complete-001.json). No images were downloaded or attached.

[Individual review](editorial-reviewed-001.json.gz) approved 111 and held 65. Additions comprise 67 prints, 27 drawings, 14 paintings, two ceramics and one terracotta sculpture. Earlier strict passes excluded many blank-denomination records despite an explicit drawing or print domain. This pass uses that unambiguous domain while retaining the original blank field and an explicit derivation note. Ceramic classification additionally requires a literal vessel denomination and fired-clay medium. A conflicting drawing/engraving record remains held.

Creation dates remain distinct from model dates, depicted history and acquisition dates. Nancy's Boucher control proof retains its first-half twentieth-century date, not the 1630–34 model. Jacqueline Besson's 1970 drawing is eligible. Before dates keep unknown lower bounds and exclusive endpoints; circa ranges use independently stated source periods, not invented tolerances. Qualified attributions, unknown copyists, printers and publishers remain literal object-level labels without new painter authorities or artist links.

Each selected record represents one physical object. Nilouss's painted board with landscape and reverse still life counts once. Brouardel's seven recovered watercolors have separate modern accessions despite a shared historical gift catalogue number; the five unlocated gift works were not added. Marc and Cornillet sheets retain their individual measurements, dates, subjects and inventories within documented acquisition lots. Hadol's boxed 32-plate collection and uncertain Bracquemond portfolio components remain held.

The [identity scope](native-identity-001.json.gz) covers 39,592 existing artworks and [85,995 citations](identity-citations-001.json.gz), using surnames, aliases, titles, inventories, native URLs and source IDs. The prior linked/pending scope contains 464 records across the five museums. [Validation](identity-recomputed-001.json) reparsed all 176 current records and recomputed all comparisons. Live preflight rechecked the query results and citations before the atomic local write. A reused Courbet historical inventory, incomplete Riesener Venus versions, Ordinaire duplicates, ambiguous Ziem views and other unresolved physical versions remain research holds.

[Thirteen new offline checks](checks-001.json) passed, including an independent linear reference check of the indexed identity comparator. The 874 historical checks remain hash-pinned, for 887 cumulative verified checks; they were not all rerun. No test databases or real catalogue fixtures were created. This is not a large-scale load test.

The [wave56 coverage register](../../museum-coverage-after-wave-56.csv), [campaign report](../../verification-after-wave-56.json) and [delivery checkpoint](delivery-checkpoint-001.json) preserve this update. Campaign totals are **5,754 additions and 785 existing-artwork links across 165 institutions**. These five museums were already source-passed and expanded, so distinct institution totals remain unchanged. **1,191 canonical museum entries still have fewer than 100 linked records**; counts do not newly validate every legacy physical identity. The global goal remains active. The separate minimum-100 job remains unchanged and its totals are separate.
