#!/usr/bin/env python3
"""Read-only follow-up on the 452 event description fallbacks, with cached sources."""
import argparse, collections, gzip, hashlib, json, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/research/event-description-followup-20260918'
PREVIOUS=ROOT/'docs/research/event-descriptions-20260918/descriptions.json'
LANGUAGES=['en','fr','de','es','ru','it','nl','pl','sv','fi','pt','uk']
LANGUAGE_NAMES=dict(zip(LANGUAGES,['English','French','German','Spanish','Russian','Italian','Dutch','Polish','Swedish','Finnish','Portuguese','Ukrainian']))

def write(name,data):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def request(host,params):
    key=hashlib.sha256(json.dumps([host,params],sort_keys=True).encode()).hexdigest()[:20]
    path=OUT/'sources'/(key+'.json.gz');path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():return json.loads(gzip.decompress(path.read_bytes()))
    for attempt in range(5):
        delay=60*(attempt+1)
        try:
            req=urllib.request.Request('https://'+host+'/w/api.php?'+urllib.parse.urlencode({'format':'json','formatversion':2,'maxlag':5,**params}),headers={'User-Agent':'ArtlineResearch/1.0 (+https://github.com/vadimdulub; event descriptions)','Accept-Encoding':'gzip'})
            with urllib.request.urlopen(req,timeout=50) as response:
                raw=response.read()
                if response.headers.get('Content-Encoding')=='gzip':raw=gzip.decompress(raw)
            data=json.loads(raw)
            if 'error' in data:raise ValueError(data['error'])
            result={'host':host,'params':params,'retrievedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'response':data}
            path.write_bytes(gzip.compress(json.dumps(result,ensure_ascii=False).encode(),mtime=0))
            time.sleep(1)
            return result
        except (urllib.error.URLError,TimeoutError,ValueError) as error:
            if isinstance(error,urllib.error.HTTPError) and error.headers.get('Retry-After','').isdigit():delay=max(delay,int(error.headers['Retry-After']))
            print('Retry',host,attempt+1,str(error),flush=True)
            if attempt==4:raise
            time.sleep(delay)

def authorities():
    records=[r for r in json.loads(PREVIOUS.read_text()) if r['source']['kind']=='wikidata']
    result={}
    for offset in range(0,len(records),50):
        ids=['Q'+r['id'].split('-q')[1] for r in records[offset:offset+50]]
        response=request('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(ids),'props':'info|labels|descriptions|sitelinks','languages':'|'.join(LANGUAGES),'sitefilter':'|'.join(l+'wiki' for l in LANGUAGES)})
        result.update(response['response']['entities'])
        print('Authorities',min(offset+50,len(records)),'/',len(records),flush=True)
    write('authorities.json',result)

def introductions():
    authorities=json.loads((OUT/'authorities.json').read_text())
    previous={r['id']:r for r in json.loads(PREVIOUS.read_text())}
    groups=collections.defaultdict(list)
    queue=[]
    for qid,entity in authorities.items():
        # Use another language when English redirects to a broader subject.
        # We already retained the English lookup and its identity mismatch.
        site=next((lang for lang in LANGUAGES[1:] if lang+'wiki' in entity.get('sitelinks',{})),None)
        if not site:continue
        title=entity['sitelinks'][site+'wiki']['title']
        groups[site].append(title)
        queue.append({'id':'event-'+qid.lower(),'sourceId':qid,'language':site,'title':title,'basic':'assembled' in previous['event-'+qid.lower()]['source']['notice']})
    for lang,titles in groups.items():
        for offset in range(0,len(titles),20):
            request(lang+'.wikipedia.org',{'action':'query','prop':'extracts|info|pageprops','exintro':1,'explaintext':1,'exchars':1100,'exlimit':20,'inprop':'url','ppprop':'wikibase_item|disambiguation','redirects':1,'titles':'|'.join(titles[offset:offset+20])})
        print(lang,len(titles),'introductions',flush=True)
    write('article-queue.json',queue)

def match():
    pages={}
    for path in sorted((OUT/'sources').glob('*.json.gz')):
        evidence=json.loads(gzip.decompress(path.read_bytes()))
        if not evidence['host'].endswith('.wikipedia.org'):continue
        lang=evidence['host'].split('.')[0]
        query=evidence['response'].get('query',{})
        aliases={p['from']:p['to'] for key in ['normalized','redirects'] for p in query.get(key,[])}
        by_title={p['title']:p for p in query.get('pages',[])}
        for title in evidence['params']['titles'].split('|'):
            target=title;seen=set()
            while target in aliases and target not in seen:
                seen.add(target);target=aliases[target]
            pages[(lang,title)]=(by_title.get(target,{}),evidence['retrievedAt'],'sources/'+path.name,target)
    matched=[];issues=[]
    for item in json.loads((OUT/'article-queue.json').read_text()):
        page,retrieved,evidence,target=pages.get((item['language'],item['title']),({},'', '',item['title']))
        props=page.get('pageprops',{})
        if props.get('wikibase_item')!=item['sourceId'] or 'disambiguation' in props or not page.get('extract','').strip():
            issues.append({'id':item['id'],'target':target,'reason':'No exact identity/introduction'})
            continue
        matched.append({**item,'extract':page['extract'],'url':page['fullurl'],'revision':page['lastrevid'],'retrievedAt':retrieved,'evidenceFile':evidence})
    write('matched-introductions.json',matched);write('article-issues.json',issues)
    print('Exact matches:',len(matched),'excluded:',len(issues))

def prepare():
    previous={r['id']:r for r in json.loads(PREVIOUS.read_text())}
    matched={r['id']:r for r in json.loads((OUT/'matched-introductions.json').read_text())}
    reviewed=json.loads((OUT/'reviewed-summaries.json').read_text())
    updates=[]
    for id,summary in reviewed.items():
        article=matched[id];prior=previous[id];language=article['language'];name=LANGUAGE_NAMES[language]+' Wikipedia'
        assert prior['source']['kind']=='wikidata' and article['basic'] and 0<len(summary)<=1200
        updates.append({'id':id,'previousDescription':prior['description'],'previousSource':prior['source'],'description':summary,'source':{
            'name':name,'url':article['url'],'kind':'wikipedia','language':language,'title':article['title'],
            'revision':article['revision'],'retrievedAt':article['retrievedAt'],'license':'CC BY-SA 4.0',
            'licenseUrl':'https://creativecommons.org/licenses/by-sa/4.0/',
            'notice':'English summary translated and adapted from the '+name+' introduction.',
            'evidenceFile':str(OUT.relative_to(ROOT)/article['evidenceFile'])}})
    write('descriptions.json',updates)
    files={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file() and (p.suffix=='.json' or p.name.endswith('.json.gz')) and p.name!='manifest.json'}
    write('manifest.json',{'previousPayloadSHA256':hashlib.sha256(PREVIOUS.read_bytes()).hexdigest(),
        'fallbacksReviewed':sum(r['source']['kind']=='wikidata' for r in previous.values()),
        'articleCandidates':len(json.loads((OUT/'article-queue.json').read_text())),
        'exactArticleMatches':len(matched),'reviewedEnglishSummaries':len(updates),
        'languageCounts':dict(collections.Counter(u['source']['language'] for u in updates)),
        'changes':['description','descriptionSource'],'files':files})
    print('Prepared:',len(updates),'description updates; no database writes')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['authorities','introductions','match','prepare']);args=parser.parse_args()
    globals()[args.stage]()
