#!/usr/bin/env python3
"""Selected Sarian captions: trilingual source validation and read-only identity audit."""
import argparse
import difflib
import gzip
import hashlib
import importlib.util
import re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museum-expansion-20261006.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
RUN=m.RUN/'native/armenia';IID='e6814861-29d2-559b-b22d-e5df7596d475';SLUG='national-gallery-armenia'
NAMES=['Martiros Sarian','Martiros Saryan','Мартирос Сарьян','Մարտիրոս Սարյան']
MATERIAL_CONFLICTS={12:'Armenian/Russian canvas; English cardboard.',14:'Armenian/Russian canvas; English cardboard.',16:'Armenian/Russian canvas; English cardboard.',34:'Armenian watercolor; Russian/English Indian ink.'}
HOLDS={2:'Armenian and collection narrative identify panthers/leopards; Russian/English object headings say hyenas. Resolve title/version identity.',13:'Collection narrative dates Egyptian Masks 1913; all object headings say 1911. Resolve creation-date evidence.'}

def clean(value):return ' '.join(value.split())
def reference(path):return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def body(cap):
    raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes())
    assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256']
    return raw

def captions(raw):
    soup=BeautifulSoup(raw,'html.parser')
    titles=[clean(x.get_text(' ',strip=True)) for x in soup.select('span.category-options')]
    details=[clean(x.get_text(' ',strip=True)) for x in soup.select('span.more')]
    assert len(titles)==len(details)==3,'Exactly three language captions required'
    assert 'MARTIROS' in soup.get_text(' ',strip=True).upper() and 'SARIAN' in soup.get_text(' ',strip=True).upper()
    return titles,details

def fields(d,number):
    titles=[clean(x) for x in d['title_fields']];details=[clean(x) for x in d['detail_fields']]
    years=[re.findall(r'\b(?:18|19)\d{2}\b',t) for t in titles]
    assert all(len(y)==1 for y in years) and years[0]==years[1]==years[2]
    year=int(years[0][0]);assert year<=1970
    dims=[]
    for detail,holding in zip(details,['Հայաստանի ազգային պատկերասրահ','Армении, Ереван','National Gallery of Armenia, Yerevan']):
        assert holding in detail,'Missing explicit collection label'
        match=re.search(r'(\d+(?:[.,]\d+)?)\s*[xх]\s*(\d+(?:[.,]\d+)?)\s*(?:cm|см|սմ)',detail)
        assert match,'Missing object dimensions'
        dims.append(tuple(float(x.replace(',','.')) for x in match.groups()))
    assert dims[0]==dims[1]==dims[2],'Dimension conflict requires review'
    match=re.search(r'\d+(?:[.,]\d+)?\s*[xх]\s*\d+(?:[.,]\d+)?\s*cm',details[2])
    medium=details[2][:match.start()].strip(' .,')
    assert medium.lower() in ['oil on canvas','tempera on canvas','tempera on cardboard','tempera on paper','indian ink on paper','watercolor on paper','pencil on paper','gouache on paper','gouache and watercolor on paper']
    title=clean(re.sub(r'\b'+str(year)+r'\b','',titles[2])).strip(' .')
    kind='drawing' if medium.lower() in ['indian ink on paper','pencil on paper'] else 'painting'
    if number in MATERIAL_CONFLICTS:
        medium=None
        if number==34:kind='unknown'
    return dict(title=title,creator_label='Martiros Sarian',date_display=str(year),first=year,last=year,date_precision='exact',work_type=kind,medium=medium,dimensions=match[0],accession=None,source_url=d['entry']['url'],holding_basis='Martiros Sarian House-Museum identifies this individual original artwork in its National Gallery of Armenia collection section and in Armenian, Russian and English object captions. Source distinguishes the physical drawing/painting/design from later illustrations or stage productions. Collection holding only; no current-display claim.')

def validate_record(r,raw):
    d=r['raw_source_record']['object_capture'];number=r['raw_source_record']['queue_number']
    assert d==m.load(RUN/'sarian-object-captures-001'/f'{number:03}.json')
    assert captions(raw)==([clean(x) for x in d['title_fields']],[clean(x) for x in d['detail_fields']])
    assert d['capture']==dict(receipt=r['source_receipt'],body_path=r['body_path'])
    assert d['entry']['url']==r['source_receipt']['url']==r['source_receipt']['final_url']
    assert urlparse(d['entry']['url']).hostname=='www.sarian.am'
    assert r['source_record_id']==Path(urlparse(d['entry']['url']).path).stem
    assert r['museum']['id']==IID and number not in HOLDS
    assert r['raw_source_record']['material_discrepancy']==MATERIAL_CONFLICTS.get(number)
    return fields(d,number)

def research():
    queue=m.load(RUN/'sarian-object-queue-001.json');baseline=m.load(RUN/'armenia-001-before.json');records=[];held=[]
    assert len(queue['entries'])==41
    for number,entry in enumerate(queue['entries'],1):
        d=m.load(RUN/'sarian-object-captures-001'/f'{number:03}.json');assert d['entry']==entry
        raw=body(d['capture']);assert captions(raw)==([clean(x) for x in d['title_fields']],[clean(x) for x in d['detail_fields']])
        f=fields(d,number)
        if number in HOLDS:held.append(dict(queue_number=number,entry=entry,note=HOLDS[number],object_capture=d));continue
        r=dict(source_record_id=Path(urlparse(entry['url']).path).stem,museum=baseline['museum'],facts=f,source_receipt=d['capture']['receipt'],body_path=d['capture']['body_path'],raw_source_record=dict(object_capture=d,queue_number=number,material_discrepancy=MATERIAL_CONFLICTS.get(number),caption_policy='Use only object caption spans. Preserve all three languages. Generic print-store template help is unrelated. Conflicting material left unknown; original graphic/painting and date preserved. Source title spelling retained.'))
        assert validate_record(r,raw)==f;records.append(r)
    m.save(RUN/'sarian-caption-research-001.json.gz',dict(at=m.now(),records=records,held=held,index_capture=queue['index_capture']))
    print(len(records),'candidates;',len(held),'source holds')

def current_identity(db,records):
    keys=[m.norm(x) for x in NAMES]
    artists=db.execute('SELECT id::text,display_name,normalized_name,slug FROM artists WHERE normalized_name=ANY(%s) ORDER BY id',(keys,)).fetchall()
    aliases=db.execute('SELECT aa.artist_id::text,aa.alias,aa.normalized_alias,a.display_name FROM artist_aliases aa JOIN artists a ON a.id=aa.artist_id WHERE aa.normalized_alias=ANY(%s) ORDER BY aa.artist_id,aa.alias',(keys,)).fetchall()
    ids=sorted({x['id'] for x in artists}|{x['artist_id'] for x in aliases})
    cols='''a.id::text,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_display,a.accession_number,a.unlinked_creator_label,a.current_institution_id::text,a.work_type,a.medium_text,a.dimensions_text,
      ARRAY(SELECT ar.display_name FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id ORDER BY ar.display_name) creators,
      ARRAY(SELECT c.source_url FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id ORDER BY c.source_url) source_urls'''
    linked=db.execute('SELECT '+cols+' FROM (SELECT DISTINCT artwork_id FROM artwork_artists WHERE artist_id=ANY(%s::uuid[])) scoped JOIN artworks a ON a.id=scoped.artwork_id ORDER BY a.id',(ids,)).fetchall()
    unlinked=db.execute('SELECT '+cols+' FROM artworks a WHERE unlinked_creator_label ILIKE ANY(%s) ORDER BY a.id',(['%sarian%','%saryan%','%сарьян%','%սարյան%'],)).fetchall()
    titlekeys=sorted({m.norm(re.sub(r'\b(?:18|19)\d{2}\b','',v)) for r in records for v in r['raw_source_record']['object_capture']['title_fields']}|{m.norm(r['facts']['title']) for r in records})
    collisions=db.execute('SELECT '+cols+' FROM artworks a WHERE normalized_title=ANY(%s) OR lower(title)=ANY(%s) OR lower(alternate_title)=ANY(%s) ORDER BY a.id',(titlekeys,titlekeys,titlekeys)).fetchall()
    baseline=m.load(RUN/'armenia-001-before.json')
    museum_scope=db.execute('SELECT '+cols+' FROM artworks a WHERE id=ANY(%s::uuid[]) ORDER BY a.id',(baseline['scoped_ids'],)).fetchall()
    return dict(artists=artists,aliases=aliases,linked=linked,unlinked=unlinked,collisions=collisions,museum_scope=museum_scope)

def identity():
    records=m.load(RUN/'sarian-caption-research-001.json.gz')['records']
    with m.connect() as db:snapshot=current_identity(db,records)
    comparisons=[];pool={r['id']:r for k in ['linked','unlinked','collisions','museum_scope'] for r in snapshot[k]}
    for r in records:
        titles=r['raw_source_record']['object_capture']['title_fields']+[r['facts']['title']]
        keys=[m.norm(re.sub(r'\b(?:18|19)\d{2}\b','',t)) for t in titles]
        def score(v):return max(difflib.SequenceMatcher(None,k,m.norm(v[t])).ratio() for k in keys for t in ['title','alternate_title'] if v.get(t))
        comparisons.append(dict(queue_number=r['raw_source_record']['queue_number'],title=r['facts']['title'],date=r['facts']['first'],leads=[dict(v,title_similarity=score(v)) for v in sorted(pool.values(),key=score,reverse=True)[:8]]))
    m.save(RUN/'sarian-identity-001.json.gz',dict(at=m.now(),**snapshot))
    m.save(RUN/'sarian-comparison-001.json.gz',dict(at=m.now(),records=comparisons))
    print({k:len(v) for k,v in snapshot.items()})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['research','identity']);args=parser.parse_args()
    research() if args.command=='research' else identity()
