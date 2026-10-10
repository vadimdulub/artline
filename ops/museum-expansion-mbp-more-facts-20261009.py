"""MBP physical-object facts; edition dates and anonymous/qualified creators retained."""
import collections,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-mbp-more-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
def invkey(v):
 t=re.sub(r'\s+','',m.norm(v)).translate(str.maketrans({'b':'β','e':'ε','i':'ι','n':'ν','t':'τ'}))
 return re.sub(r'(?<=[^0-9])0+(?=[1-9])','',t)
def inventory(v):
 return (v.get('registry') or {}).get('number') or next((x.split(' : ',1)[1].strip() for x in (v.get('oldCode') or '').split(', ') if x.startswith('Κατάλογος ') and ' : ' in x),None)
HOLDS={
 698191:'BΨ13 and BΨ14 share a four-panel altar-floor description; parent and component identities need reconciliation.',
 698211:'BΨ14 and BΨ13 share a four-panel altar-floor description; parent and component identities need reconciliation.',
 968763:'Physical digital print was created in2007, beyond the creation cutoff. Its medieval model is not its creation date.',
 802566:'Structured1900–1999 impression period and narrative mid19th-century engraving require physical edition-date reconciliation.',
 754670:'AG3231/1 shares assembly stem with3231/31 and3231/9; resolve physical component/parent relationship before another count.',
 1042616:'Description distinguishes1849August4 and1845Gennadios signature; reconcile plate versus impression date before addition.',
 635183:'The physical paper impression explicitly dates to1977, despite the older1680–1720 woodblock period. Outside cutoff.',
 805614:'NET41Η record describes22Horarion paintings collectively; reconcile this component versus ensemble and other catalogue records.',
}

def kind(v):
 ts={t.get('en') for t in v.get('types') or []}
 if ts & {'Portable icon','Bilateral icon','Triptych','Altarscreen door','Labarum (liturgical textile)'}:return 'painting','icon'
 if 'Wallpainting' in ts:return 'fresco',None
 if ts & {'Wall mosaic','Floor mosaic','Mosaic'}:return 'unknown',None
 if ts & {'Double-sided panel','Corinthian capital','Capital','Colonette'}:return 'sculpture',None
 if 'Painting' in ts:return 'painting',None
 if ts & {'Etching','Engraving','Lithograph','Xylography','Chromolithograph','Overpainted etching','Overpainted lithograph','Colour etching'}:return 'print',None
 raise ValueError(ts)
def dates(v):
 def y(key):
  raw=v.get(key)
  if not raw:return None
  assert re.fullmatch(r'\d{4}-\d\d-\d\d',raw);return int(raw[:4])
 a,b=y('start'),y('end');rid=v['recordId'];note=None
 if a is None or b is None:return None,None,'unknown','Creation date under review',None
 assert 100<=a<=b<=2000
 p='exact' if a==b else 'range';display=str(a) if a==b else str(a)+'–'+str(b)
 if rid==635527:p='circa';display='c. 1820';note='Description explicitly qualifies Ca.1820; do not represent structured1820 as exact.'
 return a,b,p,display,note
def rows():
 source=m.load(RUN/'national-details-001.json.gz');base=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];byinv={invkey(a['accession_number']):a['id'] for a in base['artworks'] if a['accession_number']};byid={}
 for c in base['citations']:
  if (c.get('source_url') or '').startswith('https://nationalarchive.culture.gr/exhibits/'):byid[c['source_record_id']]=c['entity_id']
 out=[];held=[];existing=[]
 for row in source['rows']:
  n=row['number']
  v=row['raw'];rid=v['recordId'];sid=str(rid);inv=inventory(v);known=byid.get(sid) or byinv.get(invkey(inv))
  if rid==709797:known='d29f0ee1-aaf6-5a7b-9ec7-b317044f2c4f';assert known in {a['id']for a in base['artworks']}
  if known:existing.append(dict(number=n,source_id=sid,inventory=inv,existing_artwork_id=known,state='already_catalogued',basis='Exact national source identifier or museum-scoped inventory including Greek/Latin and zero-padding variants; object title/media checked.',raw=v));continue
  why=HOLDS.get(rid)
  if v.get('stolen') or v.get('lost'):why='Lost/stolen flag requires custody review.'
  assert v['storeLocation']['id']==6051 and v['provider']['providerId']==274
  if not inv:why=why or 'No unambiguous museum inventory.'
  if why:held.append(dict(number=n,source_id=sid,reason=why,raw=v));continue
  a,b,p,display,note=dates(v);wt,form=kind(v);title=' '.join((v['title'].get('en')or v['title']['gr']).split());creator='; '.join(t.get('en')or t.get('gr')or''for t in v.get('creators')or[])or'Anonymous / unknown creator'
  dims=[]
  for k,val in (v.get('dimensions')or{}).items():
   if val.get('value') not in [None,0]:dims.append(k+' '+str(val['value'])+' '+{'LENGTH_UNIT_CENTIMETERS':'cm','LENGTH_UNIT_METERS':'m','WEIGHT_UNIT_KILOGRAMS':'kg'}.get(val.get('unit'),val.get('unit')or''))
  u='https://nationalarchive.culture.gr/exhibits/'+sid;f=dict(source_id=sid,native_id=sid,title=title,titles=[title,v['title'].get('gr')or title],creator_label=creator,first=a,last=b,date_precision=p,date_display=display,date_note=note,work_type=wt,object_form=form,medium='; '.join(t.get('en')or t.get('gr')or''for t in v.get('materials')or[])or None,dimensions_text='; '.join(dims)or None,inventory=inv,alternative_inventories=[inv],source_url=u,native_page_urls=[u,'https://www.searchculture.gr/aggregator/edm/mnam/000150-'+sid+'?language=en'],native_metadata_urls=[row['receipt']['url']],source_fields=v)
  out.append(dict(number=n,source_id=sid,institution_id=s.IID,facts=f,retrieved_at=row['receipt']['retrieved_at'],source_reference=ref(RUN/'national-details-001.json.gz')))
 return out,held,existing
if __name__=='__main__':
 out,held,existing=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,held=held,existing=existing,script_reference=ref(Path(__file__).resolve())));print(json.dumps(dict(candidates=len(out),held=len(held),already=len(existing),types=dict(collections.Counter(v['facts']['work_type']for v in out)),dates=dict(collections.Counter(v['facts']['date_precision']for v in out))),ensure_ascii=False))
