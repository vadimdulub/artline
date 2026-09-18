"""Compare captured museum object identities without conflating query-string IDs."""
from collections import defaultdict
from urllib.parse import parse_qsl, unquote, urlsplit


def canonical_url(url):
    parts = urlsplit(url or '')
    return (
        (parts.hostname or '').lower().removeprefix('www.'),
        unquote(parts.path).rstrip('/'),
        tuple(sorted(parse_qsl(parts.query, keep_blank_values=True))),
    )


def belongs_to(url, domain):
    host = (urlsplit(url or '').hostname or '').lower()
    return host == domain or host.endswith('.' + domain)


def find_conflicts(plan, existing, domains):
    by_url = defaultdict(list)
    by_id = defaultdict(list)
    for item in existing:
        if item.get('url'):
            by_url[canonical_url(item['url'])].append(item)
        for domain in domains:
            if item.get('id') and belongs_to(item.get('url'), domain):
                by_id[(domain, item['id'])].append(item)
    conflicts = []
    for row in plan:
        evidence = row['evidence']
        url, identifier = evidence['object_url'], evidence['object_id']
        candidates = list(by_url.get(canonical_url(url), [])) if url else []
        for domain in domains:
            if identifier and belongs_to(url, domain):
                candidates.extend(by_id.get((domain, identifier), []))
        seen = set()
        for item in candidates:
            key = (item['slug'], item['scheme'], item['id'])
            if key in seen or row['slug'] == item['slug']:
                continue
            seen.add(key)
            conflicts.append({'rid': row['rid'], 'object_id': identifier, 'existing': item})
    return conflicts
