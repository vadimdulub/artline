"""Literal M0284 object facts; artwork dates never inferred from creator lifetimes."""
import collections,gzip,hashlib,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-girodet-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
MANUAL_HOLDS={
'M0284000012':'Catalogue circa1825 creation conflicts with Girodet death1824; native dating/version review needed.',
'M0284000103':'Bound sketchbook and individual sheets need parent/component policy; do not multiply sheets.',
'M0284000108':'Bound sketchbook with eight separately catalogued components; count parent and children only after reconciliation.',
'M0284000296':'Photograph album requires physical-object and author-role review.',
'M0284000297':'Decorative clock, outside this selected painting/drawing/print/sculpture pass.',
'M0284000298':'Bound print collection; exact parent/components require reconciliation.',
'M0284000960':'Lithographic limestone matrix, not a paper impression; artwork form requires explicit matrix support.',
'M0284003930':'Printed volume, artist roles and parent/components need reconciliation.',
'M0284002755':'Source explicitly marks missing; no new accepted holding claim.',
}
for n in range(3963,3971):MANUAL_HOLDS['M028400'+str(n)]='Component of the 009.1.1.0 sketchbook; no separate count with parent.'
def dates(v):
 raw=(v.get('Millesime_de_creation') or '').strip();period=(v.get('Periode_de_creation') or '').strip();a=b=None;prec='unknown';display=raw or period or 'Creation date under review'
 if re.fullmatch(r'\d{4}(?: de)?',raw):a=b=int(raw[:4]);prec='exact'
 elif re.fullmatch(r'(?:vers )?\d{4}(?:,? ?vers)?',raw) and 'vers' in raw:a=b=int(re.search(r'\d{4}',raw)[0]);prec='circa'
 elif re.fullmatch(r'\d{4}(?:-| entre,)\d{4}(?: et)?(?: vers)?',raw):a,b=map(int,re.findall(r'\d{4}',raw));prec='circa_range' if 'vers' in raw else 'range'
 elif re.fullmatch(r'(?:avant \d{4}|\d{4} avant)',raw):b=int(re.search(r'\d{4}',raw)[0]);prec='before'
 elif not raw or raw=='vers':
  match=re.fullmatch(r'(?:(1er|[1-4]e) quart |(1ere|2e) moitie )?(\d{1,2})e siecle',m.norm(period))
  if match:
   century=int(match[3]);a,b=(century-1)*100+1,century*100;prec='century'
   if match[1]:a+=(int(match[1][0])-1)*25;b=a+24;prec='range'
   elif match[2]:a+=(int(match[2][0])-1)*50;b=a+49;prec='range'
   display=period+(' (millesime: vers, sans année)' if raw else '')
  elif re.fullmatch(r'\d{4} \(vers\)',period):a=b=int(period[:4]);prec='circa'
 else:raise ValueError('Unparsed date: '+raw+' / '+period)
 assert a is None or b is not None and 100<=a<=b
 return a,b,prec,display

def rows():
 source=m.load(RUN/'joconde-current-003.json.gz');out=[];held=[]
 for n,v in enumerate(sorted(source['rows'],key=lambda v:v['Reference']),1):
  rid=v['Reference'];why=MANUAL_HOLDS.get(rid);domain=(v.get('Domaine') or '').split(';');kind=next((k for d,k in [('peinture','painting'),('dessin','drawing'),('estampe','print'),('sculpture','sculpture')] if d in domain),None)
  if not kind:why=why or 'Outside selected painting/drawing/print/sculpture object scope; preserved for later research.'
  if v.get('MANQUANT') or v.get('MANQUANT_COM'):why=why or 'Missing-object flag requires reconciliation.'
  if v.get('Lieu_de_depot'):why=why or 'Explicit deposit: custody/ownership and existing lender record need reconciliation.'
  if not v.get('Titre') or not v.get('Numero_inventaire'):why=why or 'Missing title or object inventory.'
  legal=m.norm(v.get('Statut_juridique'))
  if not legal.startswith(('propriete de la commune','propriete de la communaute d agglomeration')) or any(t in legal for t in ['depot','pret','privee','restitution']):why=why or 'Holding context requires further review.'
  if m.norm(v.get('Localisation'))!='montargis musee girodet':why=why or 'Current catalogue institution needs reconciliation.'
  if why:held.append(dict(number=n,source_id=rid,reason=why,source_fields=v));continue
  try:a,b,prec,display=dates(v)
  except ValueError as e:held.append(dict(number=n,source_id=rid,reason=str(e),source_fields=v));continue
  u='https://pop.culture.gouv.fr/notice/joconde/'+rid
  facts=dict(source_id=rid,native_id=rid,title=v['Titre'].strip(),titles=[v['Titre'].strip()],creator_label=v.get('Auteur') or 'Anonymous / unknown creator',first=a,last=b,date_precision=prec,date_display=display,work_type=kind,object_form=None,medium=v.get('Materiaux_techniques'),dimensions_text=v.get('Mesures'),inventory=v['Numero_inventaire'],alternative_inventories=[],source_url=u,native_page_urls=[u],native_metadata_urls=[source['receipts'][0]['url']],source_fields=v)
  out.append(dict(number=n,source_id=rid,institution_id=s.IID,facts=facts,retrieved_at=source['receipts'][0]['retrieved_at'],source_reference=ref(RUN/'joconde-current-003.json.gz')))
 return out,held
if __name__=='__main__':
 out,held=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,held=held,script_reference=ref(Path(__file__).resolve())));print(json.dumps(dict(candidates=len(out),held=len(held),dates=dict(collections.Counter(v['facts']['date_precision'] for v in out))),ensure_ascii=False))
