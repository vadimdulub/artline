#!/usr/bin/env python3
"""Read-only draft transcription of the original 1933 Chicago catalogue.

No import command: OCR candidates, old attributions and subparts require review.
The captured library scan is independent of the held museum publications host.
"""
import json
import re
import sys
from pathlib import Path
import exhibitions_common as c

OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/chicago-1933'
SOURCE='https://archive.org/details/catalogueofcentu00arti'
EID='2cd58f72-a7e7-5e46-8018-5b208f0c70e4'
MEDIUM=re.compile(r'^(?:Oil|Tempera|Water\s*colou?r|Pastel|Pencil|Pen\b|Sepia|Wash|Charcoal|Chalk|Crayon|Silver.?point|Red chalk|Black chalk|Brush|Drawing|Line and|Gouache|Sanguine|Colored|Ink\b)',re.I)
NUMBER=re.compile(r'^([*†tTf|!§ilIO0-9]+[a-gA-G]?)\.\s*(.*)$')
SUBPART=re.compile(r'^([*†]?[b-g])\.\s*(.*)$')
STOP=re.compile(r'^(?:Lent\b|Owned\b|Signed\b|Inscribed\b|Marked\b|Coll[.:]|Ex[hH][.:]|Lit[.:])')


def artist_line(line):
    if ',' not in line:return False
    prefix=line.split(',',1)[0]
    letters=[x for x in prefix if x.isalpha()]
    nationality=re.search(r',\s*(?:American|French|German|Italian|English|Dutch|Flemish|Spanish|Swiss|Belgian|Russian|Polish|Austrian|Swedish|Norwegian|Danish|Portuguese)\b',line,re.I)
    if len(letters)<4 or (sum(x.isupper()for x in letters)/len(letters)<.80 and not nationality):return False
    if re.match(r'^(?:NESE|MAN|ISH|CAN|IAN|RAN|RINE),',line):return False
    return not re.match(r'^(?:GALLERY|GALLERIES|PAINTINGS|DRAWINGS|LIT|COLL|EXH|SIGNED|INSCRIBED)',prefix)


def join(lines):
    text=' '.join(lines)
    # Preserve OCR glyphs and factual uncertainties. Only rejoin explicit
    # end-of-line hyphenation; retain source lines in every candidate.
    return re.sub(r'(\w)- ([a-z])',r'\1\2',text).strip()


def token(value):
    cleaned=value.lstrip('*†tTf|!§').replace('l','1').replace('I','1').replace('O','0')
    match=re.fullmatch(r'(\d{1,4})([a-gA-G]?)',cleaned)
    if not match:return None
    return (int(match[1]),match[2].lower())


def extract():
    import pdfplumber
    rows=[]
    with pdfplumber.open(OUT/'catalogueofcentu00arti.pdf')as pdf:
        geometry={r['pdfPage']:r for r in c.load(OUT/'checklist-columns-v2.json')}
        for n in range(22,127):
            p=pdf.pages[n];g=geometry[n+1];mid=g['columnDivider'];heads=[]
            for line in p.extract_text_lines(x_tolerance=2,y_tolerance=3):
                text=line['text'];letters=[a for a in text if a.isalpha()]
                if 'PAINTING' in text and letters and sum(a.isupper()for a in letters)/len(letters)>.8 and line['x0']<mid<line['x1']:
                    heads.append(dict(text=text,top=line['top']))
            bounds=[0]+[h['top']-2 for h in heads if 50<h['top']<p.height-50]+[p.height-25]
            bounds=sorted(set(bounds));segments=[]
            for lo,hi in zip(bounds,bounds[1:]):
                if hi-lo<5:continue
                for col,(left,right)in enumerate([(0,mid),(mid,p.width)]):
                    text=p.crop((left,lo,right,hi)).extract_text(x_tolerance=2,y_tolerance=3)or''
                    segments.append(dict(column=col+1,top=lo,bottom=hi,text=text))
            rows.append(dict(pdfPage=n+1,printedPage=n-21,columnDivider=mid,dividerCost=g['dividerCost'],segments=segments,sectionHeadings=heads))
    c.save(OUT/'checklist-reading-order-v3.json',rows)
    print('Extracted 105 pages with section-band reading order; split pages:',[(r['pdfPage'],[h['text']for h in r['sectionHeadings']])for r in rows if len(r['segments'])>2],flush=True)


def draft():
    rows=c.load(OUT/'checklist-reading-order-v3.json');lines=[]
    assert len(rows)==105 and rows[0]['pdfPage']==23 and rows[-1]['pdfPage']==127
    for page in rows:
        for segment in page['segments']:
            lines.extend(dict(text=t.strip(),pdfPage=page['pdfPage'],printedPage=page['printedPage'],column=segment['column'],
                              bandTop=segment['top'],divider=page['columnDivider'],dividerCost=page['dividerCost'])for t in segment['text'].splitlines()if t.strip())
    candidates=[];rejected=[];last_artist=None;last_artist_at=-100;last_number=0;last_letter='';active=None
    for i,line in enumerate(lines):
        text=line['text']
        if artist_line(text):
            creator=[text];j=i+1
            # Creator headings can wrap nationalities/life dates. Keep their
            # literal text, rather than mistaking those dates for artwork dates.
            while j<len(lines)and j<=i+2:
                following=lines[j]['text']
                if NUMBER.match(following)or MEDIUM.match(following):break
                if re.match(r'^(?:\d{4}|c\.|before|after|man,|ish,|can,|nese,|r[a-z]*,|ian,|logne|School|Contempo|rary)',following,re.I):
                    creator.append(following);j+=1
                else:break
            last_artist=join(creator);last_artist_at=i
        match=NUMBER.match(text);parsed=token(match[1])if match else None
        sub=SUBPART.match(text)if parsed is None else None
        if parsed:
            number,letter=parsed;tail=match[2];raw_token=match[1]
        elif sub and last_letter:
            number,letter=last_number,sub[1].lstrip('*†');tail=sub[2];raw_token=sub[1]
        else:continue
        nearby_artist=i-last_artist_at<=4
        if number>1094 and str(number).startswith('1') and nearby_artist and tail:
            recovered=int(str(number)[1:])
            if last_number<recovered<=last_number+8:number=recovered
        subgroup=number==last_number and bool(letter)and letter>last_letter
        medium_near=any(MEDIUM.match(x['text'])for x in lines[i+1:i+6])
        sequence_ok=(number>last_number and number-last_number<=8)or subgroup
        if not(1<=number<=1094 and sequence_ok and (nearby_artist or subgroup or medium_near)):
            rejected.append(dict(**line,rawToken=raw_token,parsed=[number,letter],previous=last_number,reason='Candidate requires manual numbering/context review'))
            continue
        if active is not None:active['endLine']=i
        active=dict(catalogueNumber=str(number)+letter,number=number,suffix=letter,rawToken=raw_token,
            pdfPage=line['pdfPage'],printedPage=line['printedPage'],column=line['column'],startLine=i,
            creatorLabel=last_artist,creatorHeadingDistance=i-last_artist_at,titleLines=[tail]if tail else[],
            participation='catalogued',sourceURL=SOURCE,scope='painting'if line['printedPage']<=85 else'drawing_watercolour_pastel',
            flags=[],reviewState='unreviewed_ocr_candidate',dividerCost=line['dividerCost'])
        if number>last_number+1:active['flags'].append('number_gap_before')
        if not nearby_artist and not subgroup:active['flags'].append('creator_not_adjacent')
        if raw_token.lstrip('*†')!=str(number)+letter and not subgroup:active['flags'].append('number_ocr_normalized')
        if subgroup:active['flags'].append('shared_group_metadata')
        candidates.append(active);last_number,last_letter=number,letter
    if active:active['endLine']=len(lines)
    for item in candidates:
        segment=lines[item['startLine']:item['endLine']];body=[x['text']for x in segment[1:]]
        medium_index=next((i for i,x in enumerate(body)if MEDIUM.match(x)),None)
        if medium_index is None:
            item['flags'].append('medium_not_located');item['mediumLabel']=None
        else:
            title_more=body[:medium_index]
            if any(artist_line(x)or STOP.match(x)for x in title_more):item['flags'].append('title_boundary_ambiguous')
            item['titleLines'].extend(title_more)
            item['mediumLabel']=body[medium_index]
        item['titleLabel']=join(item['titleLines'])
        if not item['titleLabel']or len(item['titleLabel'])>220:item['flags'].append('title_length_review')
        if re.search(r'[\^{}\\]|\b(?:lY|Yz|WA)\b',item['titleLabel']):item['flags'].append('title_ocr_glyphs')
        item['rawLines']=segment
        item['creatorIdentity']=None;item['artworkID']=None
    covered={x['number']for x in candidates};missing=sorted(set(range(1,1095))-covered)
    result=dict(at=c.now(),exhibitionID=EID,sourceURL=SOURCE,edition='Third edition, fifth printing, 1933',
        pdfSHA256=c.sha((OUT/'catalogueofcentu00arti.pdf').read_bytes()),sourcePages=105,candidates=candidates,
        distinctBaseNumbers=len(covered),missingBaseNumbers=missing,rejectedNumberCandidates=rejected,
        knownExcludedSection=dict(firstNumber=1095,pdfPage=128,printedPage=106,reason='Sculpture'),
        publicationSymbols=dict(asterisk='Illustration exists; not itself proof of installation.',dagger='Offered for sale.'),
        productionWrites=False,realLocalDatabaseWrites=False,checklistComplete=False)
    c.save(OUT/'transcription-draft-v2.json',result)
    print('Draft candidates:',len(candidates),'distinct base numbers:',len(covered),'missing:',len(missing),'rejected:',len(rejected),flush=True)
    print('Missing numbers:',missing,flush=True)
    for x in candidates[:8]:print(x['catalogueNumber'],x['creatorLabel'],x['titleLabel'],x['flags'],flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['extract','draft']:raise SystemExit('Use extract or draft; no import action is implemented')
    globals()[sys.argv[1]]()
