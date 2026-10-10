"""Literal Acropolis object facts; BC/AD dates and qualified creators preserved."""
import collections,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-acropolis-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
SITE='https://www.theacropolismuseum.gr'
def invkey(v):
 return re.sub(r'\s+','',m.norm(v)).replace('acr','ακρ').replace('akr','ακρ').replace('nma','νμα').replace('eam','εαμ')
def date(v):
 raw=v or'Creation date under review';t=re.sub(r'\s+',' ',raw).replace('–','-').strip();qual=bool(re.search(r'around|probably|circa',t,re.I));note=None
 def out(a,b,p,n=None):
  assert a is None or -10000<=a<=1970
  assert b is None or(a is not None and a<=b<=1970)
  assert a!=0 and b!=0
  return a,b,p,raw,n
 t=re.sub(r'^(?:Around|Probably)\s+','',t,flags=re.I)
 if re.fullmatch(r'After \d+ BC',t):return out(-int(re.search(r'\d+',t)[0]),None,'after','Open-ended source date retained; not automatically date-eligible.')
 if re.fullmatch(r'\d+ BC or shortly after',t):return out(-int(re.search(r'\d+',t)[0]),None,'after','Source says this year or shortly after; no invented upper boundary.')
 if t=='After the middle of the 2nd cent. BC':return out(-150,None,'after','Open-ended after-middle source date, not automatically date-eligible.')
 v=re.fullmatch(r'(?:AD )?(\d+)(?:\s*[-/]\s*(\d+))?\s*(BC|AD)?',t)
 if v:
  a=int(v[1]);b=int(v[2]or v[1]);era=v[3]or('AD'if t.startswith('AD ')else None)
  if era is None:raise ValueError('Missing explicit era: '+raw)
  if v[2]and '/'in t and len(v[2])<len(v[1]):b=int(v[1][:-len(v[2])]+v[2])
  if era=='BC':a,b=-a,-b
  return out(a,b,'circa_range'if qual and a!=b else'circa'if qual else'range'if a!=b else'exact')
 v=re.fullmatch(r'(\d+) BC-AD (\d+)',t)
 if v:return out(-int(v[1]),int(v[2]),'circa_range'if qual else'range')
 # Full-century envelopes retain original beginning/end/mid qualifiers in display;
 # no invented quarter-century boundary or false exact creation year.
 pattern=r'(?:(?:the )?(?:Beginning of|beginning of|End of|end of|Mid|mid) )?(\d+)(?:st|nd|rd|th)(?: cent\.)?(?: (BC|AD))?'
 vals=list(re.finditer(pattern,t));century='cent.'in t
 if century and len(vals)in[1,2]and len(re.findall(r'\d+',t))==len(vals):
  last_era=next((v[2]for v in reversed(vals)if v[2]),None)
  if last_era is None:raise ValueError(raw)
  eras=[v[2]or last_era for v in vals];numbers=[int(v[1])for v in vals]
  def bounds(c,e):return(-100*c,-100*(c-1)-1)if e=='BC'else(100*(c-1)+1,100*c)
  a=bounds(numbers[0],eras[0])[0];b=bounds(numbers[-1],eras[-1])[1]
  return out(a,b,'circa_range'if qual else'century'if len(vals)==1 else'range','Conservative full-century envelope; literal source qualifiers retained without invented narrow boundaries.')
 raise ValueError('Unhandled literal date: '+raw)
def rows():
 source=m.load(RUN/'native-details-001.json.gz');base=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];byinv={invkey(a['accession_number']):a['id']for a in base['artworks']if a['accession_number']};out=[];known=[];held=[]
 for row in source['rows']:
  n=row['number'];fs=row['fields'];inv=fs['Inventory number'];title=row['title'];sid=row['source_url'].split('/en/',1)[1]
  if invkey(inv)in byinv:known.append(dict(number=n,source_id=sid,existing_artwork_id=byinv[invkey(inv)],reason='Exact museum-scoped inventory; original title,dimensions and source page retained for comparison.',raw=row));continue
  try:a,b,p,display,note=date(fs.get('Date'))
  except ValueError as e:held.append(dict(number=n,source_id=sid,reason=str(e),raw=row));continue
  assert fs['Category']=='Sculpture';creator=fs.get('Artist')or'Anonymous / unknown sculptor';urls=list(dict.fromkeys([row['source_url'],row['canonical_url']]))
  facts=dict(source_id=sid,native_id=sid.replace('/','-'),title=title,titles=[title],creator_label=creator,first=a,last=b,date_precision=p,date_display=display,date_note=note,work_type='sculpture',object_form=None,medium=fs.get('Material')or None,dimensions_text=fs.get('Dimensions')or None,inventory=inv,alternative_inventories=[inv],source_url=row['source_url'],native_page_urls=urls,native_metadata_urls=[],source_fields=row)
  out.append(dict(number=n,source_id=sid,institution_id=s.IID,facts=facts,retrieved_at=row['receipt']['retrieved_at'],source_reference=ref(RUN/'native-details-001.json.gz')))
 return out,held,known
if __name__=='__main__':
 out,held,known=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,held=held,existing=known,script_reference=ref(Path(__file__).resolve())));print(json.dumps(dict(candidates=len(out),held=[(v['number'],v['reason'])for v in held],already=len(known),dates=dict(collections.Counter(v['facts']['date_precision']for v in out))),ensure_ascii=False))
