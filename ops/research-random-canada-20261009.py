#!/usr/bin/env python3
"""Bounded Canadian primary catalogues, including the empty McMichael institution."""
import importlib.util,re,json,sys
from pathlib import Path
from urllib.parse import urljoin
s=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-random-country-collections-20261009.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r);r.phase('CA')
def mcmichael():
 source=r.b.Source();urls=set();out=[];held=[]
 for pg in range(1,9):
  sp,rc=r.page('https://collections.mcmichael.com/collections/87758/group-of-seven-and-associates/objects/images?page='+str(pg),source)
  for a in sp.select('a[href]'):
   if re.match(r'^/objects/\d+/',a['href']):urls.add(urljoin(rc['url'],a['href'].split(';')[0].split('?')[0]))
 for n,u in enumerate(sorted(urls),1):
  try:
   sp,rc=r.page(u,source);get=lambda c:sp.select_one('.'+c).get_text(' ',strip=True) if sp.select_one('.'+c) else None
   fields={c:get(c) for c in ['peopleField','titleField','displayDateField','mediumField','paperSupportField','dimensionsField','creditlineField','invnoField','departmentField']}
   if fields['departmentField']!='Department PERMANENT COLLECTION':held.append(dict(url=u,reason='Not permanent collection'));continue
   label=re.sub(r'^Artist\s+','',fields['peopleField'] or '');label=re.sub(r'\s+\d{4}\s*[-–]\s*\d{4}.*$','',label)
   dt=(fields['displayDateField'] or '').removeprefix('Date ');medium=' '.join((fields[k] or '').removeprefix(pre) for k,pre in [('mediumField','Medium/Materials '),('paperSupportField','Support ')])
   if not re.search(r'oil|watercolour|watercolor|pencil|ink|pastel|gouache|tempera',medium,re.I):held.append(dict(url=u,reason='Outside selected pictorial media',medium=medium));continue
   row=r.record('mcmichael',dict(fields=fields,creator_life_source=fields['peopleField']),rc,source_id=u.split('/objects/')[1].split('/')[0],title=fields['titleField'],museum='McMichael Canadian Art Collection',source_url=u,creator_label=label,date_display=dt,source_type='painting' if re.search('oil|tempera|gouache',medium,re.I) else 'drawing',medium=medium,dimensions=(fields['dimensionsField'] or '').removeprefix('Dimensions ') or None,accession_number=(fields['invnoField'] or '').removeprefix('Object Number ') or None,credit=(fields['creditlineField'] or '').removeprefix('Credit Line ') or None,selection_basis='First eight pages of official Group of Seven and Associates collection; exact permanent-collection object pages')
   if r.accept(row,held):out.append(row)
  except Exception as e:held.append(dict(url=u,reason=str(e)[:250]))
  if n%25==0:print('McMichael',n,'/',len(urls),flush=True)
 r.save('mcmichael-records.json.gz',dict(records=out,held=held,inspected=len(urls)));print('McMichael selected',len(out),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
