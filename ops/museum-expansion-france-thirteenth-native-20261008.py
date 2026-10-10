#!/usr/bin/env python3
"""Bounded current national-catalogue research for five underfilled museums."""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museum-expansion-20261006.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.RUN/'native/france-thirteenth-minimum-20261008';DISCOVERY=RUN/'five-museum-discovery-001.json.gz';QUEUE=RUN/'selected-metadata-queue-001.json'
ENDPOINT='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'
def ref(path):return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def checked(dep):
    p=m.ROOT/dep['path'];assert ref(p)==dep;return p
def holding_context(d):
    path=RUN/'museum-name-reconciliation-001.json';x=m.load(path);c=x['museums'].get(d.get('Code_Museofile'))
    if not c:return None
    for dep in c['evidence']:checked(dep)
    if m.norm(d.get('Ville'))!=m.norm(c['city']) or m.norm(d.get('Nom_officiel_musee')) not in [m.norm(v) for v in c['names']]:return None
    if m.norm(d.get('Localisation')) not in [m.norm(v) for v in c['locations']]:return None
    if any(d.get(k) for k in ['Lieu_de_depot','MANQUANT','MANQUANT_COM']):return None
    legal=m.norm(d.get('Statut_juridique'))
    if not legal.startswith(tuple(c['owner_prefixes'])) or not any(legal.endswith(m.norm(v)) for v in c['owners']) or re.search(r'pret|depot|restitu|recuperation|privee|particulier',legal):return None
    return ref(path)
def explicit_period_union(raw):
    parts=(raw or '').split(';');bounds=[m.french_period(p.strip()) for p in parts]
    if not parts or len(parts)>3 or any(v[0] is None for v in bounds):return None
    return min(v[0] for v in bounds),max(v[1] for v in bounds)
def reviewed_date_notation(row,sculpture=False):
    raw=(row.get('Millesime_de_creation') or '').strip();period=row.get('Periode_de_creation') or '';bounds=explicit_period_union(period)
    if not bounds:return None,'additional_date_notation_without_wholly_eligible_explicit_period'
    first,last=bounds
    between=re.fullmatch(r'(\d{3,4})\s+entre\s*,\s*(\d{3,4})\s+et',raw,re.I)
    if between:
        low,high=map(int,between.groups())
        if not first<=low<=high<=last:return None,'explicit_between_date_conflicts_with_period'
        facts,reason=m.joconde_interval_object(row,low,high,'exact' if low==high else 'range',sculpture)
        if facts:facts['holding_basis']+=' Explicit between endpoints retained as the source creation interval; no subject-date inference.'
        return facts,reason
    if not raw and ';' in period:
        facts,reason=m.joconde_interval_object(row,first,last,'range',sculpture)
        if facts:
            facts['date_display']=period;facts['holding_basis']+=' Broad interval covers all explicitly supplied eligible creation periods; no single year or narrower period chosen.'
        return facts,reason
    match=re.fullmatch(r'(\d{3,4})(?:\s*[-–]\s*(\d{3,4}))?\s*(?:\(vers\)|:\s*vers)',raw,re.I)
    if not match:return None,'not_supported_parenthetical_circa'
    low=int(match[1]);high=int(match[2] or match[1])
    if not first<=low<=high<=last:return None,'circa_notation_conflicts_with_explicit_period'
    life=re.search(r'\((\d{4})-(\d{4})\)',row.get('Auteur') or '')
    if life and (high<int(life[1]) or low>int(life[2])):return None,'circa_notation_lifespan_conflict'
    facts,reason=m.joconde_interval_object(row,first,last,'circa_range',sculpture)
    if facts:facts['holding_basis']+=' Literal parenthetical circa wording retained; finite bounds derive solely from independently supplied creation periods, not invented numerical tolerance.'
    return facts,reason
def screen(row):
    d={k:v or '' for k,v in row.items()};q=copy.deepcopy(d);domains={m.norm(v) for v in d['Domaine'].split(';')};classes=domains & {'dessin','peinture','estampe','sculpture'};form=m.norm(d['Denomination']);derived=[];ceramic=False;photograph=False;sculpture=False
    if not d['Titre'] or not d['Numero_inventaire']:return None,'Missing title or inventory'
    if 'photographie' in domains:
        medium=m.norm(d['Materiaux_techniques']);description=m.norm(d['Description'])
        if classes or domains-{'photographie','architecture','vie sociale culturelle'} or form not in ['', 'photographie']:
            return None,'Photographic mixed assembly or competing object type needs individual unit review'
        if not (re.search(r'papier albumine|gelatino argentique|tirage argentique|procede argentique|ambrotype',medium) and re.search(r'tirage|epreuve|ambrotype',medium+' '+description)):
            return None,'No explicit physical photographic print or original ambrotype support'
        if re.search(r'retirage|posthume|photocopie|fac simile|tirage moderne|reproduction moderne',description+' '+m.norm(d['Historique'])):
            return None,'Photographic impression chronology or reproduction requires individual research'
        photograph=True;q['Denomination']='tableau';q['Domaine']='peinture';derived.append('Physical photograph from explicit photography domain and photographic support/process; parser-only type substitution for shared date and custody checks. Literal fields remain unchanged. Depicted building/sculpture is the subject, not the catalogued object. Creation field must apply to this print, separately reviewed against negative/reprint chronology.')
    elif 'ceramique' in domains and re.match(r'^(assiette|plat|saladier|coupe|bol|vase|bouteille)(?:$| )',form) and ';' not in d['Denomination'] and re.search(r'faience|porcelaine|ceramique|terre',m.norm(d['Materiaux_techniques'])):
        ceramic=True;q['Denomination']='tableau';q['Domaine']='peinture';derived.append('Work type ceramic from literal ceramic domain, single vessel/plate denomination and fired-clay medium. Temporary parser inputs used only for shared date/holding validation, never stored as source facts.')
    else:
        if len(classes)!=1:return None,'No unambiguous supported artwork category'
        typ=next(iter(classes))
        if not form and typ in ['dessin','peinture','estampe']:
            q['Denomination']={'dessin':'dessin','peinture':'tableau','estampe':'estampe'}[typ];derived.append('Work type from explicit '+typ+' domain; missing denomination stays missing in original source record.')
        if typ=='dessin' and form=='pastel' and 'pastel' in m.norm(d['Materiaux_techniques']):
            q['Denomination']='dessin';derived.append('Drawing category from explicit drawing domain and pastel denomination and medium; literal source form retained.')
        if typ=='estampe' and form=='image pieuse' and 'papier' in m.norm(d['Materiaux_techniques']):
            q['Denomination']='estampe';derived.append('Physical devotional print from explicit estampe domain, paper support and image-pieuse form. Original form retained; print edition and impression dates require separate review.')
        if typ=='dessin' and form=='element d ensemble' and d['Code_Museofile']=='M1098':
            physical=m.norm(d['Materiaux_techniques']+' '+d['Description'])
            if not d['Mesures'] or not re.search(r'papier|calque|carton',physical) or not re.search(r'encre|crayon|gouache|aquarelle|stylo|fusain|sanguine|pastel',physical):return None,'Illustration component lacks explicit physical drawing support or dimensions'
            if re.search(r'collage|assemblage|decoup|carnet|album|relie|colle sur une page',physical):return None,'Mixed or physically bound illustration needs separate unit review'
            q['Denomination']='dessin';derived.append('Drawing type from explicit drawing domain and physical ink/pencil/paint on paper, card or tracing support with object dimensions. Original element-of-ensemble designation retained. Logical project/book grouping, recto/verso and physical independence require individual review; no automatic component counting.')
        if typ=='sculpture':
            physical=m.norm(d['Materiaux_techniques'])
            if not physical:
                description=m.norm(d['Description'])
                if re.match(r'^(?:platre|bronze|pierre|marbre|terre|bois|cire|metal|resine|beton|ceramique|porcelaine)\b',description):physical=description
            if form not in ['', 'sculpture','statue','statuette','buste','figurine','relief','bas relief','haut relief','tete','torse','medaillon','groupe'] or not d['Mesures'] or not re.search(r'platre|bronze|pierre|marbre|terre|bois|cire|metal|resine|beton|ceramique|porcelaine',physical):return None,'Sculpture lacks supported physical medium, dimensions or form'
            if re.search(r'\b(?:socle|fragment|moule|matrice|empreinte)\b',m.norm(d['Titre']+' '+d['Denomination'])):return None,'Sculpture pedestal, mold, fragment or matrix needs independent unit review'
            sculpture=True;q['Domaine']='peinture';q['Denomination']='tableau';derived.append('Sculpture type from explicit sculpture domain, physical three-dimensional medium and measurements. Parser-only substitution invokes shared creation/custody checks without conflating original plaster, model, cast, related artwork or edition. Literal source fields retained and each physical version requires individual review; no inferred casting date or new form label.')

    text=m.norm(' '.join(d.get(k,'') for k in ['Titre','Denomination','Domaine','Description','Commentaires','Genese','Historique']))
    if re.search(r'\b(?:matrice|element d impression|planche a imprimer|album|carnet|portefeuille|ensemble de|serie de)\b',text):return None,'Physical assembly, printing matrix or album requires separate object-unit review'
    parsers=[m.joconde_facts,m.joconde_period_facts,m.joconde_range_facts,m.joconde_circa_facts,m.joconde_before_facts]
    context=holding_context(d)
    if not context:return None,'Museum context, ownership or custody not reconciled'
    q['Localisation']=d['Ville']+' ; '+d['Nom_officiel_musee']
    if m.norm(d['Statut_juridique']).startswith('propriete de la collectivite locale'):
        q['Statut_juridique']='propriété de la commune;'+d['Statut_juridique'].split(';',1)[-1];derived.append('Literal local-authority ownership accepted by exact source museum context; parser-only public-municipal prefix used for shared holding check. Original ownership wording retained without legal-title reclassification.')
    derived.append('Literal museum-name punctuation or historical short form reconciled through exact source code, city and municipal owner destination. Parser-only normalized location; original fields preserved.')
    parsers.append(lambda value:reviewed_date_notation(value,False))
    attempted=[]
    for parser in parsers:
        v,reason=parser(q);attempted.append(reason)
        if not v:continue
        if ceramic:v['work_type']='ceramic'
        if photograph:v['work_type']='photograph'
        if sculpture:v['work_type']='sculpture'
        period_bounds=explicit_period_union(d['Periode_de_creation'])
        low=v.get('first',v.get('year'));high=v.get('last',v.get('year'))
        if period_bounds and low is not None and high is not None and not period_bounds[0]<=low<=high<=period_bounds[1]:return None,'Explicit creation date or range conflicts with independently stated source period'
        if parser.__name__=='<lambda>':derived.append('Creation-notation derivation: all explicit eligible period components supply broad bounds; parenthetical circa remains qualified. Literal creation wording is stored unchanged.')
        return dict(facts=v,parser=('reviewed_date_notation' if parser.__name__=='<lambda>' else parser.__name__),derivations=derived,holding_context_reference=context),None
    return None,'; '.join(dict.fromkeys(x for x in attempted if x))
def queue():
    assert not QUEUE.exists();x=m.load(DISCOVERY);groups=collections.defaultdict(list);held=[]
    previous_queues=sorted(p for p in (m.RUN/'native').glob('france-*/selected-metadata-queue-*.json') if p.parent!=RUN)
    previous_selected={v['source_id'] for path in previous_queues for v in m.load(path)['selected']}
    for row in x['rows']:
        if row['already_known'] or row['raw_source_record']['Reference'] in previous_selected:continue
        if row['raw_source_record']['Code_Museofile']=='M0422' and 'lancon' in m.norm(row['raw_source_record']['Auteur']):
            held.append(dict(source_id=row['raw_source_record']['Reference'],institution_id=row['museum']['id'],reason='Lançon physical-impression chronology remains unresolved; source scene 1870 does not establish print edition date. Prior BnF evidence retained in tenth pass.'));continue
        parsed,reason=screen(row['raw_source_record'])
        if reason:held.append(dict(source_id=row['raw_source_record']['Reference'],institution_id=row['museum']['id'],reason=reason));continue
        groups[row['raw_source_record']['Code_Museofile']].append(dict(row,screen=parsed))
    caps={'M0537':130,'M1098':120,'M0634':160,'M0081':130,'M0784':80};selected=[]
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
    assert len(selected)==len({r['source_id'] for r in selected})<=650
    m.save(QUEUE,dict(at=m.now(),discovery_reference=ref(DISCOVERY),prior_queue_references=[ref(path) for path in previous_queues],selector_reference=ref(Path(__file__).resolve()),selected=selected,held=held,policy='Bounded selection for full current metadata and duplicate review, not approval. Explicit source domains can establish artwork type without inventing a missing denomination. Unknown creation and physical groups are held; no images.'))
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
