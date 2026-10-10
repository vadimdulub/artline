#!/usr/bin/env python3
"""Selected Cyprus Museum art objects in the official 2012 exhibition catalogue."""
import collections,importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('candidates',Path(__file__).with_name('nicosia-artwork-candidates-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
h,n,R=c.h,c.n,c.R

def date(value):
    text=value.replace('–','-').replace('—','-');parts=re.findall(r'\(([^()]*)\)',text)
    numeric=next((x for x in reversed(parts)if re.search(r'\b(?:BC|AD)\b',x)),text).strip()
    era='BC'if'BC'in numeric else'AD'if'AD'in numeric else None
    if not era:return None
    def out(a,b,precision):return dict(date_display=value,first=a,last=b,precision=precision)
    m=re.fullmatch(r'(?:ca\.\s*)?(\d{1,4})(?:\s*[-/]\s*(\d{1,4}))?\s*BC',numeric)
    if m:
        a=int(m[1]);b=int(m[2]or m[1])
        if a<b:return None
        return out(-a,-b,('circa_range'if m[2]else'circa')if'ca.'in numeric else'range'if m[2]else'exact')
    m=re.fullmatch(r'(?:(?:early|late|First half of the)\s+)?(\d{1,2})(?:st|nd|rd|th)(?:-(\d{1,2})(?:st|nd|rd|th))?\s*(c\.?|century|millennium|millennia)?\s*BC',numeric,re.I)
    if m:
        scale=1000 if(m[3]or'').startswith('millenn')else 100;a=int(m[1]);b=int(m[2]or m[1])
        if a<b:return None
        # Retain early/late/half literally and use broad stated-century bounds.
        return out(-a*scale,-((b-1)*scale+1),'range'if a!=b or scale==1000 else'century')
    m=re.fullmatch(r'(\d)(?:st|nd|rd|th) c\. AD',numeric)
    if m:return out((int(m[1])-1)*100+1,int(m[1])*100,'century')
    m=re.fullmatch(r'AD (\d{1,4})/(\d{1,2})',numeric)
    if m:
        a=int(m[1]);b=a//100*100+int(m[2]);return out(a,b,'range')if a<=b else None
    if numeric.startswith('Earlier than ')and numeric.endswith(' BC'):
        year=-int(re.search(r'\d+',numeric)[0]);return out(None,year,'before')
    return None

def build():
    rc=h.load(R/'catalogue-pdf.json');assert rc['status']==200
    columns=h.load(R/'catalogue-columns.json')+[h.load(R/'catalogue-additional-column-268.json')];rows=[];held=[]
    excluded={23,24,25,26,33,43,44,45,46,47,48,49,50,52,55,57,58,59,69,70,71,73,74,81,137,147,152,156,197,214,215,216,217,226,238,239}
    for column in columns:
        for match in re.finditer(r'(?:^|\n)(\d{1,3})\n((?:(?!\n\d{1,3}\n).)*?)(?=\n\d{1,3}\n|\Z)',column['text'],re.S):
            number=int(match[1]);lines=match[2].splitlines();end=next((i for i,l in enumerate(lines)if l.startswith('Cyprus Museum,')),None)
            if end is None or end>12:continue
            header=lines[:end+1];raw=dict(catalogue_number=number,pdf_page=column['pdf_page'],column=column['column'],header=header,description_and_references=lines[end+1:])
            if number in excluded or re.search(r'\(a\)|\(b\)',header[-1]):held.append(dict(raw_fields=raw,reason='tool_industrial_material_or_multiple_objects'));continue
            dims=next((i for i,l in enumerate(header)if re.match(r'^(?:L\.|H\.|Diam\.|D\.|W\.)',l)),None)
            if dims is None or dims<2:held.append(dict(raw_fields=raw,reason='header_layout_review'));continue
            datepos=next((i for i in range(dims+1,end)if re.search(r'\b(?:BC|AD|period)\b',header[i])),None)
            if datepos is None:held.append(dict(raw_fields=raw,reason='unknown_creation_date'));continue
            parsed=date(header[datepos])
            if not parsed:held.append(dict(raw_fields=raw,reason='creation_date_review'));continue
            medium=header[dims-1];title=' '.join(header[:dims-1]);title=title.replace('fi gur','figur').replace('fl ask','flask')
            accession=header[-1].removeprefix('Cyprus Museum,').strip()
            assert accession and accession!='‘Gunnis hoard’'
            f=c.fact(dict(url=rc['url'],receipt=rc),'cyprus-museum-cultures-in-dialogue-2012',str(number),'cyprus-museum-nicosia',raw)
            f.update(title=title,medium=medium,dimensions=' '.join(header[dims:datepos]),accession=accession,**parsed)
            if re.search(r'statu|figur|model|head|sphinx|musician',title,re.I):f['work_type']='sculpture'
            elif re.search(r'Clay|Faience',medium,re.I):f['work_type']='ceramic'
            elif re.search(r'Bronze|Copper|Gold|Silver',medium,re.I):f['work_type']='metalwork'
            else:f['work_type']='unknown'
            f['holding_note']='Cyprus Museum lender credit and inventory in the Department of Antiquities official 2012 catalogue, printed page '+str(column['pdf_page'])+', catalogue '+str(number)+'. The Brussels temporary exhibition is not a present-display claim.'
            f['shared_source_url']=True;f['source_publication_year']=2012
            f['remaining_uncertainty']='Documented 2012 institutional holding; subsequent transfer and present display are not independently verified. Anonymous maker remains unknown. No image use inferred.'
            rows.append(f)
    assert len({x['source_id']for x in rows})==len(rows)
    h.save(R/'cyprus-museum-artwork-candidates.json',dict(records=rows,held=held,source_receipt=rc))
    print('Cyprus Museum',len(rows),'selected art objects;',len(held),'held',dict(collections.Counter(x['reason']for x in held)))
if __name__=='__main__':build()
