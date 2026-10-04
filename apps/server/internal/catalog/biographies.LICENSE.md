# Biography reference-text attribution

The `text` values in `biographies.json` are opening excerpts of English Wikipedia
articles written by Wikipedia contributors. They are distributed under
[Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Each entry carries its article URL (including contributor history), exact captured
revision URL, licence URL, and the formatting/excerpt changes. This licence applies
to those reference texts; it does not relicense the Artline application code.

The data was captured on 4 October 2026 using Wikimedia's public APIs. Existing
catalogue authority IDs were matched to article Wikidata identities, including six
explicit Wikidata entity redirects. The original and canonical authority IDs are
both retained. Artist IDs and slugs bind the reference text to existing records.
This is identity and source verification, not a claim of independent scholarly
review of every statement in Wikipedia.

Regenerate with `ops/research-artist-biographies.py`, an existing-catalogue roster,
a retained source-evidence directory, and this file's adjacent JSON output path.
No database biographies, artist facts, publication statuses, artworks or images
are inserted or modified by that script. There are no live third-party requests
when a reader opens an artist page. Updating the bundle requires a reviewed code
release; source edits do not silently change a running release.

Relevant source policies:

- https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use/en
- https://www.mediawiki.org/wiki/Extension:TextExtracts
