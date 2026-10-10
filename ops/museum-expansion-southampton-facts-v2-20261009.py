"""Editorial date resolution and comparison-only title aliases for 80 native objects."""
import copy,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-southampton-facts-20261009.py'));f=importlib.util.module_from_spec(z);z.loader.exec_module(f);m=f.m;RUN=f.RUN;ref=f.ref;checked=f.checked;IID=f.IID
def rows():
 original=m.load(RUN/'native-candidates-001.json.gz');assert original['rows']==f.rows();out=copy.deepcopy(original['rows']);pdf=m.load(RUN/'exhibition-catalogue-001.json');pages=pdf['text_pages']
 for r in out:
  v=r['facts'];num=r['number'];v['editorial_date_evidence']=[];v['comparison_alias_notes']=[]
  if num==6:
   t=' '.join(pages[16].split());assert '1956' in t and '50.8 × 76.3 cm' in t and 'signed and dated lower right' in t;assert v['native_fields']['Date']=='' and v['dimensions_text']=='508mm x 763mm'
   v.update(date_display='1956',first=1956,last=1956,date_precision='exact',date_issue=None);v['editorial_date_evidence'].append(dict(pdf_page_index=16,reference=ref(RUN/'exhibition-catalogue-001.json'),basis='Exact artist/title, 50.8 x 76.3 cm and 1956 acquisition corroborate native object; signed and dated 1956 in museum catalogue. Other floating-bridge painting is explicitly distinguished by native narrative.'))
  if num==42:
   assert 'This triptych, painted around 1510,' in v['narrative'];v.update(date_display='c. 1510',first=1510,last=1510,date_precision='circa',date_issue=None);v['editorial_date_evidence'].append(dict(reference=r['source_reference'],basis='Explicit object creation circa 1510 in native narrative; one triptych, not three inferred artworks.'))
  if num==40:
   assert 'This painting from around 1520' in v['narrative'];v.update(date_display='c. 1520',date_precision='circa');v['editorial_date_evidence'].append(dict(reference=r['source_reference'],basis='Date field 1520 qualified by explicit native narrative around 1520.'))
  if num in [68,69]:
   page=13 if num==68 else 11;t=' '.join(pages[page].split());assert ('ci rca 1912-14' if num==68 else '1912') in t
   if num==68:v.update(date_display='c. 1912–1914 (native page: 1912)',first=1912,last=1914,date_precision='circa_range',date_issue=None)
   else:v.update(date_display='1911 or 1912 (conflicting catalogue dates)',first=1911,last=1912,date_precision='range',date_issue=None)
   v['editorial_date_evidence'].append(dict(reference=ref(RUN/'exhibition-catalogue-001.json'),pdf_page_index=page,basis='Preserve both museum sources explicitly; broader source-backed creation uncertainty, no invented year. Native original date remains in native_fields. Gosse native 67 x 51 cm versus PDF 67 x 49 cm also retained in evidence; no silent measurement reconciliation.' if num==68 else 'Native object dates this painting 1911; 2017 museum catalogue dates it 1912. Both stated bounds retained as uncertainty, not a claimed creation duration.'))
  aliases={55:['The Last Evening'],58:['Deux Chiens Jouant','Two Dogs Playing'],60:['Lancelot at the Chapel of the Holy Grail'],76:['The Mantlepiece']}.get(num,[])
  if aliases:v['titles']+=aliases;v['comparison_alias_notes'].append('Comparison-only alias/title translation. Native title remains unchanged. For Tissot, The Last Evening is specifically a historical confusion denied by the native page, not an accepted alternate title.')
  r['state']='candidate' if not v['date_issue'] and not v['native_issues'] else 'source_hold'
 return out
def main():
 dest=RUN/'native-candidates-002.json.gz';assert not dest.exists();rs=rows();m.save(dest,dict(at=m.now(),rows=rs,parser_reference=ref(Path(__file__).resolve()),dependencies=[ref(RUN/x) for x in ['native-candidates-001.json.gz','exhibition-catalogue-001.json','source-catalogue-001.pdf']],policy='80 selected objects only. Explicit narrative/PDF dates resolve two blank fields; source conflicts remain visible. Aliases only widen comparisons; do not overwrite native titles.'))
 print(json.dumps(dict(rows=len(rs),candidates=sum(r['state']=='candidate' for r in rs))),flush=True)
if __name__=='__main__':main()
