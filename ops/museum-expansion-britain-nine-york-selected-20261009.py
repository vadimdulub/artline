"""Bounded exact-object York native research for identity and creation-scope questions."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-britain-nine-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN
QUERIES=['Layerthorpe','Clifford','Burton','The Reflection','Early Memory','My Room','Profile of George','Nameless','York from']
WANTED={'1249','1250','1251','1443','382','2001.51','2001.52','2021.2','162','1483','484','487'}
def key(v):return re.sub(r'^YORAG\s*:\s*','',v).strip()
def main():
 dest=RUN/'york-selected-native-001.json.gz';assert not dest.exists();rows=[];searches=[];selected={};stopped=False;fails=0
 for query in QUERIES:
  if stopped:break
  url='https://yorkmuseumstrust.org.uk/collections/search/?'+urlencode({'CL[0]':'Fine Art','search_text':query,'limit':16,'collections_page':1})
  try:
   raw,c=n.capture('york',url);soup=n.BeautifulSoup(raw,'html.parser');hits=[]
   for a in soup.select('a[href]'):
    obj=a.select_one('.object_number')
    if not obj:continue
    inv=obj.get_text(' ',strip=True);link=urljoin(url,a['href']);entry=dict(inventory=inv,url=link,text=a.get_text(' ',strip=True));hits.append(entry)
    if key(inv) in WANTED:selected[inv]=entry
   searches.append(dict(query=query,url=url,capture=c,hits=hits));fails=0;print(json.dumps(dict(query=query,hits=len(hits),selected=[v['inventory'] for v in hits if key(v['inventory']) in WANTED])),flush=True)
  except Exception as e:
   fails+=1;searches.append(dict(query=query,url=url,error=type(e).__name__+': '+str(e)));stopped=fails>=3 or any(x in str(e) for x in ['403','429']);print(json.dumps(searches[-1]),flush=True)
 if not stopped:
  for inv,entry in sorted(selected.items()):
   try:
    raw,c=n.capture('york',entry['url']);rows.append(dict(index=entry,capture=c,parsed=n.parsed(raw)));fails=0;print(json.dumps(dict(object=inv,status=c['receipt']['status'])),flush=True)
   except Exception as e:
    fails+=1;rows.append(dict(index=entry,error=type(e).__name__+': '+str(e)));print(json.dumps(rows[-1]),flush=True)
    if fails>=3 or any(x in str(e) for x in ['403','429']):stopped=True;break
 m.save(dest,dict(at=m.now(),searches=searches,rows=rows,wanted=sorted(WANTED),unresolved=sorted(WANTED-{key(r['index']['inventory']) for r in rows if r.get('capture')}),provider_stopped=stopped,script_reference=n.ref(Path(__file__).resolve()),form_reference=n.ref(RUN/'native-extra-001.json.gz'),policy='Nine bounded native queries,16hits each maximum; only12 preselected catalogue numbers may be fetched. No guesswork IDs or image requests. Native dates retained as evidence only for holding-only review.'))
if __name__=='__main__':main()
