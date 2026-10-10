"""Literal York native object facts retain roles, date strings, aliases and physical counts."""
import collections,datetime,gzip,hashlib,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-york-additions-common-20261009.py');o=module('o','museum-expansion-york-additions-objects-20261009.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
def date_value(v):
 if re.fullmatch(r'\d{4}',v or ''):return int(v)
 if re.fullmatch(r'\d{4}-\d\d',v or ''):datetime.datetime.strptime(v,'%Y-%m');return int(v[:4])
 if re.fullmatch(r'\d{4}-\d\d-\d\d',v or ''):datetime.date.fromisoformat(v);return int(v[:4])
 raise ValueError('Unreviewed native production-date format: '+str(v))
def one(fs,key):
 values=fs.get(key,[]);assert len(values)==1 and values[0],(key,values);return values[0]
def maker(v):
 value=re.sub(r'\s*\(Artist\)$','',v).strip()
 if value in ['Unknown','Unknown artist','Anonymous']:return 'Unidentified artist'
 if ',' not in value:return value
 qualifier=''
 match=re.search(r'\s+(\([^()]+\))$',value)
 if match:qualifier=' '+match[1];value=value[:match.start()]
 parts=[p.strip() for p in value.split(',')]
 if len(parts)==2:return parts[1]+' '+parts[0]+qualifier
 if len(parts)==3 and parts[-1] in ['Sir','Dame']:return parts[-1]+' '+parts[1]+' '+parts[0]+qualifier
 return value
def facts(r):
 assert r.get('capture') and r['capture']['receipt']['status']==200;raw=gzip.decompress((m.ROOT/r['capture']['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==r['capture']['receipt']['sha256'];assert o.parsed(raw)==r['parsed'];fs=r['parsed']['fields'];issues=[];assert fs['Collection']==['Fine Art'] and fs['Object name']==['Painting'] and fs['Object category']==['Painting'];assert one(fs,'ID')==r['native_id'];inv=one(fs,'Object number');assert re.fullmatch(r'YORAG\s*:\s*[A-Za-z0-9. /()-]+',inv) and inv==r['index']['fields']['object_number'];titles=[v for v in fs['Title'] if v];title=r['index']['fields']['title'];assert m.norm(title) in {m.norm(t) for t in titles};source_makers=[v for v in fs.get('Creators',[]) if v not in ['', '()', '(Artist)']];labels=[maker(v) for v in source_makers];unidentified=not labels or all(v=='Unidentified artist' for v in labels)
 if not labels:labels=['Unidentified artist'];issues.append('creator_field_absent')
 if len(labels)>1:creator='Source attribution unresolved: '+'; '.join(labels);issues.append('multiple_source_creator_labels')
 else:creator=labels[0]
 if any(re.search(r'\b(?:attributed|after|workshop|school|manner|circle|follower|copy|formerly|unknown|unidentified)\b',v,re.I) for v in labels):issues.append('qualified_or_unidentified_creator')
 start=one(fs,'Production date start');end=one(fs,'Production date end') if fs.get('Production date end') else start;first,last=date_value(start),date_value(end);assert 100<=first<=last<=1970;precision='exact' if first==last else 'range';display=start if start==end else start+'–'+end
 if len(start)>4 or len(end)>4:issues.append('native_date_has_month_or_day')
 count=one(fs,'Number of objects')
 if count!='1':issues.append('multiple_physical_objects')
 description=' '.join(fs.get('Description',[]))
 if re.search(r'\b(?:recto|verso|after|copy|copies|panels?|triptych|wings?|fragment|study|sketch|version|repetition|replica)\b',title+' '+description,re.I):issues.append('version_or_component_requires_review')
 if re.search(r'\b(?:missing|stolen|restituted|deaccessioned|returned to|loan|lent by)\b',description,re.I):issues.append('holding_history_requires_review')
 if re.search(r'\b(?:circa|about|before|after|c\.)\s*\d{4}',description,re.I):issues.append('description_date_qualification')
 canonical='https://www.yorkmuseumstrust.org.uk/index.php?'+urlencode({'page_id':13,'id':r['native_id']});urls=list(dict.fromkeys([canonical,canonical.replace('www.yorkmuseumstrust','yorkmuseumstrust'),r['index']['url'],r['capture']['receipt']['final_url']]))
 return dict(source_id=r['source_id'],native_id=r['native_id'],source_url=canonical,source_retrieved_url=r['capture']['receipt']['url'],title=title,titles=sorted(set(titles)),creator_label=creator,identity_creator_labels=labels,source_artist_fields=source_makers,unidentified_creator=unidentified,source_fields=dict(fs,ATTRIBUZIONI=creator),inventory=inv,normalized_inventory=inv,alternative_inventories=fs.get('Alternative number',[]),date_display=display,first=first,last=last,date_precision=precision,native_date_start=start,native_date_end=fs.get('Production date end'),work_type='painting',object_form=None,medium='; '.join(fs.get('Materials',[])) or None,dimensions_text='; '.join(fs.get('Dimensions',[])) or None,description=description,physical_object_count=count,native_page_urls=urls,native_metadata_urls=[],artuk_url='',museum_qid=s.QID,issues=issues)
def rows():
 out=[];errors=[]
 for r in m.load(RUN/'selected-objects-001.json.gz')['rows']:
  try:f=facts(r);out.append(dict(number=r['number'],source_id=r['source_id'],institution_id=s.IID,facts=f,issues=f['issues']))
  except Exception as e:errors.append(dict(number=r['number'],error=type(e).__name__+': '+str(e)))
 return out,errors
def main():
 rs,errors=rows();dest=RUN/'candidate-facts-001.json.gz';assert not dest.exists();m.save(dest,dict(at=m.now(),rows=rs,source_fact_holds=errors,source_reference=ref(RUN/'selected-objects-001.json.gz'),parser_reference=ref(Path(__file__).resolve()),policy='Literal native production-date fields,not inferred creation from accession or maker lifespan. Multiple source maker labels qualified as unresolved relationships,not joint authorship. Museum inventory establishes collection association only. No image or current-display claim.'));print(json.dumps(dict(rows=len(rs),errors=errors,issues=dict(collections.Counter(i for r in rs for i in r['issues'])))),flush=True)
if __name__=='__main__':main()
