"""Keep reviewed content immutable while checking an existing city label's spelling."""
import hashlib
import exhibitions_common as c

def expected_profiles(e):
    source=e/'profiles-reviewed.json'
    profiles=c.load(source)
    spelling=e/'verified-city-spellings.json'
    if not spelling.exists():
        return profiles
    receipt=c.load(spelling)
    raw=source.read_bytes()
    assert receipt['reviewed_profiles_sha256']==hashlib.sha256(raw).hexdigest()
    assert receipt['read_only'] is True and receipt['no_data_changes'] is True
    by_slug={p['slug']:p for p in profiles}
    assert len({r['slug'] for r in receipt['spellings']})==len(receipt['spellings'])
    for row in receipt['spellings']:
        p=by_slug[row['slug']]
        assert p['city']==row['reviewed_city'] and p['country']==row['country']
        assert c.norm(p['city'])==c.norm(row['canonical_city'])
        p['city']=row['canonical_city']
    return profiles
