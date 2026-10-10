#!/usr/bin/env python3
"""Bounded current national-catalogue research for five underfilled museums."""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museum-expansion-20261006.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.RUN/'native/france-third-minimum-20261008';DISCOVERY=RUN/'five-museum-discovery-001.json.gz';QUEUE=RUN/'selected-metadata-queue-001.json'
ENDPOINT='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'
def ref(path):return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def checked(dep):
    p=m.ROOT/dep['path'];assert ref(p)==dep;return p
def screen(row):
    d={k:v or '' for k,v in row.items()};q=copy.deepcopy(d);domains={m.norm(v) for v in d['Domaine'].split(';')};classes=domains & {'dessin','peinture','estampe','sculpture'};form=m.norm(d['Denomination']);derived=[];ceramic=False
    if not d['Titre'] or not d['Numero_inventaire']:return None,'Missing title or inventory'
    if 'ceramique' in domains and re.match(r'^(assiette|plat|saladier|coupe|bol|vase|bouteille)(?:$| )',form) and ';' not in d['Denomination'] and re.search(r'faience|porcelaine|ceramique|terre',m.norm(d['Materiaux_techniques'])):
        ceramic=True;q['Denomination']='tableau';q['Domaine']='peinture';derived.append('Work type ceramic from literal ceramic domain, single vessel/plate denomination and fired-clay medium. Temporary parser inputs used only for shared date/holding validation, never stored as source facts.')
    else:
        if len(classes)!=1:return None,'No unambiguous supported artwork category'
        typ=next(iter(classes))
        if not form and typ in ['dessin','peinture','estampe']:
            q['Denomination']={'dessin':'dessin','peinture':'tableau','estampe':'estampe'}[typ];derived.append('Work type from explicit '+typ+' domain; missing denomination stays missing in original source record.')
        if typ=='sculpture':q['Domaine']='sculpture';derived.append('Sculpture is explicitly present among source domains; original multi-domain label retained.')
    text=m.norm(' '.join(d.get(k,'') for k in ['Titre','Denomination','Domaine','Description','Commentaires','Genese','Historique']))
    if re.search(r'\b(?:matrice|element d impression|planche a imprimer|album|carnet|portefeuille|ensemble de|serie de)\b',text):return None,'Physical assembly, printing matrix or album requires separate object-unit review'
    parsers=[m.joconde_sculpture_facts] if not ceramic and 'sculpture' in domains else [m.joconde_facts,m.joconde_period_facts,m.joconde_range_facts,m.joconde_circa_facts,m.joconde_before_facts]
    attempted=[]
    for parser in parsers:
        v,reason=parser(q);attempted.append(reason)
        if not v:continue
        if ceramic:v['work_type']='ceramic'
        return dict(facts=v,parser=parser.__name__,derivations=derived),None
    return None,'; '.join(dict.fromkeys(x for x in attempted if x))
def queue():
    assert not QUEUE.exists();x=m.load(DISCOVERY);groups=collections.defaultdict(list);held=[]
    for row in x['rows']:
        if row['already_known']:continue
        parsed,reason=screen(row['raw_source_record'])
        if reason:held.append(dict(source_id=row['raw_source_record']['Reference'],institution_id=row['museum']['id'],reason=reason));continue
        groups[row['raw_source_record']['Code_Museofile']].append(dict(row,screen=parsed))
    caps={'M0181':50,'M0949':50,'M0695':50,'M0703':50,'M0284':50};selected=[]
    for code,rows in sorted(groups.items()):
        # Prefer specific titles, individual dated objects and a spread of creators.
        creators=collections.defaultdict(list)
        for row in rows:
            d=row['raw_source_record'];creators[d['Auteur']].append(row)
        for rs in creators.values():rs.sort(key=lambda r:(len(r['raw_source_record']['Titre'])<12,r['screen']['facts'].get('date_precision')=='before',r['raw_source_record']['Reference']))
        chosen=[]
        while creators and len(chosen)<caps[code]:
            for creator in sorted(list(creators)):
                if len(chosen)>=caps[code]:break
                chosen.append(creators[creator].pop(0))
                if not creators[creator]:del creators[creator]
        for row in chosen:
            selected.append(dict(row,number=len(selected)+1,source_id=row['raw_source_record']['Reference'],state='metadata_research_only'))
        for rs in creators.values():
            for row in rs:held.append(dict(source_id=row['raw_source_record']['Reference'],institution_id=row['museum']['id'],reason='Outside bounded selected metadata pass; remains an unreviewed source lead'))
    assert len(selected)==len({r['source_id'] for r in selected})<=250
    m.save(QUEUE,dict(at=m.now(),discovery_reference=ref(DISCOVERY),selector_reference=ref(Path(__file__).resolve()),selected=selected,held=held,policy='Bounded selection for full current metadata and duplicate review, not approval. Explicit source domains can establish artwork type without inventing a missing denomination. Unknown creation and physical groups are held; no images.'))
    print(json.dumps(dict(selected=len(selected),by_museum=collections.Counter(r['raw_source_record']['Code_Museofile'] for r in selected),held=len(held))),flush=True)
def capture():
    x=m.load(QUEUE);checked(x['selector_reference']);assert not list((RUN/'source-errors-001').glob('*.json'))
    refs=[r['source_id'] for r in x['selected']]
    for start in range(0,len(refs),40):
        dest=RUN/'current-001'/('batch-%03d.json.gz'%(start//40+1));assert not dest.exists();group=refs[start:start+40]
        params={'Reference__in':','.join(group),'page_size':40}
        try:
            time.sleep(2)
            with requests.get(ENDPOINT,params=params,headers={'User-Agent':'ArtlineMuseumResearch/1.0 (bounded selected museum metadata; no images)'},timeout=(15,60),stream=True) as response:
                raw=b''
                for chunk in response.iter_content(65536):
                    raw+=chunk
                    if len(raw)>6_000_000:raise ValueError('Bounded metadata response exceeded')
                receipt=dict(url=response.url,final_url=response.url,status=response.status_code,retrieved_at=m.now(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                body=dest.with_suffix('.body.gz');body.parent.mkdir(parents=True,exist_ok=True);assert not body.exists();body.write_bytes(gzip.compress(raw,mtime=0));m.save(dest.with_suffix('.receipt.json'),receipt);response.raise_for_status()
            data=json.loads(raw);assert data['meta']['total']<=40 and not data['links'].get('next') and len({r['Reference'] for r in data['data']})==len(data['data']) and all(r['Reference'] in group for r in data['data'])
            m.save(dest,dict(at=m.now(),queue_reference=ref(QUEUE),requested=group,receipt=receipt,body_path=str(body.relative_to(m.ROOT)),data=data['data']));print(json.dumps(dict(batch=start//40+1,requested=len(group),returned=len(data['data']))),flush=True)
        except Exception as e:
            m.save(RUN/'source-errors-001'/('batch-%03d.json'%(start//40+1)),dict(at=m.now(),endpoint=ENDPOINT,params=params,error=repr(e),policy='Stopped first failure; no retry or source bypass.'));raise
    m.save(RUN/'capture-complete-001.json',dict(at=m.now(),queue_reference=ref(QUEUE),batches=[ref(p) for p in sorted((RUN/'current-001').glob('batch-*.json.gz'))],images=0))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['queue','capture']);globals()[p.parse_args().command]()
