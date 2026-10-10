#!/usr/bin/env python3
import sys,importlib.util,json,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'ops'))
assert not (ROOT/'docs/research/books-5000bce-1850-20261004/plan.json').exists(), 'Preserve the completed campaign; use a new campaign for new research.'
s=importlib.util.spec_from_file_location('w',ROOT/'ops/expand-pre1850-books-20261001.py');w=importlib.util.module_from_spec(s);s.loader.exec_module(w);OUT=ROOT/'docs/research/books-5000bce-1850-20261004';w.research.OUT=OUT
cs={c['qid']:c for c in json.load(open(OUT/'candidates.json'))};initial=json.load(open(OUT/'image-candidates.json'))
# Additional filenames come from the captured full articles, not fuzzy identity matching.
explicit={'Q7091533':'On the Sacred Disease.jpg','Q16385022':'The Adventures of Ferdinand, Count Fathom.jpg','Q8073404':'Zofloya; or, The Moor title page.png','Q23307984':'Mary Somerville On the Connexion of the Physical Sciences.jpg','Q48724336':'Laplace-2.jpg'}
extra=[{'category':'books','id':'wd-'+q.lower(),'qid':q,'name':cs[q]['title'],'file':f,'identityBasis':'File named in the captured matched work article.'} for q,f in explicit.items()]
searches=[('books','Q1242779','The Prelude title page'),('books','Q48770862','Nature and Art Inchbald'),('books','Q17005869','The Borough Crabbe title'),('books','Q7772638','The Village Crabbe title'),('books','Q7758286','The Princess Tennyson title page'),('books','Q3203413','Humphry Clinker title page'),('books','Q7727506','Convent of Pleasure Cavendish'),('books','Q2590941','Ibn Khordadbeh Book Roads Kingdoms'),('books','Q5244884','Frontinus aquaeductu title page'),('authors','Q1276720','Henry Mackenzie portrait engraving'),('authors','Q236236','Oliver Goldsmith portrait engraving'),('authors','Q78427','Johann Bayer portrait')]
meta=json.load(open(OUT/'metadata.json'));crabbe=next(x['id'] for x in json.load(open(OUT/'image-attempts.json')) if x['name']=='George Crabbe');searches.append(('authors',crabbe,'George Crabbe portrait engraving'))
search_receipts=[]
for category,q,query in searches:
 try:
  data,proof=w.research.capture('commons.wikimedia.org',{'action':'query','list':'search','srnamespace':6,'srsearch':query,'srlimit':3})
  results=data['query']['search'];search_receipts.append({'category':category,'qid':q,'query':query,'source':proof,'results':results})
  for hit in results:extra.append({'category':category,'id':'wd-'+q.lower() if category=='books' else q,'qid':q,'name':cs[q]['title'] if category=='books' else w.r.creator_name(meta[q]['entity']),'file':hit['title'][5:],'identityBasis':'Bounded Commons search candidate; still requires explicit identity review.','searchSource':proof})
  w.save(OUT/'image-followup-searches.json',search_receipts);print(query,[h['title'] for h in results],flush=True);time.sleep(6)
 except Exception as error:
  search_receipts.append({'category':category,'qid':q,'query':query,'error':str(error)});w.save(OUT/'image-followup-searches.json',search_receipts);print('Search held',query,str(error),flush=True)
w.save(OUT/'image-followup-identities.json',extra)
pages={};files=sorted({r['file'] for r in extra})
for off in range(0,len(files),6):
 data,proof=w.research.capture('commons.wikimedia.org',{'action':'query','titles':'|'.join('File:'+f for f in files[off:off+6]),'redirects':1,'prop':'imageinfo','iiprop':'url|size|mime|extmetadata|sha1','iiextmetadatalanguage':'en','iiurlwidth':640})
 query=data['query'];bytitle={p['title']:p for p in query['pages']};renames={r['from']:r['to'] for r in query.get('normalized',[])+query.get('redirects',[])}
 for f in files[off:off+6]:
  title='File:'+f
  for _ in range(5):title=renames.get(title,title)
  pages[f]={'page':bytitle.get(title,{}),'source':proof}
 print('Metadata',off+6,len(files),flush=True);time.sleep(6)
for r in extra:r.update(pages.get(r['file'],{}))
w.save(OUT/'image-followup-candidates.json',extra)
