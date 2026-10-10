"""Literal next160 public Rhodes objects; creation dates keep source qualifiers."""
import importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-rhodes-more-source-20261009.py'));src=importlib.util.module_from_spec(z);z.loader.exec_module(src)
s=src.s;m=s.m;RUN=s.RUN
SOURCE_FILES=['native-selection-001.json.gz']
def invkey(v):return (v or '').strip()
def date(v):
 if not v:return None,None,'unknown'
 v=v.strip()
 if re.fullmatch(r'\d{4}',v):return int(v),int(v),'exact'
 if re.fullmatch(r'περ\. \d{4}',v):return int(v[-4:]),int(v[-4:]),'circa'
 match=re.fullmatch(r'(περ\. )?(\d{4})-(\d{2}|\d{4})',v)
 if match:
  a=int(match[2]);b=int(match[3]) if len(match[3])==4 else a//100*100+int(match[3]);assert a<=b;return a,b,'circa_range' if match[1] else 'range'
 if re.fullmatch(r'δεκαετία \d{3}0',v):return int(v[-4:]),int(v[-4:])+9,'decade'
 if re.fullmatch(r'πριν από το \d{4}',v):return None,int(v[-4:]),'before'
 raise ValueError('Unreviewed physical object date: '+v)
def rows():
 out=[]
 for path in SOURCE_FILES:
  for row in m.load(RUN/path)['rows']:
   v=row['fields'];a,b,p=date(v['date']);assert v['source']=='Μουσείο Νεοελληνικής Τέχνης, Δήμου Ρόδου';typ={'ζωγραφική':'painting','χαρακτική':'print','γλυπτική':'sculpture','κατασκευές/εγκαταστάσεις':'unknown'}[v['type']];title=v['title'].strip();u=row['uuid'];url=row['source_url']
   f=dict(source_id=u,native_id=u,source_url=url,native_page_urls=[url,'https://www.searchculture.gr/aggregator/edm/TehnisRodou/000188-'+u],title=title,titles=[title],creator_label=(v['creator'] or '').strip() or None,date_display=v['date'] or 'Creation date unknown',first=a,last=b,date_precision=p,work_type=typ,object_form=None,medium=(v['material']or'').strip()or None,dimensions_text=(v['dimensions']or'').strip()or None,inventory=v['inventory'],description_md=None,source_narrative=v['description'],source_fields=v,date_policy='Dedicated physical creation field; repository timestamps, depicted historical events, artist lifespans and prototypes do not date the object. Explicit two-digit range endpoint expanded within its stated century. Decades retain all ten years. Before1948 retains an unknown lower bound and exclusive upper endpoint1948. Circa1970 and the1970s require cutoff review. No invented circa tolerance.',rights_label=v['copyright'],image_downloaded=False)
   state='unknown_date_review_deferred' if b is None else 'cutoff_date_review_hold' if (a is not None and a<=1970<b) or (p=='circa' and b==1970) else 'outside_creation_scope' if b>1970 else 'eligible_metadata_candidate'
   out.append(dict(number=row['n'],source_id=u,retrieved_at=row['receipt']['retrieved_at'],facts=f,receipt=row['receipt'],metadata_state=state))
 assert len(out)==160 and len({v['source_id']for v in out})==160;return out
if __name__=='__main__':
 from collections import Counter
 result=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=result,source_references=[s.ref(RUN/p)for p in SOURCE_FILES],parser_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(records=len(result),states=Counter(v['metadata_state']for v in result))))
