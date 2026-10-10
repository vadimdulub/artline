#!/usr/bin/env python3
import sys,importlib.util,json,time,re,html,hashlib,gzip,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'ops'))
assert not (ROOT/'docs/research/books-5000bce-1850-20261004/plan.json').exists(), 'Preserve the completed campaign; use a new campaign for new research.'
s=importlib.util.spec_from_file_location('w',ROOT/'ops/expand-pre1850-books-20261001.py');w=importlib.util.module_from_spec(s);s.loader.exec_module(w)
OUT=ROOT/'docs/research/books-5000bce-1850-20261004';w.OUT=OUT;w.research.OUT=OUT
selection=json.load(open(OUT/'selection.json'));cs={c['qid']:c for c in json.load(open(OUT/'candidates.json'))}
data,proof=w.research.capture('en.wikipedia.org',{'action':'query','titles':'George Crabbe','prop':'pageprops|extracts|revisions','ppprop':'wikibase_item','exintro':1,'explaintext':1,'rvprop':'ids|timestamp'})
p=data['query']['pages'][0];crabbe=p['pageprops']['wikibase_item'];w.save(OUT/'crabbe-identity.json',{'page':p,'source':proof})
for x in selection['items']:
 q=x['qid']
 if q in ['Q7772638','Q17005869']:x.update(creatorIds=[crabbe],creatorReview='The matched work introduction explicitly credits George Crabbe; reconciled to the captured creator article identity.')
 if q=='Q5244884':x.update(date=[97,98,True,'c. 97–98 CE','Rodgers’s Cambridge edition places the account around the first year after Frontinus’s appointment in 97 CE. Preserve an approximate 97–98 interval.'],additionalSources=[{'name':'Cambridge University Press — Frontinus, edited by R. H. Rodgers','url':'https://assets.cambridge.org/052183/2519/frontmatter/0521832519_frontmatter.htm'}])
 if q=='Q25100963':x.update(date=[1788,1788,False,'1788','First edition dated 1788 by ETH Library’s digitised original. The secondary article’s 1788–1789 claim is not adopted.'],omitOverview=True,additionalSources=[{'name':'ETH Library — original 1788 edition','url':'https://www.e-rara.ch/zut/content/titleinfo/2488394'}])
 if q=='Q48724336':x.update(date=[1799,1825,False,'1799–1825','Original five-volume publication interval from Kyoto University’s catalogue; the secondary article’s 1798 start is retained only in research evidence.'],omitOverview=True,additionalSources=[{'name':'Kyoto University Library — original edition','url':'https://rmda.kulib.kyoto-u.ac.jp/en/item/rb00033955'}])
 if q=='Q23307984':x.update(additionalSources=[{'name':'University of Glasgow — original 1834 text','url':'https://www.scottishcorpus.ac.uk/cmsw/document/?documentid=97'}])
w.save(OUT/'selection.json',selection)
qids=set()
for x in selection['items']:
 e=cs[x['qid']]['wikidata']['entity'];qids.update(x.get('creatorIds',w.r.ids(e,'P50')));qids.update(w.r.ids(e,'P407'));qids.update(w.r.ids(e,'P495'))
metadata=json.load(open(OUT/'metadata.json')) if (OUT/'metadata.json').exists() else {}
missing=sorted(qids-metadata.keys())
for offset in range(0,len(missing),8):
 data,proof=w.research.capture('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(missing[offset:offset+8]),'props':'info|labels|descriptions|claims|sitelinks','languages':'en','sitefilter':'enwiki'})
 metadata.update({q:{'entity':e,'source':proof} for q,e in data['entities'].items()});w.save(OUT/'metadata.json',metadata);print('Metadata',len(metadata),flush=True);time.sleep(3)
images=[];audits=[]
portraits={r['creatorId']:r for r in json.load(open(ROOT/'apps/server/internal/books/portrait-selection.json'))}
for x in selection['items']:
 c=cs[x['qid']];e=c['wikidata']['entity'];files=w.r.values(e,'P18')[:2]
 images_from_article=[im['title'][5:] for im in c.get('images',[]) if re.search(r'cover|title|page|edition|calculi|connexion|Frontinus|Hesperides|Prelude|Fathom|Nature and Art|Princess|Borough|Village|Mécanique',im['title'],re.I) and not re.search(r'Commons-logo|Wikisource|Wikiquote',im['title'],re.I)]
 files=list(dict.fromkeys(files+images_from_article))[:4]
 audits.append({'category':'books','id':'wd-'+x['qid'].lower(),'name':c['title'],'files':files,'attempt':'Wikidata P18 and images in matched work article'})
 for f in files:images.append({'category':'books','id':'wd-'+x['qid'].lower(),'qid':x['qid'],'name':c['title'],'file':f})
author_ids=sorted({a for x in selection['items'] for a in x.get('creatorIds',w.r.ids(cs[x['qid']]['wikidata']['entity'],'P50'))})
for q in author_ids:
 e=metadata[q]['entity'];files=w.r.values(e,'P18')[:2]
 audits.append({'category':'authors','id':q,'name':w.r.creator_name(e),'files':files,'existingSelection':portraits.get(q),'attempt':'Wikidata P18 linked to the exact creator identity'})
 if q in portraits:continue
 for f in files:images.append({'category':'authors','id':q,'qid':q,'name':w.r.creator_name(e),'file':f})
w.save(OUT/'image-attempts.json',audits)
files=sorted({r['file'] for r in images});pages={}
for offset in range(0,len(files),6):
 data,proof=w.research.capture('commons.wikimedia.org',{'action':'query','titles':'|'.join('File:'+f for f in files[offset:offset+6]),'redirects':1,'prop':'imageinfo','iiprop':'url|size|mime|extmetadata|sha1','iiextmetadatalanguage':'en','iiurlwidth':640})
 query=data['query'];bytitle={p['title']:p for p in query['pages']};renames={r['from']:r['to'] for r in query.get('normalized',[])+query.get('redirects',[])}
 for f in files[offset:offset+6]:
  title='File:'+f
  for _ in range(5):title=renames.get(title,title)
  pages[f]={'page':bytitle.get(title,{}),'source':proof}
 print('Image metadata',min(offset+6,len(files)),len(files),flush=True);time.sleep(8)
for r in images:r.update(pages.get(r['file'],{}))
w.save(OUT/'image-candidates.json',images)
plain=lambda v:' '.join(html.unescape(re.sub('<[^>]*>',' ',str(v))).split())
for i,r in enumerate(images):
 info=r.get('page',{}).get('imageinfo',[{}])[0];m=info.get('extmetadata',{});print(i,r['category'],r['name'],r['file'],json.dumps({k:plain(m.get(k,{}).get('value','')) for k in ['LicenseShortName','Restrictions','DateTimeOriginal','Artist','Credit','ImageDescription']},ensure_ascii=False),flush=True)
