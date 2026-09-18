#!/usr/bin/env python3
"""Catalogue-wide coverage audit, bounded Wikimedia discovery and selection.

Only read-only catalogue queries. Images and database application are separate.
Each collection is scoped explicitly; unknown/qualified dates remain unresolved.
"""
import argparse, hashlib, importlib.util, json, re, time, unicodedata, uuid, fcntl
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlencode, urlparse
import requests

ROOT=Path(__file__).resolve().parent.parent
RUN=ROOT/'docs/research/wikimedia-catalogue-scan-20260913'
BACKUPS=Path('/Users/vadimdulub/Library/Application Support/Artline/backups/wikimedia-catalogue-scan-20260913')
spec=importlib.util.spec_from_file_location('fresco',ROOT/'ops/import-michelangelo-frescoes.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
core=base.core
SESSION=requests.Session()
SESSION.headers['User-Agent']='Artline/1.0 (https://github.com/vadimdulub/artline; selected catalogue research)'

# Reviewed names + official website P856 matches; umbrella portals, similarly
# named organisations, website entities and shared-host ambiguities excluded.
MAPPING={
 'byzantine-christian-museum-athens':'Q1018775', 'national-gallery-greece':'Q1167467',
 'state-russian-museum':'Q211043', 'moscow-kremlin-museums':'Q4304009',
 'pushkin-state-museum-fine-arts':'Q4872', 'kroller-muller-museum':'Q1051928',
 'museo-bellas-artes-valencia':'Q1748404', 'gallerie-accademia-venezia':'Q338330',
 'scrovegni-chapel':'Q963954', 'germanisches-nationalmuseum':'Q478695',
 'kunsthaus-zurich':'Q685038', 'staatliche-kunsthalle-karlsruhe':'Q658725',
 'museu-nacional-de-arte-antiga':'Q212459', 'musee-de-grenoble':'Q1952944',
 'ordrupgaard':'Q770918', 'museo-bellas-artes-sevilla':'Q2163496',
 'nationalmuseum-stockholm':'Q842858', 'van-gogh-museum':'Q224124',
 'tate':'Q430682', 'galleria-borghese':'Q841506', 'courtauld-gallery':'Q12110695',
 'museu-calouste-gulbenkian':'Q211262', 'museo-de-arte-moderno-mexico':'Q3032842',
 'musee-beaux-arts-rouen':'Q3086934', 'national-museum-cardiff':'Q1321874',
 'museum-boijmans-van-beuningen':'Q679527', 'skagens-museum':'Q3555520',
 'art-institute-of-chicago':'Q239303', 'fondation-beyeler':'Q673833',
 'hilma-af-klint-foundation':'Q104904877', 'cleveland-museum-of-art':'Q657415',
 'hamburger-kunsthalle':'Q169542', 'kunsthistorisches-museum':'Q95569',
 'musee-orsay':'Q23402', 'the-met':'Q160236', 'museum-of-fine-arts-ghent':'Q2365880',
 'musee-orangerie':'Q726781', 'mauritshuis':'Q221092',
 'musee-marmottan-monet':'Q1327886', 'musee-du-louvre':'Q19675',
 'national-museum-oslo':'Q1132918', 'museo-del-prado':'Q160112',
 'national-gallery-ireland':'Q2018379', 'national-gallery-london':'Q180788',
 'museo-thyssen-bornemisza':'Q176251', 'neue-pinakothek':'Q170152',
 'rijksmuseum':'Q190804', 'staedel-museum':'Q163804', 'uffizi':'Q51252',
 'statens-museum-for-kunst':'Q671384',
}

@contextmanager
def evidence_lock(identity):
    # Shared captures are immutable. Different country workers may request the
    # same source; serialize that exact key without serializing all research.
    folder=Path('/Users/vadimdulub/Library/Application Support/Artline/research-locks')
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/(core.sha((str(RUN)+'/'+identity).encode())+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(lock,fcntl.LOCK_UN)

def fetch(url):
    with evidence_lock(url):return fetch_locked(url)

def fetch_locked(url):
    key=core.sha(url.encode());path=RUN/'captures'/(key+'.json')
    if path.exists():
        data=json.loads(path.read_bytes())
        if 'error' not in data:return data, json.loads(path.with_suffix('.receipt.json').read_text())
    for attempt in range(4):
        time.sleep(1.2)
        try:r=SESSION.get(url,timeout=(15,65))
        except requests.RequestException:
            if attempt==3:raise
            time.sleep(5*(attempt+1));continue
        if r.status_code==429:
            wait=int(r.headers.get('Retry-After','60'));print('Wikimedia requests pause:',wait,'seconds',flush=True)
            time.sleep(min(wait,300));continue
        if r.status_code in (502,503,504):
            time.sleep(5*(attempt+1));continue
        r.raise_for_status();data=r.json()
        if data.get('error',{}).get('code')=='maxlag':time.sleep(10);continue
        if 'error' in data:raise ValueError(data['error'])
        assert len(r.content)<20_000_000
        receipt={'url':r.url,'retrieved_at':core.now(),'sha256':core.sha(r.content),'bytes':len(r.content)}
        core.save_new(path,r.content);core.save_new(path.with_suffix('.receipt.json'),receipt)
        return data,receipt
    raise RuntimeError('Source remains unavailable after respectful bounded retries')

def entities(ids):
    result={};receipts={}
    missing=[]
    for q in ids:
        path=RUN/'entities'/(q+'.json')
        if path.exists():
            cached=json.loads(path.read_text());result[q]=cached['entity'];receipts[q]=cached['receipt']
        else:missing.append(q)
    for start in range(0,len(missing),10):
        part=missing[start:start+10]
        data,receipt=fetch('https://www.wikidata.org/w/api.php?'+urlencode({'action':'wbgetentities','ids':'|'.join(part),'props':'labels|descriptions|aliases|claims|sitelinks','languages':'en|el|ru|fr|de|it|es|nl|sv|da|pt|nb|nn|pl|cs|hu|ro|uk|mul','format':'json','maxlag':5}))
        for q in part:
            with evidence_lock('entity/'+q):
                path=RUN/'entities'/(q+'.json')
                if path.exists():cached=json.loads(path.read_text())
                else:
                    cached={'entity':data['entities'][q],'receipt':receipt};core.save_new(path,cached)
                result[q]=cached['entity'];receipts[q]=cached['receipt']
    return result,receipts

def claims(entity,prop):
    values=[x for x in entity.get('claims',{}).get(prop,[]) if x.get('rank')!='deprecated' and x.get('mainsnak',{}).get('snaktype')=='value']
    preferred=[x for x in values if x.get('rank')=='preferred']
    return preferred or values

def value(claim):return claim['mainsnak']['datavalue']['value']
def values(entity,prop):return [value(c) for c in claims(entity,prop)]
def label(entity):
    names=entity.get('labels',{})
    # Wikidata may store an internationally shared name only under `mul`.
    # Prefer it to whichever translated label happens to arrive first.
    return names.get('en',{}).get('value') or names.get('mul',{}).get('value') or next((x['value'] for x in names.values()),entity.get('id',''))
def norm(text):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKD',text.casefold()),re.UNICODE))
def labels(entity):return list(dict.fromkeys([x['value'] for x in entity.get('labels',{}).values()]+[x['value'] for group in entity.get('aliases',{}).values() for x in group]))

def year(entity,prop):
    cs=claims(entity,prop)
    years=set()
    if not cs:return None
    for c in cs:
        v=value(c)
        # P7452 explains why a statement has preferred rank; it does not make
        # an otherwise exact date approximate. Keep every temporal qualifier
        # conservative, including circa and earliest/latest bounds.
        if set(c.get('qualifiers',{}))-{'P7452'} or not isinstance(v,dict) or v.get('precision',0)<9 or v.get('before',0) or v.get('after',0):return None
        match=re.match(r'^\+(\d+)-',v.get('time',''))
        if not match:return None
        years.add(int(match[1]))
    return next(iter(years)) if len(years)==1 else None

def date(entity):
    y=year(entity,'P571')
    if y:return {'first':y,'last':y,'precision':'exact','display':str(y),'eligible':1100<=y<=1970}
    cs=claims(entity,'P571')
    if len(cs)==1:
        c=cs[0];v=value(c);qs=c.get('qualifiers',{})
        allowed={'P1319','P1326','P580','P582','P1480'}
        def bound(properties):
            found=[]
            for prop in properties:
                for snak in qs.get(prop,[]):
                    x=snak.get('datavalue',{}).get('value',{})
                    if not isinstance(x,dict) or x.get('precision',0)<9 or x.get('before',0) or x.get('after',0):return None
                    match=re.match(r'^\+(\d+)-',x.get('time',''))
                    if not match:return None
                    found.append(int(match[1]))
            return found[0] if found and len(set(found))==1 else None
        first,last=bound(('P1319','P580')),bound(('P1326','P582'))
        circa=bool(qs.get('P1480'))
        valid_circa=not circa or all(x.get('datavalue',{}).get('value',{}).get('id')=='Q5727902' for x in qs['P1480'])
        if first is not None and last is not None and first<=last and set(qs)<=allowed and valid_circa:
            precision=('circa' if first==last else 'circa_range') if circa else ('exact' if first==last else 'range')
            return {'first':first,'last':last,'precision':precision,'display':('c. ' if circa else '')+str(first)+('–'+str(last) if first!=last else ''),'eligible':1100<=first<=last<=1970}
        if isinstance(v,dict) and v.get('precision',0)>=9 and not v.get('before',0) and not v.get('after',0):
            match=re.match(r'^\+(\d+)-',v.get('time',''))
            if match and set(qs)=={'P1480'} and all(x.get('datavalue',{}).get('value',{}).get('id')=='Q5727902' for x in qs['P1480']):
                y=int(match[1]);return {'first':y,'last':y,'precision':'circa','display':'c. '+str(y),'eligible':1100<=y<=1970}
    return {'first':None,'last':None,'precision':'unknown','display':'Creation date under review','eligible':False}

def collection_mapping(audit):
    inst={i['slug']:i for i in audit['institutions']}
    mapping=dict(MAPPING)
    museofile=json.loads((RUN/'museofile-authority-matches.json').read_text())['results']['bindings']
    byid={}
    for row in museofile:byid.setdefault(row['id']['value'].lower(),set()).add(row['museum']['value'].rsplit('/',1)[-1])
    for slug in inst:
        ids=byid.get(slug.removeprefix('joconde-'),set())
        if slug.startswith('joconde-') and len(ids)==1:mapping[slug]=next(iter(ids))
    return mapping

def discover():
    audit=json.loads((RUN/'local-catalogue-audit.json').read_text())
    matches=json.loads((RUN/'website-authority-matches.json').read_text())
    matched={x['museum']['value'].rsplit('/',1)[-1] for x in matches}
    inst={i['slug']:i for i in audit['institutions']}
    assert set(MAPPING.values())<=matched
    mapping=collection_mapping(audit)
    canonical={}
    for slug,qid in mapping.items():canonical.setdefault(qid,slug)
    reviewed=[];allworks={}
    for qid,slug in canonical.items():
        path=RUN/'discovery'/(slug+'.json')
        if path.exists():record=json.loads(path.read_text())
        else:
            query=f'SELECT DISTINCT ?work WHERE {{ ?work wdt:P195 wd:{qid}; wdt:P31 wd:Q3305213; wdt:P18 ?image. }} ORDER BY ?work LIMIT '+('20' if slug.startswith('joconde-') else '150')
            data,receipt=fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
            ids=[x['work']['value'].rsplit('/',1)[-1] for x in data['results']['bindings']]
            record={'institution':inst[slug],'qid':qid,'works':ids,'bounded':True,'illustrated_objects_scan_cap':500,'painting_candidate_cap':150,'receipt':receipt}
            core.save_new(path,record)
        record['related_institution_ids']=[inst[s]['id'] for s,q in mapping.items() if q==qid]
        record['related_institution_slugs']=[s for s,q in mapping.items() if q==qid]
        reviewed.append(record)
        for q in record['works']:allworks.setdefault(q,[]).append(slug)
        print('Discovered',slug,len(record['works']),'illustrated painting candidates',flush=True)
    coverage=[{'institution':i['name'],'slug':i['slug'],'artworks':i['artworks'],'images':i['images'],'wikimedia_status':'verified_identity_and_bounded_discovery' if i['slug'] in mapping else 'identity_requires_further_review'} for i in audit['institutions']]
    core.save_new(RUN/'collection-coverage.json',coverage)
    core.save_new(RUN/'discovery-index.json',{'collections':reviewed,'unique_candidate_works':len(allworks)})

def research():
    partial=not (RUN/'discovery-index.json').exists()
    if partial:
        audit=json.loads((RUN/'local-catalogue-audit.json').read_text());mapping=collection_mapping(audit)
        inst={i['slug']:i for i in audit['institutions']};canonical={}
        for slug,q in mapping.items():canonical.setdefault(q,slug)
        index={'collections':[]}
        for q,slug in canonical.items():
            path=RUN/'discovery'/(slug+'.json')
            if path.exists():
                record=json.loads(path.read_text());record['related_institution_ids']=[inst[s]['id'] for s,v in mapping.items() if v==q];record['related_institution_slugs']=[s for s,v in mapping.items() if v==q];index['collections'].append(record)
    else:index=json.loads((RUN/'discovery-index.json').read_text())
    with_additions=(RUN/'additional-collections.json').exists()
    if with_additions:index['collections'].extend(json.loads((RUN/'additional-collections.json').read_text()))
    allselected=[];deferred=[]
    with base.connect(False) as db:
        db.execute('SET default_transaction_read_only=on')
        for collection in index['collections']:
            slug=collection['institution']['slug'];output=RUN/'selected'/(slug+'.json')
            if output.exists():
                old=json.loads(output.read_text());allselected.extend(old['selected']);deferred.extend(old['deferred']);continue
            # Inspect metadata in a bounded first tranche, preserving discovery
            # cursors for remaining IDs rather than downloading whole oeuvres.
            metadata_limit=10 if slug.startswith('joconde-') else 50
            selection_limit=2 if slug.startswith('joconde-') else 12
            ids=collection['works'][:metadata_limit]
            if not ids:continue
            es,receipts=entities(ids)
            creatorids=sorted({v['id'] for e in es.values() for v in values(e,'P170') if isinstance(v,dict) and 'id' in v})
            creators,creator_receipts=entities(creatorids) if creatorids else ({},{})
            inventory=db.execute('''SELECT a.id::text,a.slug,a.title,a.alternate_title,a.normalized_title,a.accession_number,a.work_type,a.primary_media_id::text,a.creation_year_start,a.creation_year_end,a.date_precision,a.status,a.revision,
              COALESCE((SELECT jsonb_agg(e.external_id) FROM artwork_artists aa JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=aa.artist_id AND e.scheme='wikidata' WHERE aa.artwork_id=a.id),'[]') creators,
              COALESCE((SELECT jsonb_agg(p.display_name) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') creator_names
              FROM artworks a WHERE a.current_institution_id=ANY(%s::uuid[])''',(collection.get('related_institution_ids',[collection['institution']['id']]),)).fetchall()
            byaccess={};bytitle={}
            for row in inventory:
                if row['accession_number']:byaccess.setdefault(row['accession_number'].strip().casefold(),[]).append(row)
                for title in (row['title'],row['alternate_title']):
                    if title:bytitle.setdefault(norm(title),[]).append(row)
            selected=[];reasons=[]
            for qid in ids:
                e=es[qid];reason=None;d=date(e)
                if e.get('id')!=qid:reason='redirected_or_missing_identity'
                if d['first'] is not None and not d['eligible']:reason='outside_1100_1970_scope'
                holdings=[c for c in claims(e,'P195') if value(c).get('id')==collection['qid'] and 'P582' not in c.get('qualifiers',{})]
                if len(holdings)!=1:reason='holding_ambiguous_or_historical'
                cs=claims(e,'P170')
                if len(cs)>1 or any(c.get('qualifiers') for c in cs):reason='qualified_or_multiple_creators_require_review'
                cq=value(cs[0])['id'] if len(cs)==1 else None
                creator=creators.get(cq,{}) if cq else {}
                if cq and (creator.get('id')!=cq or cq.startswith('Q') and label(creator)==cq):reason='unresolved_creator_identity'
                # Anonymous icons stay actual object records, without a fabricated person.
                anonymous=not cq or bool(re.search(r'\b(anonymous|unknown|unidentified)\b',label(creator),re.I))
                if anonymous and slug not in ('byzantine-christian-museum-athens','moscow-kremlin-museums','state-russian-museum'):reason='anonymous_nonpriority_attribution_needs_review'
                accession=list(dict.fromkeys(v for v in values(e,'P217') if isinstance(v,str)))
                exact={r['id']:r for x in accession for r in byaccess.get(x.strip().casefold(),[])}
                if len(exact)>1:reason='ambiguous_existing_accession'
                existing=next(iter(exact.values())) if len(exact)==1 else None
                titlehits={r['id']:r for t in labels(e) for r in bytitle.get(norm(t),[]) if (cq and cq in r['creators']) or set(norm(n) for n in r['creator_names']) & set(norm(n) for n in labels(creator))}
                if existing and cq and existing['creators'] and cq not in existing['creators']:reason='existing_accession_creator_conflict'
                if not existing and len(titlehits)==1:existing=next(iter(titlehits.values()))
                elif not existing and len(titlehits)>1:reason='ambiguous_existing_title_creator'
                if existing and existing['primary_media_id']:reason='existing_image_preserved'
                globalid=db.execute("SELECT entity_type,entity_id::text FROM external_identifiers WHERE scheme='wikidata' AND external_id=%s",(qid,)).fetchone()
                if globalid and (not existing or globalid['entity_id']!=existing['id']):reason='existing_global_authority_requires_reconciliation'
                if existing and existing['status']=='archived':reason='archived_record_preserved'
                if reason:
                    reasons.append({'qid':qid,'collection':slug,'reason':reason});continue
                record={'qid':qid,'title':label(e),'titles':labels(e),'date':d,'entity':e,'entity_receipt':receipts[qid],
                  'creator_qid':None if anonymous else cq,'creator_label':'Anonymous' if anonymous else label(creator),'creator_entity':creator,'creator_receipt':creator_receipts.get(cq),
                  'collection':collection,'holding_statement':holdings[0],'accession':accession[0] if len(accession)==1 else None,'images':values(e,'P18'),'existing_local':existing}
                selected.append(record)
                if len(selected)>=selection_limit:break
            core.save_new(output,{'selected':selected,'deferred':reasons,'metadata_inspected':len(ids),'discovery_remaining':max(0,len(collection['works'])-len(ids))})
            allselected.extend(selected);deferred.extend(reasons)
            print('Selected',slug,len(selected),'works; existing',sum(bool(r['existing_local']) for r in selected),flush=True)
    output='metadata-selection-partial-'+str(len(index['collections']))+'.json' if partial else ('metadata-selection-with-additions.json' if with_additions else 'metadata-selection.json')
    core.save_new(RUN/output,{'selected':allselected,'deferred':deferred})
    print('Metadata selected',len(allselected),'works from',len(index['collections']),'collections',flush=True)

def additional():
    authorities=json.loads((RUN/'additional-museum-authorities.json').read_text())
    records=[]
    for row in authorities:
        qid=row['qid'];slug='wikimedia-museum-'+qid.lower();website=values(row['entity'],'P856')[0]
        iid=str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/wikimedia-catalogue/institution/'+qid))
        query=f'SELECT DISTINCT ?work WHERE {{ ?work wdt:P195 wd:{qid}; wdt:P31 wd:Q3305213; wdt:P18 ?image. }} ORDER BY ?work LIMIT 150'
        data,receipt=fetch('https://query.wikidata.org/sparql?'+urlencode({'query':query,'format':'json'}))
        ids=[x['work']['value'].rsplit('/',1)[-1] for x in data['results']['bindings']]
        institution={'id':iid,'slug':slug,'name':row['name'],'website_url':website,'wikidata_id':qid,'new_institution':True,'authority_receipt':row['receipt']}
        record={'institution':institution,'qid':qid,'works':ids,'bounded':True,'painting_candidate_cap':150,'receipt':receipt,'related_institution_ids':[iid],'related_institution_slugs':[slug]}
        records.append(record);core.save_new(RUN/'discovery'/(slug+'.json'),record)
        print('Additional collection',row['name'],len(ids),'painting candidates',flush=True)
    core.save_new(RUN/'additional-collections.json',records)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['discover','research','additional']);a=p.parse_args()
    {'discover':discover,'research':research,'additional':additional}[a.phase]()
