#!/usr/bin/env python3
"""Source-backed original-language audit of the existing book catalogue."""
import argparse,collections,concurrent.futures,datetime,gzip,hashlib,json,os,re,threading,time,urllib.parse,uuid
from pathlib import Path
import psycopg,requests
from psycopg.rows import dict_row

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/book-languages-20260922'
BACKUP=Path.home()/'Library/Application Support/Artline/backups/book-languages-20260922'
DSN='postgres://localhost/artline'
GATE=threading.Lock();NEXT=0.0
AGENT='ArtlineBookLanguageReview/1.0 (existing historical book catalogue; metadata research; https://artline-web-lpuqqlugnq-ew.a.run.app)'

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def encode(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),default=str).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def read(p):return json.loads(p.read_bytes())
def save(p,value):
    raw=value if isinstance(value,bytes) else encode(value)
    if p.exists():assert p.read_bytes()==raw,('Immutable evidence differs',str(p));return
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp');tmp.write_bytes(raw);os.replace(tmp,p)

def baseline():
    ref=RUN/'baseline-local-reference.json'
    if ref.exists():return
    with psycopg.connect(DSN,row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
        books=db.execute('SELECT to_jsonb(b) book,to_jsonb(d) discovery FROM book_records b LEFT JOIN book_discovery d ON d.book_id=b.id ORDER BY b.id').fetchall()
        terms=db.execute("SELECT to_jsonb(t) record FROM book_discovery_terms t WHERE kind='language' ORDER BY key").fetchall()
    path=BACKUP/'baseline-local.json';save(path,{'at':now(),'books':books,'terms':terms})
    save(ref,{'path':str(path),'sha256':sha(path.read_bytes()),'books':len(books)})
    print('Read-only baseline',len(books),'books;',sum(not r['discovery'] or not r['discovery']['languages'] for r in books),'without language',flush=True)

def source_request(host,params):
    global NEXT
    url='https://'+host+'/w/api.php?'+urllib.parse.urlencode({'format':'json','formatversion':2,'maxlag':5,**params})
    key=sha(url.encode());path=RUN/'sources'/(key+'.json.gz');receipt_path=RUN/'sources'/(key+'.receipt.json')
    if path.exists():return json.loads(gzip.decompress(path.read_bytes())),read(receipt_path)
    for attempt in range(4):
        with GATE:
            delay=max(0,NEXT-time.monotonic())
            if delay:time.sleep(delay)
            NEXT=time.monotonic()+1.2
        try:
            response=requests.get(url,headers={'User-Agent':AGENT},timeout=(15,65))
            if response.status_code in (429,503):
                try:delay=float(response.headers.get('Retry-After','15'))
                except ValueError:delay=15
                with GATE:NEXT=max(NEXT,time.monotonic()+max(delay,15*(attempt+1)))
            response.raise_for_status();data=response.json()
            if 'error' in data:raise RuntimeError(str(data['error']))
            raw=response.content;archive=gzip.compress(raw,mtime=0)
            receipt={'url':url,'final_url':response.url,'retrieved_at':now(),'sha256':sha(raw),'bytes':len(raw),'archive':str(path),'archive_sha256':sha(archive),'http_status':response.status_code}
            # Each request URL belongs to only one worker. Preserve the receipt
            # first, then the immutable response, so resumed reads are complete.
            save(receipt_path,receipt);save(path,archive)
            return data,receipt
        except (requests.RequestException,RuntimeError) as error:
            print('Source request retry',host,attempt+1,str(error)[:180],flush=True)
            if attempt==3:raise
            with GATE:NEXT=max(NEXT,time.monotonic()+min(30,5*(attempt+1)))

def active_claims(entity,prop):
    rows=[c for c in entity.get('claims',{}).get(prop,[]) if c.get('rank')!='deprecated' and c.get('mainsnak',{}).get('snaktype')=='value']
    return [c for c in rows if c.get('rank')=='preferred'] or rows
def values(entity,prop):return [c['mainsnak']['datavalue']['value'] for c in active_claims(entity,prop)]
def ids(entity,prop):return [v['id'] for v in values(entity,prop) if isinstance(v,dict) and v.get('id')]

def capture():
    baseline();base=read(Path(read(RUN/'baseline-local-reference.json')['path']))
    qids=sorted({v['book']['source_id'] for v in base['books']});batches=[qids[i:i+50] for i in range(0,len(qids),50)]
    def work_batch(batch):
        if all((RUN/'entities'/(q+'.json')).exists() for q in batch):return len(batch)
        data,receipt=source_request('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(batch),'props':'info|labels|aliases|descriptions|claims|sitelinks','languages':'en|mul','sitefilter':'enwiki|dewiki|frwiki|eswiki|ruwiki|zhwiki|jawiki|arwiki|ptwiki|itwiki'})
        for q in batch:
            save(RUN/'entities'/(q+'.json'),{'entity':data['entities'].get(q,{'id':q,'missing':True}),'receipt':receipt})
        return len(batch)
    n=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for count in pool.map(work_batch,batches):
            n+=count
            if n%500==0 or n==len(qids):print('Fresh Wikidata book records',n,'of',len(qids),flush=True)
    save(RUN/'wikidata-capture-finished.json',{'qids':qids})
    wikipedia_capture()

def wikipedia_capture():
    entries=[]
    for path in sorted((RUN/'entities').glob('*.json')):
        entity=read(path)['entity'];link=entity.get('sitelinks',{}).get('enwiki')
        if link:entries.append({'qid':path.stem,'title':link['title']})
    batches=[entries[i:i+50] for i in range(0,len(entries),50)]
    def page_batch(batch):
        if all((RUN/'wikipedia'/(v['qid']+'.json')).exists() for v in batch):return len(batch)
        data,receipt=source_request('en.wikipedia.org',{'action':'query','titles':'|'.join(v['title'] for v in batch),'redirects':1,'prop':'revisions|pageprops','rvprop':'ids|timestamp|content','rvslots':'main','ppprop':'wikibase_item'})
        remap={v['from']:v['to'] for v in data.get('query',{}).get('normalized',[])+data.get('query',{}).get('redirects',[])}
        pages={p['title']:p for p in data.get('query',{}).get('pages',[])}
        for entry in batch:
            title=entry['title'];seen=set()
            while title in remap and title not in seen:seen.add(title);title=remap[title]
            page=pages.get(title,{'title':title,'missing':True})
            if not (RUN/'wikipedia'/(entry['qid']+'.json')).exists():save(RUN/'wikipedia'/(entry['qid']+'.json'),{'requested':entry,'page':page,'receipt':receipt})
        return len(batch)
    n=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for count in pool.map(page_batch,batches):
            n+=count
            if n%500==0 or n==len(entries):print('Wikipedia book pages',n,'of',len(entries),flush=True)
    save(RUN/'wikipedia-capture-finished.json',{'requested':entries})

def capture_terms():
    base=read(Path(read(RUN/'baseline-local-reference.json')['path']))
    qids={v['record']['key'] for v in base['terms']}
    for path in (RUN/'entities').glob('*.json'):qids.update(ids(read(path)['entity'],'P407'))
    qids=sorted(qids)
    for offset in range(0,len(qids),50):
        batch=qids[offset:offset+50]
        if all((RUN/'language-entities'/(q+'.json')).exists() for q in batch):continue
        data,receipt=source_request('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(batch),'props':'info|labels|aliases|descriptions|claims|sitelinks','languages':'en|mul','sitefilter':'enwiki'})
        for q in batch:save(RUN/'language-entities'/(q+'.json'),{'entity':data['entities'].get(q,{'id':q,'missing':True}),'receipt':receipt})
        print('Source language vocabulary',min(offset+50,len(qids)),'of',len(qids),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['baseline','capture','wikipedia_capture','capture_terms']);args=parser.parse_args();globals()[args.phase]()
