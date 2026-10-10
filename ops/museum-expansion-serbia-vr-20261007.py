#!/usr/bin/env python3
"""Bounded metadata research for museum-linked Serbian virtual exhibitions."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from bs4 import BeautifulSoup

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-serbia-20261007.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m=s.m;n=s.n;RUN=s.RUN
n.SITES['serbia-vr']='https://vrallart.com'
EXHIBITIONS=['vr-bukovac-exhibition-001','vr-jovanovic-exhibition-001']
# Same named creator and specific titles in the museum's 2015 report, printed
# page 47 (PDF page 48). Inventory numbers are retained as comparison leads:
# no physical dimensions appear in that list, so they are not attached yet.
REPORT_TITLES={
 'SgQa7N9XBnpfMnrbZ':('Оџаклија','121'),
 'XK26xDbf5RmpXaAiD':('Скица за композицију „Раде Неимар предаје модел манастира Манасије“','427'),
 'gTgHcEZJs9jET4osb':('Жена у оријенталној ношњи','124'),
 'rBnjii4AQteggN95q':('Арнаутин са чибуком','428'),
 '2xaProrS8FWehKqiW':('Манастир Сопоћани','1113'),
 'YQwXSuHgbYFiy6aiF':('Милош, Марко и Вила','583'),
}
HOLDS={
 'xLLFXLESYmebYj5pq':'The title/date identify Alexander Obrenovic (1901), but the attached narrative describes the 1922 Alexander Karadjordjevic portrait. Resolve source-record contamination.',
 'uQToHzQxkrwusMzfB':'First wing of the Daedalus and Icarus diptych; reconcile whole-work versus component catalogue records before counting.',
 '2yrLZ2TfC9mD7qqaa':'Second wing of the Daedalus and Icarus diptych; reconcile whole-work versus component catalogue records before counting.',
}


def state(raw):
    scripts=[x.string for x in BeautifulSoup(raw,'html.parser').find_all('script') if x.string and 'window.__PRELOADED_STATE__ =' in x.string]
    assert len(scripts)==1
    prefix,payload=scripts[0].split('=',1);assert prefix.strip()=='window.__PRELOADED_STATE__'
    return json.loads(payload.strip().removesuffix(';'))


def reference(path):return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def literal_date(obj):
    creation=obj.get('creationDate') or {};value=creation.get('override') or creation.get('year') or obj.get('shrYear')
    if obj['_id']=='8M3EpxiR3LMgSe899':
        assert value=='1900' and obj.get('shrYear')=='Oko 1900'
        value=obj['shrYear']  # Keep the explicit approximation; both anchors agree.
    elif creation.get('circa') and value and not re.match(r'(?:Oko|oko|c\.)',value):value='Oko '+value
    return value


def dates(value):
    if not value:return None
    return s.creation_date(re.sub(r'^Oko\s+','око ',value).replace('c. ','око '))


def object_url(obj):return 'https://vrallart.com/artworks/'+quote(obj['shrUrl'],safe='_-')+'/'


def facts(obj,exhibition,key):
    oid=obj['_id'];value=literal_date(obj);date=dates(value)
    if oid in HOLDS:return None,'source_or_component_identity_requires_review'
    if not date:return None,'creation_date_requires_review'
    artists={a['_id']:a for a in exhibition['artists']};artist=artists.get(obj['shrArtistId']);assert artist
    creator=' '.join(v for v in [artist.get('firstName'),artist.get('lastName')] if v)
    if key=='vr-bukovac-exhibition-001':
        assert creator=='Vlaho Bukovac' and 'keeps twenty-three' in exhibition['description'] and len(exhibition['artPieces'])==23
        basis='The official museum virtual-exhibition index links this exact Bukovac exhibition. Its curatorial description explicitly identifies all twenty-three paintings as the National Museum of Serbia collection; this is an individually identified member.'
    elif obj.get('shrCollection')=='Belgrade National Museum':
        basis='Official museum index links this Paja Jovanovic exhibition, and the individual virtual object explicitly labels its collection Belgrade National Museum.'
    elif oid in REPORT_TITLES:
        basis='Official museum index links this Paja Jovanovic exhibition. The museum annual report for 2015, printed page 47 (PDF page 48), lists the same creator and specific title among works from its Serbian painting collection. The report inventory is retained as a comparison lead, not assigned solely by title.'
    else:return None,'individual_collection_holding_requires_review'
    medium=obj.get('shrMedium');assert medium
    if medium.lower().startswith(('ulje','oil','tempera')):kind='painting'
    elif medium.lower() in ['olovka','lavirani tuš']:kind='drawing'
    else:return None,'object_kind_requires_review'
    painting=obj['painting'];height=str(painting['height']);width=str(painting['width'])
    assert all(re.fullmatch(r'\d+(?:\.\d+)?',v) for v in [height,width])
    return dict(title=obj['shrTitle'],creator_label=creator,first=date[0],last=date[1],date_precision=date[2],date_display=value,
        work_type=kind,medium=medium,dimensions='height '+height+' × width '+width+' cm',accession=None,source_url=object_url(obj),
        holding_basis=basis+' Holding only; virtual exhibition membership makes no current physical-display claim.'),None


def validate_record(record,raw):
    original=record['raw_source_record'];obj=original['index_object'];key=original['exhibition_key']
    assert key in EXHIBITIONS and record['museum']['slug']==s.SLUG
    assert record['source_record_id']=='vr-'+obj['_id']
    index=original['index_capture'];exhibition=state(s.captured_body(index))['exhibition']
    assert obj in exhibition['artPieces'] and exhibition['business']['url']=='national_museum_in_belgrade'
    official=s.captured_body(original['official_index_capture'])
    links={unquote(a['href']).rstrip('/') for a in BeautifulSoup(official,'html.parser').select('a[href]')}
    assert unquote(index['receipt']['url']).rstrip('/') in links
    assert urlparse(original['official_index_capture']['receipt']['url']).hostname=='www.narodnimuzej.rs'
    assert hashlib.sha256(raw).hexdigest()==record['source_receipt']['sha256']
    native=state(raw)['artPieces'];assert native==original['native_object'] and native['_id']==obj['_id']
    for k in ['shrTitle','shrMedium','shrArtistId','creationDate','shrYear','painting','shrCollection','shrFullDescription']:
        assert native.get(k)==obj.get(k),(obj['_id'],k)
    assert native.get('artist',{}).get('_id')==obj['shrArtistId']
    assert record['source_receipt']['url']==object_url(obj)
    assert unquote(urlparse(record['source_receipt']['final_url']).path)==unquote(urlparse(object_url(obj)).path)
    if obj['_id'] in REPORT_TITLES:
        report=original['annual_report_comparison'];assert (report['title'],report['inventory'])==REPORT_TITLES[obj['_id']]
        assert report['printed_page']==47 and report['pdf_page']==48
        ref=report['pdf_reference'];assert ref==reference(RUN/'annual-report-2015.pdf')
        assert report['receipt']['sha256']==ref['sha256']
    result,reason=facts(obj,exhibition,key);assert not reason,reason
    return result


def research():
    dest=RUN/'serbia-vr-001-research.json.gz';assert not dest.exists()
    baseline=m.load(RUN/'serbia-001-before.json');official=m.load(RUN/'vr-official-index-001.json');official_raw=s.captured_body(official['capture'])
    links={unquote(a['href']).rstrip('/') for a in BeautifulSoup(official_raw,'html.parser').select('a[href]')}
    pdf=RUN/'annual-report-2015.pdf';receipt=m.load(pdf.with_suffix('.receipt.json'))
    assert hashlib.sha256(pdf.read_bytes()).hexdigest()==receipt['sha256']
    records=[];held=[];selected=[]
    for key in EXHIBITIONS:
        capture=m.load(RUN/(key+'.json'))['capture'];exhibition=state(s.captured_body(capture))['exhibition']
        assert unquote(capture['receipt']['url']).rstrip('/') in links
        assert exhibition['business']['url']=='national_museum_in_belgrade'
        assert len(exhibition['artPieces'])==23
        for obj in exhibition['artPieces']:
            f,reason=facts(obj,exhibition,key)
            common=dict(exhibition_key=key,index_object=obj,index_capture=capture,official_index_capture=official['capture'],note=HOLDS.get(obj['_id']))
            if obj['_id'] in REPORT_TITLES:common['annual_report_comparison']=dict(title=REPORT_TITLES[obj['_id']][0],inventory=REPORT_TITLES[obj['_id']][1],pdf_reference=reference(pdf),receipt=receipt,printed_page=47,pdf_page=48)
            if reason:held.append(dict(source_record_id=obj['_id'],reason=reason,raw_source_record=common));continue
            selected.append((obj,f,common,exhibition,key))
    for obj,f,common,exhibition,key in selected:
        raw,cap=n.capture('serbia-vr',f['source_url']);page=state(raw);native=page['artPieces'];assert isinstance(native,dict) and native['_id']==obj['_id']
        for k in ['shrTitle','shrMedium','shrArtistId','creationDate','shrYear','painting','shrCollection','shrFullDescription']:
            assert native.get(k)==obj.get(k),(obj['_id'],k)
        assert native.get('artist',{}).get('_id')==obj['shrArtistId']
        assert unquote(urlparse(cap['receipt']['final_url']).path)==unquote(urlparse(f['source_url']).path)
        common['native_object']=native
        records.append(dict(source_record_id='vr-'+obj['_id'],museum=baseline['museum'],facts=f,source_receipt=cap['receipt'],body_path=cap['body_path'],raw_source_record=common))
        print(len(records),obj['_id'],f['title'],flush=True)
    m.save(dest,dict(at=m.now(),records=records,held=held,before=baseline['before'],policy='46 selected exhibition identities, bounded metadata object requests only. Research candidates require catalogue-wide creator/version review before import. No images requested.'))
    print('VR research:',len(records),'candidates;',len(held),'holds',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['research']);p.parse_args();research()
