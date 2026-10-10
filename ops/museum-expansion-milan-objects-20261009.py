"""Selected151 pre-existing museum claims: bounded native object corroboration."""
import collections,hashlib,gzip,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urljoin
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-milan-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);s=p.s;m=p.m;n=p.n;RUN=p.RUN;ref=p.ref
OVERRIDES={29:'Presso Cremieu',99:'Farrington Street',132:'caprone',141:"Immacolatella"}
def creator(r):
 if r['artwork']['unlinked_creator_label']:return r['artwork']['unlinked_creator_label']
 assert r['number'] in [73,119];return 'Carpi, Aldo'
def fields(raw):
 soup=n.BeautifulSoup(raw,'html.parser');data=collections.defaultdict(list)
 for row in soup.select('.row-dati'):
  k=row.select_one('.label-scheda');v=row.select_one('.campo-scheda')
  if k and v:data[k.get_text(' ',strip=True)].append(v.get_text(' ',strip=True))
 h=soup.select_one('.titleItemWrap h2');dt=soup.select_one('.titleItemWrap .data-scheda')
 return dict(title=h.get_text(' ',strip=True) if h else None,date=dt.get_text(' ',strip=True) if dt else None,fields=dict(data))
def main():
 dest=RUN/'native-objects-001.json.gz';assert not dest.exists();src=m.load(RUN/'source-context-001.json.gz');out=[];errors=[]
 for r in src['rows']:
  num=r['number'];title=r['artwork']['title'];query=OVERRIDES.get(num,title.split(', ')[-1].split(';')[0].strip());url=n.SITES['milan']+'/settori/collezioni-d-arte?'+urlencode({'query':query});result=dict(number=num,query=query,source_id=r['source_id'],creator_label=creator(r),search_url=url)
  try:
   raw,cap=n.capture('milan',url);soup=n.BeautifulSoup(raw,'html.parser');cards=[]
   for a in soup.select('a[href^="/detail/"]'):
    h=a.select_one('h3');sp=a.select('.caption-title');cards.append(dict(title=h.get_text(' ',strip=True) if h else None,url=urljoin(url,a['href']),caption=[v.get_text(' ',strip=True) for v in sp],text=a.get_text(' ',strip=True)))
   words={v for v in m.norm(re.sub(r'\([^)]*\)','',creator(r))).split() if len(v)>2};selected=[c for c in cards if words&set(m.norm(' '.join(c['caption'][:1])).split())];result.update(search_capture=cap,cards=cards,selected_urls=[c['url'] for c in selected],objects=[])
   if len(selected)>4:result['hold']='More than4 same-creator search results; require narrower editorial selection.'
   else:
    for c in selected:
     body,bc=n.capture('milan',c['url']);result['objects'].append(dict(index=c,capture=bc,parsed=fields(body)))
  except Exception as e:
   result['error']=type(e).__name__+': '+str(e);errors.append(dict(number=num,url=url,error=result['error']));out.append(result);break
  out.append(result);print(json.dumps(dict(number=num,query=query,cards=len(cards),objects=len(result.get('objects',[])),hold=result.get('hold'))),flush=True)
 m.save(dest,dict(at=m.now(),rows=out,source_reference=ref(RUN/'source-context-001.json.gz'),script_reference=ref(Path(__file__).resolve()),errors=errors,policy='Only151 preselected existing artwork claims searched; at most4 same-creator object pages per selected query, no pagination. Search selection is not identity approval. Preserve source inventories, alias titles, dates, materials, measurements, acquisitions and location wording verbatim. No image requests. Stop on access failure; no retry or bypass.'))
 print(json.dumps(dict(rows=len(out),errors=len(errors),objects=sum(len(v.get('objects',[])) for v in out))),flush=True)
if __name__=='__main__':main()
