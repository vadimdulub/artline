#!/usr/bin/env python3
"""Review date-wording differences and indexed object records at the agreed threshold."""
import argparse,collections,concurrent.futures,gzip,importlib.util,json,re,threading
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=mod('task','ops/assess-random-5000-round2-20261006.py');r=t.r;RUN=t.RUN
def dates():
 a=mod('adapters','ops/research-random-5000-primary-20261006.py');a.RUN=RUN;a.r.RUN=RUN;a.r.PORT=55483
 p=mod('primary','ops/research-artwork-location-primary-20261004.py');p.r.RUN=RUN;p.source=a.cached_source;i=a.index(p);original=i.match
 def match(row,scheme,oid,titles,artists,accession,dates):
  basis=original(row,scheme,oid,titles,artists,accession,dates)
  if basis=='supplied_date_wording_mismatch' and accession and len(t.norm(row['artwork']['title']).split())>=3:
   return 'unique_exact_supplied_creator_title_collection_with_source_inventory_date_wording_preserved; editorial confidence 82%, not a calibrated probability'
  return basis
 i.match=match;output=p.output
 def save(name,claims,holds):
  for c in claims:c['editorial_confidence']=.82 if '82%'in c['identity_basis']else .94
  output(name+'-date-reviewed',claims,holds)
 p.output=save;p.moma(i);p.fng(i)
def pages():
 cs=r.load(RUN/'indexed-candidate-review.json');byurl={c['source_url']:c for c in cs};blocked=set();locks=collections.defaultdict(threading.Lock)
 def one(url):
  hostname=urlsplit(url).hostname
  with locks[hostname]:
   if hostname in blocked:return {'url':url,'outcome':'host_stopped_after_access_failure'}
   try:
    raw,rc=r.capture(url,tag='indexed-primary-page-validation',timeout=35)
    if rc['status']in[403,429]:blocked.add(hostname)
    if rc['status']!=200:return {'url':url,'receipt':rc,'outcome':'http_'+str(rc['status'])}
    soup=BeautifulSoup(raw,'html.parser')
    for n in soup.select('script,style,nav,footer'):n.decompose()
    return {'url':url,'receipt':rc,'outcome':'captured','text':soup.get_text(' ',strip=True)}
   except Exception as exc:return {'url':url,'outcome':'request_failed','error':str(exc)[:400]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:results=list(ex.map(one,byurl))
 r.save_gz(RUN/'indexed-page-validation.json.gz',results);print('Primary pages',dict(collections.Counter(v['outcome']for v in results)),flush=True)
def deposits():
 p=mod('primary_deposit','ops/research-artwork-location-primary-20261004.py');p.r.RUN=RUN
 ii=r.load(RUN/'institutions.json.gz');byid={i['id']:i for i in ii};cross=r.load(RUN/'french-institution-crosswalk-v2.json');museums={}
 for i in ii:
  found=re.search(r'(?:museo/|joconde-)(m\d{4})',(i.get('website_url')or'')+' '+i['slug'],re.I)
  if found:museums.setdefault(found[1].upper(),[]).append(i)
 for code,v in cross.items():museums[code]=[byid[v['institution_id']]]
 done={c['artwork_id']for c in r.load(RUN/'primary-plans/primary-reconciled.json.gz')['claims']};rows={x['artwork']['id']:x for x in r.load(RUN/'primary-input-rows.json.gz')};claims=[];holds=[]
 for h in r.load(RUN/'primary-plans/joconde-final.json.gz')['holds']:
  if h['reason']!='deposit_requires_location_review'or h['artwork_id']in done:continue
  o=h['object_evidence'];city=t.norm(o.get('Ville'));museum=t.norm(o.get('Nom_officiel_musee'));location=t.norm(o.get('Localisation'));legal=t.norm(o.get('Statut_juridique'));deposit=t.norm(o.get('Lieu_de_depot'));code=o.get('Code_Museofile','').upper();inst=museums.get(code,[])
  if len(inst)!=1 or o.get('MANQUANT')or o.get('MANQUANT_COM')or re.search(r'usufruit|restitut|inconnu|pret|retour|termine',deposit+' '+legal):holds.append({'artwork_id':h['artwork_id'],'reason':'deposit_conditions_not_resolved'});continue
  # Explicit official object location and named receiving-museum deposit agree.
  # A recovered-work status (EARM) concerns title/ownership, not an invented
  # transfer of ownership; that original legal field remains in the evidence.
  agreed=location==t.norm(city+' '+museum)and city in deposit and ('musee'in deposit or 'abattoirs'in deposit)
  if not agreed:holds.append({'artwork_id':h['artwork_id'],'reason':'deposit_museum_or_city_not_concordant'});continue
  c=p.claim(rows[h['artwork_id']],'joconde-object',h['reference'],inst[0],h['source_receipt'],'https://pop.culture.gouv.fr/notice/joconde/'+h['reference'],{'current_object_record':o,'collection_role':'explicit_receiving_museum_deposit_or_allocation','institution_identity_review':cross.get(code)},'Unique exact supplied creator, title, date and museum, current national object reference and inventory rechecked; official location and named receiving-museum deposit agree. Editorial confidence 86%, not a calibrated probability.')
  c['editorial_confidence']=.86;c['limitation']='Officially documented receiving-museum deposit or allocation. Source owner, deposit and legal-status fields, including EARM where supplied, are retained separately. No ownership transfer, physical whereabouts or current display is asserted. Artwork metadata and review status stay unchanged.';claims.append(c)
 p.output('museum-deposits-reviewed',claims,holds)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['dates','pages','deposits']);a=ap.parse_args();globals()[a.phase]()
