# Popular paintings: direct museum-image follow-up, 17 September 2026

Added **8 images to both local and production**, with matching files verified in Google Storage. All eight records remain in review. Artwork facts, creators, holdings and publication states were preserved. No new artwork or painter rows were created.

## What unlocked this batch

The Reims general terms had previously been held because an Etalab metadata licence was insufficient evidence for the exact photographs. The individual object pages have a separate HD-image section explicitly linking **[CC BY 2.0 France](https://creativecommons.org/licenses/by/2.0/fr/)**. This round verified that image-specific release.

Only public image renditions already embedded in the museum page were downloaded. No HD download form was submitted, no personal details were sent, and no download control was bypassed. The selected displayed photograph must agree with the licensed preview on exact inventory, painter, title, photographer, photographic content and aspect ratio. The licensed thumbnail names the same HD file and photographic view. Whole-image RGB comparison is a conservative additional check, followed by visual review of every delivered painting. The page statement establishes rights; pixel similarity alone does not.

## Delivered works

| Artist | Artwork | Inventory | Museum record |
|---|---|---|---|
| Claude Monet | Les Rochers de Belle-Ile ; Port-Dormois ; Belle-Isle | 907.19.191 | [Record](https://musees-reims.fr/oeuvre/les-rochers-de-belle-ile) |
| Gustave Courbet | Le défilé | 928.13.5 | [Record](https://musees-reims.fr/oeuvre/le-defile) |
| Jean-François Millet | Portrait d'homme anonyme ; Portrait de Delacroix | 949.1.41 | [Record](https://musees-reims.fr/oeuvre/portrait-d-homme-anonyme-304492002720691967) |
| Gustave Courbet | Paysage sans ciel | 937.15.1 | [Record](https://musees-reims.fr/oeuvre/paysage-sans-ciel) |
| Claude Monet | Les ravins de la Creuse | 907.19.192 | [Record](https://musees-reims.fr/oeuvre/les-ravins-de-la-creuse) |
| Pierre-Auguste Renoir | Paysage | 949.1.61 | [Record](https://musees-reims.fr/oeuvre/paysage-324526570339585105) |
| Alfred Sisley | La rade de Cardiff | 907.19.233 | [Record](https://musees-reims.fr/oeuvre/la-rade-de-cardiff) |
| Gustave Courbet | Étude de nu | 893.16.19 | [Record](https://musees-reims.fr/oeuvre/etude-de-nu-232566458820925197) |

All files contain the full museum-supplied view, with only proportional resizing and JPEG compression. Photographer attribution, licence jurisdiction/version, source page, exact source-image URL, checksum and verification timestamps are retained in the existing media and rights-evidence tables.

## Remaining Reims work

Of 12 eligible missing popular-painter paintings, 11 had explicit CC BY statements and eight passed the full rendition check. Three photographs differ from the licensed preview: Courbet’s *Le sculpteur Marcello* and *Rochers, sapins, ruisseau*, and Renoir’s *Marine*. Checking their remaining displayed views did not resolve the mismatch. Courbet’s *Sous-bois* lacks the explicit CC release. These four remain without an attached image.

## Museum permission route

Belvedere’s [Open Content page](https://sammlung.belvedere.at/opencontent/images) describes CC0, but current object-specific image captions still restrict checked files to private/scientific use and require contact for commercial use. The [museum Image Archive](https://www.belvedere.at/en/researchcenter) is the official permission channel. Twenty-five eligible popular-painter gaps remain there; the drafted initial request selects 23 with older creator death dates. Artwork age does not clear the digital photograph.

[Ready-to-send permission drafts](museum-permission-drafts.md) list exact museum records and inventory numbers for Belvedere and Reims. **No requests have been sent.** The drafts request PDM/CC0/CC BY/CC BY-SA files and photographer credits, including permission to serve proportionally resized images through Artline’s storage.

Additional policy checks: [Mauritshuis](https://www.mauritshuis.nl/contact/beeldmateriaal-aanvragen) publishes a permissive general collection policy, but an exact approved image licence and conflicting individual download text remain unresolved; [Strasbourg’s reproduction form](https://www.musees.strasbourg.eu/documents/30424/572651/Formulaire%2Bde%2Bdemande%2Bde%2Breproduction_2025.pdf/b342a9b6-352a-d651-169c-9819619b5004?t=1747051872322&version=1.0) specifies a quotation and usage contract; [Troyes](https://musees-troyes.com/phototheque-des-musees/) offers a paid reproduction service. These are permission channels, not approved files in this batch. Rouen research did not establish a qualifying new image release.

## Coverage after delivery

| Scope | Total | Usable images | Still missing |
|---|---:|---:|---:|
| Popular painters’ paintings | 5,261 | 2,318 | 2,943 |
| Eligible, source-supported popular paintings | 4,158 | 2,194 | 1,964 |

Both targets agree on these popular-painting counts. The wider local catalogue retains a pre-existing two-record/two-image difference from production; this round did not create that difference.

## Validation and evidence

120 synthetic popular-image tests passed, including 16 new cases for licence scope, jurisdiction, attribution, accession, image view, conflicting restrictions, crop mismatch and different photographs. Read-only audits verified all eight local records, all eight production records, eight Google Storage files, unchanged artwork/creator/source preimages, zero shared-image conflicts and 24 anonymous public image/artwork requests. Re-running the local writer and production uploader made no further attachments.

- [Exact approved-image manifest](approved-image-manifest.jsonl)
- [Aggregate report](final-aggregate-report.json)
- [Local audit](local-final-audit.json)
- [Production and Google Storage audit](production-final-audit.json)
- [All public delivery checks](public-all-images-final.json)
- [Preimage and duplicate audit](final-preimage-and-duplicate-audit.json)
- [Coverage snapshot](coverage-both-final.json)
- [Artifact scan](artifact-safety-scan-final.json)

Recoverable before-images are stored only in the approved Application Support backup directory, referenced by `backups.json`. The round uses public museum sources only. Evidence captures retain selected factual fields and image-rights statements, omitting authored descriptions and form/session inputs.

The reusable adapter is `ops/popular-reims-images.py`; existing local/production writers and audits recognize the provider. The exact French ported CC BY URI is retained rather than rewritten to the generic CC BY URI. No deployment or schema migration was required.
