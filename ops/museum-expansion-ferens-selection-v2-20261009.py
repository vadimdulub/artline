"""Select at most180 eligible-date metadata leads from at most4 bounded result pages."""
import collections,gzip,importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin,urlsplit,parse_qs
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-ferens-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;n=p.n;RUN=p.RUN;ref=p.ref
def creation(v):
 text=(v or '').strip();s=text.lower().replace('–','-').replace('—','-');circ=bool(re.match(r'^(?:c\.?|circa|about)\s*\d',s));s=re.sub(r'^(?:c\.?|circa|about)\s*','',s)
 if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}',s):y=int(s.split('/')[-1]);return dict(first=y,last=y,date_precision='exact',date_display=text,date_basis='Literal native Date/Period; full day retained as text.')
 if re.fullmatch(r'\d{3,4}',s):y=int(s);return dict(first=y,last=y,date_precision='circa' if circ else 'exact',date_display=text,date_basis='Literal native Date/Period,not an inferred acquisition or life date.')
 match=re.fullmatch(r'(\d{3,4})\s*-\s*(?:c\.?\s*)?(\d{3,4})',s)
 if match:
  a,b=map(int,match.groups())
  if a<=b:return dict(first=a,last=b,date_precision='range',date_display=text,date_basis='Entire explicit native Date/Period range preserved,including circa text; no narrowed year.')
 match=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th) century',s)
 if match:
  c=int(match[1]);return dict(first=(c-1)*100,last=c*100-1,date_precision='range',date_display=text,date_basis='Whole named native century retained as catalogue search bounds; no invented narrower date.')
 match=re.fullmatch(r'(\d{3}0)\x27?s',s)
 if match:
  a=int(match[1]);return dict(first=a,last=a+9,date_precision='range',date_display=text,date_basis='Whole named native decade retained as catalogue search bounds.')
 return None
def index(raw,url):
 soup=n.BeautifulSoup(raw,'html.parser');out=[]
 for dl in soup.select('dl'):
  a=dl.select_one('dt a[href*="display.php?irn="]')
  if a is None:continue
  ds=dl.find_all('dd',recursive=False);assert 1<=len(ds)<=3;target=urljoin(url,a['href']);qid=parse_qs(urlsplit(target).query)['irn'];assert len(qid)==1 and qid[0].isdigit();title=a.get_text(' ',strip=True);values=[d.get_text(' ',strip=True) for d in ds];museum=values[-1];assert museum=='Ferens Art Gallery';creator=date=None
  if len(values)==3:creator,date=values[:2]
  elif len(values)==2:
   if re.search(r'\d',values[0]):date=values[0]
   else:creator=values[0]
  out.append(dict(source_id=qid[0],title=title,creator=creator,date=date,museum=museum,url=target,index_values=values))
 assert 1<=len(out)<=96;links={urljoin(url,a['href']) for a in soup.select('a[href]') if a.get_text(' ',strip=True)=='Next Page of Results'};assert len(links)<=1;return out,next(iter(links),None)
def main():
 dest=RUN/'native-selection-001.json.gz';assert not dest.exists();prior=m.RUN/'native/britain-six-holdings-20261009';seen_prior=set();priorrefs=[]
 for v in m.load(prior/'ferens-native-002.json.gz')['rows']:
  path=m.ROOT/v['reference']['path'];assert ref(path)==v['reference'];row=m.load(path);priorrefs.append(v['reference'])
  if row['state']=='captured_exact_inventory':seen_prior.add(parse_qs(urlsplit(row['object_url']).query)['irn'][0])
 initial=m.load(RUN/'initial-scope-001.json.gz');titles={m.norm(v['title']) for v in initial['snapshot']['artworks']};probe=m.load(RUN/'native-list-probe-002.json');url=probe['url'];pages=[];rows=[];selected=0;seen=set()
 for page in range(1,5):
  raw,cap=n.capture('ferens',url);items,nexturl=index(raw,url);pagepath=RUN/'index-selected-001'/('%03d.json'%page);assert not pagepath.exists();m.save(pagepath,dict(at=m.now(),page=page,capture=cap,rows=items,next_url=nexturl));pages.append(ref(pagepath))
  for v in items:
   assert v['source_id'] not in seen;seen.add(v['source_id']);date=creation(v['date']);state='selected_detail_review'
   if v['source_id'] in seen_prior:state='previously_reviewed_native_object'
   elif m.norm(v['title']) in titles:state='existing_museum_title_lead'
   elif not date or date['first']<100 or date['last']>1970:state='date_requires_review_or_outside_scope'
   elif selected>=180:state='bounded_selection_limit'
   else:selected+=1
   rows.append(dict(number=len(rows)+1,index=v,date=date,state=state,index_reference=ref(pagepath)))
  print(json.dumps(dict(page=page,index_rows=len(rows),selected=selected)),flush=True)
  if selected>=180 or not nexturl:break
  url=nexturl
 m.save(dest,dict(at=m.now(),rows=rows,selected_count=selected,index_references=pages,script_reference=ref(Path(__file__).resolve()),prior_native_references=priorrefs,initial_reference=ref(RUN/'initial-scope-001.json.gz'),policy='At most4 pages of96 short metadata records from1252 painting results; at most180 detail requests selected before fetching. Prior native objects and existing museum title leads retained separately,not reimported. Unknown/post1970 dates deferred. Native date bounds are screening only; detailed creation context,creator qualifications and cross-catalogue physical identity require editorial review. Anonymous and Russian icon records are included when source date is explicit. No images.'))
 print(json.dumps(dict(selected=selected,states=dict(collections.Counter(r['state'] for r in rows)))),flush=True)
if __name__=='__main__':main()
