#!/usr/bin/env python3
"""Pinned, offline historical exhibition discovery from the official AIC dump.

The cached archive was captured before the current museum-site access hold.
No requests to held museum routes, image acquisition, or local database writes.
"""
import collections
import datetime as dt
import difflib
import gzip
import json
import re
import sys
import tarfile
from pathlib import Path

from bs4 import BeautifulSoup
import exhibitions_common as c

OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012/aic-exhibitions'
ARCHIVE=Path.home()/'Library/Application Support/Artline/source-metadata/million-catalogue-20261010/aic/api-data.tar.bz2'
RECEIPT=c.ROOT/'docs/research/million-catalogue-20261010/sources/aic/api-data.tar.bz2.receipt.json'
OP='historical-exhibitions-aic-archive-20261012'
MID='9e75033c-8e6b-464b-974b-d94fcc91c6a3'
OBJECTS=ARCHIVE.parent/'artworks.jsonl.gz'
PICTORIAL=re.compile(r'\b(paintings?|drawings?|water[ -]?colou?rs?|prints?|etchings?|engravings?|lithographs?|woodcuts?|pastels?|aquatints?|mezzotints?|drypoints?|sketches|portraits?|miniatures?)\b',re.I)
OTHER=re.compile(r'\b(photographs?|photographers?|photography|photographic|sculptures?|sculptors?|textiles?|tapestr(?:y|ies)|needlework|ceramics?|pottery|rugs?|carpets?|furniture|jewelry|jewellery|costumes?|silver|architecture|architects?|architectural|metalwork|embroider(?:y|ed)|books?|bookbindings?|decorative|graphic design|posters?|advertising|postcards?|reproductions?|facsimiles?|commercial|schools?|students?|children|childhood|junior|industrial|designs?|chintzes|woodcarvings|bronzes|robes|wax|porcelain|rooms?|models?|negatives?|platinum)\b',re.I)
SPECIAL_HOLDS={
    4307:'Drawing/manual training association: original objects and event scope need review.',
    4733:'Drawing teachers association: original objects and event scope need review.',
    4960:'Drawing/manual training association: original objects and event scope need review.',
    3206:'Fund-class drawings: student collection scope needs review.',
    7304:'Decorator competition: pictorial versus applied design scope unresolved.',
    7306:'Child drawing exhibition: collection scope requires review.',
    8627:'Scholarship-class exhibition: student collection scope requires review.',
    4102:'George Platt Lynes portrait exhibition is photographic, not pictorial.',
    6101:'Ferrucci Portrait of a Warrior is a sculptural relief; not a painting.',
    7319:'Whistleriana portraits may include photographs; exact media unresolved.',
    7252:'Portrait medium not established in this title; photography remains possible.',
    3445:'Antiquarian portrait collection medium unresolved.',
    4449:'Benefit portrait exhibition medium needs original catalogue confirmation.',
    4512:'Benefit portrait exhibition medium needs original catalogue confirmation.',
}


def scope_reason(r):
    if r['status']!='Closed':return 'Source does not confirm a closed historical exhibition.'
    if not PICTORIAL.search(r['title']):return 'No explicit pictorial scope in this index title; further source review.'
    if OTHER.search(r['title']):return 'Non-pictorial, mixed, educational or applied-art scope needs individual review.'
    if r['nativeID']in SPECIAL_HOLDS:return SPECIAL_HOLDS[r['nativeID']]
    if re.search(r'\b(SAIC|Arts Club|Gallery of Art Interpretation|Symphony and Art|replica|copies|re-opened)\b',r['title'],re.I):return 'Venue, reproduction, educational or recurrence identity requires individual review.'
    if re.search(r'\b(at Wildenstein|Garfield Park|Renaissance Society|circulated by)\b',r['title'],re.I):return 'External venue or tour needs reconciliation; do not infer Chicago occurrence from archive ownership.'
    if r['last'][:4]>'1970':return 'Later historical exhibition: eligible through-1970 object content still needs review.'
    return None


def title_tokens(title):
    return set(c.norm(title).split())-set('the a an of by from in to at and on for with exhibition paintings painting drawings drawing prints print etchings etching water colors colour color collection art institute chicago annual'.split())


def discover():
    survey=c.load(OUT/'date-survey.json');existing=c.load(OUT/'existing-exhibition-audit.json')['exhibitions']
    decisions=[];selected=[]
    for r in survey['historicalCandidates']:
        reason=scope_reason(r)
        decisions.append(dict(nativeID=r['nativeID'],title=r['title'],reason=reason,action='held'if reason else'candidate'))
        if not reason:selected.append(r)
    duplicates=[]
    allrows=survey['historicalCandidates']
    for r in selected:
        rt=title_tokens(r['title']);rn=c.norm(r['title']);year=int(r['first'][:4]);hits=[]
        # Compare every same-period source row, including out-of-medium rows:
        # a differently titled mixed exhibition may still be the same event.
        for s in allrows:
            if s['nativeID']==r['nativeID']or abs(int(s['first'][:4])-year)>1:continue
            if s['first']>r['last']or r['first']>s['last']:continue
            st=title_tokens(s['title']);sn=c.norm(s['title'])
            common=rt&st;ratio=len(common)/max(1,min(len(rt),len(st)))
            if rn==sn or (len(common)>=2 and ratio>=.7)or difflib.SequenceMatcher(None,rn,sn).ratio()>=.82:
                hits.append(dict(kind='native',id=s['nativeID'],title=s['title'],first=s['first'],last=s['last']))
        for s in existing:
            if not s['start_year']or abs(s['start_year']-year)>2:continue
            st=title_tokens(s['title']);sn=c.norm(s['title']);common=rt&st
            if rn==sn or (common and min(len(rt),len(st))>0 and len(common)/min(len(rt),len(st))>=.8 and (len(common)>=2 or len(st)==1))or difflib.SequenceMatcher(None,rn,sn).ratio()>=.84:
                hits.append(dict(kind='existing',id=s['id'],title=s['title'],first=s['start_date'],last=s['end_date'],startYear=s['start_year'],endYear=s['end_year'],status=s['status']))
        if hits:duplicates.append(dict(nativeID=r['nativeID'],title=r['title'],first=r['first'],last=r['last'],hits=hits))
    c.save(OUT/'scope-discovery-v2.json',dict(at=c.now(),selected=selected,decisions=decisions,duplicateCandidates=duplicates,
        titleReview='Read 1,116 explicit-pictorial titles through 1970; review is of event scope, not artwork checklists. Post-1970 and mixed titles remain research candidates.'))
    print('Scope candidates',len(selected),'duplicate-review groups',len(duplicates),flush=True)
    # An exact title plus event-year and venue in one object-history paragraph
    # is only a candidate. Individual histories are reviewed before ingestion.
    candidates=[];byyear=collections.defaultdict(list)
    for r in selected:byyear[r['first'][:4]].append((r,' '+c.norm(r['title'])+' '))
    with gzip.open(OBJECTS,'rt')as f:
        for line in f:
            item=json.loads(line);o=item['data'];history=o.get('exhibition_history')or''
            if not history or o.get('artwork_type_title')not in ['Painting','Print','Drawing and Watercolor']:continue
            for para in re.split(r'\n\s*\n|</p>\s*<p[^>]*>',history):
                text=BeautifulSoup(para,'html.parser').get_text(' ',strip=True)
                if not re.search(r'Art Institute of Chicago|Chicago,? (?:the )?Art Institute',text,re.I):continue
                norm=' '+c.norm(text)+' '
                for year in set(re.findall(r'\b(?:18|19)\d{2}\b',text)):
                    for r,title in byyear.get(year,[]):
                        if title in norm:
                            candidates.append(dict(exhibitionNativeID=r['nativeID'],nativeID=o['id'],history=text,archiveMember=item['archive_member'],recordSHA256=item['record_sha256'],object=o))
    c.save(OUT/'exact-history-candidates.json.gz',dict(at=c.now(),objectSource=str(OBJECTS),objectSourceSHA256=c.sha(OBJECTS.read_bytes()),candidates=candidates))
    print('Exact-title history candidates',len(candidates),'events',len({r['exhibitionNativeID']for r in candidates}),'works',len({r['nativeID']for r in candidates}),flush=True)


def extract():
    receipt=c.load(RECEIPT);assert receipt['status']==200 and c.sha(ARCHIVE.read_bytes())==receipt['sha256']
    rows=[]
    with tarfile.open(ARCHIVE,'r:bz2')as archive:
        for member in archive:
            if not member.isfile()or not re.fullmatch(r'artic-api-data/json/exhibitions/\d+\.json',member.name):continue
            raw=archive.extractfile(member).read();data=json.loads(raw)
            assert data['api_model']=='exhibitions'and str(data['id'])==Path(member.name).stem
            rows.append(dict(archiveMember=member.name,recordSHA256=c.sha(raw),data=data))
    assert len(rows)==6259 and len({r['data']['id']for r in rows})==len(rows)
    c.save(OUT/'exhibitions.json.gz',dict(at=c.now(),archiveReceipt=receipt,records=rows))
    print('Extracted',len(rows),'exact exhibition records from the pinned cached archive.',flush=True)


def survey():
    source=c.load(OUT/'exhibitions.json.gz');years=collections.Counter();states=collections.Counter();historical=[];held=[]
    for item in source['records']:
        r=item['data'];states[r.get('status')]+=1
        try:
            first=dt.datetime.fromisoformat(r['aic_start_at']).date();last=dt.datetime.fromisoformat(r['aic_end_at']).date()
            assert 1600<=first.year<=last.year<=1989 and first<=last
        except (ValueError,TypeError,AssertionError):held.append(dict(nativeID=r['id'],title=r['title'],first=r.get('aic_start_at'),last=r.get('aic_end_at')));continue
        years[first.year]+=1
        historical.append(dict(nativeID=r['id'],title=r['title'],first=str(first),last=str(last),status=r['status'],artworkIDs=r['artwork_ids'],artistIDs=r['artist_ids'],documentIDs=r['document_ids'],description=r.get('short_description')))
    c.save(OUT/'date-survey.json',dict(at=c.now(),sourceSHA256=c.sha((OUT/'exhibitions.json.gz').read_bytes()),sourceRecords=len(source['records']),historicalCandidates=historical,dateHolds=held,years=dict(sorted(years.items())),states=states))
    print(json.dumps(dict(sourceRecords=len(source['records']),historicalCandidates=len(historical),dateHolds=len(held),states=states,firstYear=min(years),lastYear=max(years),withArtworkIDs=sum(bool(r['artworkIDs'])for r in historical),nativeArtworkRelations=sum(len(r['artworkIDs'])for r in historical))),flush=True)
    print('FIRST',json.dumps(sorted(historical,key=lambda r:r['first'])[:12],ensure_ascii=False),flush=True)


if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]not in ['extract','survey','discover']:raise SystemExit('Use extract, survey or discover')
    globals()[sys.argv[1]]()
