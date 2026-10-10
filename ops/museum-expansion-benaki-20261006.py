#!/usr/bin/env python3
"""Validate individually reviewed Benaki descriptions; preserve Greek evidence."""
import gzip
import hashlib
import html
import importlib.util
import re
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('museum-expansion-native-20261006.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m=n.m
RUN=n.RUN/'benaki'
BASE='https://www.benaki.org'
SLUG='wikimedia-museum-q816669'


def source_id(url):
    p=urlparse(url);q=parse_qs(p.query)
    if p.hostname not in ['www.benaki.org','benaki.org'] or q.get('option')!=['com_collectionitems'] or q.get('view')!=['collectionitem']:return None
    values=q.get('id',[])
    return values[0] if len(values)==1 and values[0].isdigit() else None


def inventory_keys(raw):
    # Native general-register prefix may appear as Greek ΓΕ, transliterated GE,
    # or be omitted in older records. Preserve departmental/alphabetic suffixes.
    return {re.sub(r'^(?:γε|ge)[\s_\-]*','',m.norm(raw)).replace(' ','')} if raw else set()


def read_capture(cap):
    raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes())
    assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256']
    return raw


def fields(raw):
    s=n.BeautifulSoup(raw,'html.parser');main=s.select_one('.ben-main-body')
    assert main and main.h1 and len(main.select('.bena-body'))==1
    aliases=sorted({source_id(urljoin(BASE,a['href'])) for a in s.select('a[href]') if a.get_text(' ',strip=True).endswith('English') and source_id(urljoin(BASE,a['href']))})
    return dict(title=main.h1.get_text(' ',strip=True),description=main.select_one('.bena-body').get_text(' ',strip=True),language_variant_ids=aliases,
        page_title=s.title.get_text(' ',strip=True),content_id=main.select_one('input[name=content_item_id]')['value'],
        links=[dict(title=a.get_text(' ',strip=True),url=urljoin(BASE,a['href'])) for a in main.select('a.ben-button[href]')])


def reviewed_date(literal):
    # This function receives an individually selected creation statement, never
    # an entire description containing artist lifespans or donation dates.
    value=literal.replace('αιώνα.','αι.').replace('αιώνα','αι.')
    exact=re.fullmatch(r'(?:Νοέμβριος )?(\d{4})',value)
    if exact and 1000<=int(exact[1])<=1970:return int(exact[1]),int(exact[1]),'exact'
    century=re.fullmatch(r'(\d{1,2})(?:ος|ου) αι\.',value)
    if century and 1<=int(century[1])<=19:
        c=int(century[1]);return (c-1)*100+1,c*100,'century'
    half=re.fullmatch(r'(Πρώτο|Δεύτερο) μισό (?:του )?(\d{1,2})ου αι\.',value,re.I)
    if half and 1<=int(half[2])<=19:
        c=int(half[2]);second=half[1].casefold()=='δεύτερο'
        return (c-1)*100+(51 if second else 1),(c-1)*100+(100 if second else 50),'range'
    half_letter=re.fullmatch(r"([ΑAΒB])['΄’] μισό (\d{1,2})ου αι\.",value,re.I)
    if half_letter and 1<=int(half_letter[2])<=19:
        c=int(half_letter[2]);second=half_letter[1].casefold() in ['β','b']
        return (c-1)*100+(51 if second else 1),(c-1)*100+(100 if second else 50),'range'
    span=re.fullmatch(r'(\d{1,2})ος-(\d{1,2})ος αι\.',value)
    if span and 1<=int(span[1])<=int(span[2])<=19:return (int(span[1])-1)*100+1,int(span[2])*100,'range'
    # Qualitative subdivisions supply a known enclosing century. Keep that
    # entire interval, never an invented numerical boundary for early/late.
    qualified=re.fullmatch(r'(?:[ΑA]ρχές|[ΤT]έλη|Μέσα|μέσων του) (\d{1,2})ου αι\.',value,re.I)
    if qualified and 1<=int(qualified[1])<=19:
        c=int(qualified[1]);return (c-1)*100+1,c*100,'century'
    span=re.fullmatch(r'(?:[ΤT]έλη|Τέλος|[ΑA]ρχές) (\d{1,2})ου\s*-\s*(?:αρχές |τέλη )?(\d{1,2})(?:ου|ος) αι\.',value,re.I)
    if span and 1<=int(span[1])<=int(span[2])<=19:return (int(span[1])-1)*100+1,int(span[2])*100,'range'
    quarter=re.fullmatch(r'Δεύτερο τέταρτο (\d{1,2})ου αι\.',value,re.I)
    if quarter and 1<=int(quarter[1])<=19:
        start=(int(quarter[1])-1)*100;return start+26,start+50,'range'
    span=re.fullmatch(r"Τέλη (\d{1,2})ου\s*-\s*α' τέταρτο (\d{1,2})ου αι\.",value,re.I)
    if span and 1<=int(span[1])<=int(span[2])<=19:return (int(span[1])-1)*100+1,(int(span[2])-1)*100+25,'range'
    numeric=re.fullmatch(r'(\d{4})[-–](\d{4})',value)
    if numeric and 1000<=int(numeric[1])<=int(numeric[2])<=1970:return int(numeric[1]),int(numeric[2]),'range'
    circa=re.fullmatch(r'Γύρω στ[αοoa] (\d{4})',value,re.I)
    if circa and 1000<=int(circa[1])<=1900:
        # Store the publisher's approximate central year as circa, not as a
        # fabricated finite uncertainty interval or an exact creation date.
        return int(circa[1]),int(circa[1]),'circa'
    return None


def facts(parsed,review,url):
    body=parsed['description']
    assert parsed['title'] and html.unescape(parsed['page_title'])==parsed['title']+' - Μουσείο Μπενάκη'
    assert source_id(url)==parsed['content_id']
    assert review['creation_statement'] in body
    date=reviewed_date(review['creation_statement']);assert date,'Unreviewed creation statement'
    for key in ['creator_statement','dimensions_statement','medium_statement']:
        assert review.get(key) is None or review[key] in body,'Changed source excerpt: '+key
    assert '('+review['accession']+')' in body
    assert review['work_type']=='painting' and review.get('object_form') in ['icon',None]
    # Metal covers, fragments and multiple production phases remain held.
    # A separately inventoried panel or one whole two-sided icon can be
    # included after explicit object-scope review, as a single physical work.
    assert not re.search(r'επένδυση|ασημένι|αργυρ|φύλλο τριπτύχου|[ΤT]ρίπτυχο',body,re.I)
    if re.search('μεταγενέστερ',body,re.I):
        assert review.get('production_phase_review') and ('επιγραφή' in body or 'πλαστή υπογραφή' in body)
    if re.search('τμήμα',body,re.I):
        assert review.get('support_scope_review')=='painting_on_reused_chest_panel_not_fragment_of_painting' and 'πάνω σε τμήμα παλαιάς κασέλας' in body
    scope=review.get('object_scope_review')
    if re.search(r'από δωδεκάορτο',body,re.I):
        assert scope and scope['kind']=='single_templon_panel' and scope['note'] and review['dimensions_statement']
    if re.search(r'Αμφιπρόσωπη',body,re.I):
        assert scope and scope['kind']=='single_double_sided_icon' and scope['note'] and review['dimensions_statement']
    if re.match(r'(?:[ΑA]ρχές|[ΤT]έλη|Τέλος|Μέσα|μέσων του) ',review['creation_statement'],re.I):
        assert review.get('date_interval_basis')=='enclosing_source_century_without_invented_subdivision'
    if date[2]=='circa':assert review.get('date_interval_basis')=='source_circa_central_year_no_invented_uncertainty_interval'
    assert parsed['links']==[{'title':'ΜΟΥΣΕΙΟ ΕΛΛΗΝΙΚΟΥ ΠΟΛΙΤΙΣΜΟΥ','url':'https://www.benaki.org/index.php?option=com_buildings&view=building&id=1&lang=el'}]
    return dict(title=parsed['title'],creator_label=review.get('creator_statement'),first=date[0],last=date[1],date_precision=date[2],date_display=review['creation_statement'],work_type=review['work_type'],object_form=review.get('object_form'),medium=review.get('medium_statement'),dimensions=review.get('dimensions_statement'),accession=review['accession'],source_url=url,holding_basis='Official Benaki collection object linked from its Byzantine collection index, with native general-register inventory and Museum of Greek Culture collection association. Original Greek object description and attribution qualifications retained; unnamed creators and unspecified media remain unknown. This is collection evidence, not a current-display assertion.')


def validate_record(record,body):
    original=record['raw_source_record'];parsed=fields(body)
    assert parsed==original['native_fields'] and record['museum']['slug']==SLUG
    assert parsed['content_id']==record['source_record_id'] and source_id(record['source_receipt']['final_url'])==record['source_record_id']
    index=original['index'];index_body=read_capture(index['source']);s=n.BeautifulSoup(index_body,'html.parser')
    matches=[a for a in s.select('a.bena-horizonbox[href]') if source_id(urljoin(BASE,a['href']))==record['source_record_id']]
    assert len(matches)==1 and matches[0]['title']==parsed['title']
    assert parse_qs(urlparse(index['source']['receipt']['url']).query)['collectionId']==['5']
    review=original['review']
    if review.get('object_form')=='icon':
        icon=original['icon_index'];raw=read_capture(icon['source']);s=n.BeautifulSoup(raw,'html.parser')
        assert parse_qs(urlparse(icon['source']['receipt']['url']).query)['types[0]']==['27472']
        assert any(source_id(urljoin(BASE,a['href']))==record['source_record_id'] for a in s.select('a.bena-horizonbox[href]'))
        definition=read_capture(original['collection_capture']);s=n.BeautifulSoup(definition,'html.parser')
        assert s.select_one('[data-filter-type="type"][data-filter-id="27472"]')['data-filter-name']=='εικόνα'
    else:assert review['medium_statement']=='Ελαιογραφία σε ύφασμα'
    identity=original['identity_review'];assert identity['decision']=='new_distinct_work' and identity['note']
    for evidence in identity['comparison_evidence']:
        assert hashlib.sha256((m.ROOT/evidence['path']).read_bytes()).hexdigest()==evidence['sha256']
    return facts(parsed,review,record['source_receipt']['url'])


def existing_keys(db,iid):
    urls={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE 'https://%%benaki.org/%%'")}
    urls.update(r['canonical_url'] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE 'https://%%benaki.org/%%'"))
    rows=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
      SELECT a.id::text,a.title,a.alternate_title,a.accession_number FROM artworks a JOIN selected s ON s.id=a.id''',(iid,iid)).fetchall()
    return {source_id(u) for u in urls}, {m.norm(r[k]) for r in rows for k in ['title','alternate_title'] if r[k]},set().union(*(inventory_keys(r['accession_number']) for r in rows))


def title_collision_rows(db,records):
    titles=sorted({m.norm(r['facts']['title']) for r in records})
    rows=db.execute('''SELECT id::text,title,normalized_title,accession_number,date_display,
      creation_year_start,creation_year_end,date_precision,work_type,current_institution_id::text,
      unlinked_creator_label,dimensions_text FROM artworks WHERE normalized_title=ANY(%s) ORDER BY id''',(titles,)).fetchall()
    ids=[r['id'] for r in rows];native={key:set() for key in ids}
    if ids:
        for r in db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) AND source_url LIKE 'https://%%benaki.org/%%'",(ids,)):
            key=source_id(r['source_url'])
            if key:native[r['entity_id']].add(key)
    for row in rows:row['native_source_ids']=sorted(native[row['id']])
    return rows


def check_title_identities(db,records):
    rows=title_collision_rows(db,records)
    for record in records:
        f=record['facts'];actual=[r for r in rows if r['normalized_title']==m.norm(f['title'])]
        cleared=record['raw_source_record']['identity_review'].get('cleared_title_collisions',[])
        assert actual==cleared,'Unreviewed or changed Benaki title collision'
        aliases={record['source_record_id']}|set(record['raw_source_record']['native_fields']['language_variant_ids'])
        for row in actual:
            assert row['current_institution_id']==record['museum']['id'] and row['accession_number'] and row['native_source_ids']
            assert not inventory_keys(row['accession_number'])&inventory_keys(f['accession'])
            assert not aliases&set(row['native_source_ids'])
            assert (row['date_display'],row['dimensions_text'],row['unlinked_creator_label'])!=(f['date_display'],f['dimensions'],f['creator_label']),'Indistinguishable same-title work requires further review'
