#!/usr/bin/env python3
"""Museum-specific association holding context, keeping actual source labels."""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-second-native-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n);m=n.m;RUN=n.RUN;ref=n.ref;checked=n.checked
QUEUE=RUN/'selected-metadata-queue-002.json';CONTEXT=RUN/'toulouse-association-context-001.json.gz'
def context():
    assert not CONTEXT.exists();url='https://toulousainsdetoulouse.fr/le-musee'
    response=requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected museum collection context)'},timeout=(15,45));raw=response.content
    receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));dest=RUN/'toulouse-association-context-001.body.gz';dest.write_bytes(gzip.compress(raw,mtime=0));m.save(RUN/'toulouse-association-context-001.receipt.json',receipt);response.raise_for_status();assert len(raw)<4_000_000
    soup=BeautifulSoup(raw,'html.parser')
    for node in soup(['script','style','noscript']):node.decompose()
    text=soup.get_text(' ',strip=True);assert 'association propriétaire des collections' in text
    m.save(CONTEXT,dict(at=m.now(),receipt=receipt,body_reference=ref(dest),text=text,interpretation='The museum operator explicitly identifies the association as owner of the collections. This resolves the private corporate ownership label for this museum only, subject to exact current object-level museum/location and no deposit or missing flags. No current display or image-use claim.'))
def screen(d):
    if d.get('Code_Museofile')!='M0567':return n.screen(d)
    raw={k:v or '' for k,v in d.items()};legal=m.norm(raw['Statut_juridique']);location=[m.norm(v) for v in raw['Localisation'].split(';') if v.strip()]
    if not (m.norm(raw['Statut_juridique'].split(';')[0])=='propriete privee personne morale' and location==[m.norm(raw['Ville']),m.norm(raw['Nom_officiel_musee'])] and m.norm(raw['Ville'])=='toulouse' and m.norm(raw['Nom_officiel_musee'])=='musee du vieux toulouse' and not raw.get('Lieu_de_depot') and not raw.get('MANQUANT') and not raw.get('MANQUANT_COM') and not re.search(r'pret|depot|restitu|recuperation',legal)):
        return None,'Toulouse museum/location or association ownership requires further review'
    ctx=m.load(CONTEXT);checked(ctx['body_reference']);assert ctx['receipt']['status']==200 and 'association propriétaire des collections' in ctx['text']
    # Reuse unchanged creation/type validators after this separate holding check.
    # Temporary normalized association label is never stored as source metadata.
    q=copy.deepcopy(d);q['Statut_juridique']="propriété d'une association;"+raw['Statut_juridique'].split(';',1)[1]
    parsed,reason=n.screen(q)
    if parsed:
        parsed['facts']['holding_basis']='Current Joconde exact museum/location plus official museum operator statement of association collection ownership; actual private corporate ownership label remains verbatim in source facts.'
        parsed['holding_context_reference']=ref(CONTEXT)
    return parsed,reason
def queue():
    assert not QUEUE.exists();x=m.load(n.DISCOVERY);rows=[];held=[]
    for row in x['rows']:
        if row['already_known'] or row['raw_source_record']['Code_Museofile']!='M0567':continue
        parsed,reason=screen(row['raw_source_record'])
        if reason:held.append(dict(source_id=row['raw_source_record']['Reference'],reason=reason));continue
        rows.append(dict(row,screen=parsed))
    groups=collections.defaultdict(list)
    for row in rows:groups[row['raw_source_record']['Auteur']].append(row)
    for rs in groups.values():rs.sort(key=lambda r:(len(r['raw_source_record']['Titre'])<12,r['raw_source_record']['Reference']))
    selected=[];offset=len(m.load(n.QUEUE)['selected'])
    while groups and len(selected)<38:
        for key in sorted(list(groups)):
            if len(selected)>=38:break
            row=groups[key].pop(0);selected.append(dict(row,number=offset+len(selected)+1,source_id=row['raw_source_record']['Reference'],state='metadata_research_only'))
            if not groups[key]:del groups[key]
    for rs in groups.values():
        for row in rs:held.append(dict(source_id=row['raw_source_record']['Reference'],reason='Outside bounded association-collection selection'))
    m.save(QUEUE,dict(at=m.now(),selector_reference=ref(Path(__file__).resolve()),discovery_reference=ref(n.DISCOVERY),context_reference=ref(CONTEXT),selected=selected,held=held,policy='Supplemental museum-specific holding review; all raw private corporate ownership labels remain untouched. No dates or images inferred. Supersedes only the earlier Toulouse holding-parser exclusions as research selection, not import approval.'));print(json.dumps(dict(selected=len(selected),held=len(held))),flush=True)
def capture():
    x=m.load(QUEUE);checked(x['selector_reference']);group=[r['source_id'] for r in x['selected']];assert len(group)<=40
    dest=RUN/'current-002/batch-001.json.gz';assert not dest.exists();params={'Reference__in':','.join(group),'page_size':40}
    response=requests.get(n.ENDPOINT,params=params,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected museum metadata, no images)'},timeout=(15,60));raw=response.content;assert len(raw)<6_000_000
    receipt=dict(url=response.url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());body=dest.with_suffix('.body.gz');body.parent.mkdir(parents=True,exist_ok=True);body.write_bytes(gzip.compress(raw,mtime=0));m.save(dest.with_suffix('.receipt.json'),receipt);response.raise_for_status();data=json.loads(raw)
    assert data['meta']['total']<=40 and not data['links'].get('next') and {r['Reference'] for r in data['data']}==set(group)
    m.save(dest,dict(at=m.now(),queue_reference=ref(QUEUE),requested=group,receipt=receipt,body_path=str(body.relative_to(m.ROOT)),data=data['data']));m.save(RUN/'capture-complete-002.json',dict(at=m.now(),queue_reference=ref(QUEUE),batches=[ref(dest)],images=0));print(json.dumps(dict(requested=len(group),returned=len(data['data']))),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['context','queue','capture']);globals()[p.parse_args().command]()
