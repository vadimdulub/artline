#!/usr/bin/env python3
"""Discover exact inventory matches for existing popular-painter image gaps."""
import argparse,collections,importlib.util,json,re,time
from pathlib import Path
from urllib.parse import urlparse
s=importlib.util.spec_from_file_location('common',Path(__file__).with_name('overnight-commons-images.py'));common=importlib.util.module_from_spec(s);s.loader.exec_module(common);core=common.core
MUSEUMS={'tate':'Q430682','pushkin-state-museum-fine-arts':'Q4872','national-gallery-london':'Q180788','musee-marmottan-monet':'Q1327886','musee-orsay':'Q23402','the-met':'Q160236'}
def host(url):return (urlparse(url or '').hostname or '').removeprefix('www.')
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--limit-pairs',type=int,default=60);p.add_argument('--exclude-report',type=Path);p.add_argument('--deadline',type=float,required=True);a=p.parse_args();r=a.run;r.mkdir(exist_ok=True);f=core.Fetcher(r/'metadata')
 prior=json.loads(a.exclude_report.read_text())['groups_searched'] if a.exclude_report else []
 searched={(x['institution_qid'],x['artist_qid']) for x in prior}
 institutions=common.api(f,'www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(MUSEUMS.values()),'props':'claims|labels|aliases','languages':'en|fr|ru'})['entities'];core.save_new(r/'verified-institution-entities.json',institutions)
 import psycopg
 from psycopg.rows import dict_row
 with psycopg.connect('postgres://localhost/artline',row_factory=dict_row,options='-c default_transaction_read_only=on') as db:
  museums=db.execute('SELECT id::text,slug,name,website_url FROM institutions WHERE slug=ANY(%s)',(list(MUSEUMS),)).fetchall()
  for i in museums:assert host(i['website_url']) in {host(u) for u in common.values(institutions[MUSEUMS[i['slug']]],'P856') if isinstance(u,str)},'Museum authority official website mismatch'
  rows=db.execute("""WITH popular_works AS (SELECT DISTINCT aa.artwork_id FROM artist_discovery_selection d JOIN artwork_artists aa ON aa.artist_id=d.artist_id WHERE d.is_popular)
   SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.accession_number,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,
    i.slug institution_slug,i.name institution_name,i.website_url,
    ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id) roles,
    (SELECT jsonb_agg(jsonb_build_object('qid',e.external_id,'name',p.display_name,'death',p.death_year) ORDER BY p.id) FROM artwork_artists aa JOIN artists p ON p.id=aa.artist_id LEFT JOIN external_identifiers e ON e.entity_type='artist' AND e.entity_id=p.id AND e.scheme='wikidata' WHERE aa.artwork_id=a.id) creators,
    (SELECT jsonb_agg(jsonb_build_object('scheme',e.scheme,'external_id',e.external_id,'url',e.canonical_url)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme<>'wikidata') native_identifiers
   FROM popular_works pw JOIN artworks a ON a.id=pw.artwork_id JOIN institutions i ON i.id=a.current_institution_id
   WHERE i.slug=ANY(%s) AND a.status='review' AND a.primary_media_id IS NULL AND a.work_type='painting'
    AND a.accession_number IS NOT NULL AND a.accession_number<>'' AND a.creation_year_start>=1000
    AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id)
    AND NOT EXISTS(SELECT 1 FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id AND e.scheme='wikidata')""",(list(MUSEUMS),)).fetchall()
 groups=collections.defaultdict(list);held=[];selected=[];progress=[]
 for c in rows:
  c.update(institution_qid=MUSEUMS[c['institution_slug']],popular=True)
  if c['roles']!=['primary'] or not c['native_identifiers'] or len(c['creators'] or [])!=1 or not c['creators'][0]['qid']:continue
  if not any(host(e['url'])==host(c['website_url']) or host(e['url']).endswith('.'+host(c['website_url'])) for e in c['native_identifiers']):continue
  groups[(c['institution_qid'],c['creators'][0]['qid'])].append(c)
 remaining=[(key,group) for key,group in groups.items() if key not in searched]
 for n,((museum,artist),group) in enumerate(sorted(remaining,key=lambda kv:-len(kv[1]))[:a.limit_pairs],1):
  if time.time()>=a.deadline:break
  query='haswbstatement:P170='+artist+' haswbstatement:P195='+museum+' haswbstatement:P18';qids=[];offset=0;total=None
  while offset<500:
   params={'action':'query','list':'search','srsearch':query,'srnamespace':0,'srlimit':50,'srprop':''}
   if offset:params['sroffset']=offset
   data=common.api(f,'www.wikidata.org',params);total=data.get('query',{}).get('searchinfo',{}).get('totalhits',0)
   qids.extend(x['title'] for x in data.get('query',{}).get('search',[]) if re.fullmatch(r'Q\d+',x['title']))
   if 'continue' not in data:break
   offset=data['continue']['sroffset']
  entities={}
  for start in range(0,len(qids),50):entities.update(common.api(f,'www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(qids[start:start+50]),'props':'claims|labels|aliases','languages':'en|mul|fr|it|nl|de|ru|el|sv|da|fi|es|pt|nb|pl'})['entities'])
  index=collections.defaultdict(list)
  for q,e in entities.items():
   if e.get('id')!=q or common.ids(e,'P195')!={museum} or common.ids(e,'P170')!={artist}:continue
   for inv in common.values(e,'P217'):
    if isinstance(inv,str):index[common.norm(inv)].append(e)
  for c in group:
   hits={e['id']:e for e in index[common.norm(c['accession_number'])]}
   if len(hits)!=1:held.append({'artwork_id':c['artwork_id'],'reason':'Exact museum inventory not uniquely established','matches':len(hits)});continue
   e=next(iter(hits.values()));c=dict(c,qid=e['id'])
   try:
    common.entity_match(c,e)
    dates=[int(re.match(r'^\+(\d+)-',d['time'])[1]) for d in common.values(e,'P571') if isinstance(d,dict) and d.get('precision',0)>=9 and re.match(r'^\+(\d+)-',d.get('time',''))]
    if not dates or any(not c['creation_year_start']<=year<=c['creation_year_end'] for year in dates):raise ValueError('Exact inventory agrees but source creation date needs review')
    c.update(artwork_entity=e,institution_entity=institutions[museum],checked_at=core.now());selected.append(c)
   except ValueError as exc:held.append({'artwork_id':c['artwork_id'],'qid':c['qid'],'reason':str(exc)})
  progress.append({'institution_qid':museum,'artist_qid':artist,'catalogue_gaps':len(group),'search_total':total,'entities_checked':len(entities),'search_truncated':total is not None and total>len(entities)})
  print(core.now(),'Popular museum/artist searches',n,'of',min(len(remaining),a.limit_pairs),'exact inventory matches',len(selected),flush=True)
 core.save_new(r/'native-match-leads.json',selected);core.save_new(r/'native-match-held.json',held);core.save_new(r/'native-match-report.json',{'at':core.now(),'eligible_existing_gaps':len(rows),'museum_artist_groups':len(groups),'groups_searched':progress,'exact_inventory_leads':len(selected),'held':dict(collections.Counter(x['reason'] for x in held)),'policy':'Research only. Museum Wikidata authorities matched to the stored official website. Exact accession, single museum holding, single primary creator and creation year agreement required. No institution, artist, artwork or image modified. Commons file rights still require separate verification.'})
if __name__=='__main__':main()
