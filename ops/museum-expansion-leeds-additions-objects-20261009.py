"""Select40 dated catalogue watercolours before fetching bounded native object metadata."""
import html,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-leeds-additions-native-20261009.py'));n=importlib.util.module_from_spec(z);z.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref

def parsed(raw):
 s=n.n.BeautifulSoup(raw,'html.parser');fields={};repeated={}
 for tr in s.select('table tr'):
  cells=tr.find_all(['th','td'],recursive=False)
  if len(cells)!=2:continue
  k,v=(c.get_text(' ',strip=True) for c in cells);k=k.rstrip(':')
  if k in fields:repeated.setdefault(k,[fields[k]]).append(v)
  else:fields[k]=v
 return dict(fields=fields,repeated=repeated,headings=[v.get_text(' ',strip=True) for v in s.select('h1,h2,h3')],text=s.get_text(' ',strip=True),links=[dict(text=a.get_text(' ',strip=True),href=a['href']) for a in s.select('a[href]')],lists=[v.get_text(' ',strip=True) for v in s.select('[uk-accordion]')])

def date(v):
 match=re.fullmatch(r'(c\.?\s*)?(\d{4})(?:\s*[-–/]\s*(\d{4}))?',v or '')
 if not match:return None
 first,last=int(match[2]),int(match[3] or match[2]);assert 100<=first<=last<=1970;return first,last,('circa' if first==last else 'circa_range') if match[1] else ('exact' if first==last else 'range')

def main():
 source=RUN/'cotmania-watercolour-index-001.json.gz';x=m.load(source)['data'];assert len(x['hits'])==40;selection=[]
 for r in x['hits']:
  assert r['type']=='Works of Art' and r['objectname']=='Watercolour' and r['reference'].startswith('LEEAG.');d=date(r['date']);assert d;selection.append(dict(index=r,date=d,source_id=r['objectID'].split('/')[-1]))
 m.save(RUN/'cotmania-selected-001.json.gz',dict(at=m.now(),rows=selection,index_reference=ref(source),policy='First40date-eligible object metadata records from one bounded watercolour facet page. Source maker qualifiers,recto-verso,versions and provenance still require object review. Not an exhaustive collection download.'))
 out=[];failed=0
 for number,r in enumerate(selection,1):
  try:
   raw,c=n.n.capture('cotmania',r['index']['url']);p=parsed(raw);row=dict(number=number,**r,capture=c,parsed=p);failed=0
  except Exception as e:
   row=dict(number=number,**r,error=type(e).__name__+': '+str(e));failed+=1
  m.save(RUN/'selected-objects-001'/('%03d.json'%number),row);out.append(row);print(json.dumps(dict(number=number,source_id=r['source_id'],fields=row.get('parsed',{}).get('fields'),error=row.get('error')),ensure_ascii=False),flush=True)
  if failed>=3 or any(t in row.get('error','') for t in ['403','429']):break
 m.save(RUN/'cotmania-objects-001.json.gz',dict(at=m.now(),rows=out,selection_reference=ref(RUN/'cotmania-selected-001.json.gz'),script_reference=ref(Path(__file__).resolve()),policy='Selected native metadata only. No image downloads,archive-page imports or current display assumptions.'))
if __name__=='__main__':main()
