#!/usr/bin/env python3
"""Selected Serbian museum gallery captions, preserving physical-object scope."""
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
RUN=n.RUN/'serbia';SITE='https://www.narodnimuzej.rs';SLUG='wikimedia-museum-q1277393'
captured_body=a.captured_body
n.SITES['serbia']=SITE

# These gallery descriptions contain no creator field. Tuple values delimit
# the source title, date, materials and origin without guessing a maker.
ANONYMOUS={
 25:('Икона Богородица са Христом','18. век','дрво, дрворез','непознати локалитет','sculpture'),
 26:('Икона Богородица','18. век','дрво гипс темпера','непознати локалитет','painting'),
 27:('Оковани напрсни крст','18. век','шимшир, дуборез, оков сребро, позлата','Србија','unknown'),
 28:('Икона Христово рођење','18. век','дрво, гипс, темпера','непознати локалитет','painting'),
 29:('Хаџијска икона, Јерусалим','1794. година','платно, уље, каширано на дрво','Сарајево','painting'),
 30:('Пафте','17-18. век','седеф, позлата','непознати локалитет','unknown'),
 31:('Прстен са гемом','позни средњи век','сребро, карнеол','непознати локалитет','metalwork'),
 33:('Чаша','15-16 век','стакло у боји','Гацко','unknown'),
 34:('Чаша','1608. година','сребро,позлата','Манастир Дечани','metalwork'),
 79:('Мирослављево јеванђеље: страница бр. 149','осамдесте године 12. века','пергамент, кожни повез','Манастир Хиландар','manuscript_illumination'),
 80:('Двојна икона: Благовести, сусрет Јоакима и Ане','средина 14. века','јајчана темпера на дрвету','Љубижда код Призрена','painting'),
 81:('Двојна икона: Благовести и Сусрет Јоакима и Ане','средина 14. века','темпера на дрвету','непознати локалитет','painting'),
 82:('Наушница','12-13. век','сребро','Нересница код Зајечара','metalwork'),
 83:('Прстен','почетак 14. века','сребро, емајл','непознати локалитет','metalwork'),
 84:('Наушнице','прва половина 14. века','сребро, драги камен','Марков град код Прилепа','metalwork'),
 85:('Прстен','средина 15. века','злато, техника: нијело','Дубровник','metalwork'),
 86:('Прстен за лук','14-15. век','сребро','непознати локалитет','metalwork'),
 87:('Прстен војводе Владислава','прва четвртина 15. века','злато','непознати локалитет','metalwork'),
 88:('Посуда са јеванђелистима','13. век','сребро','Ариље','metalwork'),
 89:('Наушница','позни средњи век','злато, емајл','непознати локалитет','metalwork'),
 90:('Наушница','друга половина 14. века','сребро','околина Деспотовца','metalwork'),
 91:('Христ (глава)','14. век','фреска','Пећка патријаршија','fresco'),
 92:('Наруквица','прва половина 14. века','сребро','Марков град код Прилепа','metalwork'),
 93:('Здела','14. век','керамика, енгоба, колоритни зграфито, глеђ','Пећ','ceramic'),
}
SCOPE_HOLDS={
 4:'Caption says 1862 while the native gallery image filename says 1860. Resolve the source discrepancy before selecting a creation date.',
 79:'The entry shows page 149 of Miroslav Gospel. Resolve the manuscript/leaf physical scope; do not create a whole manuscript and a page as separate objects.',
 80:'Two gallery images have substantially the same double-icon title/date. Establish whether these are separate objects or views before counting.',
 81:'Two gallery images have substantially the same double-icon title/date. Establish whether these are separate objects or views before counting.',
}


def source_id(entry):
    return 'gallery-'+hashlib.sha256(entry['image_url_identity_only'].encode()).hexdigest()[:24]


def creation_date(value):
    value=value.strip()
    exact=re.fullmatch(r'(око\s+)?(\d{3,4})(?:\s*[-–]\s*(\d{2,4}))?(?:\.?(?:\s+година)?)?',value,re.I)
    if exact:
        first=int(exact[2]);end=exact[3]
        last=int(end) if end else first
        if end and len(end)==2:last=(first//100)*100+last
        if not 100<=first<=last<=1970 or (exact[1] and last==1970):return None
        return first,last,('circa' if first==last else 'circa_range') if exact[1] else ('exact' if first==last else 'range')
    century=re.fullmatch(r'(?:(крај|почетак|средина|прва половина|друга половина|прва четвртина)\s+)?(\d{1,2})(?:-(\d{1,2}))?\.?\s+век(?:а)?',value)
    if century:
        first_century=int(century[2]);last_century=int(century[3] or century[2]);qualifier=century[1]
        if not 1<=first_century<=last_century<=19 or (qualifier and century[3]):return None
        first,last=(first_century-1)*100+1,last_century*100
        if qualifier=='прва половина':last=first+49
        elif qualifier=='друга половина':first=last-49
        elif qualifier=='прва четвртина':last=first+24
        # Early, middle and late remain literal. The full stated century is
        # the supported outer interval; no arbitrary sub-century year is made up.
        return first,last,'century' if first_century==last_century and qualifier not in ['прва половина','друга половина','прва четвртина'] else 'range'
    return None


def gallery_entries(raw):
    soup=BeautifulSoup(raw,'html.parser')
    return [dict(caption=x['data-title'],image_url_identity_only=x['href']) for x in soup.select('a[data-lightbox="gallery"][data-title]')]


def fields(entry,number):
    caption=entry['caption'];page=entry['source_page'];parts=caption.split(', ')
    if number>=94:return None,'modern_copy_creation_date_missing'
    if number in ANONYMOUS:
        title,date,medium,origin,kind=ANONYMOUS[number]
        assert caption==', '.join([title,date,medium,origin])
        return dict(title=title,creator_label=None,date=date,medium=medium,dimensions=None,origin=origin,work_type=kind),None
    if number==32:return None,'named_icon_creation_date_missing'
    creator=parts[0].strip();dates=[i for i,v in enumerate(parts) if i>=2 and creation_date(v)]
    if len(dates)!=1:return None,'creation_date_requires_review'
    ix=dates[0];date=parts[ix];title=', '.join(parts[1:ix]);tail=', '.join(parts[ix+1:])
    dim=re.search(r'(?:^|, )((?:(?:[\w/]+|картон)\s*:\s*|d-)?\d+(?:[.,]\d+)?\s*[xх].*)$',tail)
    if not dim:dim=re.search(r'(?:^|, )(d-\d+\s+цм)$',tail)
    dimensions=dim[1] if dim else None
    medium=tail[:dim.start()].strip(', ') if dim else tail
    if any(v in medium for v in ['бакрорез','бакропис','литографија','линорез','линогравура','цинкографија']):kind='print'
    elif any(v in medium for v in ['уље','акварел','темпера']):kind='painting'
    elif any(v in medium for v in ['пастел','оловка','угљен','туш']):kind='drawing'
    elif 'sculpture-collection/' in page:kind='sculpture'
    elif any(v in page for v in ['serbian-18th-and-19th-century-painting','20th-century-yugoslav-painting']):kind='painting'
    else:kind='unknown'
    return dict(title=title,creator_label=creator,date=date,medium=medium or None,dimensions=dimensions,origin=None,work_type=kind),None


def facts(entry,number):
    parsed,reason=fields(entry,number)
    if reason:return None,reason
    if number in SCOPE_HOLDS:return None,'physical_identity_or_source_conflict'
    dates=creation_date(parsed['date'])
    if not dates:return None,'creation_date_requires_review'
    result=dict(title=parsed['title'],creator_label=parsed['creator_label'],first=dates[0],last=dates[1],date_precision=dates[2],date_display=parsed['date'],work_type=parsed['work_type'],medium=parsed['medium'],dimensions=parsed['dimensions'],accession=None,source_url=entry['source_page'],
        holding_basis='Official National Museum of Serbia collection-department gallery identifies this selected object in its literal caption. Native image link retained solely to locate the caption; no image requested and no museum accession supplied. Source origin: '+(parsed['origin'] or 'not stated')+'. Collection holding only, with no current-display claim.')
    if 'икона' in parsed['title'].lower():result['object_form']='icon'
    if number in ANONYMOUS:result['cultural_context']='Serbian, Byzantine and post-Byzantine collection; source origin retained without inventing a creator or nationality'
    return result,None


def validate_record(record,raw):
    original=record['raw_source_record'];entry=original['gallery_entry'];number=original['queue_number']
    assert record['museum']['slug']==SLUG and record['source_record_id']==source_id(entry)
    queue=m.load(RUN/'caption-queue-001.json');assert queue['entries'][number-1]==entry
    assert entry['capture']==dict(receipt=record['source_receipt'],body_path=record['body_path'])
    assert hashlib.sha256(raw).hexdigest()==record['source_receipt']['sha256']
    assert {k:entry[k] for k in ['caption','image_url_identity_only']} in gallery_entries(raw)
    assert original['native_fields']==fields(entry,number)[0]
    result,reason=facts(entry,number);assert not reason,reason
    return result


def research():
    queue=m.load(RUN/'caption-queue-001.json');baseline=m.load(RUN/'serbia-001-before.json');records=[];held=[]
    assert len(queue['entries'])==107
    for number,entry in enumerate(queue['entries'],1):
        cap=entry['capture'];raw=captured_body(cap)
        identity={k:entry[k] for k in ['caption','image_url_identity_only']}
        assert identity in gallery_entries(raw)
        assert cap['receipt']['url']==entry['source_page'] and urlparse(entry['source_page']).hostname=='www.narodnimuzej.rs'
        f,reason=facts(entry,number)
        if reason:
            held.append(dict(number=number,entry=entry,reason=reason,note=SCOPE_HOLDS.get(number)));continue
        records.append(dict(source_record_id=source_id(entry),museum=baseline['museum'],facts=f,source_receipt=cap['receipt'],body_path=cap['body_path'],raw_source_record=dict(gallery_entry=entry,queue_number=number,native_fields=fields(entry,number)[0])))
    m.save(RUN/'serbia-caption-001-research.json.gz',dict(at=m.now(),records=records,held=held,before=baseline['before'],policy='Caption-derived research candidates only. Creator/version/title/physical-object review still required. All 107 discovery keys retained. No images or catalogue writes.'))
    print('Serbia captions:',len(records),'candidates;',len(held),'holds',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['research']);p.parse_args();research()
