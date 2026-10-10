"""Literal selected object facts, qualified dates and separately tracked research holds."""
import collections,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-beziers-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
MANUAL_HOLDS={59:'Fontaine du Tibre combines separately made sculptures; reconcile fountain/components before counting.',100:'Source creator birth1874 contradicts creation1866; identity/source correction needs independent confirmation.',101:'Source creator birth1874 contradicts creation1866; identity/source correction needs independent confirmation.',134:'One inventory covers two physical busts; reconcile group and components before counting.',184:'Former Louvre INV159 and Fabre deposit; reconcile old creator attributions and lender records before adding.'}
def period_span(raw):
 out=[]
 for piece in raw.split(';'):
  text=m.norm(piece);match=re.fullmatch(r'(?:(1er|[1-4]e) quart |(1ere|2e) moitie )?(\d{1,2})e siecle',text)
  if not match:raise ValueError('Unparsed or uncertain period: '+raw)
  a=(int(match[3])-1)*100+1;b=int(match[3])*100
  if match[1]:a+=(int(match[1][0])-1)*25;b=a+24
  elif match[2]:a+=(int(match[2][0])-1)*50;b=a+49
  out.append((a,b))
 return min(a for a,b in out),max(b for a,b in out),'century' if len(out)==1 and not match[1] and not match[2] else 'range'
def dates(v):
 raw=(v.get('Millesime_de_creation') or '').strip();period=(v.get('Periode_de_creation') or '').strip();a=b=None;precision='unknown';display=raw or period or 'Creation date under review'
 if re.fullmatch(r'\d{4}',raw):a=b=int(raw);precision='exact'
 elif re.fullmatch(r'\d{4}-\d{4}',raw):a,b=map(int,raw.split('-'));precision='range'
 elif re.fullmatch(r'avant \d{4}',raw):b=int(raw[-4:]);precision='before'
 elif re.fullmatch(r'après \d{4}',raw):a=int(raw[-4:]);precision='after'
 elif not raw and period:
  if '?' in period:pass
  else:a,b,precision=period_span(period)
 elif raw:raise ValueError('Unparsed date: '+raw)
 assert a is None or a>=100
 assert b is None or b>=100 and (a is None or b>=a)
 return a,b,precision,display
def rows():
 source=m.load(RUN/'joconde-selected-001.json.gz');base=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot'];known={v['external_id'] for v in base['identifiers']}|{v['source_record_id'] for v in base['citations']};out=[];held=[];existing=[]
 for n,v in enumerate(source['rows'],1):
  rid=v['Reference']
  if rid in known:existing.append(dict(number=n,source_id=rid,state='already_catalogued',source_fields=v));continue
  why=MANUAL_HOLDS.get(n);domain=(v.get('Domaine') or '').split(';');kind=next((k for d,k in [('peinture','painting'),('dessin','drawing'),('estampe','print'),('sculpture','sculpture')] if d in domain),None)
  if not kind:why=why or 'Outside selected painting/drawing/print/sculpture scope.'
  if 'carnet' in m.norm(' '.join(str(v.get(k) or '') for k in ['Titre','Denomination','Description'])):why=why or 'Sketchbook or sketchbook leaf: reconcile parent/components; no double counting.'
  if v.get('MANQUANT') or v.get('MANQUANT_COM'):why=why or 'Missing-object flag needs reconciliation.'
  if v.get('Lieu_de_depot'):why=why or 'State deposit: reconcile lender identity and historical custody before adding.'
  if not v.get('Titre') or not v.get('Numero_inventaire'):why=why or 'Missing title or inventory.'
  legal=m.norm(v.get('Statut_juridique'))
  if not legal.startswith(('propriete de la commune','legs')) or any(t in legal for t in ['depot','pret','privee','restitution']):why=why or 'Holding context needs review.'
  if m.norm(v.get('Localisation'))!='beziers musee des beaux arts':why=why or 'Institution mismatch.'
  try:a,b,precision,display=dates(v)
  except ValueError as e:why=why or str(e)
  if not why and a is not None and a>1970:why='Explicit artwork creation after1970; out of scope.'
  if why:held.append(dict(number=n,source_id=rid,reason=why,source_fields=v));continue
  u='https://pop.culture.gouv.fr/notice/joconde/'+rid;inv=v['Numero_inventaire'].strip();alt=[re.sub(r'\s*\([^)]*\)','',t).strip() for t in inv.split(';')]
  facts=dict(source_id=rid,native_id=rid,title=v['Titre'].strip(),titles=[v['Titre'].strip()],creator_label=v.get('Auteur') or 'Anonymous / unknown creator',first=a,last=b,date_precision=precision,date_display=display,work_type=kind,object_form=None,medium=v.get('Materiaux_techniques'),dimensions_text=v.get('Mesures'),inventory=inv,alternative_inventories=alt,source_url=u,native_page_urls=[u],native_metadata_urls=[source['receipts'][-1]['url']],source_fields=v)
  out.append(dict(number=n,source_id=rid,institution_id=s.IID,facts=facts,retrieved_at=source['receipts'][-1]['retrieved_at'],source_reference=ref(RUN/'joconde-selected-001.json.gz')))
 return out,held,existing
if __name__=='__main__':
 out,held,existing=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,held=held,existing=existing,script_reference=ref(Path(__file__).resolve())));print(json.dumps(dict(candidates=len(out),held=len(held),already=len(existing),dates=dict(collections.Counter(v['facts']['date_precision'] for v in out))),ensure_ascii=False))
