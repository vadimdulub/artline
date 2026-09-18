#!/usr/bin/env python3
"""Select evidenced covers/title pages; keep rejected candidates and all gaps.

This intentionally does not accept an image merely because it is on Commons.
The work-to-file claim, cover identity, underlying design's public-domain basis,
reproduction license, credit and absence of rights warnings must all be present.
No database writes or image downloads. See the accompanying research README.
"""
import collections
import html
import json
import pathlib
import re
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/research/book-covers-20260917'


def plain(value):
    return ' '.join(html.unescape(re.sub(r'<[^>]*>', ' ', str(value))).split())


def classify(candidate, result):
    page = result.get('page', {})
    info = page.get('imageinfo', [{}])[0]
    meta = info.get('extmetadata', {})
    if not meta:
        return None, 'source-metadata-unavailable'
    val = lambda key: plain(meta.get(key, {}).get('value', ''))
    cats = val('Categories')
    identity = candidate['file'] + ' ' + cats
    description = val('ImageDescription')
    # A mention of a cover somewhere in a long description is insufficient.
    # Keep only an explicit opening description or a file/category identity.
    if re.match(r'^(?:English: )?(?:The )?(?:[Ff]ront cover|[Cc]over|[Tt]itle[ -]?page|[Tt]itelblatt|[Pp]ortada|[Cc]ouverture)\b', description):
        identity += ' ' + description[:200]
    is_title = re.search(r'title[ _-]?pages?|titelbl[aä]tt|page de titre|frontespizio|титульн', identity, re.I)
    is_cover = re.search(r'\bcovers?\b|couverture|portada|обложк', identity, re.I)
    if not (is_title or is_cover):
        return None, 'image-not-identified-as-cover-or-title-page'
    if re.search(r'\b(?:detail|miniature|fragment|portrait)\b', candidate['file'], re.I) and not re.search(r'cover|title[ _-]?page|titelblatt', candidate['file'], re.I):
        return None, 'partial-image-needs-identity-review'
    if info.get('mime') not in {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}:
        return None, 'missing-or-unsupported-image'
    if val('Restrictions') or re.search(r'disputed copyright|copyright violations?|deletion requests?|missing permission|no permission|possibly unfree|fair use|de minimis|freedom of panorama|unfree|permission pending|license review needed|license review failed', cats, re.I):
        return None, 'rights-warning-or-restriction'
    origin = str(meta.get('Credit', {}).get('value', ''))
    if not plain(origin) or plain(origin).lower() in {'unknown', 'unknown source'}:
        return None, 'reproduction-origin-not-established'
    if re.search(r'gallica|bnf\.fr|Biblioth[eè]que nationale de France', origin, re.I):
        return None, 'bnf-commercial-reuse-needs-clearance'
    if re.search(r'Biblioteca (?:Nazionale|Medicea|Angelica|Casanatense|Braidense)|beniculturali\.it|cultura\.gov\.it|museogalileo|gutenberg\.beic\.it', origin, re.I):
        return None, 'italian-custodian-permission-needs-review'
    if re.search(r'non[ -]?commercial|personal use only|study only|placa conmemorativa|commemorative plaque', plain(origin), re.I):
        return None, 'source-use-or-edition-identity-needs-review'
    # A photographer's PD-self/CC license alone does not clear a book design.
    text_design = re.search(r'PD[ -](?:text(?:logo)?|ineligible)(?:[ |(]|$)', cats, re.I)
    old_design = re.search(r'PD[ -]Old(?:[ |(]|$)|PD-old-(?:[7-9]\d|\d{3}|auto)|Author died more than 100 years|PD-anon-expired', cats, re.I)
    date = val('DateTimeOriginal')
    date_years = [int(y) for y in re.findall(r'(?<!\d)(1\d{3}|20\d{2})(?!\d)', date)]
    category_years = [int(y) for y in re.findall(r'\b(1\d{3}) (?:book covers|title pages|books)(?:\b|\|)', cats)]
    old_publication = bool(date_years and max(date_years) <= 1930 or category_years and max(category_years) <= 1930)
    expired = bool(re.search(r'PD-old-(?:[7-9]\d|\d{3}|auto)-expired|PD-anon-expired|PD US expired', cats))
    if not text_design and not (old_design and (old_publication or expired)):
        return None, 'underlying-design-rights-not-established'
    license_name = val('LicenseShortName')
    license_url = val('LicenseUrl')
    if license_name == 'Public domain':
        license_url = 'https://creativecommons.org/publicdomain/mark/1.0/'
    elif license_name == 'CC0':
        license_url = 'https://creativecommons.org/publicdomain/zero/1.0/'
    elif not re.fullmatch(r'CC BY(?:-SA)? (?:[1-4]\.0|2\.5)', license_name):
        return None, 'unsupported-reproduction-license'
    if not license_url.startswith(('https://creativecommons.org/', 'http://creativecommons.org/')):
        return None, 'missing-license-link'
    license_url = license_url.replace('http://', 'https://', 1)
    credit = val('Attribution') or val('Artist')
    if not credit or re.fullmatch(r'(?:unknown(?: author)?\s*)+', credit, re.I):
        if license_name == 'Public domain' and val('AttributionRequired').lower() == 'false':
            credit = 'Creator not identified in the source'
        else:
            return None, 'credit-needs-review'
    image_url = info.get('thumburl') or info.get('url', '')
    parsed = urllib.parse.urlsplit(image_url)
    if parsed.scheme != 'https' or parsed.hostname not in {'upload.wikimedia.org', 'thumb.wikimedia.org'}:
        return None, 'unsupported-image-host'
    source_url = info.get('descriptionurl', '')
    if not source_url.startswith('https://commons.wikimedia.org/wiki/File:'):
        return None, 'missing-source-page'
    label = 'Title page' if is_title else 'Edition cover'
    # Label only an unambiguous source date; do not infer an edition's year from
    # the work's composition date, the author's life, or a photograph timestamp.
    if re.fullmatch(r'1\d{3}', date) and int(date) <= 1930:
        label += ' · ' + date
    cover = {'bookId': candidate['bookId'], 'sourceId': candidate['sourceId'],
             'imageUrl': urllib.parse.urlunsplit(parsed._replace(query='', fragment='')),
             'sourceUrl': source_url, 'label': label, 'credit': credit,
             'license': license_name, 'licenseUrl': license_url, 'checkedAt': '2026-09-17'}
    basis = {'design': 'Explicit text/ineligible design declaration' if text_design else 'Explicit old-work public-domain declaration with pre-1931 publication or expired-US declaration',
             'reproduction': license_name, 'origin': plain(origin), 'fileSha1': info.get('sha1'), 'commons': {k: result[k] for k in ['evidenceFile', 'evidenceSha256']}, 'work': candidate['workEvidence'], 'claimId': candidate.get('claimId')}
    return (cover, basis), 'selected'


def main():
    candidates = json.loads((OUT / 'candidates.json').read_text())
    index = json.loads((OUT / 'commons-index.json').read_text())
    books = json.loads((ROOT / 'docs/research/historical-books-20260916/books.json').read_text())
    chosen, decisions = {}, []
    for candidate in candidates:
        selected, reason = classify(candidate, index.get(candidate['file'], {}))
        decision = {'bookId': candidate['bookId'], 'file': candidate['file'], 'decision': reason}
        if selected:
            cover, basis = selected
            decision['basis'] = basis
            if candidate['bookId'] not in chosen:
                chosen[candidate['bookId']] = cover
            else:
                decision['decision'] = 'eligible-alternative-not-used'
        decisions.append(decision)
    manifest = sorted(chosen.values(), key=lambda row: row['bookId'])
    (OUT / 'cover-decisions.json').write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'selected-covers.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'apps/server/internal/books/cover-selection.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    audit = json.loads((OUT / 'book-audit.json').read_text())
    for row in audit:
        row['status'] = 'sourced-edition-image' if row['bookId'] in chosen else 'original-artline-text-cover'
        row['reproductionSelected'] = row['bookId'] in chosen
    (OUT / 'book-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    summary = {'books': len(books), 'selectedReproductions': len(chosen), 'originalTextCovers': len(books) - len(chosen), 'decisions': dict(collections.Counter(d['decision'] for d in decisions)), 'licenses': dict(collections.Counter(c['license'] for c in manifest))}
    (OUT / 'selection-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
