"""Resolve five search-selection gaps with exact observed native object links."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urlencode,urljoin
z=importlib.util.spec_from_file_location('o',Path(__file__).with_name('museum-expansion-milan-objects-20261009.py'));o=importlib.util.module_from_spec(z);z.loader.exec_module(o);m=o.m;n=o.n;RUN=o.RUN;ref=o.ref
QUERIES={6:'ponte della Maddalena',59:'Corso Vittorio Emanuele',81:'via Toledo',117:'Bazzaro'}
def main():
 dest=RUN/'native-followup-001.json.gz';assert not dest.exists();first=m.load(RUN/'native-objects-001.json.gz');out=[]
 for number,query in QUERIES.items():
  url=n.SITES['milan']+'/settori/collezioni-d-arte?'+urlencode({'query':query});raw,cap=n.capture('milan',url);p=n.BeautifulSoup(raw,'html.parser');cards=[]
  for a in p.select('a[href^="/detail/"]'):
   if not a.select_one('h3'):continue
   cards.append(dict(title=a.h3.get_text(' ',strip=True),url=urljoin(url,a['href']),caption=[v.get_text(' ',strip=True) for v in a.select('.caption-title')],text=a.get_text(' ',strip=True)))
  chosen=[v for v in cards if ('bazzaro' if number==117 else 'pratella') in m.norm(' '.join(v['caption'][:1]))];assert 0<len(chosen)<=4;objects=[]
  for c in chosen:
   body,bc=n.capture('milan',c['url']);objects.append(dict(index=c,capture=bc,parsed=o.fields(body)))
  out.append(dict(number=number,query=query,search_url=url,search_capture=cap,cards=cards,objects=objects));print(number,len(objects),flush=True)
 r=first['rows'][49];cards=[v for v in r['cards'] if v['title']=='Ritratto di Guido Rossi' and v['caption'][0]=='Gaudenzi, Pietro'];assert len(cards)==1;c=cards[0];body,cap=n.capture('milan',c['url']);out.append(dict(number=50,selection='Exact already observed title and creator; initial broad name selection exceeded4.',objects=[dict(index=c,capture=cap,parsed=o.fields(body))]))
 m.save(dest,dict(at=m.now(),rows=out,prior_reference=ref(RUN/'native-objects-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Five preselected object-search gaps. Narrower subject/creator queries or exact observed object link; no pagination or images.'))
if __name__=='__main__':main()
