#!/usr/bin/env python3
"""Preserve native Belvedere facts and source uncertainty; no database writes."""
import importlib.util,re,collections
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-belvedere-native-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
m=c.m;d=c.d;RUN=c.RUN;ref=c.ref;checked_record=c.checked_record;creation=c.creation
def facts(x,p):
 fields={r['label']:r['value'] for r in p['fields']};creators=[r for r in p['fields'] if 'peopleField' in r['classes'] and r['label'] in ['Artist','Maker','Attribution to','Perimeter']]
 # The same peopleField class also marks depicted sitters. Respect its role.
 # Nested uncertainty parentheses can occur within an authority lifespan.
 clean_creator=lambda r:re.sub(r'\s*\([^()]*\b\d{3,4}\b.*\)$','',r['creator_with_biography']).strip()
 creator='; '.join(('Attributed to ' if r['label']=='Attribution to' else '')+clean_creator(r) for r in creators) or None
 index_names=[clean_creator(r).removesuffix(' (Umkreis)') for r in creators]
 identity_names=[clean_creator(r) for r in p['fields'] if 'peopleField' in r['classes'] and r['label'] in ['Artist','Maker','Attribution to','Perimeter','Earlier attribution to']]
 title=p['title'];titles=[title];date=fields.get('Date');caption_titles=[]
 for caption in p['captions']:
  # Additional literal-language title is only a discovery lead. Never invent
  # an alternate catalogue title or infer metadata from the image itself.
  if not creator or not caption.startswith(creator+', ') or not date:continue
  germandate=re.sub(r'^c\.\s*','um ',date);germandate=re.sub(r'^before ','vor ',germandate);germandate=re.sub(r'^after ','nach ',germandate)
  for dt in [date,germandate]:
   value=caption[len(creator)+2:];marker=', '+dt+', '
   if marker in value:caption_titles.append(value.split(marker)[0]);break
 titles.extend(caption_titles)
 return dict(source_id=x['index']['source_id'],source_url=x['index']['url'],native_object_id=x['index']['source_id'],index_internal_id=x['index']['index_internal_id'],title=title,titles=list(dict.fromkeys(titles)),caption_title_leads=caption_titles,creator_label=creator,detail_creator_label=creator,index_creator_names=index_names,identity_creator_labels=identity_names,native_artist_field='; '.join(r['creator_with_biography'] for r in creators) or None,creator_fields=creators,date_display=date,**creation(date),inventory=fields.get('Inventory number'),medium=fields.get('Medium'),dimensions_text=fields.get('Dimensions'),work_type={'Painting':'painting','Drawing':'drawing','Print':'print','Sculpture':'sculpture'}.get(fields.get('Object type'),'unknown'),object_form=None,source_work_type=fields.get('Object type'),credit_line=fields.get('Credit Line'),provenance_text=(p['history_text'] or '').split('Contact Provenance Research')[0],history_text=p['history_text'],history_html=p['history_html'],source_fields=p['fields'],captions=p['captions'],source_note='Official Belvedere object HTML and HTTP receipts. Literal creator qualifications, biography, creation dates, provenance, caption language, rights and source display text remain evidence. Only creation fields supply dates. Source location/display text is not projected into a display assertion. Native URL object number is separate from accession and internal index ID.')
def candidates():
 out=[];refs=m.load(RUN/'selected-capture-001.json.gz')['records']
 for reference in refs:
  path=m.ROOT/reference['path'];assert ref(path)==reference;x,p=checked_record(path);f=facts(x,p);holds=[]
  if f['date_issue']:holds.append(f['date_issue'])
  if not f['inventory']:holds.append('No inventory supplied')
  if len(f['creator_fields'])!=1:holds.append('Missing or multiple creator fields require attribution review')
  repeated=collections.Counter(r['label'] for r in p['fields'])
  if any(repeated[k]>1 for k in ['Date','Object type','Medium','Dimensions','Inventory number','Artist','Maker']):holds.append('Repeated identity or physical-object field requires review')
  if f['title']!=x['index']['title']:holds.append('Index/object title discrepancy')
  if m.norm(x['index']['creator_label']) not in [m.norm(n) for n in f['index_creator_names']]:holds.append('Index/object creator discrepancy; retain all qualifications')
  if f['date_display']!=x['index']['date_display']:holds.append('Index/object creation wording discrepancy')
  if not f['history_text'] and not f['credit_line']:holds.append('No object acquisition/history evidence')
  if not any('Belvedere' in t and str(f['inventory']) in t for t in f['captions']):holds.append('No caption agreeing on museum and inventory')
  out.append(dict(source_id=f['source_id'],facts=f,index=x['index'],source_reference=reference,state='source_hold' if holds else 'candidate',reasons=holds))
 m.save(RUN/'native-candidates-002.json.gz',dict(at=m.now(),rows=out,counts=dict(collections.Counter(r['state'] for r in out)),policy='Candidate facts only; provenance, custody, identity, version and grouping review required. Source explicit before dates preserve unknown lower bounds. Current attribution roles are distinguished from former attributions and depicted people; index creator names are abbreviated identity leads, never authority for dropping source qualifications.'))
 print(collections.Counter(r['state'] for r in out),flush=True)
if __name__=='__main__':candidates()
