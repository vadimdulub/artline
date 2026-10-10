"""Verify native Chicago objects and exact CC0 image resources before ingestion.

Factual metadata can qualify without an image. This module neither writes the
catalogue nor downloads images. Source artist IDs must come from a separately
captured name/alias and life-date match to the existing painter authority.
"""
import re
import unicodedata

CC0 = 'https://creativecommons.org/publicdomain/zero/1.0/'
SCHEME = 'european-chicago-art-institute-of-chicago-object'
SLUG = 'art-institute-of-chicago'


def norm(value):
    text = ''.join(c for c in unicodedata.normalize('NFKD', str(value or '').casefold())
                   if not unicodedata.combining(c))
    return ' '.join(re.findall(r'[^\W_]+', text))


def same_date_wording(left, right):
    """Compare date text while expanding only explicit abbreviated end years."""
    def expand(value):
        def end_year(match):
            first=int(match[1]); modulus=10**len(match[2])
            last=first//modulus*modulus+int(match[2])
            if last<first:last+=modulus
            return str(first)+'–'+str(last)
        return norm(re.sub(r'\b(\d{4})\s*[–—/-]\s*(\d{1,2})\b(?!\d)', end_year, str(value or '')))
    return expand(left)==expand(right)


def verify_artist(artist, source):
    names = {norm(n) for n in [artist['display_name'], *artist.get('aliases', [])]}
    source_names = {norm(n) for n in [source['title'], *(source.get('alt_titles') or [])]}
    if source.get('is_artist') is not True or not names.intersection(source_names):
        raise ValueError('Native artist name or alias is not independently matched')
    years = [(artist.get(k), source.get(s)) for k, s in
             [('birth_year', 'birth_date'), ('death_year', 'death_date')]]
    if not any(isinstance(a, int) and a == b for a, b in years):
        raise ValueError('Artist match lacks a corroborating life date')
    if any(isinstance(a, int) and isinstance(b, int) and abs(a-b) > 2 for a,b in years):
        raise ValueError('Artist life dates conflict')
    if not artist.get('qid'):
        raise ValueError('Existing artist authority is absent')


def metadata(o, artist, source_artist):
    verify_artist(artist, source_artist)
    if not isinstance(o.get('id'), int) or not str(o.get('title') or '').strip():
        raise ValueError('Native object ID or title is missing')
    preferred = [p for p in o.get('artist_pivots', []) if p.get('is_preferred') is True]
    if (len(preferred) != 1 or preferred[0].get('artist_id') != source_artist['id']
            or preferred[0].get('role_title') != 'Artist'
            or o.get('artist_id') != source_artist['id']):
        raise ValueError('Unique unqualified primary artist is not established')
    if any(p.get('role_title') not in ('Artist', 'Printer', 'Publisher')
           for p in o.get('artist_pivots', [])):
        raise ValueError('Additional source creator roles need review')
    if sum(p.get('role_title') == 'Artist' for p in o['artist_pivots']) != 1:
        raise ValueError('Multiple source artists need attribution review')
    display = o.get('artist_display') or ''
    if re.search(r'\b(after|attributed|workshop|studio|circle|follower|school|copy|formerly|possibly|manner|style|imitator)\b', display, re.I):
        raise ValueError('Qualified source attribution requires editorial review')
    if re.search(r'\b(engraved|etched|lithographed|drawn) by\b', display, re.I):
        raise ValueError('Additional visual creator in source display needs role review')
    # Object captions sometimes use an explicit alias from the very same
    # native person record. Accept that complete leading name, while keeping
    # the independently matched person ID, life dates and role checks above.
    normalized_display = norm(display)
    displayed_alias = any(name and (normalized_display == name or normalized_display.startswith(name+' '))
                          for name in (norm(n) for n in source_artist.get('alt_titles') or []))
    if norm(source_artist['title']) not in normalized_display and not displayed_alias:
        raise ValueError('Object artist display differs from native artist identity')
    typ = {'Painting':'painting', 'Drawing and Watercolor':'drawing', 'Print':'print'}.get(o.get('artwork_type_title'))
    if not typ:
        raise ValueError('Object classification is outside this selected pass')
    lo, hi = o.get('date_start'), o.get('date_end')
    date = o.get('date_display') or ''
    if (type(lo) is not int or type(hi) is not int or not 1000 <= lo <= hi <= 1970
            or not re.search(r'\d{3,4}', date)
            or re.search(r'\b(undated|unknown|before|after|possibly|or later|or earlier|n\.d\.)\b|\?', date, re.I)):
        raise ValueError('Source creation interval is incomplete, open-ended or outside scope')
    birth, death = source_artist.get('birth_date'), source_artist.get('death_date')
    # A few native date_end fields omit an explicitly written abbreviated end
    # year (e.g. date_display=1916–17, date_end=1916). Preserve the museum's
    # textual interval as well as its numeric uncertainty; never drop that end.
    for span in re.finditer(r'\b(\d{4})\s*[–—/-]\s*(\d{1,2})\b(?!\d)', date):
        first=int(span[1]); modulus=10**len(span[2])
        last=first//modulus*modulus+int(span[2])
        if last<first:last+=modulus
        lo,hi=min(lo,first),max(hi,last)
    if not 1000<=lo<=hi<=1970:
        raise ValueError('Explicit textual creation range is outside scope')
    if birth and death and (lo,hi) in ((birth,death),(birth+15,death)):
        raise ValueError('Source interval resembles a lifespan or default activity range')
    if re.search(r'\b(later|posthumous|reprint\w*|reissue\w*|restrike\w*)\b', date, re.I):
        raise ValueError('Later physical impression requires separate date review')
    if any(not lo<=int(y)<=hi for y in re.findall(r'\b(\d{4})\b',date)):
        raise ValueError('Additional creation or publication date lies outside the normalized interval')
    if (birth and lo < birth) or (death and hi > death+2):
        raise ValueError('Creation or later impression dates require physical-object review')
    accession = o.get('main_reference_number') or ''
    credit = o.get('credit_line') or ''
    if o.get('fiscal_year_deaccession') is not None:
        raise ValueError('Museum record indicates deaccession; current holding needs review')
    if (not re.fullmatch(r'\d{4}\.[\w.\-]+', accession)
            or not re.search(r'\b(gift|collections?|funds?|purchase[ds]?|bequest|endowments?|acquisition|exchange)\b', credit, re.I)
            or re.search(r'\b(loans?|lent|lenders?|private collections?|promised|sold|deaccession\w*|returned)\b', credit, re.I)):
        raise ValueError('Accession and collection credit do not establish an accepted museum holding')
    approx = bool(re.search(r'\b(?:c\.|ca\.)\s*\d|\b(circa|about|early|mid|late|probably)\b', date, re.I))
    precision = ('circa' if lo==hi else 'circa_range') if approx else ('exact' if lo==hi else 'range')
    return dict(title=o['title'], date_display=date, creation_year_start=lo,
                creation_year_end=hi, date_precision=precision, work_type=typ,
                accession_number=accession, medium_text=o.get('medium_display'),
                dimensions_text=o.get('dimensions'))


def image(o, resource):
    """CC0 must be on the exact image, not merely on the metadata response."""
    if o.get('is_public_domain') is not True or o.get('copyright_notice'):
        raise ValueError('Object has no clear public-domain image designation')
    iid = o.get('image_id')
    if not isinstance(iid,str) or not re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',iid):
        raise ValueError('Primary image ID is absent or malformed')
    if (resource.get('id') != iid or resource.get('type') != 'image'
            or resource.get('credit_line') != 'CC0 Public Domain Designation'
            or resource.get('iiif_url') != '/'+iid
            or resource.get('artwork_ids') != [o['id']]):
        raise ValueError('Exact image CC0 rights or unique object association are absent')
    if not all(type(resource.get(k)) is int and resource[k]>0 for k in ('width','height')):
        raise ValueError('Image dimensions are absent')
    return 'https://www.artic.edu/iiif/2/'+iid+'/full/843,/0/default.jpg'
