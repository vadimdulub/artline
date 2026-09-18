#!/usr/bin/env python3
"""Resolve exact French museum identifiers for existing artwork image research.

No institution or artwork metadata is changed. An exact public Museofile ID
must agree before it can be used as the holding-authority matching evidence.
"""
import argparse,collections,importlib.util,json,re,time
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
s=importlib.util.spec_from_file_location('common',Path(__file__).with_name('overnight-commons-images.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);core=m.core
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();a.run.mkdir(parents=True,exist_ok=True);f=core.Fetcher(a.run/'metadata')
 rows=json.loads((a.reference/'commons/target-held.json').read_text());blocked={x['artwork_id'] for x in json.loads((a.run.parent/'withdrawn-images.json').read_text())['records']}
 with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
  current={x['id']:x for x in db.execute("SELECT id::text,title,creation_year_start,creation_year_end,work_type FROM artworks WHERE id=ANY(%s::uuid[]) AND status='review' AND primary_media_id IS NULL AND artline_has_selection_evidence(id)",([r['artwork_id'] for r in rows],))}
 groups=collections.defaultdict(list);held=[];selected=[]
 for row in rows:
  if row['artwork_id'] in blocked or row['artwork_id'] not in current:continue
  if any(current[row['artwork_id']][k]!=row[k] for k in ('title','creation_year_start','creation_year_end','work_type')):continue
  match=re.fullmatch(r'joconde-(m\d{4})',row['institution_slug'])
  if not match:continue
  code=match[1].upper()
  if row['website_url']!='https://pop.culture.gouv.fr/notice/museo/'+code:continue
  groups[code].append(row)
 for n,(code,group) in enumerate(sorted(groups.items(),key=lambda kv:(-sum(c['popular'] for c in kv[1]),-len(kv[1]))),1):
  if time.time()>=a.deadline:break
  capture=a.run/'institutions'/(code+'.json')
  if capture.exists():d=json.loads(capture.read_text())
  else:
   search=m.api(f,'www.wikidata.org',{'action':'query','list':'search','srsearch':'haswbstatement:P539='+code,'srnamespace':0,'srlimit':10,'srprop':''});qids=[x['title'] for x in search.get('query',{}).get('search',[]) if re.fullmatch(r'Q\d+',x['title'])]
   entities=m.api(f,'www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(qids),'props':'claims|labels|aliases','languages':'en|fr'})['entities'] if qids else {}
   d={'at':core.now(),'museofile_id':code,'official_museum_record':'https://pop.culture.gouv.fr/notice/museo/'+code,'search':search,'entities':entities};core.save_new(capture,d)
  matches=[e for e in d['entities'].values() if code in m.values(e,'P539')]
  if len(matches)!=1:
   held.extend({'artwork_id':c['artwork_id'],'reason':'No unique independently retrieved Museofile authority'} for c in group);continue
  e=matches[0]
  for c in group:
   selected.append(dict(c,institution_qid=e['id'],museum_authority_evidence={'museofile_id':code,'source_url':'https://www.wikidata.org/wiki/'+e['id'],'official_museum_record':d['official_museum_record'],'authority_entity':e,'retrieved_at':d['at']}))
  print(core.now(),'Museum identities researched',n,'of',len(groups),'candidate paintings',len(selected),flush=True)
 core.save_new(a.run/'candidates-local.json',selected);core.save_new(a.run/'museum-identity-held.json',held)
 m.prepare_targets(a.run,core.cloud_dsn())
 core.save_new(a.run/'museum-identity-summary.json',{'at':core.now(),'museum_groups':len(groups),'independently_matched_existing_artworks':len(selected),'held':len(held),'database_metadata_modified':False,'policy':'Exact P539 authority supports museum identity; artwork P195 must still agree, and exact photograph rights and provenance are checked independently.'})
if __name__=='__main__':main()
