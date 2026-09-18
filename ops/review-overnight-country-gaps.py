#!/usr/bin/env python3
"""Review missing painter affiliations from exact authorities and biographies."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('review-painter-countries.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('prepare-country-round.py'));p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
RUN=m.x.BASE/'country-gap-followup';SOURCE='overnight-country-gaps-20260913';ACTOR='local-european-research'
WORDS={**c.COUNTRIES,'Haitian':'HT','Nicaraguan':'NI','Namibian':'NA'}
ROLE=r'(?:painter|artist|iconographer|printmaker|engraver|illustrator|draughtsman|sculptor|photographer|graphic designer)'

def labels(text):
 return {word:code for word,code in WORDS.items() if re.search(r'\b'+re.escape(word)+r'(?![- ]born)\b(?:[\w, /–-]+?){0,1}\s'+ROLE+r'\b',text,re.I)}

def biography_labels(text):
 found=re.search(r'\b(?:was|is)\s+(?:a|an)\s+(.{0,180}?'+ROLE+r')\b',text[:750],re.I)
 return labels(found[1]) if found else {}

def plan():
 if (RUN/'gap-plan.json').exists():return
 wiki=json.loads((RUN/'known-wiki-country-research.json').read_text());bios=p.bio_index('country-gap-followup')
 museum_holds=[r for r in json.loads((m.x.BASE/'country-review-museums/holds.json').read_text()) if r['reason']=='country_not_yet_in_configured_taxonomy']
 slugs=sorted({r['artist']['slug'] for r in wiki}|{r['slug'] for r in museum_holds})
 with m.m.r.base.connect(False) as db,db.transaction():
  db.execute('SET TRANSACTION READ ONLY');rows=c.selected(db,[{'artist':{'slug':slug}} for slug in slugs]);configured={r['code'] for r in db.execute('SELECT code FROM countries').fetchall()}
 proposals={};holds=[]
 for item in wiki:
  slug=item['artist']['slug'];current=rows[slug];a=current['row'];e=item['entity'];qid=item['artist']['external_id'];bio=bios.get(qid)
  if current['countries'] or a['status']!='review':holds.append({'slug':slug,'reason':'country_already_present_or_not_review'});continue
  if e.get('id')!=qid or {'scheme':'wikidata','id':qid} not in current['authorities']:holds.append({'slug':slug,'reason':'exact_authority_identity_changed'});continue
  if any(m.m.r.year(e,prop) is not None and a[field] is not None and m.m.r.year(e,prop)!=a[field] for prop,field in [('P569','birth_year'),('P570','death_year')]):holds.append({'slug':slug,'reason':'source_lifespan_conflict'});continue
  desc=e.get('descriptions',{}).get('en',{}).get('value','');source_labels=labels(desc);biolabels=biography_labels(bio['intro']) if bio else {}
  codes=set(source_labels.values())&set(biolabels.values())&configured
  if not codes:holds.append({'slug':slug,'reason':'explicit_affiliation_not_corroborated','source_description':desc,'biography_available':bool(bio)});continue
  proposals[slug]={'slug':slug,'codes':sorted(codes),'evidence':[{'kind':'wikimedia_biography_crosscheck','qid':qid,'source_description':desc,'description_labels':source_labels,'biography_labels':biolabels,'polity_context':[m.m.r.value(cl) for cl in m.m.r.claims(e,'P27')],'source_url':'https://www.wikidata.org/wiki/'+qid,'receipt':item['receipt'],'wikipedia_url':bio['url'],'wikipedia_receipt':bio['receipt'],'source_excerpt':bio['intro'][:320]}]}
 registries,receipts=c.museum_rows();conflicts=set()
 for h in museum_holds:
  slug=h['slug'];current=rows[slug];a=current['row'];rec=registries[h['scheme']][h['source_id']];code=WORDS.get(rec['nationality'])
  if slug in conflicts:continue
  if current['countries'] or a['status']!='review' or code not in configured:continue
  if {'scheme':h['scheme'],'id':h['source_id']} not in current['authorities']:raise AssertionError('Museum identity changed')
  if any(rec[k] is not None and a[k+'_year'] is not None and rec[k]!=a[k+'_year'] for k in ['birth','death']):holds.append({'slug':slug,'reason':'museum_lifespan_conflict'});continue
  entry=proposals.setdefault(slug,{'slug':slug,'codes':[code],'evidence':[]})
  if entry['codes']!=[code]:holds.append({'slug':slug,'reason':'cross_source_country_conflict'});proposals.pop(slug,None);conflicts.add(slug);continue
  receipt=receipts[h['scheme']];entry['evidence'].append({'kind':'museum_nationality','scheme':h['scheme'],'person_id':h['source_id'],'nationality':rec['nationality'],'source_record':rec['raw'],'receipt':receipt,'source_url':receipt['url']})
 entries=sorted(proposals.values(),key=lambda e:e['slug'])
 for e in entries:e['expected']=rows[e['slug']]
 m.m.core.save_new(RUN/'gap-plan.json',entries);m.m.core.save_new(RUN/'gap-holds.json',holds)
 result={'at':m.m.core.now(),'plan_sha256':m.m.core.sha((RUN/'gap-plan.json').read_bytes()),'painters':len(entries),'affiliations':sum(len(e['codes']) for e in entries),'countries':dict(collections.Counter(code for e in entries for code in e['codes'])),'holds':dict(collections.Counter(e['reason'] for e in holds)),'policy':'Cultural affiliation explicitly supported by a primary museum nationality field or matched Wikidata description and Wikipedia biographical role. No birthplace, holding-country, imperial-citizenship or Flemish-to-modern-country inference. Review remains unchanged.'}
 m.m.core.save_new(RUN/'gap-manifest.json',result);print(json.dumps(result,indent=2),flush=True)

def signature(row):
 return {'artist':{k:row['row'][k] for k in ['slug','display_name','birth_year','death_year','entity_type','status','published_at']},'countries':[{k:v for k,v in c.items() if k!='artist_id'} for c in row['countries']],'authorities':row['authorities']}

def preflight(entries,pin):
 for target in ['local','production']:
  path=m.BACKUPS/('country-gaps-'+target+'-preimages.json')
  if path.exists():continue
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries])
   for e in entries:assert signature(rows[e['slug']])==signature(e['expected']),e['slug']
  m.m.core.save_new(path,{'at':m.m.core.now(),'plan_sha256':pin,'rows':rows})

def apply():
 raw=(RUN/'gap-plan.json').read_bytes();entries=json.loads(raw);pin=json.loads((RUN/'gap-manifest.json').read_text())['plan_sha256'];assert m.m.core.sha(raw)==pin
 review=json.loads((RUN/'gap-quality-review.json').read_text());assert review['plan_sha256']==pin and review['approved']
 preflight(entries,pin)
 for target in ['local','production']:
  done=RUN/('gap-'+target+'-applied.json')
  if done.exists():continue
  before=json.loads((m.BACKUPS/('country-gaps-'+target+'-preimages.json')).read_text())['rows']
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute("SET LOCAL statement_timeout='120s'");db.execute('SELECT pg_advisory_xact_lock(559220260914)')
   rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries],True)
   db.execute("INSERT INTO sources(slug,name,source_type,base_url) VALUES(%s,'Painter cultural affiliation review: museum and Wikimedia authority evidence','authority_data','https://www.wikidata.org/') ON CONFLICT(slug) DO NOTHING",(SOURCE,));sid=db.execute('SELECT id FROM sources WHERE slug=%s',(SOURCE,)).fetchone()['id']
   for e in entries:
    now=rows[e['slug']];assert now==before[e['slug']];a=now['row'];assert a['status']=='review' and not now['countries']
    for code in e['codes']:db.execute("INSERT INTO artist_countries(artist_id,country_code,relationship_type,is_primary,note) VALUES(%s,%s,'cultural_affiliation',false,%s)",(a['id'],code,'Source-supported cultural affiliation; not exclusive citizenship or a claim based on birthplace or museum location.'))
    for ev in e['evidence']:
     m.m.r.base.insert(db,'citations',dict(entity_type='artist',entity_id=a['id'],source_id=sid,field_name='geography',source_record_id=ev.get('qid') or ev.get('person_id'),source_url=ev['source_url'],retrieved_at=ev['receipt']['retrieved_at'],created_by=ACTOR,evidence_note=json.dumps({'plan_sha256':pin,'codes':e['codes'],'evidence':ev,'publication_status':'review'},ensure_ascii=False)))
    db.execute("UPDATE artists SET geography_review_state=CASE WHEN geography_review_state='not_reviewed' THEN 'classified' ELSE geography_review_state END,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s",(ACTOR,a['id']))
  m.m.core.save_new(done,{'at':m.m.core.now(),'plan_sha256':pin,'painters':len(entries),'affiliations':sum(len(e['codes']) for e in entries)})
  print(target,'country gaps applied',len(entries),flush=True)
 verify()

def verify():
 entries=json.loads((RUN/'gap-plan.json').read_text());out={}
 for target in ['local','production']:
  before=json.loads((m.BACKUPS/('country-gaps-'+target+'-preimages.json')).read_text())['rows']
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY');rows=c.selected(db,[{'artist':{'slug':e['slug']}} for e in entries])
   for e in entries:
    now=rows[e['slug']];old=before[e['slug']]
    for k,v in old['row'].items():
     if k not in ['geography_review_state','revision','updated_at','updated_by']:assert now['row'][k]==v,(e['slug'],k)
    assert now['authorities']==old['authorities'] and {c['country_code'] for c in now['countries']}==set(e['codes'])
    assert now['row']['status']=='review' and now['row']['published_at'] is None
    assert db.execute("SELECT 1 FROM citations c JOIN sources s ON s.id=c.source_id WHERE c.entity_type='artist' AND c.entity_id=%s AND c.field_name='geography' AND s.slug=%s",(now['row']['id'],SOURCE)).fetchone()
   out[target]={'painters_verified':len(entries),'missing_country':db.execute("SELECT count(*) n FROM artists a WHERE status='review' AND NOT EXISTS(SELECT 1 FROM artist_countries c WHERE c.artist_id=a.id)").fetchone()['n']}
 m.m.core.save_new(RUN/'gap-verification.json',{'at':m.m.core.now(),'databases':out});print(out,flush=True)
if __name__=='__main__':
 cli=argparse.ArgumentParser();cli.add_argument('command',choices=['plan','apply','verify']);args=cli.parse_args();globals()[args.command]()
