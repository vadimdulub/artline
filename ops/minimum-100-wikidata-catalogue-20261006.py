#!/usr/bin/env python3
"""Bounded museum-scoped painting/icon metadata, full statements checked before import."""
import argparse,ast,collections,datetime,gzip,importlib.util,json,re,time
import requests
from pathlib import Path
from urllib.parse import urlencode
s=importlib.util.spec_from_file_location('minimum',Path(__file__).with_name('all-museums-minimum-100-20261006.py'))
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
w=c.module('minimum_wd_links','minimum-100-wikidata-links-20261006.py')
ROOT=c.RUN/'wikidata-catalogue';c.h.RUN=ROOT
KINDS={'Q3305213','Q132137'}
API_LAST=0
UA='ArtlineMuseumResearch/1.0 (+https://github.com/vadimdulub/artline; selected museum catalogue metadata)'
CAPTURE_CACHE={}


def save_bytes(path,raw):
    assert isinstance(raw,bytes)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw,'Preserve source bytes: '+str(path)
    else:path.write_bytes(raw)


def label(entity):
    values=entity.get('labels',{})
    for lang in ['en','fr','de','it','es','el','ru','nl','pt']:
        if lang in values:return values[lang]['value']
    return next(iter(values.values()))['value']if values else None


def fields(entity,museum,creators,receipt):
    claims=w.active(entity,'P195')
    if len(claims)!=1 or w.value(claims[0])!={'entity-type':'item','numeric-id':int(museum['wikidata_id'][1:]),'id':museum['wikidata_id']}:return None,'museum_collection_identity_conflict'
    cl=claims[0]
    if cl.get('qualifiers')and not w.allowed_qualifiers(cl,receipt):return None,'qualified_collection_requires_review'
    if not any(ref.get('snaks',{}).get('P854')or ref.get('snaks',{}).get('P248')for ref in cl.get('references',[])):return None,'collection_reference_required'
    types={w.value(x).get('id')for x in w.active(entity,'P31')if isinstance(w.value(x),dict)}
    if not types or not types<=KINDS:return None,'specific_object_type_requires_review'
    if w.active(entity,'P361')or w.active(entity,'P527'):return None,'part_or_ensemble_requires_review'
    dates=w.active(entity,'P571')
    if len(dates)!=1 or dates[0].get('qualifiers'):return None,'creation_statement_requires_review'
    date=w.value(dates[0]);match=re.fullmatch(r'\+(\d{4})-(\d\d)-(\d\d)T00:00:00Z',date.get('time',''))if isinstance(date,dict)else None
    if not match or date.get('precision')not in {9,10,11}or date.get('before')or date.get('after')or not 100<=int(match[1])<=1970:return None,'creation_precision_or_cutoff_requires_review'
    if date.get('calendarmodel')!='http://www.wikidata.org/entity/Q1985727':return None,'creation_calendar_requires_review'
    try:
        if date['precision']>=10:datetime.date(int(match[1]),int(match[2]),int(match[3])if date['precision']==11 else 1)
    except ValueError:return None,'invalid_source_calendar_date'
    title=label(entity)
    if not title:return None,'missing_source_title'
    artists=w.active(entity,'P170');names=[]
    for artist in artists:
        if artist.get('qualifiers')or not isinstance(w.value(artist),dict):return None,'creator_attribution_requires_review'
        q=w.value(artist).get('id');name=label(creators.get(q,{}))
        if not name:return None,'creator_label_requires_review'
        names.append(name)
    inventory=[str(w.value(x))for x in w.active(entity,'P217')if isinstance(w.value(x),str)and not x.get('qualifiers')]
    inventory.extend(x['datavalue']['value']for x in cl.get('qualifiers',{}).get('P217',[]))
    # Anonymous icons remain real review objects when museum/date evidence is
    # explicit. No invented named painter, medium, dimensions or image.
    display=match[1]if date['precision']==9 else '-'.join(match.groups()[:2])if date['precision']==10 else '-'.join(match.groups())
    return dict(title=title,creator_label='; '.join(names)or None,first=int(match[1]),last=int(match[1]),date_precision='exact',date_display=display,
        work_type='painting',object_form='icon'if 'Q132137'in types else None,medium=None,dimensions=None,accession='; '.join(sorted(set(inventory)))or None,
        source_url='https://www.wikidata.org/wiki/'+entity['id'],holding_basis='Wikidata explicitly records this individual painting/icon in the existing museum authority through one non-deprecated referenced collection statement. Original creation precision, qualifiers, creator identities and source references retained. Secondary-source documented collection connection; not an independent verification of referenced documents, legal ownership or current display.'),None


def checked_capture(rc):
    key=(rc['body_path'],rc['sha256'])
    if key in CAPTURE_CACHE:return CAPTURE_CACHE[key]
    raw=gzip.decompress((c.ROOT/rc['body_path']).read_bytes())
    if c.d.sha(raw)==rc['sha256']:
        CAPTURE_CACHE[key]=(raw,rc);return raw,rc
    # An early writer JSON-encoded the repr of gzip bytes. Recover losslessly,
    # retaining that original artifact and proving the original response hash.
    encoded=ast.literal_eval(json.loads(raw));assert isinstance(encoded,bytes)
    recovered=gzip.decompress(encoded);assert c.d.sha(recovered)==rc['sha256']and len(recovered)==rc['bytes']
    body=ROOT/'recovered-captures'/(rc['sha256']+'.body.gz')
    save_bytes(body,encoded)
    corrected=dict(rc,body_path=str(body.relative_to(c.ROOT)),encoding_recovery=dict(original_encoded_body_path=rc['body_path'],original_response_sha256_verified=True,description='Lossless removal of a JSON/string/gzip wrapper; original encoded artifact retained. Source bytes and retrieval date unchanged.'))
    c.save(body.with_suffix('.receipt.json'),corrected)
    CAPTURE_CACHE[key]=(recovered,corrected);return recovered,corrected


def native_urls(entity):
    result=set()
    for prop in ['P6002','P1679','P347']:
        for claim in w.active(entity,prop):
            v=w.value(claim)
            if not isinstance(v,str)or claim.get('qualifiers'):continue
            if prop=='P6002'and re.fullmatch(r'[^/]+/[^/]+',v):result.add('https://www.wikiart.org/en/'+v)
            elif prop=='P1679'and re.fullmatch(r'[a-z0-9-]+-\d+',v):result.add('https://artuk.org/discover/artworks/'+v)
            elif prop=='P347'and re.fullmatch(r'[A-Za-z0-9]+',v):
                for host in ['pop.culture.gouv.fr','www.pop.culture.gouv.fr']:result.add('https://'+host+'/notice/joconde/'+v)
    return sorted(result)


def entity_capture(url):
    """Compliant identified client, below ten requests/minute, one delayed retry."""
    global API_LAST
    key=c.d.sha(url.encode());dest=ROOT/'captures'/(key+'.json')
    if dest.exists():
        rc=c.load(dest);raw,rc=checked_capture(rc)
        if rc['status']==200:return raw,rc
        if rc['status']!=429:raise ValueError('Retained unsuccessful entity response: '+str(rc['status']))
        # Preserve the denied request. Retry once after ten minutes, under the
        # same identity and endpoint, at a rate below the strictest API tier.
        stamp=datetime.datetime.fromisoformat(rc['retrieved_at'].replace('Z','+00:00')).timestamp()
        until=stamp+max(600,int(rc.get('retry_after')or 0))
        dest=ROOT/'retry-after-backoff-001'/'captures'/(key+'.json')
        if dest.exists():
            return checked_capture(c.load(dest))
        while time.time()<until:
            print('Respecting API backoff; seconds remaining',int(until-time.time()),flush=True);time.sleep(min(55,until-time.time()))
    time.sleep(max(0,API_LAST+6.5-time.monotonic()));API_LAST=time.monotonic()
    with requests.get(url,headers={'User-Agent':UA},timeout=(15,60),stream=True)as response:
        raw=b''
        for part in response.iter_content(65536):raw+=part;assert len(raw)<8_000_000
        body=dest.with_suffix('.body.gz');rc=dict(url=url,final_url=response.url,status=response.status_code,sha256=c.d.sha(raw),bytes=len(raw),retrieved_at=c.d.now(),body_path=str(body.relative_to(c.ROOT)),retry_after=response.headers.get('Retry-After'),user_agent=UA,request_spacing_seconds=6.5)
    save_bytes(body,gzip.compress(raw,mtime=0));c.save(dest,rc);return raw,rc


def entities(ids):
    out={}
    for part in c.d.chunks(sorted(set(ids)),25):
        url='https://www.wikidata.org/w/api.php?'+urlencode(dict(action='wbgetentities',ids='|'.join(part),props='labels|aliases|claims',format='json'))
        raw,rc=entity_capture(url);assert rc['status']==200,('entity_api_http',rc['status'])
        data=json.loads(raw);assert 'entities'in data,data.get('error')
        for q,e in data['entities'].items():out[q]=dict(entity=e,receipt=rc)
        if len(out)%100==0:print('Wikidata selected entity metadata',len(out),'/',len(set(ids)),flush=True)
    return out


def index_history():
    """Continue capped museum pages; do not discard museums after one page."""
    history=collections.defaultdict(list)
    for path in sorted(ROOT.glob('*/index-evidence.json.gz')):
        for item in c.load(path)['evidence']:history[item['museum']['id']].append(item)
    # Different campaign prefixes do not sort chronologically. Page depth is
    # authoritative; source capture time orders equivalent-depth observations.
    for pages in history.values():pages.sort(key=lambda x:(x.get('page_number',1),x['receipt']['retrieved_at']))
    return history


def next_cursor(pages):
    if not pages:return '',None
    # A museum-specific metadata research budget, not an exhaustive download.
    if len(pages)>=5:return None,'five_bounded_metadata_pages_reviewed'
    latest=pages[-1]
    if not latest['capped']or not latest['selected_ids']:return None,'source_index_exhausted'
    return max(latest['selected_ids']),None


def index_query(museum_qid,bound,cursor=''):
    assert re.fullmatch(r'Q\d+',museum_qid)and 1<=bound<=250
    after=''
    if cursor:
        assert re.fullmatch(r'Q\d+',cursor)
        after=' FILTER(STR(?work) > "http://www.wikidata.org/entity/'+cursor+'")'
    return 'SELECT DISTINCT ?work WHERE { VALUES ?museum { wd:'+museum_qid+' } VALUES ?kind { wd:Q3305213 wd:Q132137 } ?work wdt:P195 ?museum; wdt:P31 ?kind; wdt:P571 ?date . FILTER(?date < "1971-01-01T00:00:00Z"^^xsd:dateTime)'+after+' } ORDER BY STR(?work) LIMIT '+str(bound)


def research(wave,limit,target_count=100):
    dest=ROOT/wave/'selected-museums.json';held=[]
    if dest.exists():selection=c.load(dest)
    else:
        byq=collections.Counter(x['institution'].get('wikidata_id')for x in c.BASE.values())
        projected={iid:0 for iid,x in c.BASE.items()if x['institution'].get('wikidata_id')and byq[x['institution']['wikidata_id']]==1}
        with c.d.connect()as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            for part in c.d.chunks(list(projected),100):
                projected.update({x['id']:x['n']for x in db.execute("SELECT current_institution_id::text id,count(*)n FROM artworks WHERE current_institution_id=ANY(%s::uuid[])AND status<>'archived'GROUP BY current_institution_id",(part,))})
            pending={x['artwork_id']:x['institution']['id']for name in ['wikidata-001','wikidata-002']for x in c.load(c.RUN/'links'/name/'claims.json.gz')['claims']}
            for part in c.d.chunks(list(pending),500):
                for x in db.execute('SELECT id::text FROM artworks WHERE id=ANY(%s::uuid[])AND current_institution_id IS NULL',(part,)):
                    if pending[x['id']]in projected:projected[pending[x['id']]]+=1
        history=index_history();selection=[];source_outcomes=[]
        for iid,x in c.BASE.items():
            if iid not in projected or projected[iid]>=100:continue
            if re.search(r'horlivka|sevastopol|roerich.*moscow',x['institution']['name'],re.I):
                source_outcomes.append(dict(museum_id=iid,reason='historical_or_displaced_collection_requires_specific_review'));continue
            cursor,reason=next_cursor(history[iid])
            if reason:source_outcomes.append(dict(museum_id=iid,reason=reason));continue
            selection.append(dict(museum=x['institution'],projected_count=projected[iid],cursor=cursor,page_number=len(history[iid])+1))
        c.save(ROOT/wave/'source-outcomes.json',source_outcomes)
        selection=sorted(selection,key=lambda x:(-x['projected_count'],x['museum']['name']))[:limit];c.save(dest,selection)
    candidates=[];index_evidence=[]
    for n,selected in enumerate(selection,1):
        museum=selected['museum'];mq=museum['wikidata_id'];assert re.fullmatch(r'Q\d+',mq)
        bound=min(250,2*(target_count-selected['projected_count'])+30)
        query=index_query(mq,bound,selected.get('cursor',''))
        url='https://query.wikidata.org/sparql?'+urlencode(dict(query=query,format='json'))
        try:
            raw,rc=entity_capture(url)
            if rc['status']!=200:raise ValueError('HTTP '+str(rc['status']))
            rows=json.loads(raw)['results']['bindings'];ids=[x['work']['value'].rsplit('/',1)[-1]for x in rows]
            assert all(re.fullmatch(r'Q\d+',q)for q in ids)and ids==sorted(set(ids))
            if selected.get('cursor'):assert all(q>selected['cursor']for q in ids)
            index_evidence.append(dict(museum=museum,receipt=rc,selected_ids=ids,capped=len(ids)==bound,cursor=selected.get('cursor',''),page_number=selected.get('page_number',1)))
            candidates.extend(dict(qid=q,museum=museum,index_receipt=rc)for q in ids)
            print('Wikidata museum index',n,'/',len(selection),museum['name'],len(ids),'objects',flush=True)
        except Exception as exc:
            held.append(dict(museum_id=museum['id'],reason='museum_index_unavailable',error=type(exc).__name__+': '+str(exc)[:150]))
            if 'HTTP 403'in str(exc)or 'HTTP 429'in str(exc):break
    c.save(ROOT/wave/'index-evidence.json.gz',dict(evidence=index_evidence,held=held))
    if any(re.search(r'HTTP (403|429)',x.get('error',''))for x in held):
        raise RuntimeError('Museum index access response requires backoff/review; stopping this source pass before further requests')
    with c.d.connect()as db:
        known=set()
        for part in c.d.chunks([x['qid']for x in candidates],500):
            known.update(x['external_id']for x in db.execute("SELECT external_id FROM external_identifiers WHERE entity_type='artwork'AND scheme='wikidata'AND external_id=ANY(%s)",(part,)))
    selected=[x for x in candidates if x['qid']not in known]
    c.save(ROOT/wave/'selected-new-object-ids.json',selected)
    data=entities([x['qid']for x in selected]);creatorids={w.value(a)['id']for x in data.values()for a in w.active(x['entity'],'P170')if isinstance(w.value(a),dict)}
    artists=entities(creatorids);creators={q:x['entity']for q,x in artists.items()};c.save(ROOT/wave/'creator-evidence.json.gz',artists)
    ready=[]
    for candidate in selected:
        q=candidate['qid'];source=data[q];facts,reason=fields(source['entity'],candidate['museum'],creators,source['receipt'])
        if reason:held.append(dict(qid=q,museum_id=candidate['museum']['id'],reason=reason));continue
        artist_qids=[w.value(x)['id']for x in w.active(source['entity'],'P170')]
        ready.append(dict(artwork_id=c.d.uid('wikidata-new/'+q),slug=c.OP+'-wikidata-'+q.lower(),source_record_id=q,provider='wikidata-catalogue',origin='verified_native_entity',museum=candidate['museum'],facts=facts,alternate_native_urls=native_urls(source['entity']),
            source_receipt=source['receipt'],body_path=source['receipt']['body_path'],raw_source_record=dict(entity=source['entity'],creators={q:artists[q]for q in artist_qids},index_receipt=candidate['index_receipt'])))
    c.prepare_wave(wave,ready,held)


OLD_CHECK=c.check_body
def check_body(row,cache):
    if row['provider']!='wikidata-catalogue':return OLD_CHECK(row,cache)
    rc=row['source_receipt'];raw=gzip.decompress((c.ROOT/row['body_path']).read_bytes());assert c.d.sha(raw)==rc['sha256']and rc['status']==200
    source=row['raw_source_record'];e=json.loads(raw)['entities'][row['source_record_id']];assert e==source['entity'];creators={}
    assert row['alternate_native_urls']==native_urls(e)
    for q,value in source['creators'].items():
        cr=value['receipt'];body=gzip.decompress((c.ROOT/cr['body_path']).read_bytes());assert c.d.sha(body)==cr['sha256']and cr['status']==200
        assert json.loads(body)['entities'][q]==value['entity'];creators[q]=value['entity']
    facts,reason=fields(e,row['museum'],creators,rc);assert not reason and facts==row['facts']


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['research','plan','apply']);ap.add_argument('--wave',required=True);ap.add_argument('--museums',type=int,default=30);args=ap.parse_args()
    if args.phase=='research':research(args.wave,args.museums)
    else:
        c.d.TARGET_FIELD='linked';c.d.DEFAULT_CONFIDENCE=0.85;c.d.SOURCE_NAME='Museum coverage: selected referenced Wikidata catalogue metadata';c.d.SOURCE_BASE_URL='https://www.wikidata.org/'
        c.d.CONFIDENCE_BASIS='Exact Wikidata painting/icon entity, single referenced collection statement, unique museum authority, explicit pre-1971 creation date and retained creator labels. Secondary-source editorial assessment 0.85, not calibrated probability; referenced documents not independently verified.'
        oldscheme=c.ORIGINAL_SCHEME;c.ORIGINAL_SCHEME=lambda row:'wikidata'if row['provider']=='wikidata-catalogue'else oldscheme(row)
        c.check_body=check_body;c.delivery(args.phase,args.wave)
