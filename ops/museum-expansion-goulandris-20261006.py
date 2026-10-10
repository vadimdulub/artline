#!/usr/bin/env python3
"""Bounded Goulandris collection metadata research; no image requests."""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import re
from pathlib import Path
from urllib.parse import parse_qs,urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m;n=a.n
RUN=n.RUN/'goulandris'
SITE='https://goulandris.gr'
SLUG='basil-elise-goulandris-athens'
n.SITES['goulandris']=SITE
captured_body=a.captured_body
clean=a.clean
title_collisions=a.title_collisions
VALIDATED_EDITORIAL={}

LAUTREC_1948={
 'the-jockey','amazon-and-carriage','elsa-the-viennese','the-passenger','white-and-black','sleep',
 'miss-ida-heath','napoleon','cecy-loftus','miss-may-belfort','the-box-with-the-gilded-mask','study-of-a-woman',
}
PRINT_CREATION={
 **{'henri-de-toulouse-lautrec-'+key:('Printed by Mourlot Frères, Paris, and André Thiry, Brittany, published by Librairie Gründ, Paris, 1948','1948') for key in LAUTREC_1948},
 'braque-georges-thistle':('Printed by Mourlot Frères, Paris, published by Adrien Maeght, Paris, 1955','1955'),
 'picasso-pablo-profile-of-woman-jacqueline':('Printed by Schaub, published by Galerie Beyeler, Basel, 1970','1970'),
 'picasso-pablo-jacqueline-with-hair-loose':('Printed by Fernand Mourlot, Paris, published by Galerie Louise Leiris, Paris, 1958-1959','1958-1959'),
 'picasso-pablo-painter-and-model-in-an-armchair':('Printed in approximately five impressions by Hidalgo Arnéra, Vallauris, circa 1963-1964','circa 1963-1964'),
 **{'matisse-henri-'+key:('Original edition, printed by Edmond Vairel and Draeger Frères, Paris, published by Tériade, Paris, 1947','1947') for key in ['the-nightmare-of-the-white-elephant-jazz','the-cow-boy-jazz']},
}

# These are identifiable, dated works with explicit materials but no defensible
# mapping to one existing type. Keep the records in review with an unknown type.
UNKNOWN_TYPES={
 'samaras-lucas-untitled':'Acrylic on plaster, fabric, canvas and feathers laid down on panel',
 'chagall-marc-untitled-for-elise-and-basil':'Mixed media on paper',
 'christo-packed-coast-project-for-australia-near-sydney':'Pencil, crayon, twine and polyethylene on paper laid down on board',
}


def source_id(url):
    p=urlparse(url or '')
    match=re.fullmatch(r'/(?:en|el)/artwork/([a-z0-9.-]+)/?',p.path)
    return match[1] if p.hostname=='goulandris.gr' and match else None


def creation_date(raw):
    raw=clean(raw)
    direct=a.creation_date(re.sub(r'^[Cc]irca\s+','c. ',raw))
    if direct:return direct
    either=re.fullmatch(r'(\d{4}) or (\d{4})',raw)
    if either:
        first,last=map(int,either.groups())
        return (first,last,'range') if 100<=first<=last<=1970 and last-first==1 else None
    month=r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
    dated=re.fullmatch(r'(?:\d{1,2} )?'+month+r'(?:[-–]'+month+r')? (\d{4})',raw)
    if dated:
        return n.creation_date(dated[1])
    decade=re.fullmatch(r'(?:Early |Late |Mid-)?(\d{3})0s',raw)
    if decade:
        first=int(decade[1])*10
        # Retain the whole stated decade, never invent an early/late boundary.
        return (first,first+9,'range') if 100<=first<=1960 else None
    return None


def index_rows(raw,url):
    p=urlparse(url);q=parse_qs(p.query)
    assert p.hostname=='goulandris.gr' and p.path=='/en/collection/browse-request'
    assert q.get('type') in [['8'],['35'],['41']] and q.get('creation-to')==['1970'] and q.get('requestLocale')==['en-US']
    soup=BeautifulSoup(raw,'html.parser');offset=int(soup.select_one('.artwork-list__offset').get_text())
    assert offset==int(q['offset'][0]) and offset%6==0
    rows=[]
    for item in soup.select('.collection-browser__grid-item'):
        link=item.select_one('a[href]');title=item.select_one('.collection-browser__artwork-title');creator=item.select_one('.collection-browser__artwork-artist')
        assert link and title and creator and source_id(link['href'])
        rows.append(dict(source_id=source_id(link['href']),url=link['href'],title_and_date=clean(title.get_text(' ',strip=True)),creator=clean(creator.get_text(' ',strip=True)),type=q['type'][0]))
    assert 0<len(rows)<=6 and len({r['source_id'] for r in rows})==len(rows)
    return rows,int(soup.select_one('.artwork-list__total').get_text())


def fields(raw):
    soup=BeautifulSoup(raw,'html.parser')
    def one(sel):
        nodes=soup.select(sel)
        return clean(nodes[0].get_text(' ',strip=True)) if len(nodes)==1 else None
    values={};repeated={}
    for item in soup.select('.artwork-id__item'):
        label=item.select_one('.artwork-id__label');value=item.select_one('.artwork-id__value')
        if not label or not value:continue
        k=clean(label.get_text(' ',strip=True));v=clean(value.get_text(' ',strip=True))
        if k in values:repeated.setdefault(k,[values[k]]).append(v)
        else:values[k]=v
    canon=soup.select('link[rel="canonical"]');media=soup.select('.artwork__media')
    return dict(creator=one('.artwork__artist'),title=one('.artwork__title'),translated_title=one('.artwork__original-title'),date=one('.artwork__date'),
        medium=clean(media[0].get_text(' ',strip=True)) if media else None,
        medium_notes=[clean(v.get_text(' ',strip=True)) for v in media[1:]],
        medium_notes_labelled=all(v.select_one('li') is not None for v in media[1:]),
        dimensions=one('.artwork__dimensions'),donation=one('.artwork__donation'),
        fields=values,repeated=repeated,canonical=canon[0].get('href') if len(canon)==1 else None,
        narratives=[clean(v.get_text(' ',strip=True)) for v in soup.select('.artwork__audio-transcript')],
        rights=[clean(v.get_text(' ',strip=True)) for v in soup.select('[class*=copyright]')])


def object_kind(medium,types):
    text=(medium or '').lower()
    if re.search(r'\b(?:album|slipcase|book|plaster|feathers|construction|assemblage|cut out|cut-out|collage)\b',text):return None
    if re.search(r'\b(?:lithograph|lithography|etching|drypoint|aquatint|woodcut|linocut|screenprint|screen print|engraving|pochoir)\b',text):
        return 'print' if {'8','35','41'}&set(types) else None
    if '8' in types and re.search(r'\b(?:oil|acrylic|tempera)\b',text):return 'painting'
    if '8' in types and text in ['Mixed media on canvas'.lower(),'Mixed media on paper laid down on canvas'.lower(),'Enamel on steel'.lower()]:return 'painting'
    if '35' in types:
        if re.search(r'\b(?:watercolou?r|gouache|oil|tempera)\b',text):return 'painting'
        if re.search(r'\b(?:pencil|charcoal|ink|pen|crayon|pastel|chalk|graphite)\b',text):return 'drawing'
    return None


def facts(parsed,index,types):
    if parsed['canonical']!=index['url']:return None,'native_canonical_identity_conflict'
    bare=re.sub(r'\s*\(\d{4}\s*[-–]\s*(?:\d{4})?\)\s*$','',parsed['creator'] or '').strip()
    if index['source_id']=='christo-packed-coast-project-for-australia-near-sydney':
        if parsed['creator']!='Christo (1935 - 2020) and Jeanne-Claude (1935 - 2009)' or index['creator']!='Christo , Jeanne-Claude':
            return None,'native_creator_identity_requires_review'
        bare='Christo and Jeanne-Claude'
    elif bare!=index['creator']:return None,'native_creator_identity_requires_review'
    title=parsed['translated_title'] or parsed['title'];date=parsed['date']
    if not title or not date:return None,'native_title_or_creation_missing'
    if index['title_and_date']!=title+', '+date:return None,'native_title_or_date_conflict'
    dates=creation_date(date)
    if not dates:return None,'creation_date_requires_review'
    kind=object_kind(parsed['medium'],types)
    if index['source_id'] in UNKNOWN_TYPES and parsed['medium']==UNKNOWN_TYPES[index['source_id']]:kind='unknown'
    if not kind:return None,'physical_object_type_requires_review'
    if not parsed['medium_notes_labelled']:return None,'unlabelled_multiple_medium_fields'
    if kind=='print' and any(int(y)>1970 for note in parsed['medium_notes'] for y in re.findall(r'\b\d{4}\b',note)):
        return None,'later_printing_or_edition_requires_review'
    phase=''
    if index['source_id'] in PRINT_CREATION:
        note,physical_date=PRINT_CREATION[index['source_id']]
        if kind!='print' or note not in parsed['medium_notes']:return None,'reviewed_print_edition_statement_missing'
        if index['source_id']=='picasso-pablo-profile-of-woman-jacqueline' and '1er Avril 1970' not in parsed['fields'].get('Signatures and Inscriptions',''):
            return None,'dated_intervention_evidence_missing'
        dates=creation_date(physical_date);assert dates
        phase=' The physical print uses its explicit printing/edition date '+physical_date+'; the source header '+date+' remains in evidence for the design or earlier production phase. Edition statement: '+note+'.'
        date=physical_date
    if any(k in parsed['repeated'] for k in ['Signatures and Inscriptions','Current location','Inventory Number','Accession Number']):return None,'repeated_object_fields_require_review'
    if re.search(r'\b(?:album|suite|portfolio|book|frontispiece|triptych|diptych|studies|verso|recto)\b',title,re.I):return None,'compound_or_version_scope_requires_review'
    if re.search(r'\b(?:loan|lent|private collection|returned|restitut|promised)\b',(parsed['donation'] or '')+' '+parsed['fields'].get('Current location',''),re.I):return None,'collection_identity_requires_review'
    return dict(title=title,creator_label=bare,first=dates[0],last=dates[1],date_precision=dates[2],date_display=date,
        work_type=kind,medium=parsed['medium'],dimensions=parsed['dimensions'] or None,accession=None,source_url=index['url'],
        holding_basis='The official Foundation collection catalogue identifies this work by native object URL, creator, original/translated title, creation statement and physical medium. The linked collection introduction identifies the Athens museum as the home of this collection. This records collection association, not legal ownership or present physical display. Native donation: '+(parsed['donation'] or 'not stated')+'. No accession is given in the inspected object fields; Tour Guide Code is not an inventory number.'+phase),None


def existing_keys(db,iid):
    rows=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
      SELECT a.id::text,a.title,a.alternate_title FROM selected s JOIN artworks a ON a.id=s.id''',(iid,iid)).fetchall()
    urls={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%goulandris.gr/%'")}
    urls.update(r['canonical_url'] for r in db.execute("SELECT canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url LIKE '%goulandris.gr/%'"))
    return {source_id(u) for u in urls}-{None},{m.norm(r[k]) for r in rows for k in ['title','alternate_title'] if r[k]}


def title_keys(record):
    p=record['raw_source_record']['native_fields']
    return {m.norm(v) for v in [record['facts']['title'],p['title'],p['translated_title']] if v}


def title_collision_rows(db,records):
    variants=[dict(facts=dict(title=value)) for r in records for value in [r['facts']['title'],r['raw_source_record']['native_fields']['title']] if value]
    ids=[r['id'] for r in title_collisions(db,variants)]
    if not ids:return []
    return db.execute('''SELECT a.id::text,a.title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,
      a.work_type,a.medium_text,a.dimensions_text,a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,
      ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
      ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls
      FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY id''',(ids,)).fetchall()


def matching_title_rows(rows,record):
    keys=title_keys(record)
    return [r for r in rows if keys&{m.norm(r[k]) for k in ['title','alternate_title'] if r[k]}]


def check_title_identities(db,records):
    current=title_collision_rows(db,records)
    for record in records:
        review=record['raw_source_record']['title_identity_review'];path=m.ROOT/review['evidence_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==review['evidence_sha256']
        previous=matching_title_rows(m.load(path)['rows'],record)
        assert [r['id'] for r in previous]==review['existing_ids']
        assert matching_title_rows(current,record)==previous,'New or changed exact-title identity requires review'


def validate_record(record,raw):
    original=record['raw_source_record'];index=original['index_record']
    assert record['museum']['slug']==SLUG and record['source_record_id']==index['source_id']
    types=[]
    for membership in original['index_memberships']:
        rows,_=index_rows(captured_body(membership['capture']),membership['capture']['receipt']['url'])
        row=membership['record'];assert row in rows
        assert {k:v for k,v in row.items() if k!='type'}=={k:v for k,v in index.items() if k!='type'}
        types.append(row['type'])
    assert sorted(types)==original['types']
    assert record['source_receipt']['url']==record['source_receipt']['final_url']==index['url']
    parsed=fields(raw);assert parsed==original['native_fields']
    intro=BeautifulSoup(captured_body(original['collection_introduction']),'html.parser').get_text(' ',strip=True)
    assert 'The primary objective of the new museum built in Athens is to house the collection' in intro
    result,reason=facts(parsed,index,types);assert not reason,reason
    ref=original['editorial_manifest'];path=m.ROOT/ref['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256']
    if ref['sha256'] not in VALIDATED_EDITORIAL:
        manifest=m.load(path)
        for evidence in manifest['evidence']:
            assert hashlib.sha256((m.ROOT/evidence['path']).read_bytes()).hexdigest()==evidence['sha256']
            if 'supplemental-primary-captures-' in evidence['path']:
                for item in m.load(m.ROOT/evidence['path'])['records']:
                    if 'capture' in item:captured_body(item['capture'])
        VALIDATED_EDITORIAL[ref['sha256']]={v['source_record_id']:v for v in manifest['decisions']}
    decision=VALIDATED_EDITORIAL[ref['sha256']][record['source_record_id']]
    assert original['editorial_review']==decision and decision['decision']=='approve_review_record'
    assert decision['facts']==result
    assert decision['exact_title_comparison_ids']==original['title_identity_review']['existing_ids']
    return result


def research(pass_id='001'):
    assert re.fullmatch(r'\d{3}',pass_id)
    dest=RUN/('goulandris-'+pass_id+'-research.json.gz');assert not dest.exists()
    baseline=m.load(RUN/'goulandris-001-before.json');museum=baseline['museum']
    intro=m.load(RUN/'discovery-002.json')['capture'];groups={};indexes=[]
    for path in sorted(RUN.glob('*index-*.json')):
        data=m.load(path);cap=data['capture'];rows,total=index_rows(captured_body(cap),cap['receipt']['url']);indexes.append(dict(path=str(path.relative_to(m.ROOT)),rows=len(rows),total_reported=total))
        for row in rows:groups.setdefault(row['source_id'],[]).append(dict(record=row,capture=cap))
    assert len(groups)<=180
    with m.connect() as db:known,titles=existing_keys(db,museum['id'])
    def get(item):
        oid,members=item;index=members[0]['record'];types=sorted(r['record']['type'] for r in members)
        if oid in known:return 'held',dict(index=index,reason='existing_native_identity')
        try:
            raw,cap=n.capture('goulandris',index['url']);parsed=fields(raw);f,reason=facts(parsed,index,types)
        except (a.i.requests.RequestException,AssertionError) as exc:
            return 'held',dict(index=index,reason='native_source_failure',error=str(exc)[:250])
        if not reason and any(m.norm(v) in titles for v in [parsed['title'],parsed['translated_title']] if v):reason='existing_scoped_title'
        if reason:return 'held',dict(index=index,reason=reason,parsed=parsed,capture=cap)
        return 'record',dict(source_record_id=oid,museum=museum,facts=f,source_receipt=cap['receipt'],body_path=cap['body_path'],
            raw_source_record=dict(index_record=index,index_memberships=members,types=types,native_fields=parsed,collection_introduction=intro))
    records=[];held=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for num,(state,row) in enumerate(pool.map(get,groups.items()),1):
            (records if state=='record' else held).append(row)
            if num%10==0:
                print('Goulandris examined',num,'candidates',len(records),'held',len(held),flush=True)
                m.save(RUN/'progress'/f'research-{pass_id}-{num:03d}.json.gz',dict(records=records,held=held))
    with m.connect() as db:collisions=title_collisions(db,records)
    m.save(dest,dict(at=m.now(),museum=museum,before=baseline['before'],records=records,held=held,indexes=indexes,distinct_index_identities=len(groups),title_collisions=collisions,
        policy='Selected metadata from at most 180 distinct pre-1971 painting/works-on-paper/print search identities. Overlapping categories deduplicated by native URL. Individual narrative and version review still required; no import approval from parser output. No media requested.'))
    print('Goulandris retained',len(records),'candidates',len(held),'holds',len(groups),'distinct source identities',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['research']);p.add_argument('--pass-id',default='001');args=p.parse_args();research(args.pass_id)
