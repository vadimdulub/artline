"""Literal Rhodes museum metadata, bounded physical-object dates and preserved uncertainty."""
import importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-rhodes-source-20261009.py'));src=importlib.util.module_from_spec(z);z.loader.exec_module(src)
s=src.s;m=s.m;RUN=s.RUN
SOURCE_FILES=['native-sample-001.json.gz','native-selection-001.json.gz']
def invkey(v):return (v or '').strip()
def date(v):
 if not v:return None,None,'unknown'
 if re.fullmatch(r'\d{4}',v):return int(v),int(v),'exact'
 if re.fullmatch(r'περ\. \d{4}',v):return int(v[-4:]),int(v[-4:]),'circa'
 if re.fullmatch(r'\d{4}(?:-| ή )\d{4}',v):
  a,b=map(int,re.findall(r'\d{4}',v));assert a<=b;return a,b,'range'
 if v=='αρχές 19ου αιώνα':return 1801,1900,'century'
 raise ValueError('Unreviewed physical object date: '+v)
def rows():
 out=[]
 for path in SOURCE_FILES:
  for row in m.load(RUN/path)['rows']:
   v=row['fields'];a,b,p=date(v['date']);assert v['source']=='Μουσείο Νεοελληνικής Τέχνης, Δήμου Ρόδου';typ={'ζωγραφική':'painting','χαρακτική':'print'}[v['type']];title=v['title'].strip();u=row['uuid'];url=row['source_url']
   f=dict(source_id=u,native_id=u,source_url=url,native_page_urls=[url,'https://www.searchculture.gr/aggregator/edm/TehnisRodou/000188-'+u],title=title,titles=[title],creator_label=(v['creator'] or '').strip() or None,date_display=v['date'] or 'Creation date unknown',first=a,last=b,date_precision=p,work_type=typ,object_form=None,medium=(v['material']or'').strip()or None,dimensions_text=(v['dimensions']or'').strip()or None,inventory=v['inventory'],description_md=None,source_narrative=v['description'],source_fields=v,date_policy='Dedicated physical object creation field, not repository timestamps, artist lifespan, depicted date or prototype. Early19th century uses full1801–1900 century envelope; qualifier retained verbatim. Alternative1777or1778 retained as1777–1778 range.',rights_label=v['copyright'],image_downloaded=False)
   out.append(dict(number=row['n'],source_id=u,retrieved_at=row['receipt']['retrieved_at'],facts=f,receipt=row['receipt'],metadata_state='unknown_date_review_deferred'if a is None else 'outside_creation_scope'if b>1970 else 'eligible_metadata_candidate'))
 assert len(out)==120 and len({v['source_id']for v in out})==120;return out
if __name__=='__main__':
 from collections import Counter
 result=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=result,source_references=[s.ref(RUN/p)for p in SOURCE_FILES],parser_reference=s.ref(Path(__file__).resolve())));print(json.dumps(dict(records=len(result),states=Counter(v['metadata_state']for v in result))))
