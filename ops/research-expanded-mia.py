#!/usr/bin/env python3
"""Select exact Minneapolis museum objects for retained CSV candidates."""
import argparse,collections,importlib.util,json,re,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
s=importlib.util.spec_from_file_location('planner',ROOT/'ops/plan-expanded-round2.py');p=importlib.util.module_from_spec(s);s.loader.exec_module(p)

def closed_biography(text):
 # Only a complete, unqualified lifespan can create a new painter timeline.
 # “1639 or later” and “1750s” must not become exact death years.
 if re.search(r'active|circa|\bc\.|\?|born|died|before|after|about',text,re.I):return None
 return re.fullmatch(r'[^\d]*(\d{4})\s*[-–—]\s*(\d{4})\s*\)?',text)

def main(directory,archive):
 pending=json.loads((directory/'unlinked.json').read_text());wanted=collections.defaultdict(list)
 for row in pending:
  if row['source'] is None and row['cells'][3]=='Minneapolis Institute of Art':
   wanted[(p.namekey(row['cells'][0]),p.norm(row['cells'][1]),p.datestr(row['cells'][2]))].append(row)
 receipt=p.verify(archive);matches=collections.defaultdict(dict);counts=collections.Counter();selected=[]
 with tarfile.open(archive,'r:gz') as tar:
  for member in tar:
   if not member.isfile() or '/objects/' not in member.name or not member.name.endswith('.json'):continue
   try:obj=json.load(tar.extractfile(member))
   except (ValueError,UnicodeError):counts['invalid_json']+=1;continue
   if not isinstance(obj,dict):counts['non_object_json']+=1;continue
   counts['objects_scanned']+=1
   name=re.sub(r'^artist:\s*','',obj.get('artist') or '',flags=re.I).strip()
   key=(p.namekey(name),p.norm(obj.get('title')),p.datestr(obj.get('dated') or ''))
   rows=wanted.get(key,[])
   if not rows:continue
   if p.previous.QUALIFIED.search(name) or re.search(r'\b(after|possibly|probably|studio|manner of|formerly)\b',name,re.I):counts['qualified']+=len(rows);continue
   typ={'Paintings':'painting','Drawings':'drawing'}.get((obj.get('classification') or '').strip())
   if not typ:counts['unsupported_type']+=len(rows);continue
   if obj.get('role') and obj['role'].lower()!='artist':counts['other_role']+=len(rows);continue
   life=obj.get('life_date') or '';bio=closed_biography(life)
   oid=Path(member.name).stem
   person={'name':name,'sort_name':name,'birth':int(bio[1]) if bio else None,'death':int(bio[2]) if bio else None,'source_id':'','role':'artist','date_display':life}
   fact={'source':'mia','object_id':oid,'object_url':'https://collections.artsmia.org/art/'+oid,'painter':person,'date':p.date_literal(obj.get('dated') or ''),'type':typ,'medium':obj.get('medium') or '', 'dimensions':obj.get('dimension') or '', 'accession':obj.get('accession_number') or '', 'evidence':[dict(receipt,archive_member=member.name)],'object_record':{k:v for k,v in obj.items() if not k.startswith('image') and k not in ['room','see_also']}}
   for row in rows:matches[row['rid']]['mia:'+oid]=fact
   selected.append({'rid':[r['rid'] for r in rows],'object_id':oid,'archive_member':member.name})
 p.previous.save(directory/'mia-source-matches.json',matches);p.previous.save(directory/'mia-audit.json',{'counts':dict(counts),'candidate_keys':len(wanted),'matched_candidates':len(matches),'selected':selected})
 print(dict(counts),'matched_candidates',len(matches),flush=True)
 p.main(directory=directory,matches_path=directory/'mia-source-matches.json',round_slug='round3')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--dir',type=Path,required=True);a.add_argument('--archive',type=Path,required=True);args=a.parse_args();main(args.dir,args.archive)
