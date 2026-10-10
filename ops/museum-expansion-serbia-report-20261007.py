#!/usr/bin/env python3
"""Selected inventory-bearing Serbian report entries; never date works by loans."""
import hashlib
import importlib.util
import re
import subprocess
from pathlib import Path

spec=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-serbia-20261007.py'))
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
m=s.m;RUN=s.RUN
PDF=RUN/'annual-report-2015.pdf'


def page_rows():
    text=subprocess.check_output(['pdftotext','-f','56','-l','56','-layout',str(PDF),'-'],text=True)
    assert 'Коме позамљујемо: Музеју рудничко-таковског краја' in text
    assert 'Коме позамљујемо: Историјском музеју Србије' in text
    assert 'Збирка српског сликарства 18. и 19.' in text
    rows=[];section='obrenovic'
    for line in text.splitlines():
        if 'МИХАИЛО ИДВОРСКИ ПУПИН' in line:section='pupin'
        match=re.match(r'^\s*(\d+)\.\s+(.+?)\s*(?:инв\.?\s*(?:бр\.?\s*)?|Инв\.\s*)(.+?)\s*$',line)
        if not match:continue
        number=int(match[1]);description=match[2].strip();inventory=match[3].strip()
        creator,rest=description.split(', ',1)
        title,date=rest.rsplit(', ',1)
        rows.append(dict(section=section,number=number,literal_line=line.strip(),creator_label=creator,title=title,date=date,inventory=inventory))
    assert [r['number'] for r in rows if r['section']=='obrenovic']==list(range(1,15))
    assert [r['number'] for r in rows if r['section']=='pupin']==list(range(1,11))
    return text,rows


def facts(row,url):
    dates=s.creation_date(row['date'])
    if not dates:return None,'creation_date_requires_review'
    if row['section']=='pupin' and row['number'] in [6,7]:return None,'gallery_or_virtual_identity_overlap'
    return dict(title=row['title'],creator_label=row['creator_label'],date_display=row['date'],first=dates[0],last=dates[1],date_precision=dates[2],
        work_type='unknown',medium=None,dimensions=None,accession=row['inventory'],source_url=url+'#page=56',
        holding_basis='National Museum in Belgrade annual report for 2015, printed page 55 (PDF page 56), explicitly lists this inventory among objects lent FROM its Serbian 18th/19th-century collection. The borrowing institution is an exhibition venue, not assigned as owner. This is dated 2015 collection evidence, not a fresh current-display or legal-ownership claim. Individual medium and object type are not supplied; unknowns retained.'),None


def research():
    dest=RUN/'serbia-report-001-research.json.gz';assert not dest.exists()
    receipt=m.load(PDF.with_suffix('.receipt.json'));raw=PDF.read_bytes();assert hashlib.sha256(raw).hexdigest()==receipt['sha256']
    text,rows=page_rows();baseline=m.load(RUN/'serbia-001-before.json');records=[];held=[]
    cap=dict(receipt, status=200,retrieved_at=receipt['at'])
    for row in rows:
        f,reason=facts(row,receipt['url']);oid='report-2015-p55-'+row['section']+'-'+str(row['number'])
        original=dict(report_entry=row,printed_page=55,pdf_page=56,page_text=text,source_document_year=2015)
        if reason:held.append(dict(source_record_id=oid,reason=reason,raw_source_record=original));continue
        records.append(dict(source_record_id=oid,museum=baseline['museum'],facts=f,source_receipt=cap,body_path=str(PDF.relative_to(m.ROOT)),raw_source_record=original))
    m.save(dest,dict(at=m.now(),records=records,held=held,before=baseline['before'],policy='Twenty-four explicitly inventoried lines on one visually reviewed annual-report page. Two overlaps and one unbounded creation date excluded. Unknown individual medium/type retained, including the possibly photographic Queen Draga entry. Creator qualifications remain literal. Research only; no catalogue changes.'))
    print('Report research:',len(records),'candidates;',len(held),'holds')


def validate_record(record,raw):
    assert hashlib.sha256(raw).hexdigest()==record['source_receipt']['sha256']
    assert record['museum']['slug']==s.SLUG
    original=record['raw_source_record'];text,rows=page_rows();row=original['report_entry']
    assert row in rows and text==original['page_text']
    assert original['source_document_year']==2015 and original['printed_page']==55 and original['pdf_page']==56
    assert record['source_record_id']=='report-2015-p55-'+row['section']+'-'+str(row['number'])
    f,reason=facts(row,record['source_receipt']['url']);assert not reason,reason
    return f


if __name__=='__main__':research()
