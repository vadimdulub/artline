#!/usr/bin/env python3
import concurrent.futures, json, pathlib, urllib.request, urllib.parse, html, re, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/research/author-portraits-20260929'
rows=json.loads((OUT/'creator-identities.json').read_text())
ids='Q36322 Q40909 Q991 Q7243 Q38337 Q905 Q3335 Q7200 Q5686 Q80137 Q131333 Q47152 Q101638 Q7245 Q30875 Q9068 Q535 Q1035 Q5879 Q1067 Q7241 Q180903 Q23114 Q81731 Q234816 Q93354 Q4985 Q937'.split()
def fetch(url,path):
 if path.exists(): return json.loads(path.read_text())
 time.sleep(3)
 req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0 (selected author portrait research)'})
 with urllib.request.urlopen(req,timeout=40) as res: body=res.read()
 result=json.loads(body);path.write_bytes(body);return result
plain=lambda x:' '.join(html.unescape(re.sub('<[^>]*>',' ',str(x))).split())
def work(row):
 try:
  qid=row['id']; e=fetch('https://www.wikidata.org/wiki/Special:EntityData/'+qid+'.json',OUT/'captures'/f'{qid}-entity.json')['entities'][qid]
  claims=[c for c in e.get('claims',{}).get('P18',[]) if c.get('rank')!='deprecated' and 'datavalue' in c['mainsnak']]
  claims.sort(key=lambda c:c.get('rank')!='preferred')
  if not claims: return dict(row,error='no selected P18')
  filename=claims[0]['mainsnak']['datavalue']['value']
  url='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(dict(action='query',format='json',prop='imageinfo',iiprop='url|size|mime|extmetadata',iiurlwidth='440',titles='File:'+filename))
  data=fetch(url,OUT/'captures'/f'{qid}-commons.json')
  page=next(iter(data['query']['pages'].values())); info=page.get('imageinfo',[{}])[0];meta=info.get('extmetadata',{})
  return dict(row,file=filename,info=info,metadata={k:plain(v.get('value','')) for k,v in meta.items()},entityRevision=e.get('lastrevid'))
 except Exception as e:return dict(row,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
 result=list(pool.map(work,[r for r in rows if r['id'] in ids]))
(OUT/'candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for r in result:
 m=r.get('metadata',{});print(json.dumps({k:r.get(k) for k in ['id','name','file','error']}|{k:m.get(k) for k in ['LicenseShortName','LicenseUrl','DateTimeOriginal','Artist','Restrictions','ImageDescription']},ensure_ascii=False))
