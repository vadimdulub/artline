#!/usr/bin/env python3
"""Select bounded artwork metadata with separate date, physical-form and holding checks."""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,re,time
from pathlib import Path
import requests
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museum-expansion-20261006.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.RUN/'native/france-fourteenth-minimum-20261008';DISCOVERY=RUN/'five-museum-discovery-001.json.gz';QUEUE=RUN/'selected-metadata-queue-001.json'
ENDPOINT='https://tabular-api.data.gouv.fr/api/resources/7e3307c2-f2ff-455c-bbca-bb6f11aec7bb/data/'
def ref(path):return dict(path=str(path.relative_to(m.ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
def checked(dep):
    p=m.ROOT/dep['path'];assert ref(p)==dep;return p

def holding_context(d):
    path=RUN/'museum-name-reconciliation-001.json';c=m.load(path)['museums'].get(d.get('Code_Museofile'))
    if not c:return None
    for dep in c['evidence']:checked(dep)
    if m.norm(d.get('Ville'))!=m.norm(c['city']) or m.norm(d.get('Nom_officiel_musee')) not in [m.norm(v) for v in c['names']]:return None
    if m.norm(d.get('Localisation')) not in [m.norm(v) for v in c['locations']]:return None
    if any(d.get(k) for k in ['Lieu_de_depot','MANQUANT','MANQUANT_COM']):return None
    legal=m.norm(d.get('Statut_juridique'))
    if c['mode']=='named_collection':
        if legal not in [m.norm(v) for v in c['accepted_acquisition_labels']]:return None
    elif not legal.startswith(tuple(c['owner_prefixes'])) or not any(legal.endswith(m.norm(v)) for v in c['owners']) or re.search(r'pret|depot|restitu|recuperation|privee|particulier',legal):return None
    return ref(path)

def period_bounds(raw,require_eligible=True):
    """Explicit period union, including post-cutoff bounds for contradiction checks."""
    parts=(raw or '').split(';');out=[]
    if not raw or len(parts)>3 or re.search(r'[?]|\b(?:vers|avant|après|peut-être|probable|supposé)\b',raw,re.I):return None
    for part in parts:
        match=re.fullmatch(r'(?:(1er|1ere|[1-4]e) quart |(1ere|1er|2e) moitie )?(\d{1,2})e siecle',m.norm(part))
        if not match:return None
        first=(int(match[3])-1)*100+1;last=first+99
        if match[1]:first+=(int(match[1][0])-1)*25;last=first+24
        elif match[2]:first+=(int(match[2][0])-1)*50;last=first+49
        out.append((first,last))
    result=(min(v[0] for v in out),max(v[1] for v in out))
    return result if result[0]>=100 and (not require_eligible or result[1]<=1970) else None

def date_facts(row):
    raw=(row.get('Millesime_de_creation') or '').strip();period=row.get('Periode_de_creation') or '';bounds=period_bounds(period,False);qualified=False
    if not raw:
        bounds=period_bounds(period)
        if not bounds:return None,'Unknown, qualified or cutoff-crossing creation period'
        first,last=bounds;precision='century' if last-first==99 and ';' not in period else 'range';display=period
    elif re.fullmatch(r'\d{3,4}',raw):first=last=int(raw);precision='exact';display=raw
    elif match:=re.fullmatch(r'(\d{3,4})\s*[-–]\s*(\d{3,4})',raw):first,last=map(int,match.groups());precision='exact' if first==last else 'range';display=raw
    elif match:=re.fullmatch(r'(\d{3,4})\s+entre\s*,\s*(\d{3,4})\s+et',raw,re.I):first,last=map(int,match.groups());precision='exact' if first==last else 'range';display=raw
    elif match:=re.fullmatch(r'(?:avant\s+(\d{3,4})|(\d{3,4})\s+avant)',raw,re.I):
        first=None;last=int(match[1] or match[2]);precision='before';display=raw
        if not 100<last<=1971 or bounds and bounds[0]>=last:return None,'Before date fails cutoff or conflicts with explicit period'
    elif match:=re.fullmatch(r'(?:vers\s+(\d{3,4})|(\d{3,4})\s*(?:vers|\(vers\)|:\s*vers))',raw,re.I):
        year=int(match[1] or match[2]);bounds=period_bounds(period)
        if not bounds or not bounds[0]<=year<=bounds[1]:return None,'Circa year lacks an independently supplied eligible consistent period'
        first,last=bounds;precision='circa_range';display=raw;qualified=True
    else:return None,'Creation notation requires individual research'
    if first is not None:
        if not 100<=first<=last<=1970:return None,'Creation outside scope or reversed'
        if bounds and not bounds[0]<=first<=last<=bounds[1]:return None,'Creation year/range conflicts with explicit period'
    # A source life-date conflict is an editorial hold, never repaired from another artist.
    for life in re.finditer(r'\((\d{4})\s*-\s*(\d{4}|\?)?\)',row.get('Auteur') or ''):
        born=int(life[1]);died=int(life[2]) if life[2] and life[2]!='?' else None
        if (precision=='before' and born>=last) or (precision!='before' and born>last) or (first is not None and died is not None and died<first):return None,'Source creator lifespan conflicts with creation interval; role/version review needed'
        if qualified and (year<born or died is not None and year>died):return None,'Source circa year conflicts with creator lifespan'
    return dict(first=first,last=last,date_precision=precision,date_display=display),None

def physical_type(d):
    form=m.norm(d.get('Denomination'));domains={m.norm(v).replace(' domaine','') for v in (d.get('Domaine') or '').split(';')};medium=m.norm(d.get('Materiaux_techniques'));description=m.norm(d.get('Description'));derived=[]
    physical=medium+' '+description
    if any(re.search(r'\b'+v+r'\b',form) for v in ['matrice','album','carnet','livre','periodique','fragment','plaque de verre','lettre','manuscrit','ensemble']):return None,'Physical matrix, volume, archive, negative or component requires separate review'
    if re.search(r'\b(?:carnet|album|relie|colle sur une page|extrait de volume|page d un livre)\b',description):return None,'Physically bound or mounted component requires separate unit evidence'
    if domains & {'photographie','bijouterie joaillerie','vetements et accessoires de vetement','mobilier','archeologie'}:return None,'Separate photograph, garment, furnishing or archaeological-object workflow needed'
    if form in ['dessin','dessin double face','aquarelle','pastel'] and domains & {'arts graphiques','dessin','beaux arts'}:
        if re.search(r'collage|assemblage|decoup|photocopie|impression numerique',physical):return None,'Mixed reproduction or assembly requires physical-object review'
        if not re.search(r'encre|crayon|graphite|plume|lavis|gouache|aquarelle|pastel|fusain|sanguine|pierre noire|mine de plomb|stylo|pointe d argent',physical):return None,'Drawing form lacks an explicit drawing or painting technique'
        if not d.get('Mesures'):return None,'Physical drawing lacks dimensions for individual-sheet review'
        derived.append('Drawing type from explicit drawing/pastel/watercolor denomination, graphic-arts domain and physical drawing/painting technique. Source fields remain literal; double-face sheets count once and logical collection/series references require individual unit review.')
        return ('drawing',derived),None
    if form in ['estampe','gravure'] and domains & {'estampe','arts graphiques'}:
        if re.search(r'collage|assemblage|photocopie|impression numerique',physical):return None,'Print assembly or reproduction requires separate review'
        derived.append('Print type from explicit estampe/gravure denomination and matching graphic-arts/print domain. Edition, impression date, physical independence and reproduction chronology remain individual-review requirements.')
        return ('print',derived),None
    if form in ['tableau','peinture'] and 'peinture' in domains:
        if re.search(r'collage|assemblage|neon',physical):return None,'Mixed painting assembly requires individual review'
        return ('painting',['Painting type from explicit painting denomination and domain.']),None
    if 'sculpture' in domains and form in ['sculpture','statue','statuette','buste','figurine','relief','bas relief','haut relief','tete','torse','medaillon sculpture','ronde bosse','groupe','groupe relie']:
        if not d.get('Mesures') or not re.search(r'platre|bronze|pierre|marbre|terre|bois|cire|metal|ceramique|porcelaine',physical):return None,'Sculpture lacks physical medium and dimensions'
        if re.search(r'\b(?:fragment|moule|matrice|empreinte)\b',m.norm(d.get('Titre'))+' '+description):return None,'Sculptural fragment, mold or matrix needs individual-unit research'
        return ('sculpture',['Sculpture type from explicit sculptural domain/form, physical medium and dimensions. Modeling and casting dates remain separate; literal labels preserved.']),None
    return None,'No supported unambiguous physical artwork type'

def screen(row):
    d={k:v or '' for k,v in row.items()}
    if not d['Titre'].strip() or not d['Numero_inventaire'].strip():return None,'Missing title or inventory'
    typ,reason=physical_type(d)
    if reason:return None,reason
    dates,reason=date_facts(d)
    if reason:return None,reason
    context=holding_context(d)
    if not context:return None,'Museum source identity, collection or custody not reconciled'
    facts=dict(dates,title=d['Titre'].strip(),creator_label=d['Auteur'].strip() or None,work_type=typ[0],medium=d['Materiaux_techniques'] or None,dimensions=d['Mesures'] or None,accession=d['Numero_inventaire'].strip(),source_url='https://pop.culture.gouv.fr/notice/joconde/'+d['Reference'],holding_basis='Exact national source code, city, official museum name and named collection destination reconciled to official institution/operator evidence. Literal acquisition and unknown ownership fields retained. Holding only; no legal-title determination, physical-site assignment or current-display claim.')
    return dict(facts=facts,parser='separate_source_date_and_collection_checks',derivations=typ[1]+['Dates parsed separately from collection evidence, without fabricating ownership or modifying parser-only source fields. Literal creation notation retained; broad bounds come only from explicit source periods and before bounds stay exclusive.'],holding_context_reference=context),None

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
    caps={'M1108':150,'M1114':150,'M1113':150,'M1102':150,'M0184':20};selected=[]
    for code,rows in sorted(groups.items()):
        # Prefer specific titles, individual dated objects and a spread of creators.
        creators=collections.defaultdict(list)
        for row in rows:
            d=row['raw_source_record'];creators[d['Auteur']].append(row)
        for rs in creators.values():rs.sort(key=lambda r:(len(r['raw_source_record']['Titre'])<12,not bool(r['raw_source_record']['Mesures']),r['screen']['facts'].get('date_precision')=='before',r['raw_source_record']['Reference']))
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
