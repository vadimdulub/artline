#!/usr/bin/env python3
"""Parse retained official-page web-tool extracts, never claiming raw HTTP evidence."""
import argparse,gzip,hashlib,importlib.util,json,re
from functools import lru_cache
from pathlib import Path
s=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-dulwich-discovery-20261007.py'));d=importlib.util.module_from_spec(s);s.loader.exec_module(d);m=d.m;RUN=d.RUN;BASE=d.BASE

def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def pages(text):
    pattern=r'^([^\n]+) \((https://[^\n]+)\)\n\ue200cite\ue202(turn\d+\w+\d+)\ue201 \[wordlim:.*?Total lines: (\d+)\n'
    heads=list(re.finditer(pattern,text,re.M));out=[]
    for pos,h in enumerate(heads):
        raw=text[h.end():heads[pos+1].start() if pos+1<len(heads) else len(text)].split('-'*80,1)[0]
        lines=[(int(n),t.strip()) for n,t in re.findall(r'L(\d+):\s?(.*?)(?=L\d+:|\Z)',raw,re.S)]
        total=int(h[4]);seen=[n for n,t in lines]
        header=text[h.start():h.end()];call=re.search(r'Source: (click|open)\((\{.*?\})\)',header);assert call
        out.append(dict(title=h[1],url=h[2],web_ref=h[3],source_metadata=header,source_call=dict(method=call[1],args=json.loads(call[2])),total_lines=total,complete=seen==list(range(total)),lines=lines))
    return out

def index_rows(p):
    assert p['complete'] and p['url'].split('?')[0]==BASE+'/explore/explore-the-collection/'
    rows=[]
    for number,line in p['lines']:
        if line=='## Footer':break
        if number<85:continue
        match=re.match(r'\ue200cite\ue202(\d+)†([^\ue201]+)\ue201',line)
        if not match or match[2].startswith('Image:'):continue
        label=re.fullmatch(r'(.+) by(?: (.*))?',match[2])
        if not label:continue
        title,creator=label[1],label[2] or None
        rows.append(dict(index_web_ref=p['web_ref'],index_url=p['url'],link_id=int(match[1]),title=title,creator_label=creator))
    headings=[]
    for number,line in p['lines']:
        if line.startswith('## ') and re.search(r' By(?: |$)',line):
            match=re.fullmatch(r'## (.+?) By(?: (.*))?',line);assert match
            headings.append((match[1],match[2] or None))
    assert len(rows)==len(headings)==48 and len({r['link_id'] for r in rows})==48
    # The render's capitalized By delimiter distinguishes title prepositions
    # and creators described as "after a print by ... after a painting by ...".
    for row,(title,creator) in zip(rows,headings):
        assert m.norm(row['title']+' by '+(row['creator_label'] or ''))==m.norm(title+' by '+(creator or ''))
        row.update(title=title,creator_label=creator)
    return rows

def object_facts(p):
    assert p['complete'],'incomplete web-tool extract'
    assert re.fullmatch(re.escape(BASE)+r'/explore/explore-the-collection/[^/?]+/',p['url'])
    texts=[t for n,t in p['lines'] if t];heading=[t for t in texts if t.startswith('# ')];assert len(heading)==1
    if ' by ' in heading[0]:title,creator=[x.strip() for x in heading[0][2:].rsplit(' by ',1)]
    else:
        title=heading[0][2:].strip();nextline=texts[texts.index(heading[0])+1];creator=nextline[3:].strip() if nextline.startswith('by ') else None
    start=texts.index('Item details') if 'Item details' in texts else texts.index(heading[0])
    stop=next(i for i in range(start+1,len(texts)) if texts[i].startswith('## Want to use') or ('Item details' in texts and texts[i].startswith('## ')))
    fields={};narrative=[];i=start+1
    while i<stop:
        if texts[i].startswith('* '):
            label=texts[i][2:];assert label not in fields
            assert i+1<stop and not texts[i+1].startswith('* ');fields[label]=texts[i+1];i+=2
        else:narrative.append(texts[i]);i+=1
    dates=[t[6:] for t in texts if t.startswith('Date: ')];assert len(dates)<=1
    detail_creator=fields.get('Artist',fields.get('Artist description'))
    if detail_creator:
        clean_heading=re.sub(r'\s+',' ',heading[0][2:]).strip();suffix=' by '+re.sub(r'\s+',' ',detail_creator).strip()
        if clean_heading.endswith(suffix):title=clean_heading[:-len(suffix)].strip();creator=detail_creator
    issues=[]
    if detail_creator and m.norm(detail_creator)!=m.norm(creator):issues.append('heading/detail creator labels differ')
    if dates and fields.get('Date') and m.norm(dates[0])!=m.norm(fields['Date']):issues.append('heading/detail creation dates differ')
    assert any('Dulwich Picture Gallery' in t for t in texts[stop:])
    return dict(source_url=p['url'],source_id=p['url'].rstrip('/').rsplit('/',1)[1],title=title,creator_label=creator,detail_creator_label=detail_creator,inventory=fields.get('Accession number'),date_display=fields.get('Date') or (dates[0] if dates else None),heading_date=dates[0] if dates else None,source_issues=issues,medium=fields.get('Materials'),dimensions_text=fields.get('Dimensions'),acquisition=fields.get('Acquisition'),inscription=fields.get('Inscription'),notes=fields.get('Notes'),fields=fields,narrative=narrative,rights_text=[t for t in texts if any(x in t for x in ['personal use','commercial use','commercial use?','licence','download this artwork'])],web_ref=p['web_ref'],source_metadata=p['source_metadata'],capture_kind='Official-page web-tool text extraction; not original HTTP bytes')

@lru_cache(maxsize=16)
def checked_index_pages(path,digest):
    file=m.ROOT/path;assert hashlib.sha256(file.read_bytes()).hexdigest()==digest
    return {p['web_ref']:index_rows(p) for p in pages(m.load(file)['result']) if p['complete'] and p['url'].split('?')[0]==BASE+'/explore/explore-the-collection/'}

def checked_index(p,record):
    call=p['source_call']
    if call['method']=='click':
        rs=[r for r in record['requests'] if r['index_web_ref']==call['args']['ref_id'] and r['link_id']==call['args']['id']]
    else:
        assert call['args']['ref_id']==p['url'] and record.get('retry_of') and len(record['requests'])==1
        rs=record['requests']
    assert len(rs)==1
    request=rs[0];reference=request['index_capture_reference']
    rows=checked_index_pages(reference['path'],reference['sha256'])[request['index_web_ref']]
    row=next(r for r in rows if r['link_id']==request['link_id'])
    return dict(**row,index_capture_reference=reference)

def queue():
    rows=[]
    for name in ['web-discovery-001.json.gz','web-discovery-samples-001.json.gz']:
        path=RUN/name
        for page in pages(m.load(path)['result']):
            if page['url'].split('?')[0]==BASE+'/explore/explore-the-collection/':
                rows.extend([dict(r,index_capture_reference=ref(path)) for r in index_rows(page)])
    assert len(rows)==96
    m.save(RUN/'web-object-queue-001.json',dict(at=m.now(),rows=rows,policy='First two bounded48-row official indexes. Queue membership does not approve creation dates, physical identity, holdings, additions or images.'))
    print('Queued',len(rows),flush=True)

def review():
    out=[];errors=[]
    for path in sorted(RUN.glob('web-objects-*/batch-*.json.gz')):
        record=m.load(path);parsed=pages(record['result'])
        for page in parsed:
            try:
                facts=object_facts(page);index=checked_index(page,record)
                if m.norm(facts['title'])!=m.norm(index['title']):facts['source_issues'].append('index/object title differs')
                if m.norm(facts['creator_label'])!=m.norm(index['creator_label']):facts['source_issues'].append('index/object creator differs')
                out.append(dict(state='object_facts_pending_identity_review',facts=facts,index=index,source_reference=ref(path)))
            except Exception as ex:errors.append(dict(url=page['url'],source_reference=ref(path),error=type(ex).__name__+': '+str(ex),complete=page['complete'],total_lines=page['total_lines'],last_line=page['lines'][-1][0] if page['lines'] else None))
        if len(parsed)!=len(record['requests']):errors.append(dict(source_reference=ref(path),error='Response page count differs from requested pages',parsed=len(parsed),requested=len(record['requests'])))
    return dict(at=m.now(),rows=out,errors=errors)

def creation(raw):
    """Only source-explicit eligible years/periods; uncertainty at1970 stays held."""
    t=re.sub(r'\s+',' ',raw or '').strip().casefold().replace('–','-').replace('—','-')
    fail=lambda reason:dict(first=None,last=None,date_precision='unknown',date_issue=reason)
    if not t:return fail('No explicit creation date')
    before=re.fullmatch(r'before (\d{3,4})',t)
    if before:
        last=int(before[1]);return dict(first=None,last=last,date_precision='before',date_issue=None) if 100<last<=1971 else fail('Before endpoint does not establish eligibility')
    circa=t.startswith('c.');t=re.sub(r'^c\.\s*','',t)
    numeric=re.fullmatch(r'(\d{3,4})(?:\s*-\s*(\d{1,4}))?\.?',t)
    if numeric:
        first=int(numeric[1]);tail=numeric[2];last=first
        if tail:last=int(tail) if len(tail)>=len(numeric[1]) else (first//(10**len(tail)))*(10**len(tail))+int(tail)
        if not 100<=first<=last<=1970 or (circa and last==1970):return fail('Unordered, post-cutoff or uncertain cutoff year')
        return dict(first=first,last=last,date_precision=('circa' if first==last else 'circa_range') if circa else ('exact' if first==last else 'range'),date_issue=None)
    period=re.fullmatch(r'(?:(?:early|mid|late)[ -])?(\d{3}0)s',t)
    if period:
        first=int(period[1]);last=first+9
        return dict(first=first,last=last,date_precision='circa_range' if circa else 'decade',date_issue=None) if last<=1970 else fail('Decade extends beyond cutoff')
    century=re.fullmatch(r'(?:(?:early|mid|late)[ -]|(?:first|second) half of (?:the )?)?(\d{1,2})(?:st|nd|rd|th) century',t)
    if century:
        first=(int(century[1])-1)*100;last=first+99
        return dict(first=first,last=last,date_precision='century',date_issue=None) if 100<=first<=last<=1970 else fail('Century extends beyond cutoff')
    return fail('Creation qualifier, alternative, multiple phase or period requires editorial review')

def candidates(suffix):
    x=review();rows=[]
    for row in x['rows']:
        facts=row['facts'];facts.update(creation(facts['date_display']))
        facts['work_type']='painting' if (facts['medium'] or '').casefold().startswith('oil on ') else ('drawing' if (facts['medium'] or '').casefold().startswith('pastel on ') else 'unknown')
        facts.update(titles=[facts['title']],object_form=None,date_basis='Literal creation Date field, not acquisition/sitter/artist life. Century/decade search bounds retain the whole named period; no narrower early/mid/late or half-century boundaries invented.')
        holds=[]
        if facts['date_issue']:holds.append(facts['date_issue'])
        if not facts['inventory']:holds.append('No native accession for physical identity')
        if not facts['acquisition']:holds.append('Acquisition field absent; collection context requires review')
        rows.append(dict(source_id=facts['source_id'],source_reference=row['source_reference'],index=row['index'],state='source_hold' if holds else 'candidate',reasons=holds,facts=facts))
    assert len(rows)==len({r['source_id'] for r in rows})==336
    m.save(RUN/('native-candidates-'+suffix+'.json.gz'),dict(at=m.now(),rows=rows,capture_errors=x['errors'],policy='Candidates require creator/version/narrative/holding review. Heading/detail conflicts retained, never silently reconciled. Unknown creator/type/date fields stay unknown; no artist biography inference.'))
    print(json.dumps(dict(rows=len(rows),candidates=sum(r['state']=='candidate' for r in rows),source_holds=sum(r['state']=='source_hold' for r in rows))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['queue','review','candidates']);p.add_argument('--suffix',default='001');args=p.parse_args()
    if args.command=='queue':queue()
    elif args.command=='candidates':candidates(args.suffix)
    else:
        x=review();print(json.dumps(dict(rows=len(x['rows']),errors=x['errors']),ensure_ascii=False))
