# Hide empty museum collections — 8 October 2026

The user requested an attempt to add content to the 1955–1959 Struggle Museum at Holy Cross Monastery, Omodos, and to stop showing museums without catalogue items.

## Omodos research

Reviewed the [Omodos Community Council museum page](https://omodos.org/en/museums/), its [Greek version](https://omodos.org/mouseia/), three selected official display photographs, and [Cyprus University of Technology archive item CUT_OMODOS (99)](https://apsida.cut.ac.cy/items/show/40340). The sources establish a real historical collection but do not securely identify an individual eligible artwork for this pass. A secondary directory's hideout-flag reference remains a research lead. No catalogue work or image was invented or imported. See [omodos-review.json](omodos-review.json).

The neighbouring Byzantine museum, art gallery, lace museum and monastery church are distinct institutions/collections. Their objects were not assigned to the Struggle Museum. A museum's absence from browsing means Artline has no visible catalogue items for it; it does not mean the actual museum has no exhibits.

## Visibility change

The backend now requires at least one visible artwork for museum directory results, counts, pages, geographic choices, detail lookups and works endpoints. Empty institutions remain in the database and become browsable automatically after a visible artwork is linked. Anonymous, undated and unillustrated review works continue to count. Existing publication safeguards remain intact.

The production read-only snapshot returns **1,740 nonempty museums globally** and **24 in Cyprus**, down from 2,038 and 169 respectively. All Cyprus pages were checked for positive work counts, consistent totals and duplicate-free pagination. Omodos search results contain no empty collections. Cyprus Museum retains all 102 anonymous holdings; a review collection without a venue still works through institution geography.

Go catalog and HTTP package tests pass. Read-only production regression tests pass. Actual execution plans are captured in `global.json` and `cyprus.json`: directory count execution measured approximately 18.5 ms and 12.0 ms respectively. This is evidence from the current production catalogue, not a 10-million-row load test.

No local or production catalogue data writes, publication changes, image attachments, Git commits or Terraform apply. The API release uses the verified current production source archive with only `museums.go` and its read-only regression test changed. The web release removing the Artworks tab is preserved.

Source captures, inspected research photographs and release artifacts are under `/Users/vadimdulub/Library/Application Support/Artline/backups/nonempty-museums-20261008/`.

## Deployment

Live API revision `artline-api-nonempty-museums-1008` receives 100% of traffic. Candidate and public API checks passed; the public Omodos museum page returns 404 and Pedoulas remains available. See [deployment.json](deployment.json). Independent catalogue ingestion increased the total artwork count during this pass; no artworks were added or edited by this task.
