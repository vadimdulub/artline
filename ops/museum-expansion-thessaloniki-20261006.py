#!/usr/bin/env python3
"""Selected Museum of Byzantine Culture metadata; pinned source review, no media."""
import argparse
import hashlib
import importlib.util
import re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-agsa-20261006.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
m=a.m;n=a.n
RUN=n.RUN/'thessaloniki'
SITE='https://www.mbp.gr'
SLUG='museum-of-byzantine-culture-thessaloniki'
n.SITES['thessaloniki']=SITE
captured_body=a.captured_body
title_collisions=a.title_collisions

# Each entry was read in full. Sponsors, prototypes and excavated originals
# are not treated as the creators or creation dates of these physical objects.
REVIEW={
 'chalkografia-geniki-apopsi-tou-agiou-or':dict(inventory='ΒΧει 248',date='1767',first=1767,last=1767,creator=None,kind='print',type='Engraving',
   anchor='The engraver is not known.',note='Gabriel is explicitly the sponsor, not the engraver. May 1767 refers to this engraving. The 18th/19th-century discussion describes the general subject tradition.'),
 'chalkografia-geniki-apopsi-tou-orous-si':dict(inventory='ΒΧει 233',date='1804',first=1804,last=1804,creator=None,kind='print',type='Engraving',
   anchor='Engraving printed in Constantinople with the care and the expenses of Ilarion',note='Ilarion and the hieromonks financed the print; no engraver is named. The mid-16th-century date concerns the iconographic prototype, not this 1804 impression.'),
 'chalkografia-i-panagia-gerontissa':dict(inventory='ΒΧει 91',date='1869',first=1869,last=1869,creator='Ioannis Kaldis',kind='print',type='Engraving',
   anchor='is made by Ioannis Kaldis, an engraver on Mount Athos in 1869.',note='A paper engraving with tempera, distinct from its miraculous painted prototype at Pantokratoros Monastery. Narrative and Chronology agree on 1869.'),
 'parastasi-lychnariou-mesa-se-stefani-e':dict(inventory='ΝΕΤ 009',date='1950-1960',first=1950,last=1960,creator=None,kind='painting',type='Copy of a fresco',
   anchor='Copy of a fresco from a tomb.',note='This is the separately inventoried 1950–1960 watercolor copy on paper attached to canvas. The excavation site describes the original fresco. No individual creator is stated on this object page.'),
 'parastasi-me-poulia-kai-kanistro-ergo':dict(inventory='NET 004',date='1950-1960',first=1950,last=1960,creator='Christos Lefakis',kind='painting',type='Copy of a fresco',
   anchor='Copy of a fresco from a tomb found outside the western walls.',note='The heading names Lefakis. The 1950–1960 watercolor copy is one inventoried work, distinct from the ancient tomb fresco it records.'),
 'kalos-poimenas-ergo-tou-christou-lefak':dict(inventory='ΝΕΤ 001',date='1950-1960',first=1950,last=1960,creator='Christos Lefakis',kind='painting',type='Copy of a fresco',
   anchor='Copy of a fresco found in a tomb.',note='The heading names Lefakis. The 1950–1960 watercolor copy is distinct from the original tomb painting and from sculptural representations of the Good Shepherd.'),
 'eikona-me-ton-agio-dimitrio-ergo-tou-po':dict(inventory='ΝΕΤ 014',date='1935',first=1935,last=1935,creator='Polycletos Rengos',kind='painting',type='Icon',
   anchor='By hand of Polycletos N. Rengos, 1935.',note='Native Chronology and the reported signature agree. Preserve the literal native creator spelling without inventing an artist link; this egg-tempera wooden icon counts once.'),
}
HOLDS={
 'lithografia-i-ypodochi-tis-zonis-tis-theo':('native_title_and_date_conflict','Chronology 1871 conflicts with narrative 1798; the URL refers to the Virgin’s girdle while heading and narrative repeat Saint George. Resolve native object identity.'),
 'chalkografia-o-agios-georgios-kai-i-mon':('native_creation_date_conflict','Chronology 1833 conflicts with the statement that this engraving was made and printed in 1798. Plate versus impression is not explicitly resolved.'),
 'therinos-martyras-ergo-tou-christou-lef':('mosaic_replica_classification_review','The 1953 plaster, dye and glass mosaic replica is distinct from the fourth-century Rotunda original. Preserve its sculptural/mosaic classification for model review.'),
 'eikastiko-ergo-orario-ergo-tou-spyrou':('compound_object_scope_review','The single NET 041 record describes 22 paintings from an original set of 24. Individual panels lack their own inventories here; do not count it as 22 separately identified artworks.'),
 'eikastiko-ergo-the-end-ergo-tou-nikou-alexio':('post_1970_creation','This physical digital print is dated 2007; the eleventh-century mosaic prototype does not make it eligible.'),
}


def inventory_keys(value):
    # Greek and Latin register-prefix spellings identify the same local series.
    key=m.norm(value).replace(' ','').translate(str.maketrans({'β':'b','χ':'x','ε':'e','ι':'i','ν':'n','τ':'t'}))
    match=re.fullmatch(r'(bxei|bei|bt|net)0*(\d+)([a-zα-ω]?)',key)
    return {match[1]+str(int(match[2]))+match[3]} if match else a.inventory_keys(value)


def fields(raw):
    soup=BeautifulSoup(raw,'html.parser');values={}
    for node in soup.select('.text-aside-note'):
        h=node.select_one('h3');v=node.select_one('.toggle-content')
        if h and v:
            key=h.get_text(' ',strip=True);assert key not in values
            values[key]=v.get_text(' ',strip=True)
    titles=[v.get_text(' ',strip=True) for v in soup.select('h1') if v.get_text(' ',strip=True)]
    canonical=soup.select('link[rel="canonical"]');desc=soup.select('.single-item-text')
    return dict(fields=values,title=titles[0] if len(titles)==1 else None,
        canonical=canonical[0].get('href') if len(canonical)==1 else None,
        descriptions=[v.get_text(' ',strip=True) for v in desc])


def index_rows(raw):
    soup=BeautifulSoup(raw,'html.parser');rows=[]
    for link in soup.select('a[href]'):
        u=link['href']
        if u.startswith(SITE+'/en/exhibit/'):
            row=dict(source_id=urlparse(u).path.strip('/').split('/')[-1],title=link.get_text(' ',strip=True),url=u)
            if row not in rows:rows.append(row)
    return rows


def facts(parsed,index):
    oid=index['source_id'];review=REVIEW[oid];f=parsed['fields']
    assert parsed['canonical']==index['url']==SITE+'/en/exhibit/'+oid+'/'
    assert parsed['title']==index['title'] and f['Code']==review['inventory']
    assert f['Chronology']==review['date'] and f['Type']==review['type']
    assert len(parsed['descriptions'])==1 and review['anchor'] in parsed['descriptions'][0]
    if review['creator']=='Christos Lefakis':assert 'Christos Lefakis' in parsed['title']
    if review['creator']=='Polycletos Rengos':assert 'Polycletos Rengos' in parsed['title']
    assert f.get('Origin') and f.get('Material of Construction')
    result=dict(title=index['title'],creator_label=review['creator'],first=review['first'],last=review['last'],
        date_precision='exact' if review['first']==review['last'] else 'range',date_display=f['Chronology'],work_type=review['kind'],
        medium=f['Material of Construction'],dimensions=f.get('Dimensions'),accession=f['Code'],source_url=index['url'],
        cultural_context='Museum of Byzantine Culture: post-Byzantine religious prints and modern Greek paintings',
        holding_basis='Official museum collection index and object record identify this inventory. Native Origin: '+f['Origin']+'. '+review['note']+' Collection holding only; no current-display assertion.')
    if f['Type']=='Icon':result['object_form']='icon'
    return result


def existing_keys(db,iid):
    rows=db.execute('''WITH selected AS MATERIALIZED (SELECT id FROM artworks WHERE current_institution_id=%s
      UNION SELECT artwork_id FROM artwork_location_assertions WHERE institution_id=%s AND superseded_by IS NULL)
      SELECT a.id::text,a.title,a.alternate_title,a.accession_number FROM selected s JOIN artworks a ON a.id=s.id''',(iid,iid)).fetchall()
    urls={r['source_url'] for r in db.execute("SELECT DISTINCT source_url FROM citations WHERE entity_type='artwork' AND source_url LIKE '%mbp.gr/%'")}
    ext=db.execute("SELECT scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND (scheme ILIKE '%thessaloniki%' OR canonical_url LIKE '%mbp.gr/%')").fetchall()
    urls.update(r['canonical_url'] for r in ext if r['canonical_url'])
    ids={urlparse(u).path.strip('/').split('/')[-1] for u in urls if '/exhibit/' in u}
    ids.update(r['external_id'] for r in ext if 'thessaloniki' in r['scheme'].lower())
    return ids,{m.norm(r[k]) for r in rows for k in ['title','alternate_title'] if r[k]},set().union(*(inventory_keys(r['accession_number']) for r in rows))


def validate_record(record,raw):
    original=record['raw_source_record'];index=original['index_record'];cap=original['index_capture']
    assert record['museum']['slug']==SLUG and record['source_record_id']==index['source_id']
    assert index in index_rows(captured_body(cap))
    assert record['source_receipt']['url']==record['source_receipt']['final_url']==index['url']
    parsed=fields(raw);assert parsed==original['native_fields']
    assert original['editorial_review']==REVIEW[index['source_id']]
    return facts(parsed,index)


def prepare():
    baseline=m.load(RUN/'thessaloniki-001-before.json');museum=baseline['museum'];records=[];held=[]
    with m.connect() as db:known,titles,inventories=existing_keys(db,museum['id'])
    for number in ['002','003','004']:
        discovery=m.load(RUN/('discovery-'+number+'.json'));cap=discovery['capture']
        for index in index_rows(captured_body(cap)):
            oid=index['source_id']
            if oid in known or m.norm(index['title']) in titles:
                held.append(dict(index=index,reason='existing_native_identity_or_title'));continue
            body,obj=n.capture('thessaloniki',index['url']);parsed=fields(body)
            if oid in HOLDS:
                reason,note=HOLDS[oid];held.append(dict(index=index,reason=reason,editorial_note=note,native_fields=parsed,capture=obj));continue
            assert oid in REVIEW
            f=facts(parsed,index);assert not inventory_keys(f['accession'])&inventories
            records.append(dict(source_record_id=oid,museum=museum,facts=f,source_receipt=obj['receipt'],body_path=obj['body_path'],
                raw_source_record=dict(index_record=index,index_capture=cap,native_fields=parsed,editorial_review=REVIEW[oid])))
    assert len(records)==7 and len(held)==16
    with m.connect() as db:collisions=title_collisions(db,records)
    m.save(RUN/'thessaloniki-001-research.json.gz',dict(at=m.now(),museum=museum,before=baseline['before'],records=records,held=held,title_collisions=collisions))
    print('Thessaloniki candidates',len(records),'held',len(held),'title leads',len(collisions),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare'])
    parser.parse_args();prepare()
