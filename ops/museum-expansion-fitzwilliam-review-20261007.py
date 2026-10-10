#!/usr/bin/env python3
"""Read-only Fitzwilliam source validation and candidate extraction. No catalogue writes."""
import argparse,copy,gzip,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-fitzwilliam-native-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;RUN=f.RUN;IID=f.IID

def compact(v):return re.sub(r'[^a-z0-9]','',m.norm(v or ''))
def clean(v):return re.sub(r'\s+',' ',v).strip()
def values(rows):return [r['value'] for r in rows if r.get('value')]
def checked_reference(ref):
 p=m.ROOT/ref['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==ref['sha256'];return p
def checked_object(ref):
 x=m.load(checked_reference(ref));sid=x['index']['source_id'];url=f.BASE+'/id/object/'+sid;assert x['url']==url
 for key,suffix in [('native',''),('json','?format=json')]:
  cap=x[key]['capture'];rc=cap['receipt'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes())
  assert rc['status']==200 and rc['url']==rc['final_url']==url+suffix and hashlib.sha256(raw).hexdigest()==rc['sha256']
  assert (f.parse_page(raw) if key=='native' else json.loads(raw))==x[key]['parsed']
 assert url+'?format=json' in x['native']['parsed']['json_links']
 assert x['json']['parsed']['admin']['id']=='object-'+sid and x['json']['parsed']['admin']['uri']==url
 return x

def date_facts(creation):
 assert len(creation)==1,'multiple or missing creation events'
 c=creation[0];dates=c.get('date',[]);periods=[p['summary_title'] for p in c.get('periods',[])]
 if dates:
  assert len(dates)==1,'multiple alternative production dates'
  d=dates[0];ends=[d['from'],d['to']] if d.get('range') else [d]
  assert not (set(d)-{'earliest','latest','value','precision','era','from','to','range','note'}),'unreviewed production date fields'
  years=[];circa=False;parts=[]
  for e in ends:
   assert e.get('era',['CE'])==['CE'],'non-CE creation date'
   assert e.get('precision','') in ['','circa','c.'],'open-ended or uncertain date qualifier'
   assert re.fullmatch(r'\d{3,4}',str(e.get('value',''))),'non-year literal production date'
   year=int(e['value']);assert e['earliest']==e['latest']==year,'machine date differs from literal'
   years.append(year);circa|=bool(e.get('precision'));parts.append(('c. ' if e.get('precision') else '')+str(year))
  first,last=years[0],years[-1];assert d['earliest']==first and d['latest']==last,'inconsistent date bounds'
  precision=('circa_range' if circa else 'range') if len(ends)==2 else ('circa' if circa else 'exact')
  return dict(first=first,last=last,date_precision=precision,date_display='–'.join(parts),date_basis='Explicit lifecycle.creation.date; source literals and notes retained.',date_notes=values(d.get('note',[])))
 assert periods,'creation date and period absent'
 spans=[]
 for period in periods:
  # Preserve early/mid/late wording. Use the whole named century as a conservative
  # search envelope, never invent narrower sub-century years or a single year.
  for part in period.split('-'):
   match=re.fullmatch(r'(\d{1,2})(?:st|nd|rd|th) Century(?:, (?:Early|Mid|Late|first half|second half))?',part)
   if match:
    century=int(match[1]);spans.append(((century-1)*100,century*100-1));continue
   match=re.fullmatch(r'(\d{3}0)s',part);assert match,'unreviewed period: '+part
   decade=int(match[1]);spans.append((decade,decade+9))
 first=min(a for a,b in spans);last=max(b for a,b in spans)
 return dict(first=first,last=last,date_precision='century' if len(spans)==1 and last-first==99 else ('decade' if len(spans)==1 and last-first==9 else 'range'),date_display='; '.join(periods),date_basis='Explicit creation period in publicly linked museum JSON. Whole named century/decade envelope; literal early/mid/late wording retained without inferred subdivision.',date_notes=[])

def source_facts(x):
 j=x['json']['parsed'];cre=j.get('lifecycle',{}).get('creation',[]);names=[n['reference']['summary_title'] for n in j.get('name',[])];cats=[n['summary_title'] for n in j.get('categories',[])];titles=values(j.get('title',[]));inv=[a['value'] for a in j.get('identifier',[]) if a.get('type')=='accession number'];makers=[a for c in cre for a in c.get('maker',[])];sections=x['native']['parsed']['sections']
 labels=[a['summary_title']+(' ('+a['@link']['qualifier'].strip('()')+')' if a.get('@link',{}).get('qualifier') else '') for a in makers]
 out=dict(source_id=x['index']['source_id'],source_url=x['url'],title=titles[0] if titles else None,titles=titles,inventory=inv[0] if len(inv)==1 else None,creator_label='; '.join(labels) or None,maker_records=makers,entity_names=names,categories=cats,creation=cre,acquisition=j.get('lifecycle',{}).get('acquisition',[]),owners=j.get('owners',[]),source_identifiers=j.get('identifier',[]),source_modified=j['admin'].get('modified'),medium='; '.join(values(t.get('description',[]))[0] for t in j.get('techniques',[]) if values(t.get('description',[]))) or None,dimensions_text='; '.join(clean(v) for v in sections.get('Measurements and weight',[])) or None,school_or_style=[t['summary_title'] for t in j.get('school_or_style',[])],notes={k:v for k,v in sections.items() if k in ['Description','Note','Notes','Legal notes','Maker(s)','Dating','Current Location']},creation_notes=[v for c in cre for v in values(c.get('note',[]))],object_form='icon' if names==['icon'] else None)
 out['work_type']=({'painting':'painting','miniature (painting)':'manuscript_illumination','icon':'painting','relief':'sculpture','printing plate':'unknown','print':'print'}.get(names[0],'unknown') if len(names)==1 else 'unknown')
 if names==['miniature (painting)'] and not any('manuscript' in c.lower() for c in cats):out['work_type']='painting'
 out['date_issue']=None
 try:out.update(date_facts(cre))
 except AssertionError as error:out['date_issue']=str(error)
 return out

def candidates(suffix):
 dest=RUN/f'native-candidates-{suffix}.json.gz';assert not dest.exists();rows=[]
 for p in sorted((RUN/'native-objects-001').glob('*.json.gz'),key=lambda p:int(p.name.split('.')[0])):
  ref=f.reference(p);x=checked_object(ref);facts=source_facts(x);holds=[]
  if facts['date_issue']:holds.append(facts['date_issue'])
  elif not 1<=facts['first']<=facts['last']<=1970:holds.append('outside pre-1971 creation scope')
  if not facts['title'] or not facts['inventory'] or not facts['creator_label']:holds.append('incomplete title/inventory/creator')
  if facts['entity_names'] not in [['painting'],['icon'],['relief'],['miniature (painting)'],['printing plate'],['print']]:holds.append('object type requires separate review')
  if len(facts['owners'])!=1 or facts['owners'][0]['summary_title']!='The Fitzwilliam Museum':holds.append('holding identity requires separate review')
  methods=[a.get('method',{}).get('value') for a in facts['acquisition']]
  if len(methods)!=1 or methods[0] not in ['bought','bequeathed','given']:holds.append('acquisition/loan status requires separate review')
  rows.append(dict(source_id=facts['source_id'],facts=facts,state='source_hold' if holds else 'candidate',holds=holds,source_reference=ref))
 m.save(dest,dict(at=m.now(),rows=rows,captured=len(rows),policy='Source gates only; candidate is not approval. No catalogue writes. Period envelopes are conservative; acquisition and biographical dates never substitute for creation. All candidates require duplicate/version and narrative review.'))
 print(json.dumps(dict(captured=len(rows),candidates=sum(r['state']=='candidate' for r in rows),held=sum(r['state']=='source_hold' for r in rows))))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);candidates(a.suffix)
