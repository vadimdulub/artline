"""Museum-specific aliases and public ownership, preserving original source fields."""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-third-native-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=n.RUN;ref=n.ref;checked=n.checked;QUEUE=RUN/'selected-metadata-queue-002.json'
CONTEXTS={
 'tournus':('https://pop.culture.gouv.fr/notice/museo/M0181',['M0181','Autres noms','Musée Greuze','musée Greuze - hôtel-Dieu','Tournus']),
 'montargis':('https://www.agglo-montargoise.fr/culture-sport-et-tourisme/musee-girodet-11199',['Musée Girodet','Collections','Montargis']),
 'flers':('https://www.flers-agglo.fr/mon-quotidien/culture/les-musees/musee-du-chateau-de-flers-2/',['300 peintures','musée municipal']),
 'carpentras':('https://inguimbertine.carpentras.fr/la-bibliotheque-musee/expositions-et-collections/les-collections-permanentes/oeuvres-remarquables',['887.2.1','2007.0.16','2012.2.1'])
}
def context_path(key):return RUN/'context'/('official-'+key+'-001.json.gz')
def context():
    for key,(url,need) in CONTEXTS.items():
        dest=context_path(key);assert not dest.exists();response=requests.get(url,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected museum identity context; no images)'},timeout=(15,45));raw=response.content;assert len(raw)<6_000_000
        receipt=dict(url=url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));body=dest.with_suffix('.body.gz');body.parent.mkdir(parents=True,exist_ok=True);assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(dest.with_suffix('.receipt.json'),receipt);response.raise_for_status()
        soup=BeautifulSoup(raw,'html.parser')
        for node in soup(['script','style','noscript']):node.decompose()
        text=soup.get_text(' ',strip=True);assert all(v in text for v in need),(key,need)
        m.save(dest,dict(at=m.now(),receipt=receipt,body_reference=ref(body),text=text,policy='Official museum identity/collection context. Only explicit object-level holdings can support additions. Generic display and digital Micro-Folie collections do not establish this museum holding.'))
        print(json.dumps(dict(context=key,status=response.status_code,bytes=len(raw))),flush=True)
def screen(d):
    code=d.get('Code_Museofile');q=copy.deepcopy(d);ctx=None
    if code=='M0181' and m.norm(d.get('Localisation'))=='tournus musee greuze':
        if m.norm(d.get('Ville'))!='tournus' or m.norm(d.get('Nom_officiel_musee'))!='musee greuze hotel dieu':return None,'Tournus alias disagrees with museum code/name/city'
        ctx=context_path('tournus');c=m.load(ctx);checked(c['body_reference']);assert c['receipt']['status']==200 and all(v in c['text'] for v in CONTEXTS['tournus'][1])
        q['Localisation']='Tournus ; '+d['Nom_officiel_musee']
    elif code=='M0284' and m.norm((d.get('Statut_juridique') or '').split(';')[0])=='propriete de la communaute d agglomeration':
        if m.norm(d.get('Ville'))!='montargis' or m.norm(d.get('Nom_officiel_musee'))!='musee girodet' or m.norm(d.get('Localisation'))!='montargis musee girodet' or m.norm((d.get('Statut_juridique') or '').split(';')[-1])!='musee girodet':return None,'Montargis public owner/museum/location requires review'
        ctx=context_path('montargis');c=m.load(ctx);checked(c['body_reference']);assert c['receipt']['status']==200 and all(v in c['text'] for v in CONTEXTS['montargis'][1])
        q['Statut_juridique']='propriété de la commune;'+d['Statut_juridique'].split(';',1)[1]
    parsed,reason=n.screen(q)
    if parsed and ctx:
        parsed['holding_context_reference']=ref(ctx)
        parsed['facts']['holding_basis']='Exact native museum code/name/city plus source-backed alias or public intercommunal ownership. Temporary parser normalization is not a source-field correction; original location and legal labels preserved. No deposit, missing or current-display inference.'
    return parsed,reason
def queue():
    assert not QUEUE.exists();initial=m.load(n.QUEUE);selectedids={v['source_id'] for v in initial['selected']};groups=collections.defaultdict(list);held=[]
    for row in m.load(n.DISCOVERY)['rows']:
        d=row['raw_source_record']
        if row['already_known'] or d['Reference'] in selectedids or d['Code_Museofile'] not in ['M0181','M0284']:continue
        parsed,reason=screen(d)
        if reason:held.append(dict(source_id=d['Reference'],reason=reason));continue
        groups[d['Code_Museofile']].append(dict(row,screen=parsed))
    selected=[]
    for code,rows in sorted(groups.items()):
        creators=collections.defaultdict(list)
        for row in rows:creators[row['raw_source_record']['Auteur']].append(row)
        for rs in creators.values():rs.sort(key=lambda v:(len(v['raw_source_record']['Titre'])<12,v['raw_source_record']['Reference']))
        cap={'M0181':50,'M0284':10}[code];chosen=[]
        while creators and len(chosen)<cap:
            for key in sorted(list(creators)):
                if len(chosen)>=cap:break
                chosen.append(creators[key].pop(0))
                if not creators[key]:del creators[key]
        for row in chosen:selected.append(dict(row,number=len(initial['selected'])+len(selected)+1,source_id=row['raw_source_record']['Reference'],state='metadata_research_only'))
        for rs in creators.values():
            for row in rs:held.append(dict(source_id=row['raw_source_record']['Reference'],reason='Outside bounded supplemental selection'))
    m.save(QUEUE,dict(at=m.now(),selector_reference=ref(Path(__file__).resolve()),discovery_reference=ref(n.DISCOVERY),context_references=[ref(context_path(k)) for k in ['tournus','montargis']],selected=selected,held=held,policy='Research selection only. Narrowly supported museum alias/public owner does not waive object identity, creation, deposit, missing or physical-unit review. Supersedes initial exclusions only for selected source IDs.'))
    print(json.dumps(dict(selected=len(selected),by_museum=collections.Counter(v['raw_source_record']['Code_Museofile'] for v in selected),held=len(held))),flush=True)
def capture():
    x=m.load(QUEUE);checked(x['selector_reference']);refs=[v['source_id'] for v in x['selected']]
    for start in range(0,len(refs),40):
        group=refs[start:start+40];dest=RUN/'current-002'/('batch-%03d.json.gz'%(start//40+1));assert not dest.exists();time.sleep(2)
        response=requests.get(n.ENDPOINT,params={'Reference__in':','.join(group),'page_size':40},headers={'User-Agent':'ArtlineMuseumResearch/1.0 (selected metadata; no images)'},timeout=(15,60));raw=response.content;assert len(raw)<6_000_000
        receipt=dict(url=response.url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));body=dest.with_suffix('.body.gz');body.parent.mkdir(parents=True,exist_ok=True);assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(dest.with_suffix('.receipt.json'),receipt);response.raise_for_status();data=json.loads(raw)
        assert data['meta']['total']<=40 and not data['links'].get('next') and {v['Reference'] for v in data['data']}==set(group)
        m.save(dest,dict(at=m.now(),queue_reference=ref(QUEUE),requested=group,receipt=receipt,body_path=str(body.relative_to(m.ROOT)),data=data['data']));print(json.dumps(dict(batch=start//40+1,returned=len(data['data']))),flush=True)
    m.save(RUN/'capture-complete-002.json',dict(at=m.now(),queue_reference=ref(QUEUE),batches=[ref(p) for p in sorted((RUN/'current-002').glob('batch-*.json.gz'))],images=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['context','queue','capture']);globals()[p.parse_args().command]()
