#!/usr/bin/env python3
"""Resolve source collection/deposit roles and exact Italian museum/city names."""
import collections,gzip,importlib.util,re,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=module('task','ops/research-random-5000-primary-20261006.py');r=t.r;RUN=t.RUN
p=module('primary','ops/research-artwork-location-primary-20261004.py');p.r.RUN=RUN
w=module('wiki','ops/reconcile-random-5000-wikiart-museums-20261006.py');norm=w.norm

def deposit_role(o):
    """Collection administration may continue while the work is deposited elsewhere."""
    name,city=norm(o.get('Nom_officiel_musee')),norm(o.get('Ville'))
    legal=norm(o.get('Statut_juridique'));location=norm(o.get('Localisation'))
    if not name or not city or location!=norm(city+' '+name):return None
    if o.get('MANQUANT')or o.get('MANQUANT_COM'):return None
    if re.search(r'usufruit|restitut|recuperation|earm|prive|particulier|inconnu',legal):return None
    if legal.startswith('propriete') and name in legal and city in legal:
        return 'registered_museum_collection_with_separately_disclosed_deposit'
    parts=[norm(v)for v in (o.get('Lieu_de_depot')or'').split(';')if v.strip()]
    if len(parts)>=3 and parts[-2:]==[city,name] and parts[-3]in {'depot','depot reglementaire','depot de l etat'} and not re.search(r'pret|retour|restitu|termine|\?',o.get('Lieu_de_depot')or'',re.I):
        return 'documented_deposit_received_by_registered_museum'
    return None

def main():
    rows={x['artwork']['id']:x for x in r.load(RUN/'primary-input-rows.json.gz')};ii=r.load(RUN/'institutions.json.gz');byid={i['id']:i for i in ii};claims=[];holds=[]
    selected={x['object_id']:x for x in r.load(RUN/'italy-selection.json.gz')['unique']};current={}
    for path in (RUN/'italy-batches').glob('*.json.gz'):
        b=r.load(path)
        for o in b['data']:current[o['idk']]=(o,b['receipt'])
    # These names are already present with city/province in their authority name.
    italian={('Istituto dei Ciechi di Milano - Museo Louis Braille','Milano'):'d55cfa08-90f8-509a-a948-e5e4d4a62758',('Museo Morando Bolognini',"Sant'Angelo Lodigiano"):'ea56eab1-4783-5ae2-b145-c1c861c1f390'}
    italian={(norm(a),norm(b)):c for(a,b),c in italian.items()}
    for h in r.load(RUN/'primary-plans/lombardia.json.gz')['holds']:
        oid=h['object_id'];o,rc=current[oid];v=selected[oid];prior=v['source_record'];iid=italian.get((norm(o.get('ldcm')),norm(o.get('pvcc'))))
        if not iid:holds.append({**h,'reason':'foundation_historic_site_or_other_collection_requires_separate_review'});continue
        assert all(p.titlekey(o.get(k))==p.titlekey(prior.get(k))for k in ['autn','sgtt','sgti','ldcm','ldci','pvcc'])
        url=o['url'].replace('http://','https://',1);assert url.rstrip('/').endswith('/'+oid)
        inst=byid[iid];assert norm(o['ldcm'])in norm(inst['name'])and norm(o['pvcc'])in norm(inst['name'])
        claims.append(p.claim(rows[h['artwork_id']],'lombardia-object',oid,inst,rc,url,o,v['identity_basis']+'; exact museum name and city reconciled to existing city-qualified institution authority'))
    museums={}
    for i in ii:
        c=re.search(r'(?:museo/|joconde-)(m\d{4})',(i.get('website_url')or'')+' '+i['slug'],re.I)
        if c:museums.setdefault(c[1].upper(),[]).append(i)
    crosswalk=r.load(RUN/'french-institution-crosswalk-v2.json')
    for code,a in crosswalk.items():museums[code]=[byid[a['institution_id']]]
    selected={x['reference']:x for x in r.load(RUN/'france-selection.json.gz')['unique']}
    for h in r.load(RUN/'primary-plans/joconde-final.json.gz')['holds']:
        if h['reason']!='deposit_requires_location_review':continue
        o=h['object_evidence'];role=deposit_role(o);v=selected[h['reference']];code=o.get('Code_Museofile','').upper();inst=museums.get(code,[])
        if not role or len(inst)!=1:holds.append({'artwork_id':h['artwork_id'],'reason':'deposit_and_collection_roles_not_sufficiently_resolved','reference':h['reference']});continue
        assert p.titlekey(o['Titre'])==p.titlekey(v['title'])and r.namekey(o['Auteur'])==r.namekey(v['artist'])and p.acckey(o['Numero_inventaire'])==p.acckey(v['inventory'])and code==v['museum_code'].upper()
        c=p.claim(rows[h['artwork_id']],'joconde-object',h['reference'],inst[0],h['source_receipt'],'https://pop.culture.gouv.fr/notice/joconde/'+h['reference'],{'current_object_record':o,'collection_role':role,'institution_identity_review':crosswalk.get(code)},'Unique exact supplied creator, title, date and museum; current national reference and inventory rechecked; '+role)
        c['limitation']='Documented administering museum collection or explicit receiving-museum deposit. Source deposit destination and legal status are preserved separately. No physical whereabouts, ownership transfer or current-display claim; original dates, creators and publication state are unchanged.'
        claims.append(c)
    p.output('primary-reconciled',claims,holds)
    print('Resolved museums',dict(collections.Counter(c['institution']['name']for c in claims)),flush=True)

if __name__=='__main__':main()
