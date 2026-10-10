#!/usr/bin/env python3
"""Reparse retained official Wallace evidence; candidates are not approvals."""
import argparse,collections,importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-wallace-capture-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c);d=c.d;m=c.m;RUN=c.RUN;ref=c.ref
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-dulwich-web-review-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)

def creation(raw):
 value=re.sub(r'^about\s+','c. ',raw or '',flags=re.I)
 # Both alternatives lie in the same explicitly named period. Preserve the
 # whole period and original wording, rather than inventing subdivision years.
 value=re.sub(r'^(?:early|mid|late) or (?:early|mid|late) (\d{1,2}(?:st|nd|rd|th) century)$',r'\1',value,flags=re.I)
 return dates.creation(value)

def checked_record(path):
 record=m.load(path);assert 'error' not in record
 r=record['index_reference'];p=m.ROOT/r['path'];assert ref(p)==r;idx=m.load(p);parsed_index=c.index(c.saved_body(idx['capture']),idx['url'],idx['capture'])
 assert parsed_index['rows']==idx['rows'] and parsed_index['next_url']==idx['next_url'];row=record['index_row'];assert row in idx['rows']
 parsed=c.object_page(c.saved_body(record['capture']),row['click_url']);assert parsed==record['parsed']
 for key in ['title','creator_label','date_display']:assert parsed[key]==row[key]
 assert record['capture']['receipt']['url']==row['click_url'] and record['capture']['receipt']['status']==200
 tabs={}
 for tab in record.get('tabs',[]):
  assert 'error' not in tab;request=tab['request'];assert request in parsed['tabs']
  again=c.object_page(c.saved_body(tab['capture']),request['url']);assert again==tab['parsed'] and again['source_id']==parsed['source_id'] and again['active_tab']==request['label'];assert request['label'] not in tabs
  for k in ['title','creator_statement','date_display','medium','inventory','dimensions']:assert again[k]==parsed[k]
  tabs[request['label']]=again['active_text']
 expected={t['label'] for t in parsed['tabs'] if t['label'] in ['Provenance','Marks/Inscriptions']};assert set(tabs)==expected
 return record,parsed,tabs

def facts(record,parsed,tabs):
 p=parsed;medium=p['medium'];mt=(medium or '').casefold();work_type='painting' if mt.startswith(('oil on ','oil painting on ','painted on ')) else 'unknown'
 return dict(source_id=p['source_id'],source_url=p['source_url'],literal_bookmark=p['literal_bookmark'],title=p['title'],titles=[p['title']],creator_label=p['creator_label'],detail_creator_label=p['creator_label'],creator_statement=p['creator_statement'],date_display=p['date_display'],**creation(p['date_display']),medium=medium,dimensions_text='; '.join(v for v in p['dimensions'] if not v.startswith('Frame size:')) or None,all_dimensions=p['dimensions'],inventory=p['inventory'],work_type=work_type,object_form=None,description=p['active_text'] if p['active_tab']=='Description' else None,provenance=tabs.get('Provenance'),marks=tabs.get('Marks/Inscriptions'),location_label=p['location_label'],native_fields=p['fields'],date_basis='Literal object Date, not artist lifespan, acquisition or prototype date. About retained as circa; shortened numeric endpoints expanded within the same century only when ordered. Early/mid/late period statements retain the entire named century/decade and source qualifiers; no invented narrower boundaries.',source_limitation='Official native HTML and full provenance/inscription tabs where offered. Current collection catalogue is museum-connection evidence, not a fresh display record. Source statements and unresolved attribution/version issues require individual review.')

def candidates(pages,suffix):
 rows=[]
 for page in range(1,pages+1):
  index=RUN/'native-index-001'/f'page-{page:03}.json.gz';idx=m.load(index)
  for pos,row in enumerate(idx['rows']):
   path=RUN/'native-objects-001'/f'page-{page:03}-row-{pos:02}.json.gz';record=m.load(path)
   try:
    record,parsed,tabs=checked_record(path);v=facts(record,parsed,tabs);reasons=[]
    if v['date_issue']:reasons.append(v['date_issue'])
    if not v['inventory']:reasons.append('No native inventory; physical identity requires review')
    if not v['creator_label']:reasons.append('No explicit native creator/school label; retain unknown')
    rows.append(dict(source_id=v['source_id'],state='source_hold' if reasons else 'candidate',reasons=reasons,facts=v,index=row,source_reference=ref(path)))
   except Exception as ex:rows.append(dict(source_id=record.get('parsed',{}).get('source_id'),state='source_capture_hold',reason=type(ex).__name__+': '+str(ex),index=row,source_reference=ref(path)))
 goodids=[r['source_id'] for r in rows if r['source_id']];assert len(goodids)==len(set(goodids))
 dest=RUN/f'native-candidates-{suffix}.json.gz';assert not dest.exists();counts=dict(collections.Counter(r['state'] for r in rows));m.save(dest,dict(at=m.now(),rows=rows,counts=counts,index_pages=pages,policy='Bounded selected native metadata, with hashed index/object/tab chain. Candidate classification is not duplicate, attribution, version or publication approval. All narrative and uncertainty retained; no database writes.'));print(len(rows),counts,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pages',type=int,required=True);p.add_argument('--suffix',required=True);args=p.parse_args();assert re.fullmatch(r'\d{3}',args.suffix);candidates(args.pages,args.suffix)
