#!/usr/bin/env python3
"""Literal Princeton object metadata; source dates and qualifiers remain explicit."""
import argparse,importlib.util,json,re,types
from pathlib import Path
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-princeton-native-20261007.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=n.RUN;IID=n.IID;ref=n.ref;checked=n.checked;QUEUE=RUN/'selected-metadata-queue-001.json'
def clean(value):return BeautifulSoup(value or '', 'html.parser').get_text(' ',strip=True) or None
def creation(d):
 first,last=d.get('datebegin'),d.get('dateend');display=d.get('displaydate');issue=None
 if type(first) is not int or type(last) is not int or not first or not last or first>last:issue='Missing, zero or reversed native creation bounds'
 elif last>1970:issue='Native creation bounds reach after1970'
 if not display or display.casefold() in ['undated','date unknown']:issue=issue or 'No literal creation date; native numeric classification requires editorial review'
 if re.search(r'printed later|printed.*or later',display or '',re.I):issue='Physical production date remains unbounded'
 if issue and (not first or not last or first>last):first=last=None
 circa=bool(re.search(r'\b(?:ca\.?|circa|about|approximately)\b',display or '',re.I))
 precision='unknown' if first is None else 'after' if re.match(r'after\b',display or '',re.I) else 'before' if re.match(r'before\b',display or '',re.I) else 'decade' if re.fullmatch(r'\d{3}0s',display or '') else 'century' if 'century' in (display or '').lower() else 'circa_range' if circa and first!=last else 'circa' if circa else 'exact' if first==last else 'range'
 return dict(first=first,last=last,date_precision=precision,date_issue=issue,date_basis='Native object-level datebegin/dateend, preserved exactly; neither maker biography nor accession year. Literal displaydate retained, including null. No invented circa tolerance.')
def kind(d):
 c=(d.get('classification') or '').lower();medium=(d.get('medium') or '').lower()
 if c=='manuscripts' and re.search(r'illuminat|tempera|paint',medium):return 'manuscript_illumination'
 if re.match(r'(?:oil|tempera|egg tempera|encaustic|acrylic)\b',medium):return 'painting'
 if c in ['paintings','painting']:return 'painting'
 if c in ['drawings','drawing']:return 'watercolor' if re.match(r'watercolou?r\b',medium) else 'drawing'
 if c in ['prints','print']:return 'print'
 if c in ['photographs','photograph','photography']:return 'photograph'
 if c in ['sculpture','sculptures']:return 'sculpture'
 if any(v.get('classification') in ['reliefs','sculpture','statuettes','statues','carvings'] for v in d.get('classifications',[])) and not re.search(r'bronze|iron|silver|gold',medium):return 'sculpture'
 if c in ['metal','metalwork']:return 'metalwork'
 if c in ['ceramics','ceramic']:return 'ceramic'
 if c in ['textiles','textile']:return 'textile'
 if any(v.get('classification') in ['reliefs','sculpture','statuettes','statues'] for v in d.get('classifications',[])):return 'sculpture'
 return 'unknown'
def creators(d):
 makers=d.get('makers') or [];labels=[]
 for v in makers:
  label=' '.join(str(v[k]).strip() for k in ['prefix','displayname','suffix'] if v.get(k))
  if v.get('role')=='Artist' and label and not re.search(r'formerly|former attribution',v.get('prefix') or '',re.I):labels.append(label)
  elif v.get('role') in ['Manufacturer','Manufactory','Scribe','Illuminator'] and label:labels.append(label if v.get('prefix') else v['role']+': '+label)
 if labels:return '; '.join(dict.fromkeys(labels)),'Native Artist-role displayname with all prefix/suffix qualifications'
 # Native cultural/period labels remain object labels, never invented people.
 for k in ['displayculture','displayperiod']:
  if d.get(k):return clean(d[k]),'Native '+k+'; cultural/period label, not a named person'
 labels=[v['culture'] for v in d.get('cultureterms',[]) if v.get('culture')]
 if not labels:labels=[v['period'] for v in d.get('periodterms',[]) if v.get('period')]
 return '; '.join(dict.fromkeys(labels)) or None,'Native culture/period terms; personal creator remains unknown'
def parse(path):
 x=m.load(path);checked(x['queue_reference']);q=m.load(QUEUE);row=next(r for r in q['selected'] if r['number']==x['number']);assert row==x['index']
 d=x['data'];assert json.loads(n.body(x['capture']))==d and str(d['objectid'])==row['source_id'] and d['type']=='artobject'
 assert x['url']==row['url']==x['capture']['receipt']['final_url'];sid=row['source_id'];flags=[]
 for key in ['objectnumber','displaytitle','displaydate','creditline','medium','dimensions']:
  if row['data'].get(key)!=d.get(key):flags.append('index_detail_'+key+'_difference')
 dates=creation(d);creator,basis=creators(d);wt=kind(d)
 if dates['date_issue']:flags.append('creation_date_requires_review')
 if not creator:flags.append('creator_unknown')
 if wt=='unknown':flags.append('type_not_mapped')
 if not d.get('objectnumber') or not d.get('creditline'):flags.append('inventory_or_credit_requires_review')
 if str(d.get('campuscollections')).lower()!='false' or d.get('campus_art') or 'Princeton University' in (d.get('creditline') or ''):flags.append('campus_collection_requires_review')
 if d['objectnumber'].startswith('PP'):flags.append('university_portrait_inventory')
 makers=d.get('makers') or []
 if len(makers)>1 or any(v.get('prefix') or v.get('suffix') or v.get('role')!='Artist' for v in makers):flags.append('creator_roles_or_qualifiers_require_review')
 for v in makers:
  if dates['first'] and dates['first']!=dates['last'] and (dates['first'],dates['last'])==(v.get('datebegin'),v.get('dateend')):flags.append('creation_matches_maker_life_or_period')
 prose=' '.join(clean(v.get('textentryhtml')) or '' for v in d.get('texts',[]) if v.get('textpurpose')=='Provenance')
 if re.search(r'\b(?:deaccession\w*|restitu\w*|repatriat\w*|lost|missing|location[^;.]*unknown|loan|lent|borrow\w*|promised gift)\b',prose+' '+(d.get('creditline') or ''),re.I):flags.append('holding_or_custody_requires_review')
 if re.search(r'\b(?:pair|diptych|triptych|polyptych|verso|reverse|fragment|fragmentary|part of|pendant|copy|after|workshop|attributed|circle|school|cast|edition|portfolio|album|studies|sketchbook|tetraconch)\b',d['displaytitle']+' '+(creator or ''),re.I):flags.append('physical_version_or_qualified_creator_review')
 if d.get('restrictions') or str(d.get('nowebuse')).lower()=='true':flags.append('source_use_label_present')
 titles=sorted({d['displaytitle']}|{v['title'] for v in d.get('titles',[]) if v.get('title')})
 facts=dict(source_id=sid,native_object_id=sid,source_url=x['url'],native_page_urls=['https://artmuseum.princeton.edu/art/collections/objects/'+sid,'https://artmuseum.princeton.edu/collections/objects/'+sid],native_metadata_urls=[x['url'],x['url']+'/tombstone'],wikidata_ids=[],title=d['displaytitle'],titles=titles,creator_label=creator,detail_creator_label=creator,identity_creator_labels=sorted({v['displayname'] for v in makers if v.get('displayname')}),creator_label_basis=basis,date_display=d.get('displaydate'),**dates,inventory=d['objectnumber'],medium=d.get('medium'),dimensions_text=d.get('dimensions'),work_type=wt,object_form=None,credit_line=d.get('creditline'),source_makers=makers,source_fields=d,source_note='Official public API metadata retained in full, including creator roles, provenance remarks, source dates, rights and campus flags. Native on_view/package names are evidence only; no current-display, image or legal-title claim. Glass and other unmatched types remain unknown rather than being forced into ceramic. Cultural labels are object-level labels, not invented painter authorities.')
 return dict(provider='princeton',institution_id=IID,number=x['number'],source_id=sid,facts=facts,index=row,source_reference=ref(path),retrieved_at=x['capture']['receipt']['retrieved_at'],state='source_candidate',review_flags=sorted(set(flags)))
def dependencies():
 paths={Path(__file__).resolve()};seen=set()
 def visit(v):
  if id(v) in seen:return
  seen.add(id(v));file=getattr(v,'__file__',None)
  if not file or Path(file).resolve().parent!=m.ROOT/'ops':return
  paths.add(Path(file).resolve())
  for item in vars(v).values():
   if isinstance(item,types.ModuleType):visit(item)
 visit(n);return [ref(p) for p in sorted(paths)]
def main(suffix,partial):
 paths=sorted((RUN/'objects-001').glob('*.json.gz'));expected=len(m.load(QUEUE)['selected']);assert partial or len(paths)==expected
 rows=[parse(p) for p in paths];out=RUN/('native-candidates-'+suffix+'.json.gz');assert not out.exists()
 m.save(out,dict(at=m.now(),rows=rows,parser_reference=ref(Path(__file__).resolve()),dependencies=dependencies(),queue_reference=ref(QUEUE),capture_count=len(paths),expected_capture_count=expected,partial=partial,policy='Source facts only, no approvals. Dates, museum collection identity, physical version and existing identities require editorial review.'))
 print(json.dumps(dict(rows=len(rows),partial=partial,flag_counts={k:sum(k in r['review_flags'] for r in rows) for k in sorted({k for r in rows for k in r['review_flags']})})),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--suffix',required=True);p.add_argument('--partial',action='store_true');a=p.parse_args();assert re.fullmatch(r'\d{3}',a.suffix);main(a.suffix,a.partial)
