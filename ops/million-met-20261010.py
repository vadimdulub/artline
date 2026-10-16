#!/usr/bin/env python3
"""Conservative Met bulk metadata selection. Native evidence stays intact."""
import argparse,collections,csv,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('nga',Path(__file__).with_name('million-nga-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=m.RUN/'met';MID='a0673ec8-1b74-ebcb-0331-a1c021b793f6';SID=m.uid('source/met')
SCHEMES=['met-object','european-met-the-met-object'];PERSON_SCHEME='met-constituent'
SELECTION='selection-v2.json.gz'
CLASSES={'Paintings':'painting','Drawings':'drawing','Prints':'print','Photographs':'photograph','Sculpture':'sculpture','Drawings|Ornament & Architecture':'drawing','Prints|Ornament & Architecture':'print','Wood-Sculpture':'sculpture','Stone Sculpture':'sculpture','Calligraphy':'calligraphy'}
def dates(r):
    text=r['Object Date'].strip();literal=re.sub(r'^dated\s+','',text,flags=re.I)
    if r['Classification'].startswith('Prints'):literal=re.sub(r'^published\s+','',literal,flags=re.I)
    return n.dates(literal)
def creators(r):
    # This export repeats Constituent ID 1206 for unrelated named artists.
    # Do not use that column as a person key or to align the other fields.
    cols=['Artist Role','Artist Prefix','Artist Display Name','Artist Display Bio','Artist Suffix','Artist Alpha Sort','Artist Wikidata URL']
    length=len(r['Artist Display Name'].split('|'));values={k:r[k].split('|') if r[k].strip() else ['']*length for k in cols}
    if not r['Artist Display Name'] or any(len(v)!=length for v in values.values()):return []
    result=[]
    for i in range(length):
        d={k:v[i].strip() for k,v in values.items()}
        if not d['Artist Display Name']:continue
        qid=d['Artist Wikidata URL'].rsplit('/',1)[-1];qid=qid if re.fullmatch('Q[0-9]+',qid) else ''
        identity='qid-'+qid if qid else 'evidence-'+m.sha((m.norm(d['Artist Display Name'])+'|'+d['Artist Display Bio']).encode())[:24]
        result.append(dict(constituentid=identity,native_constituent_field=r['Constituent ID'],identity_basis='Derived from explicit artist Wikidata identifier' if qid else 'Derived name and literal biography evidence key; not a museum authority identifier',role=d['Artist Role'],prefix=d['Artist Prefix'],suffix=d['Artist Suffix'],forwarddisplayname=d['Artist Display Name'],preferreddisplayname=d['Artist Alpha Sort'],displaydate=d['Artist Display Bio'],wikidataid=qid,constituenttype='individual'))
    return result
def selection():
    dest=RUN/SELECTION
    if dest.exists():return
    path=m.DATA/'met/MetObjects.csv';receipt=m.load(m.RUN/'sources/met/MetObjects.csv.receipt.json');assert m.sha(path.read_bytes())==receipt['sha256'];rows=[];held=[];people=collections.defaultdict(list)
    with path.open(newline='',encoding='utf-8-sig') as f:
        for raw in csv.DictReader(f):
            reason=None;dt=dates(raw);oid=raw['Object ID']
            if raw['Classification'] not in CLASSES:reason='type_needs_separate_review'
            elif re.search(r'book|album|folio|leaf|leaves|negative|portfolio|fragment',raw['Object Name'],re.I):reason='physical_unit_or_component_review'
            elif re.search(r'\bverso\b',raw['Title'],re.I):reason='recto_verso_identity_review'
            elif not dt or dt[1]==1970 and 'circa' in dt[2]:reason='literal_date_requires_review_or_after_1970'
            elif not raw['Object Number'] or not raw['Title']:reason='identity_incomplete'
            if reason:held.append(dict(native_id=oid,reason=reason));continue
            cc=creators(raw)
            for c in cc:
                if c not in people[c['constituentid']]:people[c['constituentid']].append(c)
            qid=raw['Object Wikidata URL'].rsplit('/',1)[-1];qid=qid if re.fullmatch('Q[0-9]+',qid) else ''
            label='; '.join(' '.join([c['prefix'],c['forwarddisplayname'],c['suffix']]).strip() for c in cc) if cc else raw['Artist Display Name'] or raw['Culture']
            rows.append(dict(native_id=oid,artwork_id=m.uid('artwork/met/'+oid),title=raw['Title'],normalized_title=m.norm(raw['Title']),source_url='https://www.metmuseum.org/art/collection/search/'+oid,accession_number=raw['Object Number'],date_display=raw['Object Date'],first=dt[0],last=dt[1],precision=dt[2],work_type=CLASSES[raw['Classification']],medium=raw['Medium'],dimensions=raw['Dimensions'],creator_label=label,creators=cc,cultural_context=raw['Culture'],wikidata_id=qid,raw=raw))
    m.save(dest,dict(at=m.now(),source_receipt=receipt,selected=rows,people=dict(people),held=held,policy='Fine-art source classifications, explicit literal dates through 1970; unknown/broad/complex dates and inseparable unit risks held. Numeric search bounds preserved only as raw evidence. Source native IDs and accession numbers must be reconciled before production. Metadata only; no image downloads.'))
    print(json.dumps(dict(selected=len(rows),artist_authorities=len(people),held=collections.Counter(r['reason'] for r in held),types=collections.Counter(r['work_type'] for r in rows))),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['selection']);a=ap.parse_args();globals()[a.action]()
