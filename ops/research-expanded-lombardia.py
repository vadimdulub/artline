#!/usr/bin/env python3
"""Match retained Italian artworks against pinned Regione Lombardia metadata."""
import argparse,collections,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('planner',ROOT/'ops/plan-expanded-round2.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def lifespan(text):
 m=re.fullmatch(r'\s*(\d{4})\s*[/–—-]\s*(\d{4})\s*',text or '')
 return (int(m[1]),int(m[2])) if m else (None,None)

def date_wordings(o):
 a=' '.join(filter(None,[o.get('dtsv'),o.get('dtsi')])).strip();b=' '.join(filter(None,[o.get('dtsl'),o.get('dtsf')])).strip()
 if a and b:return {a+'-'+b,*([a] if a==b else [])}
 return {a or b} if a or b else {' '.join(filter(None,[o.get('dtzg'),o.get('dtzs')]))}

def creation_date(o,text):
 a,b=o.get('dtsi',''),o.get('dtsf','');qa,qb=o.get('dtsv',''),o.get('dtsl','')
 unknown={'first':None,'last':None,'precision':'unknown','display':text or 'Date unknown'}
 if not re.fullmatch(r'\d{4}',a) or not re.fullmatch(r'\d{4}',b):return unknown
 if qa not in ('','ca','ca.') or qb not in ('','ca','ca.'):return unknown
 a,b=int(a),int(b)
 if a>b:return unknown
 circa=bool(qa or qb)
 return {'first':a,'last':b,'precision':('circa_range' if circa else 'range') if a!=b else ('circa' if circa else 'exact'),'display':text}

def museum_names(o):
 name=o.get('ldcm') or '';part=o.get('ldci') or ''
 if not name:return set()
 names={name}
 if part and part!=name:
  names.update(name+sep+part for sep in ['. ',' - ',' — '])
 return {p.norm(n) for n in names}

def main(directory):
 pending=json.loads((directory/'unlinked.json').read_text());wanted=collections.defaultdict(list)
 for row in pending:
  if row['source'] is None and row['cells'][4]=='Italy':wanted[(p.namekey(row['cells'][0]),p.norm(row['cells'][1]))].append(row)
 # The later region-wide capture subsumes the earlier Milan-only export.
 path=ROOT/'content/imports/campaign-lombardia-20260910/objects.json';receipt=p.verify(path);dataset=p.verify(path.with_name('dataset.json'))
 matches=collections.defaultdict(dict);counts=collections.Counter()
 for o in json.loads(path.read_text()):
  counts['objects_scanned']+=1;name=o.get('autn') or ''
  rows={r['rid']:r for title in [o.get('sgtt'),o.get('sgti')] for r in wanted.get((p.namekey(name),p.norm(title)),[])}
  if not rows:continue
  if o.get('autp')!='P' or o.get('auts') or p.previous.QUALIFIED.search(name) or re.search(r'\?|\|\||\b(aiuti|copia|cerchia|maniera)\b',name,re.I):counts['attribution_hold']+=len(rows);continue
  if o.get('qntn') not in (None,'','1'):counts['multiple_objects']+=len(rows);continue
  typ={'dipinto':'painting','disegno':'drawing','acquerello':'watercolor','stampa':'print'}.get(o.get('ogtd'))
  if not typ:continue
  museums=museum_names(o);dates={p.datestr(t) for t in date_wordings(o)}
  for r in rows.values():
   if p.norm(r['cells'][3]) not in museums:counts['museum_mismatch']+=1;continue
   if p.datestr(r['cells'][2]) not in dates:counts['date_mismatch']+=1;continue
   birth,death=lifespan(o.get('auta'));person={'name':name,'sort_name':name,'birth':birth,'death':death,'source_id':'','role':'artist','date_display':o.get('auta') or ''}
   dims=[]
   if o.get('misu'):
    for k,label in [('misa','Height'),('misl','Width'),('misp','Depth'),('misd','Diameter')]:
     if o.get(k):dims.append(label+': '+o[k]+' '+o['misu'])
   oid=o['idk'];url=(o.get('url') or '').replace('http://','https://',1)
   if not url.startswith('https://www.lombardiabeniculturali.it/opere-arte/schede/') or url.rstrip('/').split('/')[-1]!=oid:counts['object_url_hold']+=1;continue
   facts={'source':'lombardia','object_id':oid,'object_url':url,'painter':person,'date':creation_date(o,r['cells'][2]),'type':typ,'medium':o.get('mtc') or '', 'dimensions':'; '.join(dims),'accession':'','evidence':[receipt,dataset],'object_record':{k:v for k,v in o.items() if not k.startswith('urlimg')}}
   if re.fullmatch(r'\d{4}',o.get('dtsi','')) and int(o['dtsi'])>1970:counts['post_cutoff']+=1;continue
   matches[r['rid']]['lombardia:'+oid]=facts
 p.previous.save(directory/'lombardia-source-matches.json',matches);p.previous.save(directory/'lombardia-audit.json',{'counts':dict(counts),'matched_candidates':len(matches),'candidate_keys':len(wanted)})
 print(dict(counts),'matched',len(matches),flush=True)
 p.main(directory=directory,matches_path=directory/'lombardia-source-matches.json',round_slug='round4')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--dir',type=Path,required=True);args=a.parse_args();main(args.dir)
