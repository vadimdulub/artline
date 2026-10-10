#!/usr/bin/env python3
"""Read selected LUX Linked Art facts, preserving qualifiers and merged-source limits."""
import importlib.util,json,re,collections
from pathlib import Path
from functools import lru_cache
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-yale-lux-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
s=importlib.util.spec_from_file_location('dates',Path(__file__).with_name('museum-expansion-birmingham-facts-20261007.py'));dates=importlib.util.module_from_spec(s);s.loader.exec_module(dates)
m=c.m;d=c.d;RUN=c.RUN;ref=c.ref
def creation(raw):
 t=raw or ''
 if re.fullmatch(r'\d{3,4}\(\?\)',t):t='c. '+t[:-3]
 t=re.sub(r'^(early|mid|late) to (early|mid|late)-(?=\d{1,2}(?:st|nd|rd|th) century$)','',t)
 return dates.creation(t)
GALLERY=c.BASE+'/data/group/41310ca5-8137-45fe-ac2c-a6a04e2235f1'
def classified(x,aat):
 return any(v.get('id')=='http://vocab.getty.edu/aat/'+aat or any(e.get('id')=='http://vocab.getty.edu/aat/'+aat for e in v.get('equivalent',[])) for v in x.get('classified_as',[]))
def statements(x,aat):return [v['content'] for v in x.get('referred_to_by',[]) if classified(v,aat) and v.get('content')]
def one(values):return values[0] if len(values)==1 else None
@lru_cache(maxsize=16)
def index_rows(path,digest):
 p=m.ROOT/path;assert ref(p)['sha256']==digest;x=m.load(p);return json.loads(c.body(x['capture']))['orderedItems']
def checked_record(path):
 x=m.load(path);p=json.loads(c.body(x['capture']));assert p==x['parsed'];assert p['id']==x['index']['id']==x['capture']['receipt']['url']==x['capture']['receipt']['final_url']
 for r in x['index']['index_refs']:assert dict(id=p['id'],type=p['type']) in index_rows(r['path'],r['sha256'])
 return x,p
def creator_nodes(p):
 out=[]
 def walk(v,depth):
  assert depth<6
  desc=statements(v,'300435446')
  if desc or v.get('carried_out_by') or v.get('influenced_by'):out.append(dict(description=desc,actors=v.get('carried_out_by',[]),influenced_by=v.get('influenced_by',[]),classifications=v.get('classified_as',[]),full_production_part=v))
  for child in v.get('part',[]):walk(child,depth+1)
 walk(p.get('produced_by',{}),0);return out
def creator_label(text):
 # Only the literal Artist role and trailing nationality/lifespan are separated.
 # Attributed to, after, workshop, unknown and parenthetical maker qualifiers stay.
 text=re.sub(r'^Artist:\s*','',text)
 return re.sub(r'\s*\([^()]*\b\d{3,4}[^()]*\)\s*$','',text).strip()
def facts(x,p):
 ids=p.get('identified_by',[]);inventory=[v['content'] for v in ids if v.get('type')=='Identifier' and classified(v,'300312355')]
 native_urls=[v['id'] for v in p.get('equivalent',[]) if re.fullmatch(r'https://media\.art\.yale\.edu/content/lux/obj/\d+\.json',v['id'])]
 native_ids=[u.rsplit('/',1)[1][:-5] for u in native_urls]
 system_ids=[v['content'] for v in ids if v.get('type')=='Identifier' and classified(v,'300435704')]
 title=p.get('_label');titles=list(dict.fromkeys([title]+[v['content'] for v in ids if v.get('type')=='Name']))
 parts=creator_nodes(p);descs=list(dict.fromkeys(t for v in parts for t in v['description']))
 current_parts=[v for v in parts if not (v['description'] and all(re.match(r'^Artist, formerly attributed to:',t) for t in v['description']))]
 current_descs=list(dict.fromkeys(t for v in current_parts for t in v['description']));labels=[creator_label(t) for t in current_descs]
 timespan=p.get('produced_by',{}).get('timespan',{});date_labels=[v['content'] for v in timespan.get('identified_by',[]) if v.get('type')=='Name'];date=one(date_labels);dt=creation(date)
 if dt['date_issue'] is None:
  end=timespan.get('end_of_the_end');begin=timespan.get('begin_of_the_begin')
  if end and re.match(r'^\d{4}-',end) and int(end[:4])>1970:dt['date_issue']='LUX production bounds cross cutoff despite display label'
  if dt['first'] is not None and begin and end and re.match(r'^\d{4}-',begin) and re.match(r'^\d{4}-',end) and (dt['last']<int(begin[:4]) or dt['first']>int(end[:4])):dt['date_issue']='Display creation and merged LUX production bounds disagree'
 credit=statements(p,'300435418');medium=statements(p,'300435429');dimensions=statements(p,'300435430');provenance=statements(p,'300435438')
 return dict(source_id=p['id'].rsplit('/',1)[1],source_url=p['id'],native_object_id=one(native_ids),native_metadata_urls=native_urls,native_page_urls=['https://artgallery.yale.edu/collections/objects/'+v for v in native_ids],system_ids=system_ids,wikidata_ids=[v['id'].rsplit('/',1)[1] for v in p.get('equivalent',[]) if v['id'].startswith('http://www.wikidata.org/entity/')],title=title,titles=titles,creator_label='; '.join(labels) or None,detail_creator_label='; '.join(labels) or None,identity_creator_labels=[creator_label(t) for t in descs],creator_fields=current_parts,all_production_roles=parts,native_artist_field='; '.join(descs) or None,date_display=date,date_labels=date_labels,production_timespan=timespan,**dt,inventory=one(inventory),source_inventories=inventory,medium=one(medium),source_media=medium,dimensions_text='; '.join(dimensions) or None,work_type='painting' if classified(p,'300033618') else 'unknown',object_form=None,credit_line='; '.join(credit) or None,provenance_text='; '.join(provenance) or None,source_owner=p.get('current_owner',[]),source_collection=p.get('member_of',[]),source_fields=p.get('referred_to_by',[]),production=p.get('produced_by'),source_note='Official public Yale LUX JSON-LD is an aggregation of museum Linked Art and external equivalent records. Literal production display supplies dates; machine bounds alone do not replace a missing date label. Original qualifiers, native IDs, accessions, references, provenance, rights and date bounds retained. Museum collection connection does not establish current display, custody or legal title. No images downloaded.')
def source_holds(f,p):
 holds=[]
 if f['date_issue']:holds.append(f['date_issue'])
 if not f['title'] or f['title'] not in [v['content'] for v in p.get('identified_by',[]) if v.get('type')=='Name' and classified(v,'300404670')]:holds.append('No agreeing primary title')
 if p.get('type')!='HumanMadeObject' or f['work_type']!='painting':holds.append('Outside selected physical paintings')
 if not f['inventory'] or not f['native_object_id'] or f['native_object_id'] not in f['system_ids']:holds.append('Missing or conflicting native accession/system identity')
 if [v['id'] for v in f['source_owner']]!=[GALLERY]:holds.append('No unique Gallery owner assignment in source')
 if not f['source_collection'] or not all('Yale University Art Gallery' in v.get('_label','') for v in f['source_collection']):holds.append('Departmental collection scope requires review')
 if not f['credit_line']:holds.append('No collection credit')
 elif re.search(r'\b(?:lent|loan|promised|deaccession|restitut|returned|private collection)\w*\b',f['credit_line'],re.I):holds.append('Collection credit requires loan/ownership review; owner field alone is insufficient')
 for v in f['creator_fields']:
  if len(v['description'])!=1 or len(v['actors'])+len(v['influenced_by'])!=1:holds.append('Unresolved production-role structure requires review');continue
  if v['influenced_by'] and not re.match(r'^(?:Artist, (?:follower of|copy after|workshop of|school of|circle of|manner of):|After:)',v['description'][0]):holds.append('Influence relationship without a clear literal maker qualification')
 # No supplied current maker remains NULL. Former attributions are evidence and
 # identity leads, not a current maker. Anonymous works are not excluded here.
 if len(f['source_media'])>1:holds.append('Multiple source medium descriptions')
 return holds
def candidates():
 out=[]
 for reference in m.load(RUN/'selected-capture-001.json.gz')['records']:
  path=m.ROOT/reference['path'];assert ref(path)==reference;x,p=checked_record(path);f=facts(x,p);holds=source_holds(f,p)
  out.append(dict(source_id=f['source_id'],facts=f,index=x['index'],source_reference=reference,state='source_hold' if holds else 'candidate',reasons=holds))
 m.save(RUN/'native-candidates-001.json.gz',dict(at=m.now(),rows=out,counts=dict(collections.Counter(r['state'] for r in out)),policy='Evidence candidates only; loans, unknown display dates, incompatible machine dates and complex roles preserved in follow-up. No database writes.'))
 print(collections.Counter(r['state'] for r in out),flush=True)
if __name__=='__main__':candidates()
