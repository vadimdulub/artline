#!/usr/bin/env python3
"""Resolve the remaining Louvre records against scoped WikiArt metadata.

Reuse immutable source evidence; fresh production snapshot; explicit version
review precedes image preparation and guarded production attachment.
"""
import argparse
import collections
import concurrent.futures
import copy
import functools
import gzip
import html
import importlib.util
import json
import re
import threading
from pathlib import Path
from urllib.parse import urlparse,urljoin,quote
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('louvre_delivery',ROOT/'ops/deliver-louvre-wikiart-20261006.py')
d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
r=d.r;q=d.research
OLD=r.RUN
RUN=ROOT/'docs/research/louvre-wikiart-round2-20261006'
CACHE=ROOT/'docs/research/production-wikiart-authoritative-20261006'
r.RUN=RUN;d.RUN=RUN/'delivery';d.OP=RUN.name
d.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/d.OP
d.ORIGINALS=Path.home()/'Library/Application Support/Artline/source-images'/d.OP
r.PORT=55467
URL_LOCKS=collections.defaultdict(threading.Lock)


def capture_once(url,tag):
    with URL_LOCKS[url]:return q.capture(url,tag)


def records():return r.load(RUN/'production-artworks.json.gz')
def remaining():return [x for x in records()if not x['artwork']['primary_media_id']]
def snapshot():q.snapshot()
def mapping():return r.load(RUN/('artist-map-v2.json'if (RUN/'artist-map-v2.json').exists()else'artist-map.json'))['records']
def current_plan():return r.load(Path((RUN/'candidate-pointer.txt').read_text()))if (RUN/'candidate-pointer.txt').exists()else r.load(RUN/'candidate-plan.json')


def delivery_records():
    pointer=d.RUN/'reviewed-records-pointer.txt'
    return r.load(Path(pointer.read_text()))if pointer.exists()else r.load(RUN/'artwork-image-results.json')


d.load_records=delivery_records


TRANSLATE={}
for pairs in ['paysage:landscape paysages:landscape portrait:portrait vue:view vues:view tete:head etude:study etudes:study esquisse:sketch croquis:sketch dessin:drawing dessins:drawing',
 'homme:man hommes:men femme:woman femmes:women jeune:young jeunes:young fille:girl filles:girls garcon:boy enfant:child enfants:children vieillard:old vieille:old vieux:old agee:old',
 'assis:seated assise:seated debout:standing couche:lying couchee:lying nu:nude nue:nude nus:nude',
 'vierge:madonna virgin:madonna madone:madonna jesus:christ christ:christ saint:st sainte:st saints:st saintes:st saint:st famille:family sacree:holy sainte:st',
 'adoration:adoration bergers:shepherds berger:shepherd mages:magi annonciation:annunciation crucifixion:crucifixion croix:cross descente:descent resurrection:resurrection',
 'mort:death mortel:death naissance:birth presentation:presentation temple:temple ange:angel anges:angels musicien:musician musiciens:musicians',
 'jean:john baptiste:baptist jerome:jerome pierre:peter paul:paul etienne:stephen francois:francis marie:mary madeleine:magdalene',
 'jardin:garden jardins:gardens arbre:tree arbres:trees foret:forest bois:wood riviere:river bords:banks bord:bank lac:lake mare:pond mer:sea port:harbour soleil:sun couchant:sunset lever:sunrise',
 'montagne:mountain montagnes:mountains rocher:rock rochers:rocks nuage:cloud nuages:clouds ciel:sky orage:storm tempete:storm cascade:waterfall pont:bridge route:road chemin:road champ:field',
 'italie:italy rome:rome romain:roman romaine:roman naples:naples venise:venice eglise:church cathedrale:cathedral ville:town village:village moulin:mill maison:house maisons:houses',
 'morte:dead nature:still naturemorte:stilllife fleurs:flowers fleur:flower fruits:fruit poissons:fish poisson:fish animaux:animals oiseau:bird oiseaux:birds chien:dog chiens:dogs chat:cat',
 'cheval:horse chevaux:horses cavalier:horseman cavaliers:horsemen vache:cow vaches:cows troupeau:herd mouton:sheep moutons:sheep boeuf:ox lion:lion lions:lions tigre:tiger',
 'roi:king reine:queen prince:prince princesse:princess comte:count comtesse:countess duc:duke duchesse:duchess madame:mrs monsieur:mr pere:father mere:mother soeur:sister frere:brother',
 'peintre:painter artiste:artist atelier:studio autoportrait:selfportrait musique:music lecon:lesson lecture:reading lisant:reading musicienne:musician',
 'deux:two trois:three quatre:four cinq:five six:six sept:seven blanc:white blanche:white noir:black noire:black rouge:red bleu:blue bleue:blue vert:green verte:green',
 'grand:large grande:large petit:small petite:small interieur:interior exterieur:exterior ruines:ruins ruine:ruins chasse:hunt chasseurs:hunters chasseur:hunter repos:rest reposant:rest',
 'venus:venus amour:cupid amours:cupid psyche:psyche diane:diana apollon:apollo minerve:minerva mars:mars hercule:hercules bacchus:bacchus bataille:battle combat:battle fuite:flight egypte:egypt']:
    TRANSLATE.update(x.split(':')for x in pairs.split())


@functools.lru_cache(maxsize=30000)
def concepts(title):
    stop={'le','la','les','de','des','du','d','l','et','un','une','the','of','a','and','dit','aussi','ou','au','aux','dans','en','with','at','in','on','by','sur'}
    return ' '.join(TRANSLATE.get(t,t)for t in q.norm(title).split()if t not in stop)


@functools.lru_cache(maxsize=200)
def evidence_rows(path):
    value=r.load(ROOT/path)
    return value.get('data',[])if isinstance(value,dict)else value


def traits(row):
    for c in row['citations']:
        if c['field_name']!='museum_holding_research':continue
        try:
            note=json.loads(c['evidence_note']);path=note.get('evidence_path')
            if not path:continue
            for x in evidence_rows(path):
                if str(x.get('Reference')or x.get('reference'))==str(c['source_record_id']):
                    return {'source_url':c['source_url'],'reference':c['source_record_id'],'evidence_path':path,'title':x.get('Titre'),
                      'dimensions':x.get('Mesures'),'inventory':x.get('Numero_inventaire'),'medium':x.get('Materiaux_techniques'),
                      'description':{k:v for k,v in x.items()if any(z in k.lower()for z in ['auteur','precision','represent','inscription','description','date','photo'])}}
        except (ValueError,TypeError,KeyError):continue
    return None


def artist_map():
    directory=r.load(CACHE/'wikiart-directory.json.gz');byname=collections.defaultdict(dict)
    for x in directory:byname[q.namekey(x['name'])][x['url']]=x
    stop={'de','van','der','le','la','von','di','da','du','d'}
    directory_tokens=[(x,set(q.namekey(x['name']).split())-stop)for x in directory]
    previous={x['artwork_id']:x for x in r.load(OLD/'artwork-image-results.json')}
    previous_plan=r.load(OLD/'artist-search-plan-v2.json');urlmap={x['artwork_id']:x for x in previous_plan['records']}
    links=[];ambiguous=[]
    for row in remaining():
        w=row['artwork'];names=[]
        for a in row['artists']:names.extend([a['name']]+(a.get('aliases')or[]))
        if w.get('unlinked_creator_label'):names.append(w['unlinked_creator_label'])
        old=previous.get(w['id'],{});names+=old.get('creator_labels',[])
        names+=[x['creatorName']for x in old.get('label_evidence',[])if x.get('creatorName')]
        matches={}
        for name in names:matches.update(byname[q.namekey(name)])
        basis='Exact full creator name, supplied alias or object-linked creator authority'
        if not matches:
            for url in urlmap.get(w['id'],{}).get('artist_urls',[]):
                x=next((a for a in directory if a['url']==url),None)
                if x:matches[url]=x
            basis='Previously scoped creator variant; explicit review required'
        if not matches:
            for name in names:
                a=set(q.namekey(name).split())-stop
                if len(a)<2:continue
                for x,b in directory_tokens:
                    if len(b)>=2 and (a<=b or b<=a) and len(a&b)/max(len(a),len(b))>=.5:matches[x['url']]=x
            basis='Unique creator name variant; explicit review required'
        item={'artwork_id':w['id'],'title':w['title'],'names':list(dict.fromkeys(names)),'sources':list(matches.values()),'basis':basis,
          'title_variants':old.get('sourced_title_variants',[w['title']]),'label_evidence':old.get('label_evidence',[]),'primary_object':traits(row)}
        links.append(item)
        if len(matches)!=1:ambiguous.append(item)
    r.save(RUN/'artist-map.json',{'records':links,'directory_evidence':str((CACHE/'wikiart-directory.json.gz').relative_to(ROOT))})
    print(json.dumps({'remaining':len(links),'unique_artist_match':sum(len(x['sources'])==1 for x in links),'no_artist_match':sum(not x['sources']for x in links),'ambiguous_artist_match':sum(len(x['sources'])>1 for x in links),'unique_artist_urls':len({s['url']for x in links for s in x['sources']})}),flush=True)


def discover_artists():
    rows=r.load(RUN/'artist-map.json')['records'];groups={}
    for row in rows:
        if row['sources']:continue
        labels=[x['creatorName']for x in row['label_evidence']if x.get('creatorName')]+row['names']
        labels=list(dict.fromkeys(labels));slugs=[]
        for name in labels:
            slug=q.norm(re.sub(r'\([^)]*\)','',name)).replace(' ','-')
            if slug and slug not in slugs:slugs.append(slug)
        # The first object-linked authority name is usually canonical. A second
        # supplied spelling is checked only if the first route is absent.
        key=tuple(slugs[:2]);groups.setdefault(key,{'names':set(),'records':[]})['names'].update(labels);groups[key]['records'].append(row['artwork_id'])
    def one(pair):
        slugs,group=pair;key=r.sha('|'.join(slugs).encode());dest=RUN/'creator-discovery'/(key+'.json')
        if dest.exists():return r.load(dest)
        attempts=[];matches=[]
        for slug in slugs:
            url='https://www.wikiart.org/en/'+slug;raw,rc=capture_once(url+'/all-works/text-list','creator-discovery-captures')
            soup=BeautifulSoup(raw,'html.parser');title=soup.title.get_text(' ',strip=True).split(' - ')[0]if soup.title else''
            items=[{'title':a.get_text(' ',strip=True),'url':urljoin(url,a['href']),'text':a.parent.get_text(' ',strip=True)}for a in soup.select('li a[href]')if a['href'].startswith('/en/'+slug+'/')and not a['href'].endswith('/all-works/text-list')]
            attempt={'url':url,'receipt':rc,'page_artist_name':title,'works':len(items)};attempts.append(attempt)
            if rc['status']==200 and items and q.namekey(title)in{q.namekey(n)for n in group['names']}:
                source={'name':title,'url':url,'receipt':rc,'discovery':'Artist page absent from alphabetical directory; observed page name exactly matches catalogue authority'}
                matches.append(source);r.save(RUN/'text-indexes'/(slug+'.json'),{'artist_url':url,'receipt':rc,'items':items});break
        result={'names':sorted(group['names']),'artwork_ids':group['records'],'attempts':attempts,'sources':matches};r.save(dest,result);return result
    sources={};counts=collections.Counter()
    print('Additional creator authorities to check',len(groups),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5)as pool:
        for n,x in enumerate(pool.map(one,groups.items()),1):
            counts['found'if x['sources']else'not_found']+=1
            for aid in x['artwork_ids']:sources[aid]=x['sources']
            if n%40==0:print('Creator page discovery',n,'of',len(groups),dict(counts),flush=True)
    for row in rows:
        if sources.get(row['artwork_id']):row['sources']=sources[row['artwork_id']];row['basis']='Exact creator authority and live WikiArt artist page; absent from directory'
    r.save(RUN/'artist-map-v2.json',{'records':rows,'creator_discovery_counts':dict(counts)})
    print('Expanded artist coverage',sum(bool(x['sources'])for x in rows),'of',len(rows),flush=True)


def indexes():
    sources={x['url']:x for row in mapping()for x in row['sources']}
    def one(pair):
        url,lang=pair;slug=url.rsplit('/',1)[-1];dest=RUN/'indexes'/(lang+'-'+slug+'.json')
        if dest.exists():return r.load(dest)
        cached=CACHE/('artist-indexes'if lang=='en'else'translated-indexes')/((slug if lang=='en'else lang+'-'+slug)+'.json.gz')
        if cached.exists():
            value=r.load(cached);value['cached_evidence']=str(cached.relative_to(ROOT))
        else:
            api='https://www.wikiart.org/'+lang+'/App/Painting/PaintingsByArtist?artistUrl='+slug+'&json=2'
            raw,rc=q.capture(api,'index-captures');items=json.loads(raw)if rc['status']==200 else[]
            value={'source':sources[url],'language':lang,'api_url':api,'receipt':rc,'outcome':'indexed'if isinstance(items,list)and rc['status']==200 else'unavailable','items':items if isinstance(items,list)else[]}
        r.save(dest,value);return value
    pairs=[(u,lang)for u in sources for lang in ['en','fr']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for n,x in enumerate(pool.map(one,pairs),1):
            if n%50==0:print('Scoped source indexes',n,'of',len(pairs),flush=True)
    print('Source indexes complete',len(pairs),flush=True)


def text_indexes():
    sources={x['url']:x for row in mapping()for x in row['sources']}
    def one(url):
        dest=RUN/'text-indexes'/(url.rsplit('/',1)[-1]+'.json')
        if dest.exists():return r.load(dest)
        raw,rc=q.capture(url+'/all-works/text-list','text-index-captures');soup=BeautifulSoup(raw,'html.parser')
        prefix=urlparse(url).path+'/'
        items=[]
        for a in soup.select('li a[href]'):
            if a['href'].startswith(prefix):items.append({'title':a.get_text(' ',strip=True),'url':urljoin(url,a['href']),'text':a.parent.get_text(' ',strip=True)})
        value={'artist_url':url,'receipt':rc,'items':items};r.save(dest,value);return value
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for n,x in enumerate(pool.map(one,sorted(sources)),1):
            if n%50==0:print('Source page links',n,'of',len(sources),flush=True)


def candidate_plan():
    old={x['artwork_id']:x for x in r.load(OLD/'artwork-image-results.json')}
    indexes=collections.defaultdict(dict);links={}
    for p in (RUN/'text-indexes').glob('*.json'):
        x=r.load(p);links[x['artist_url']]=x
    for p in (RUN/'indexes').glob('*.json'):
        x=r.load(p);url=x['source']['url']
        for im in x.get('items',[]):
            entry=indexes[url].setdefault(im['contentId'],{'content_id':im['contentId'],'titles':[],'image_url':im.get('image'),'source_date':im.get('yearAsString'),'artist_url':url,'artist_name':im.get('artistName'),'evidence':[]})
            if im.get('title')and im['title']not in entry['titles']:entry['titles'].append(im['title'])
            entry['evidence'].append(str(p.relative_to(ROOT)))
    plan=[]
    for row in mapping():
        choices=[]
        for source in row['sources']:
            url=source['url'];seen=set()
            for im in indexes[url].values():
                if not im['titles']:continue
                raw_score=max(q.similarity(a,b)for a in row['title_variants']for b in im['titles'])
                translated_score=max(q.similarity(concepts(a),concepts(b))for a in row['title_variants']for b in im['titles'])
                score=max(raw_score,translated_score)
                if score<.63:continue
                urls=[z['url']for z in links.get(url,{}).get('items',[])if q.norm(z['title'])in{q.norm(t)for t in im['titles']}]
                if not urls:continue
                for page in urls:
                    if page in seen:continue
                    seen.add(page);choices.append({**im,'url':page,'title_score':round(score,4),'raw_title_score':round(raw_score,4),'concept_score':round(translated_score,4),'discovery':'Bilingual artist index and observed artwork page link; translation tokens are discovery hints only'})
        choices.sort(key=lambda x:-x['title_score'])
        for c in old.get(row['artwork_id'],{}).get('candidates',[]):
            if c['url']not in {x['url']for x in choices}:choices.append({'url':c['url'],'title_score':c.get('page_title_score',0),'discovery':'Prior verified candidate page','old_candidate':c})
        plan.append({**row,'candidates':choices[:12],'candidate_count':len(choices)})
    path=RUN/'candidate-plans'/(r.sha(d.core.encode(plan))+'.json');r.save(path,plan)
    (RUN/'candidate-pointer.txt').write_text(str(path))
    print(json.dumps({'records':len(plan),'with_candidates':sum(bool(x['candidates'])for x in plan),'unique_pages':len({c['url']for x in plan for c in x['candidates']})}),flush=True)


def pages():
    urls=sorted({c['url']for x in current_plan()for c in x['candidates']})
    def one(url):
        old=OLD/'artwork-pages'/(r.sha(url.encode())+'.json');dest=RUN/'artwork-pages'/old.name
        if old.exists()and not dest.exists():r.save(dest,r.load(old))
        return q.page(url)
    counts=collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5)as pool:
        for n,x in enumerate(pool.map(one,urls),1):
            counts[x['outcome']]+=1
            if n%30==0:print('Artwork pages',n,'of',len(urls),dict(counts),flush=True)
    print('Artwork page research',dict(counts),flush=True)


def dimensions(value):
    if not value:return None
    nums=re.findall(r'\d+(?:[.,]\d+)?',value)
    if len(nums)!=2:return None
    return sorted(float(x.replace(',','.'))for x in nums)


def evaluate():
    snapshot={x['artwork']['id']:x for x in records()};out=[];pending=0
    for item in current_plan():
        aid=item['artwork_id'];row=snapshot[aid];w=row['artwork'];found={}
        for c in item['candidates']:
            path=RUN/'artwork-pages'/(r.sha(c['url'].encode())+'.json')
            if not path.exists():pending+=1;continue
            page=r.load(path)
            if page['outcome']!='image_found':continue
            meta=page['metadata'];sid=meta['_id'];info=page['object_info']
            titles=[meta['title']]+[x.split(':',1)[1].strip()for x in info if x.startswith(('Original Title:','Titre original:'))]
            score=max(q.similarity(a,b)for a in item['title_variants']for b in titles)
            concept_score=max(q.similarity(concepts(a),concepts(b))for a in item['title_variants']for b in titles)
            loc=next((x.split(':',1)[1].strip()for x in info if x.startswith(('Location:','Lieu:'))),None)
            sd=next((x.split(':',1)[1].strip()for x in info if x.startswith('Dimensions:')),None)
            primary=item.get('primary_object')or{};pd=primary.get('dimensions');a,b=dimensions(sd),dimensions(pd)
            dim='unavailable'
            if a and b:dim='agree'if all(abs(x-y)<=max(2,.06*max(x,y))for x,y in zip(a,b))else'differ'
            candidate={'url':page['url'],'source_id':sid,'source_title':html.unescape(meta['title']),'source_artist':html.unescape(meta.get('artistName')or''),
              'source_date':meta.get('year'),'source_location':loc,'source_public_domain_label':page['public_domain_label'],'source_rights_label':page['rights_label'],
              'image_url':page['image_url'],'image_width':meta.get('width'),'image_height':meta.get('height'),'page_evidence':str(path.relative_to(ROOT)),
              'page_title_score':round(score,4),'concept_score':round(concept_score,4),'source_dimensions':sd,'catalogue_dimensions':pd,'dimension_result':dim,
              'basis':c.get('old_candidate',{}).get('basis','round2_bilingual_title_discovery'),'review_flags':[],
              'primary_object':primary,'discovery_evidence':c.get('evidence')or c.get('old_candidate',{}).get('discovery_evidence')}
            if any(a.get('role')not in ('primary',None)for a in row['artists']):candidate['review_flags'].append('Qualified catalogue creator attribution needs review')
            safety=d.safety_reason(row,candidate)
            date=d.valid_date(row,candidate)
            candidate.update(safety_hold=safety,dates=date,displayed_source_date=d.source_date(candidate))
            if loc and 'louvre'not in loc.lower():candidate['review_flags'].append('Source location differs')
            if dim=='differ':candidate['review_flags'].append('Different dimensions: version review required')
            if sid not in found or (score,dim=='agree')>(found[sid]['page_title_score'],found[sid]['dimension_result']=='agree'):found[sid]=candidate
        ranked=sorted(found.values(),key=lambda c:(bool(c['safety_hold']),c['dimension_result']=='differ',-int(c['dimension_result']=='agree'),-c['page_title_score'],-c['concept_score']))
        out.append({**item,'candidates':ranked,'existing_image':False,'outcome':'round2_candidates'if ranked else'no_source_candidate','creator_labels':item['names'],'artist_match_basis':'established_artist_or_exact_name','catalogue_status':w['status'],'catalogue_date_start':w['creation_year_start'],'catalogue_date_end':w['creation_year_end']})
    path=RUN/'review-passes'/(r.sha(d.core.encode(out))+'.json');r.save(path,out)
    (RUN/'review-pointer.txt').write_text(str(path))
    stats={'records':len(out),'records_with_candidate':sum(bool(x['candidates'])for x in out),'source_pages_pending':pending,
      'any_dimensions_agree':sum(any(c['dimension_result']=='agree'and not c['safety_hold']for c in x['candidates'])for x in out),
      'any_title_exact':sum(any(c['page_title_score']>=.97 and not c['safety_hold']for c in x['candidates'])for x in out)}
    print(json.dumps(stats),flush=True)


def review_list():
    xs=r.load(Path((RUN/'review-pointer.txt').read_text()));n=0
    for x in xs:
        options=[c for c in x['candidates']if not c['safety_hold']and(c['dimension_result']=='agree'or c['page_title_score']>=.8 or c['concept_score']>=.9)]
        if not options:continue
        n+=1;print(f"{n:03d} {x['artwork_id']} | {x['names'][0]if x['names']else'?'} | {x['title']}",flush=True)
        for c in options[:3]:print(f"  {c['source_id']} | {c['source_title']} | {c['displayed_source_date']} | {c['source_location']} | DIM {c['dimension_result']} {c['catalogue_dimensions']} / {c['source_dimensions']} | {c['page_title_score']},{c['concept_score']}",flush=True)


def finalize():
    """Only explicit pinned human-reviewed identities enter the delivery adapter."""
    approved={};holds={}
    for p in sorted((RUN/'manual-decisions').glob('*.json')):approved.update(r.load(p))
    for p in sorted((RUN/'manual-holds').glob('*.json')):holds.update(r.load(p))
    approved={aid:x for aid,x in approved.items()if holds.get(aid,{}).get('source_id')!=x['source_id']}
    reviewed={x['artwork_id']:x for x in r.load(Path((RUN/'review-pointer.txt').read_text()))}
    selected=[]
    for aid,decision in approved.items():
        if holds.get(aid,{}).get('source_id')==decision['source_id']:
            raise AssertionError('Explicit source hold conflicts with approval: '+aid)
        row=copy.deepcopy(reviewed[aid]);matches=[c for c in row['candidates']if c['source_id']==decision['source_id']]
        assert len(matches)==1,(aid,'Pinned reviewed candidate missing')
        assert not matches[0]['safety_hold'],(aid,matches[0]['safety_hold'])
        row['candidates']=matches;selected.append(row)
    r.save(RUN/'artwork-image-results.json',selected)
    r.save(d.RUN/'manual-review.json',approved)
    d.select()
    assert len(d.selection()['selected'])==len(approved)


def report():
    verified=r.load(d.RUN/'verification.json');plan=d.load_plan();attached={x['artwork_id']for x in plan['selected']}
    reviewed=r.load(Path((RUN/'review-pointer.txt').read_text()));holds={}
    page_count=len({c['url']for x in current_plan()for c in x['candidates']})
    for p in sorted((RUN/'manual-holds').glob('*.json')):holds.update(r.load(p))
    outcomes=[];counts=collections.Counter()
    for row in reviewed:
        aid=row['artwork_id'];candidates=row['candidates']
        if aid in attached:status='Image attached and production verified'
        elif aid in holds:status='Candidate rejected or held after object, version or image-quality review'
        elif not row['sources']:status='No verified WikiArt creator page found in checked directory and name variants'
        elif not candidates:status='No candidate found in checked artist works and title variants'
        elif all(c['safety_hold']for c in candidates):status='Candidates held for date, rights, creator or component checks'
        else:status='Candidate identity or version remains unverified'
        counts[status]+=1
        outcomes.append({'artwork_id':aid,'title':row['title'],'creator_names':row['names'],'status':status,
          'primary_object':row['primary_object'],'creator_sources':row['sources'],'candidate_urls':[c['url']for c in candidates],
          'specific_review':holds.get(aid),'evidence_review':(RUN/'review-pointer.txt').read_text()})
    assert len(outcomes)==2811 and counts['Image attached and production verified']==verified['artworks_updated']
    r.save(RUN/'record-outcomes.json',outcomes)
    def cell(value):return str(value).replace('|','\\|').replace('\n',' ')
    lines=['# Louvre WikiArt reconciliation — second pass, 6 October 2026','',
      f"Verified production result: **{verified['artworks_updated']} additional records illustrated**, bringing Louvre coverage to **{verified['louvre_totals']['with_images']} / {verified['louvre_totals']['artworks']}**. **{verified['remaining_without_images']} records still have no verified usable image.**",'',
      'WikiArt remains the user-selected source of truth for securely identified works. Louvre inventory photographs were used solely to establish object identity; all attached images come from WikiArt. No records were published, deleted or assigned invented metadata. Existing images, creators and holdings were preserved.','',
      f"Checked 2,811 unresolved records against 321 scoped artist pages and English/French work indexes. Direct creator checks found 143 artist-page groups absent from the directory. Reviewed {page_count:,} candidate artwork pages. Title matching and translated search terms were discovery hints, never proof of object identity.",'',
      f"All {verified['public_images_verified']} new public image URLs passed HTTP, checksum and size checks; {verified['audited_records']} database changes have verified audit history; {verified['live_api_records_verified']} live API records were sampled. Images retain the supplied frame and use proportional JPEG compression, at most {verified['largest_image_bytes']:,} bytes. All changed records remain in review.",'',
      f"{verified['date_metadata_updated']} records received WikiArt date-label/precision/range updates; {verified['year_bounds_updated']} changed numeric year bounds, including {verified['previously_unknown_years_filled']} previously unknown dates. Previous values and source captures are preserved.",'',
      '## Every starting record accounted for','','| Outcome | Records |','| --- | ---: |']
    lines += [f'| {status} | {count:,} |'for status,count in counts.items()]
    lines += ['', 'These are results from the checked sources, not proof that an artwork is absent from all of WikiArt. A record with a rejected candidate may still have another undiscovered reproduction.','',
      '## Evidence','', '[Attached records and source/image links](delivery/report.html) · [Production verification](delivery/verification.json) · [All 2,811 record outcomes](record-outcomes.json) · [First delivery](../louvre-wikiart-20261006/README.md)','',
      f"Production backup: `{verified['backup_directory']}`. Plan SHA-256: `{verified['plan_sha256']}`.",'',
      '## Records still requiring a verified image','','| Record | Artwork | Creator | Outcome |','| --- | --- | --- | --- |']
    lines += [f"| `{x['artwork_id']}` | {cell(x['title'])} | {cell(x['creator_names'][0]if x['creator_names']else'Unresolved')} | {x['status']} |"for x in outcomes if x['artwork_id']not in attached]
    r.save(RUN/'README.md',('\n'.join(lines)+'\n').encode())
    print(json.dumps({'verified':verified,'outcomes':dict(counts)},ensure_ascii=False),flush=True)


if __name__=='__main__':
    own=['snapshot','artist_map','discover_artists','indexes','text_indexes','candidate_plan','pages','evaluate','review_list','finalize','report']
    delivery=['select','prepare','sheets','plan','upload','apply','verify_assets','verify']
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=own+delivery);a=p.parse_args()
    (globals()[a.command]if a.command in own else getattr(d,a.command))()
