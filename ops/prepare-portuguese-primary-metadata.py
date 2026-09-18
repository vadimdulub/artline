#!/usr/bin/env python3
"""Pin individually reviewed CAM facts before the first Portuguese DB plan."""
import importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('apply-country-round.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
CORE=m.m.core;ROOT=m.x.ROOT;RUN=ROOT/'docs/research/overnight-countries-20260913/portugal'
FACTS={'Q10273138':('77P9',1917,1917,'circa'),'Q10349894':('77P8',1917,1917,'circa'),'Q77848260':('83P625',None,None,'unknown'),'Q99091836':('83P444',1930,1930,'exact'),'Q99094316':('68P299',1932,1934,'circa'),'Q99095492':('83P445',1934,1934,'exact'),'Q99097028':('83P82',1934,1934,'exact'),'Q99097891':('83P678',None,None,'unknown'),'Q99192757':('83P84',1932,1932,'exact'),'Q10382841':('83P161',1918,1918,'exact'),'Q99194107':('83P165',None,None,'unknown'),'Q99194293':('83P163',None,None,'unknown'),'Q99194389':('83P49',None,None,'unknown'),'Q99194402':('83P166',1917,1917,'exact'),'Q99194418':('81P164',1910,1910,'circa')}
def main():
 receipt=RUN/'primary-followup/prepared-metadata.json'
 if receipt.exists():return
 changed=[];rounds=set()
 for rp in sorted((RUN/'primary-followup').glob('round-*/research.json')):
  for ev in json.loads(rp.read_text())['records']:
   q=ev['qid']
   if q not in FACTS:continue
   sources=[v for v in ev['sources'] if v.get('receipt',{}).get('status')==200];assert len(sources)==1
   source=sources[0];raw=Path(source['capture_path']).read_bytes();assert CORE.sha(raw)==source['receipt']['sha256']
   text=Path(source['text_path']).read_text();lines=text.splitlines()
   field=lambda label:lines[lines.index(label)+1]
   acc,first,last,precision=FACTS[q];assert field('N.º de inventário')==acc
   wording=field('Data');maker=field('Autor(es)');assert any(v in maker for v in ('Amadeo de Souza-Cardoso','José Dominguez Alvarez','Armando Basto'))
   if first is None:assert wording=='não datado'
   else:
    assert str(first) in wording and str(last) in wording
    assert ('c.' in wording)==(precision=='circa'),(q,wording)
   n=int(rp.parent.name.split('-')[1]);folder=RUN/'PT'/f'round-{n:02d}'/'delivery';assert not (folder/'application-manifest.json').exists()
   path=folder/'ready'/(q+'.json');old=path.read_bytes();data=json.loads(old);record=data['record']
   assert record['qid']==q and record['creator_label'] in maker or (record['qid']==q and q in ('Q10273138','Q10349894'))
   before=dict(date=record['date'],accession=record['accession']);display='Undated (museum catalogue)' if first is None else ('c. ' if precision=='circa' else '')+str(first)+(('–'+str(last)) if last!=first else '')
   record.update(accession=acc,date=dict(first=first,last=last,precision=precision,display=display,eligible=last is not None and last<=1970),primary_medium_text=field('Técnica')+'; materials: '+field('Materiais e meios'),primary_dimensions_text=field('Dimensões'),primary_museum_review=dict(receipt=source['receipt'],capture_path=source['capture_path'],maker_wording=maker,title_wording=field('Título'),date_wording=wording,materials_wording=field('Materiais e meios'),technique_wording=field('Técnica'),dimensions_wording=field('Dimensões'),inventory=acc,previous_prepared_metadata=before,review='Exact primary object page referenced by the Wikidata object; individually reviewed maker/title/technical fields. Current primary creation date and qualifiers supersede secondary dating. Acquisition and exhibition dates excluded. Original entity and receipt retained. Museum metadata does not license an image.'))
   if first is None and data.get('image'):
    data.update(image=None,image_outcome='primary_creation_date_unknown_metadata_only')
   CORE.save_new(RUN/'primary-followup/preparation-preimages'/f'round-{n:02d}'/path.name,old)
   path.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n');rounds.add(n);changed.append(dict(qid=q,round=n,before=before,after=record['date'],accession=acc,sha256=CORE.sha(path.read_bytes()),source_url=source['receipt']['final_url']))
 for n in sorted(rounds):
  folder=RUN/'PT'/f'round-{n:02d}'/'delivery';path=folder/'image-preparation.json';raw=path.read_bytes();d=json.loads(raw);CORE.save_new(RUN/'primary-followup/preparation-preimages'/f'round-{n:02d}'/path.name,raw)
  d['ready_hashes']={p.name:CORE.sha(p.read_bytes()) for p in sorted((folder/'ready').glob('*.json'))};d['primary_metadata_followup_at']=CORE.now();d['images']=sum(bool(json.loads(p.read_text()).get('image')) for p in (folder/'ready').glob('*.json'));path.write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 CORE.save_new(receipt,dict(at=CORE.now(),objects=changed,uploaded=False,review='Prepared only. Both-target identity planning and application still required. Existing database metadata remains unchanged.'))
 print('Prepared primary Portuguese metadata',len(changed),flush=True)
if __name__=='__main__':main()
