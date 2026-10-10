# Individual Walters image reconciliation — 6 October 2026

Twenty-six previously held records were revisited. **Nineteen CC0 pictures were visually reviewed and attached locally.** Seven remain held. These are revisits, so they add no new distinct artworks to the combined review count. The already rejected single-panel photograph for the three-panel Deesis group was excluded from this pass.

Creator-name differences were resolved through existing `walters-person` identifiers, the museum's pinned object and creator CSV records, reciprocal object membership, and current native creator names and profile URLs. Explicit name pairs cover Díaz, Frère, Ribot, Vigée Le Brun and the accent difference in Beaumont. No fuzzy matching, artist merging, biography updates or catalogue name changes were performed. The nineteen image records also retain snapshots of the existing artist records and identifiers, verified unchanged after attachment.

The CSV files were already present from the 15 September operation at the museum's published commit `f7531ed751ac2c138eeb6f923a3b4fd325d78adf`. Their hashes and receipts are pinned in every authority proof. Fifteen orphaned continuation rows without numeric creator IDs are ignored; selected numeric IDs must remain unique and all required object/creator fields must agree. The initial parser rejection and candidate evidence are preserved in `events.jsonl` and `history/`. Source files were not altered or downloaded again. Image permission still comes from each selected photograph's current native CC0 grant.

Individual image review also resolved:

- The full colour front of Ferrari's *Linda of Chamonix* after the page's first image showed the back.
- A standard front of Romney's *Matilda Lockwood* and explicitly identified after-treatment fronts for Davis, Peale and Woodville.
- Complete portrait miniatures shown in open cases and two archival miniature photographs with `NF` filenames. Those two are visually confirmed monochrome and labelled as such.
- Enamel portraits with native Enameler roles for Larue and Zincke, supported by exact creator authority links.
- Literal spaces in the museum's image filenames and the exact letter-suffixed inventory `35.101F` for Fei Yigeng's [Lady Writing Poetry](https://art.thewalters.org/object/35.101F/), distinguished from its parent album.

Seven attached pictures are monochrome. The museum's question-mark creator marker for Fraser's *Mrs. Elizabeth Belin* is retained explicitly in the image attribution and evidence. All nineteen artworks retain their original creator links, dates, identifiers, holdings and review status. No publication or catalogue import occurred.

The seven remaining holds are three Japanese landscapes (35.310, 35.311 and 35.313) and Tenniel's 37.2939, whose primary photograph filenames carry different inventory numbers; two Stroganov portraits (38.376 and 38.377), with no primary image on the captured current pages; and the uncertain Silversmith attribution on Dankelmair's 37.2454. They remain unchanged and need further matching or editorial work.

Subsequent checkpoint: the [image-file concordance follow-up](../local-walters-asset-concordance-images-20261006/README.md) resolved the three Japanese landscapes and Tenniel through the museum's explicit object-to-file list. The counts above preserve this earlier operation's state.

Application JPEGs are in `apps/web/public/assets/artworks/imported/local-walters-reconciled-images-20261006/`. Originals and the inspected contact sheet are under `/Users/vadimdulub/Library/Application Support/Artline/source-images/local-walters-reconciled-images-20261006/`; locked preimages use the corresponding `backups/local-walters-reconciled-images-20261006/` directory. All approved JPEGs retain the full source frame and are below 100,000 bytes.

Files, source archives, primary-image links, media associations, exact stored rights evidence and native creator authorities passed verification. Five negative controls reject a wrong person ID, altered object-person membership, omission of a creator qualification, a selected front without its own CC0 grant, and substitution of an album inventory for a specific leaf. No database fixtures were used. HTTP delivery remains unverified because of the existing local-server timeout.

- [Attached pictures](attached-images.csv)
- [Visual decisions](visual-review.json)
- [File and database verification](verification.json)
- [Exact source evidence and unchanged holds](source-rights-verification.json)
- [Unchanged artist records and identifiers](creator-authority-verification.json)
- [Validator controls](validator-controls.json)
- [Operation counts](report.json)
- [Latest combined checkpoint](../local-image-recovery-20261006/README.md)
