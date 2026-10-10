#!/usr/bin/env python3
"""Reparse preserved primary evidence into review candidates, without DB writes."""
import argparse,collections,csv,gzip,importlib.util,re
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('research',Path(__file__).with_name('nicosia-artwork-research-20261007.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
n,h,R=r.n,r.h,r.R

def dates(value):
    literal=h.plain(value);text=re.sub(r'\s+',' ',literal.replace('–','-').replace('—','-')).strip()
    result=h.parse_date(literal)
    if result['precision']!='unknown':return result
    def bounds(a,b,precision='range'):return dict(date_display=literal,first=a,last=b,precision=precision)
    m=re.fullmatch(r'(?:around|circa|c\.|ca\.|about)\s*(\d{4})',text,re.I)
    if m:return bounds(int(m[1]),int(m[1]),'circa')
    m=re.fullmatch(r'(?:in |the )?(?:(first|second|1st|2nd) half of (?:the )?)?(?:(?:beginning|end|early|late|mid)(?:\s+of)?\s*-?\s*(?:the )?)?(\d{1,2})(?:st|nd|rd|th)\s*(?:century|c\.?)(?:\s*(?:AD|A\.D\.))?',text,re.I)
    if m:
        a=(int(m[2])-1)*100+1;b=int(m[2])*100
        if m[1]:
            if m[1].lower()in ['first','1st']:b-=50
            else:a+=50
        return bounds(a,b,'range'if m[1]else'century')
    m=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th)?\s*-\s*(\d{1,2})(?:st|nd|rd|th)\s+centur(?:y|ies)',text,re.I)
    if m and int(m[1])<=int(m[2]):return bounds((int(m[1])-1)*100+1,int(m[2])*100)
    m=re.fullmatch(r'(\d{1,4})\s*-\s*(\d{1,4})\s*(?:BC|BCE)',text,re.I)
    if m and int(m[1])>=int(m[2]):return bounds(-int(m[1]),-int(m[2]))
    m=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th) century (?:BC|BCE)',text,re.I)
    if m:return bounds(-int(m[1])*100,-((int(m[1])-1)*100+1),'century')
    return result

def cvar_dates(value):
    # In this primary catalogue YYYY-MM and YYYY--M--D are calendar dates.
    # Do not interpret a month as an abbreviated end year.
    text=h.plain(value);m=re.fullmatch(r'(\d{4})\s*-\s*(0[1-9]|1[0-2])',text)
    if m:return dict(date_display=text,first=int(m[1]),last=int(m[1]),precision='exact')
    m=re.fullmatch(r'(\d{4})--?(\d{1,2})--?(\d{1,2})',text)
    if m:
        import datetime
        try:d=datetime.date(*map(int,m.groups()))
        except ValueError:return dates(value)
        return dict(date_display=text,first=d.year,last=d.year,precision='exact')
    m=re.fullmatch(r'(\d{4})-(\d)',text)
    if m:
        a=int(m[1]);b=a//10*10+int(m[2])
        if a<=b:return dict(date_display=text,first=a,last=b,precision='range')
    return dates(value)

def soup(x):
    rc=x['receipt'];raw=gzip.decompress((n.REPO/rc['body_path']).read_bytes());assert h.sha(raw)==rc['sha256']
    return BeautifulSoup(raw,'html.parser')

def fact(x,source,source_id,museum,fields):
    return dict(source=source,scheme=source,source_id=source_id,source_url=x['url'],receipt=x['receipt'],museum_slug=museum,
        raw_fields=fields,title=None,creator_label=None,medium=None,dimensions=None,accession=None,work_type='unknown',image_url=None,
        holding_note='Object-specific primary museum catalogue evidence. Historical provenance is preserved separately; no current-display assertion.',
        editorial_confidence=.96,confidence_basis='Primary museum object identifier and object-level metadata, with captured source hash; editorial assessment, not a calibrated probability.',
        remaining_uncertainty='Present display, reuse rights and creator identity reconciliation are not established by this metadata-only selection.')

def extract():
    rows=[];held=[]
    for path in sorted((R/'artwork-pages').glob('*.json')):
        if path.stem.startswith(('municipal-','cvar-index-')):continue
        x=h.load(path)
        if x['receipt']['status']!=200:held.append(dict(source_url=x['url'],reason='source_unavailable'));continue
        s=soup(x);f=None
        if path.stem.startswith('makarios-'):
            fields={}
            for cell in s.select('td'):
                key=cell.find('strong')
                if not key:continue
                label=key.get_text(' ',strip=True).strip(' :');value=cell.get_text(' ',strip=True)
                if label in ['Title','Chronology','Artist/School','Provenance','Technique','Dimensions','Conservation status']:
                    assert label not in fields;fields[label]=value[len(key.get_text(' ',strip=True)):].strip(' :')
            source_id=path.stem.removeprefix('makarios-')
            if not fields.get('Title')or not s.title or s.title.get_text(strip=True).lower()!=source_id:
                held.append(dict(source_url=x['url'],reason='catalogue_layout_or_identity_review',raw_fields=fields));continue
            f=fact(x,'makarios-foundation-object',source_id,'makarios-byzantine-museum-nicosia',fields)
            f.update(title=fields['Title'],creator_label=fields.get('Artist/School'),medium=fields.get('Technique'),dimensions=fields.get('Dimensions'))
            f.update(dates(fields.get('Chronology')));f['work_type']=h.kind(f['medium'])or'unknown'
            if 'fresco'in (f['medium']or'').lower():f['work_type']='fresco'
            if re.search(r'\btwo\b|\bpair\b|and verso|double-sided|overpaint|repaint|replica|copies',fields['Title']+' '+fields.get('Chronology','')+' '+fields.get('Technique',''),re.I):
                held.append(dict(facts=f,reason='group_copy_or_multiple_paint_layers_review'));continue
        elif path.stem.startswith('cvar-'):
            fields={}
            for node in s.select('.info-table-row'):
                cells=node.find_all('p',recursive=False)
                if len(cells)==2:fields[cells[0].get_text(' ',strip=True).rstrip(':').strip()]=cells[1].get_text(' ',strip=True)
            if not fields.get('Identifier')or not s.h1:
                held.append(dict(source_url=x['url'],reason='cvar_layout_review'));continue
            f=fact(x,'cvar-object',x['url'].rstrip('/').rsplit('/',1)[-1],'cvar-nicosia',fields)
            f.update(title=s.h1.get_text(' ',strip=True),creator_label=fields.get('Creator'),medium=fields.get('Medium'),dimensions=fields.get('Dimensions'),accession=fields['Identifier'])
            f.update(cvar_dates(fields.get('Date')));f['work_type']=h.kind(f['medium']or fields.get('Object Type'))or'unknown'
            if fields.get('Collection')!='Paintings Collection'or re.search(r'sketchbook|\balbum\b|including two drawings',f['title'],re.I):
                held.append(dict(facts=f,reason='collection_or_grouped_sketchbook_review'));continue
        elif path.stem.startswith('leventis-'):
            headings=s.select('h2');fields={}
            for node in headings:
                m=re.match(r'^(Medium|Dimensions|Year|Code):\s*(.*)$',node.get_text(' ',strip=True))
                if m:fields[m[1]]=m[2]
            if not headings or not fields.get('Code'):
                held.append(dict(source_url=x['url'],reason='leventis_layout_review'));continue
            creator=headings[0].parent.parent.select_one('.jet-listing-dynamic-field__content')
            fields['creator']=creator.get_text(' ',strip=True)if creator else None
            fields['title']=headings[0].get_text(' ',strip=True)
            f=fact(x,'leventis-gallery-object',path.stem.removeprefix('leventis-'),'leventis-gallery',fields)
            f.update(title=fields['title'],creator_label=fields['creator']or None,medium=fields.get('Medium')or None,dimensions=fields.get('Dimensions')or None,accession=fields['Code'])
            f.update(dates(fields.get('Year')));f['work_type']=h.kind(f['medium'])or'unknown'
            if re.search(r'\bpair\b|\brecto\b|\bverso\b|\bstudies\b',f['title'],re.I):
                held.append(dict(facts=f,reason='group_or_recto_verso_review'));continue
        if f:
            if f['last']is None or f['precision']=='unknown':held.append(dict(facts=f,reason='creation_date_requires_editorial_review'))
            elif f['last']>1970:held.append(dict(facts=f,reason='after_or_crossing_1970_cutoff'))
            else:rows.append(f)
    return rows,held

def build(write=False):
    rows,held=extract()
    # Explicit project preference: retain source-backed named creators even
    # when their object's date is unknown, as actual review-only candidates.
    remaining=[]
    for item in held:
        f=item.get('facts');label=h.norm(f.get('creator_label'))if f else ''
        if item['reason']=='creation_date_requires_editorial_review'and label and not re.search(r'\bunknown\b|\banonymous\b',label):
            f['review_reason']='Creation date unknown or not safely classified; retained named-creator museum object in review. Not eligible or publishable until date review.'
            rows.append(f)
        else:remaining.append(item)
    held=remaining
    for supplemental in [R/'editorial-artwork-candidates.json',R/'cyprus-museum-artwork-candidates.json']:
      if supplemental.exists():
        for f in h.load(supplemental)['records']:
            rc=f['receipt'];assert h.sha(gzip.decompress((n.REPO/rc['body_path']).read_bytes()))==rc['sha256']
            assert f['last']<=1970 and f['precision']!='unknown';rows.append(f)
    inventory_groups=collections.defaultdict(list)
    for f in rows:
        if f['accession']:inventory_groups[(f['museum_slug'],h.norm(f['accession']))].append(f)
    removed=set();merged=[]
    for key,group in inventory_groups.items():
        if len(group)<2:continue
        signatures={(
            tuple(sorted(h.norm(t)for t in f['title'].split(' / '))),h.norm(f['creator_label']),
            h.norm(f['dimensions']),h.norm(f['medium']),f['first'],f['last'])for f in group}
        if len(signatures)==1:
            chosen=group[0];chosen['alternate_sources']=group[1:]
            merged.append(dict(institution=key[0],accession=chosen['accession'],retained_source_id=chosen['source_id'],duplicate_source_ids=[f['source_id']for f in group[1:]],basis='Same museum inventory, creator, dimensions, medium, date and title/translations.'))
            removed.update((f['scheme'],f['source_id'])for f in group[1:])
        else:
            for f in group:held.append(dict(facts=f,reason='conflicting_source_inventory_requires_object_review'));removed.add((f['scheme'],f['source_id']))
    rows=[f for f in rows if(f['scheme'],f['source_id'])not in removed]
    assert len({(f['scheme'],f['source_id'])for f in rows})==len(rows)
    report=dict(at=h.now(),target='production',status='prepared_pending_live_identity_reconciliation_and_authenticated_delivery',records=rows,held=held,
        counts=dict(collections.Counter(x['museum_slug']for x in rows)),dated_counts=dict(collections.Counter(x['museum_slug']for x in rows if x['precision']!='unknown')),
        unknown_dates=sum(x['precision']=='unknown'for x in rows),held_reasons=dict(collections.Counter(x['reason']for x in held)),merged_source_duplicates=merged,
        policy='Source-backed creations through 1970. Museum metadata only, no image downloads, no publication, no current-display claim. Primary unknown/qualified creator labels preserved. All dates are creation evidence, never acquisition or publication dates.')
    if write:
        h.save(R/'artwork-candidates.json.gz',report)
        with(R/'artwork-candidates.csv').open('x',newline='')as out:
            fields=['museum_slug','title','creator_label','date_display','first','last','precision','work_type','medium','dimensions','accession','scheme','source_id','source_url']
            w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    print('CANDIDATES',len(rows),report['counts'],'UNKNOWN DATES',report['unknown_dates'],'HELD',len(held),report['held_reasons'],flush=True)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();build(a.write)
