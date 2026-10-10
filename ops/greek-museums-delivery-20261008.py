#!/usr/bin/env python3
"""Guarded, selected Greek museum catalogue and authentic image delivery."""
import argparse, base64, collections, concurrent.futures, datetime, gzip, hashlib, importlib.util, io, json, re, subprocess, time, uuid
from pathlib import Path
from urllib.parse import quote, urlparse, urljoin, parse_qs
import requests
from PIL import Image, ImageOps, ImageDraw
from psycopg.types.json import Jsonb
from psycopg import sql

spec=importlib.util.spec_from_file_location('research',Path(__file__).with_name('greek-museums-20261008.py'))
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
m=g.m
ROOT,RUN,BACKUP,ORIGINALS=g.ROOT,g.RUN,g.BACKUP,g.ORIGINALS
save,load,sha,uid,norm,now,connect=g.save,g.load,g.sha,g.uid,g.norm,g.now,g.connect
ACTOR='local-european-research'
FACTS='combined-facts-v3.json'
PLAN='delivery-plan-v4.json.gz'
APPLIED='catalogue-applied.json'
AFTER='catalogue-transaction-after.json.gz'


def untag(v): return re.sub(r'\s*\((?:EL|EN|FR|DE)\)\s*$','',v or '').strip()
def preferred(values):
    return untag(next((v for v in values or [] if v.endswith('(EN)')),next(iter(values or []),''))) or None
def date(value):
    result=dict(first=None,last=None,precision='unknown',date_display=value or 'Creation date unknown')
    if not value: return result
    t=untag(value).strip().replace('–','-').replace('—','-')
    if re.search(r'T\d\d:\d\d|digit|retriev|modified',t,re.I): return dict(result,date_display='Creation date unknown')
    calendar=re.fullmatch(r'\d{1,2}[/.]\d{1,2}[/.](\d{4})',t)
    if calendar:return dict(result,first=int(calendar[1]),last=int(calendar[1]),precision='exact')
    signed=re.fullmatch(r'(-\d{1,4})/(-?\d{1,4})',t)
    if signed and int(signed[1])<=int(signed[2]):return dict(result,first=int(signed[1]),last=int(signed[2]),precision='range')
    compact=re.fullmatch(r'(\d{4})-(\d{2})',t)
    if compact and int(compact[2])>=int(compact[1][-2:]):return dict(result,first=int(compact[1]),last=int(compact[1][:2]+compact[2]),precision='range')
    if t=='[First half of the 20th century] [Create]':return dict(result,first=1901,last=1950,precision='range')
    t=t.strip('[]')
    greek_century=re.fullmatch(r'(?:(?:Μέσα|Αρχές|Τέλη|αρχές|τέλη|μέσα)\s+)?(\d{1,2})(?:ος|ου)(?:\s+αι(?:ώνας|ώνα|\.)?)?',t)
    if greek_century:
        c=int(greek_century[1]);result.update(first=(c-1)*100+1,last=c*100,precision='century');return result
    t=re.sub(r'B\.?\s*C\.?\s*E?\.?','BCE',t,flags=re.I)
    t=re.sub(r'A\.?\s*D\.?|C\.?\s*E\.?','CE',t,flags=re.I) if 'BCE' not in t else t
    circa=bool(re.match(r'^(?:c\.|ca\.|circa|περ\.?|around)\s*',t,re.I))
    t=re.sub(r'^(?:c\.|ca\.|circa|περ\.?|around)\s*','',t,flags=re.I)
    single=re.fullmatch(r'(\d{1,4})\s*(BCE|CE)?',t,re.I)
    span=re.fullmatch(r'(\d{1,4})\s*(BCE|CE)?\s*[-/]\s*(\d{1,4})\s*(BCE|CE)?',t,re.I)
    century=re.fullmatch(r'(?:(early|late|mid|beginning of|end of)\s+)?(\d{1,2})(?:st|nd|rd|th)(?:\s*-\s*(\d{1,2})(?:st|nd|rd|th))?\s*(?:century|cent\.?|c\.)\s*(BCE|CE)?',t,re.I)
    if single:
        yr=int(single[1])*(-1 if (single[2]or'').upper()=='BCE'else 1)
        if yr: result.update(first=yr,last=yr,precision='circa'if circa else'exact')
    elif span:
        era1=(span[2]or span[4]or'').upper();era2=(span[4]or'').upper()
        a=int(span[1])*(-1 if era1=='BCE'else 1);b=int(span[3])*(-1 if era2=='BCE'else 1)
        if a and b and a<=b:result.update(first=a,last=b,precision='circa_range'if circa else'range')
    elif century:
        c1=int(century[2]);c2=int(century[3]or c1);bce=(century[4]or'').upper()=='BCE'
        a,b=(-c1*100,-(c2-1)*100-1)if bce else((c1-1)*100+1,c2*100)
        if a<=b:result.update(first=a,last=b,precision='range'if c1!=c2 else'century')
    return result


SC_MUSEUMS={
 'AMusChania':('Archaeological Museum of Chania','Chania'),
 'AveroffMuseum':('Averoff Museum of Neohellenic Art','Metsovo'),
 'Delphi_Museum':('Archaeological Museum of Delphi','Delphi'),
 'DigAEDIK':('Corinth Canal Industrial Museum','Isthmia'),
 'DigASFA':('Athens School of Fine Arts Gallery','Athens'),
 'DigAthensMuseum':('Athens City Museum – Vouros-Eutaxias Foundation','Athens'),
 'DigFaltaits':('Manos and Anastasia Faltaits Museum','Skyros'),
 'DigIakovateios':('Iakovateios Library and Museum','Lixouri'),
 'DigJewish':('Jewish Museum of Greece','Athens'),
 'jewishmuseum':('Jewish Museum of Greece','Athens'),
 'DigKazantzakis':('Nikos Kazantzakis Museum','Myrtia'),
 'DigMacedStruggle':('Museum of the Macedonian Struggle','Thessaloniki'),
 'DigNikaia_1821':('Municipal Gallery of Nikaia – Dinos Katsafanas','Nikaia'),
 'DigOlympicMuseum':('Thessaloniki Olympic Museum','Thessaloniki'),
 'Olympic_Museum':('Thessaloniki Olympic Museum','Thessaloniki'),
 'DigVarnava':('European Bread Museum','Varnavas'),
 'DigWAR':('War Museum, Athens','Athens'),
 'EIM':('National Historical Museum','Athens'),
 'Efa_Kilkis_col':('Archaeological Museum of Kilkis','Kilkis'),
 'Frissiras':('Frissiras Museum','Athens'),
 'LEMMTH':('Folklife and Ethnological Museum of Macedonia-Thrace','Thessaloniki'),
 'Mar_Spathareio':('Spathario Shadow Theatre Museum','Marousi'),
 'National_Gallery':('National Gallery – Alexandros Soutsos Museum','Athens'),
 'PLI':('V. Papantoniou Peloponnesian Folklore Foundation Museum','Nafplio'),
 'TehnisRodou':('Municipal Art Gallery of Rhodes','Rhodes'),
 'TositsasFoundation':('Metsovo Folk Art Museum – Tossizza Mansion','Metsovo'),
 'ZoggopoulosF':('George Zongolopoulos Foundation','Psychiko'),
 'benaki_collections':('Benaki Museum','Athens'),
 'larisa_gallery':('Municipal Art Gallery of Larissa – G. I. Katsigras Museum','Larissa'),
 'pinakothiki_agrinio':('Municipal Art Gallery of Agrinio','Agrinio'),
 'theocharakis':('B. & M. Theocharakis Foundation','Athens'),
}


def sc_kind(index):
    types=set((index['fields'].get('Item type')or'').split(', '))
    for labels,kind in [({'Painting','Icon'},'painting'),({'Murals'},'fresco'),({'Engraving','Print','Lithography'},'print'),
        ({'Sketch','Drawing'},'drawing'),({'Watercolour'},'watercolor'),({'Sculpture','Relief','Figurine'},'sculpture'),
        ({'Textile','Needlework'},'textile'),({'Photo'},'photograph'),({'Medal'},'metalwork'),({'Ceramic ware'},'ceramic')]:
        if types & labels:return kind
    return 'unknown'


def facts():
    na=load(RUN/'nationalarchive-object-facts.json');records=na['records'];held=list(na['held']);museums={x['key']:x for x in na['museums']}
    for path in [RUN/'searchculture-object-facts.json',RUN/'searchculture-ordered-object-facts.json']:
        for x in load(path)['records']:
            key=x['collection'];fs=x['fields'];index=x['index'];url=index['source_url'].split('?')[0]
            if key=='momus':
                sub=preferred(fs.get('Subcollections'))
                if sub not in ['Museum of Contemporary Art','Museum of Modern Art']:
                    held.append(dict(url=url,reason='momus_branch_identity',fields=fs));continue
                name='MOMus – '+sub;city='Thessaloniki'
            elif key in SC_MUSEUMS:name,city=SC_MUSEUMS[key]
            else:held.append(dict(url=url,reason='institution_identity_review'));continue
            museum_key='sc-'+norm(name).replace(' ','-')
            if museum_key not in museums:
                col=load(RUN/'collections'/(key+'.json'))
                # Collection synopsis belongs to this exact provider, not a display claim.
                museums[museum_key]=dict(key=museum_key,name=name,city=city,source_url=col['receipt']['url'],
                    receipt=col['receipt'],collection_keys=[key],source_context=col['text'].split(' Search More search options')[0])
            elif key not in museums[museum_key]['collection_keys']:museums[museum_key]['collection_keys'].append(key)
            d=date(preferred(fs.get('Created')) or preferred(fs.get('Date')))
            if d['last'] is not None and d['last']>1970:
                held.append(dict(url=url,reason='source_creation_after_or_crossing_cutoff',date=d));continue
            title=preferred(fs.get('Title')) or index['title'];original_title=title
            if key=='AveroffMuseum':
                matched=re.search(r'[“"]([^”"]+)[”"]',title)
                if matched:title=matched[1]
            creator_values=fs.get('Creator')or[]
            creator=untag(creator_values[0]) if creator_values else None
            # Cataloguer "orphan" is an absence of attribution, never an artist.
            if norm(creator)in ['ορφανο','orphan','unknown','αγνωστος δημιουργος']:creator=None
            body=' '.join(fs.get('Description')or[])
            if key=='Delphi_Museum' and 'Photo' in index['fields'].get('Item type',''):
                held.append(dict(url=url,reason='modern_site_photo_dates_the_subject'));continue
            if key=='momus' and title=='Phobia':
                held.append(dict(url=url,reason='portfolio_versus_individual_print_identity'));continue
            if not x['original_urls'] or len(set(x['original_urls']))!=1:
                held.append(dict(url=url,reason='native_object_identity_unavailable'));continue
            source_id=url.split('/aggregator/edm/',1)[1]
            kinds=sc_kind(index)
            records.append(dict(source='searchculture',scheme='searchculture-edm',source_id=source_id,source_url=url,
                native_url=x['original_urls'][0],receipt=x['receipt'],museum_key=museum_key,title=title,alternate_title=None,
                creator_label=creator,creator_values=creator_values,**d,work_type=kinds,
                medium=preferred(fs.get('Medium')),dimensions=preferred(fs.get('Extent')),accession=preferred(fs.get('Identifier')),
                raw=x,original_title=original_title,holding_confidence=0.95,
                holding_basis='Museum-supplied object metadata in the National Documentation Centre SearchCulture collection; exact provider collection and original object link retained. Collection identity checked against the collection synopsis. No current-display assertion.'))
    keys=[(r['scheme'],r['source_id']) for r in records];assert len(set(keys))==len(keys)
    value=dict(at=now(),records=records,held=held,museums=list(museums.values()))
    save(RUN/'combined-facts.json',value)
    print('Facts',len(records),'objects;',len(museums),'museums;',len(held),'holds',flush=True)


NA_CITIES={
 'National Archaeological Museum':'Athens','Numismatic Museum':'Athens','Byzantine and Christian Museum':'Athens',
 'Museum of Byzantine Culture':'Thessaloniki','Palace of the Grand Master of Knights':'Rhodes',
 'Archaeological Museum of Rhodes':'Rhodes','Archaeological Museum of Thessaloniki':'Thessaloniki',
 'Archaeological Museum of Ioannina':'Ioannina','Archaeological Museum of Igoumenitsa':'Igoumenitsa',
 'Archaeological Museum of Mykonos':'Mykonos','Archaeological Museum of Arta':'Arta',
 'Archaeological Museum of Milos':'Milos','Archaeological Museum of Alexandroupolis':'Alexandroupolis',
 'Archaeological Museum of Nikopolis':'Nikopolis','Archaeological Museum of Sifnos':'Sifnos',
 'Archaeological Museum of Naxos':'Naxos','Archaeological Museum of Kimolos':'Kimolos',
 'Archaeological Museum of Kea':'Kea','Archaeological Museum of Drama':'Drama','Archaeological Museum of Heraklion':'Heraklion',
 'Archaeological Museum of Kastoria at Argos Orestiko':'Argos Orestiko','Archaeological Museum of Aiani, Kozani':'Aiani',
 'Byzantine Museum of Kastoria':'Kastoria','Archaeological Museum of Avdira':'Avdira',
 'Archaeological Collection of Serifos':'Serifos','Archaeological Collection of Kozani':'Kozani',
 'Archaeological Museum of Pyrgos':'Pyrgos','Collection of Icons and Relics of Pyrgos, Thira':'Pyrgos, Thira',
 'Museum of Chlemoutsi Castle':'Chlemoutsi','Archaeological Museum of Kavala':'Kavala',
 'Archaeological Museum of Messinia':'Kalamata','Archaeological Collection of Apeiranthos':'Apeiranthos',
 'Archaeological Museum of Neapolis Voion':'Neapoli Voion','Archaeological Museum of Sparti':'Sparta',
 'Μουσείο Νεώτερου Ελληνικού Πολιτισμού':'Athens',
 'Ιστορικό και Εθνολογικό Μουσείο των Ελλήνων της Καππαδοκίας':'Nea Karvali',
 'Εκκλησιαστικό Μουσείο Αγίου Γεωργίου, Δρυοπίδα, Κύθνος':'Driopida, Kythnos',
 'Εκκλησιαστικό Μουσείο Μάρπησσας Πάρου':'Marpissa, Paros',
 'Μουσείο Αγροτικής και Πολιτιστικής Κληρονομιάς Ιάσμου':'Iasmos',
 'Εκκλησιαστικό Μουσείο Ιεράς Μητροπόλεως Παροναξίας Νάξου':'Naxos',
 'Εκκλησιαστικό Μουσείο Εκατονταπυλιανής Παροικιάς Πάρου':'Parikia, Paros',
 'Συλλογή Ναού Ταξιάρχη Σαγκρίου Νάξου':'Sagri, Naxos',
 'Εκκλησιαστική Συλλογή Νάουσας, Πάρος':'Naousa, Paros',
 'Εκκλησιαστικό Μουσείο Χαλκείου, Νάξος':'Chalki, Naxos',
}


def accession_key(value):
    return re.sub(r'[^\w]','',norm(value)).replace('βχμ','bxm').lstrip('0')


def full_rows(db,ids):
    rows=[]
    for offset in range(0,len(ids),250):
        rows+=db.execute("""SELECT to_jsonb(a) artwork,
          coalesce((SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations,
          coalesce((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers,
          coalesce((SELECT jsonb_agg(to_jsonb(l)) FROM artwork_location_assertions l WHERE l.artwork_id=a.id),'[]') locations,
          coalesce((SELECT jsonb_agg(to_jsonb(ar)||jsonb_build_object('attribution_role',aa.attribution_role)) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists
          FROM artworks a WHERE a.id=ANY(%s::uuid[]) ORDER BY a.id""",(ids[offset:offset+250],)).fetchall()
    return rows


def plan():
    allfacts=load(RUN/FACTS);selected=allfacts['records'];museums={x['key']:x for x in allfacts['museums']}
    existing={x['institution']['name']:x['institution'] for x in load(RUN/'production-baseline.json')['institutions']}
    existing['Museum of Byzantine Culture']=existing['Museum of Byzantine Culture, Thessaloniki']
    ready=[];held=[];new_places={};museum_plan={}
    with connect()as db:
        institutions=db.execute('SELECT to_jsonb(i) row FROM institutions i ORDER BY id').fetchall()
        places=db.execute("SELECT to_jsonb(p) row FROM places p WHERE country_code='GR' ORDER BY id").fetchall()
        for key in sorted({f['museum_key']for f in selected}):
            mu=museums[key];name=mu['name'];city=mu.get('city') or NA_CITIES[name]
            prior=existing.get(name)
            if prior is None:
                same=[x['row']for x in institutions if x['row']['normalized_name']==norm(name)]
                assert not same,'Unreviewed existing institution name collision: '+name
            ps=[x['row']for x in places if norm(x['row']['name'])==norm(city)]
            if prior and prior['place_id']:
                ps=[x['row']for x in places if x['row']['id']==prior['place_id']]
                assert len(ps)==1
            if ps:place=ps[0]
            else:
                place=dict(id=uid('place/gr/'+norm(city)),name=city,normalized_name=norm(city),country_code='GR')
                new_places[place['id']]=place
            if prior:row=dict(prior,place_id=place['id'])
            else:
                website=mu.get('source_url') or (mu.get('directory')or{}).get('source_url')
                if not website:
                    first=next(f for f in selected if f['museum_key']==key)
                    website=first['source_url']
                row=dict(id=uid('institution/'+key),slug='greek-museum-'+key,name=name,normalized_name=norm(name),
                    kind='museum',status='review',place_id=place['id'],website_url=website)
            museum_plan[key]=dict(row=row,before=prior,evidence=mu,place=place)
        # All identities are restricted to selected source URLs, titles and museums.
        urls=sorted({u.rstrip('/')for f in selected for u in [f['source_url'],f.get('native_url')]if u})
        variants=sorted({v for u in urls for v in [u,u+'/',u.replace('https://','http://'),u+'?language=en']})
        matches=db.execute("""SELECT entity_id::text id,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s)
          UNION SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)""",(variants,variants)).fetchall()
        titles=sorted({norm(v)for f in selected for v in [f['title'],f.get('alternate_title'),f.get('original_title')]if v})
        title_ids=[r['id']for r in db.execute("SELECT id::text FROM artworks WHERE normalized_title=ANY(%s) AND status<>'archived'",(titles,))]
        ids=sorted({x['id']for x in matches}|set(title_ids)|{x['artwork']['id']for x in load(RUN/'production-scoped-artworks.json.gz')})
        current=full_rows(db,ids);by_id={x['artwork']['id']:x for x in current}
        save(BACKUP/(PLAN+'.identity-preimages.json.gz'),current)
        source_index=collections.defaultdict(set)
        for x in matches:source_index[x['url'].replace('http://','https://').split('?language=')[0].rstrip('/')].add(x['id'])
        for x in current:
            for evidence in x['citations']+x['identifiers']:
                u=evidence.get('canonical_url')or evidence.get('source_url')or''
                if 'benaki.org/' in u and parse_qs(urlparse(u).query).get('id'):
                    source_index['benaki:'+parse_qs(urlparse(u).query)['id'][0]].add(x['artwork']['id'])
        # Exact names/aliases and consistent lifespans may link existing painters.
        ar=db.execute("SELECT to_jsonb(a) row,ARRAY(SELECT alias FROM artist_aliases al WHERE al.artist_id=a.id) aliases FROM artists a WHERE a.status<>'archived' ORDER BY a.id").fetchall()
        creator_index=collections.defaultdict(set);artists={x['row']['id']:x['row']for x in ar}
        for x in ar:
            for name in [x['row']['display_name']]+x['aliases']:
                creator_index[m.creator_key(name)].add(x['row']['id'])
        for f in selected:
            f=dict(f);mu=museum_plan[f['museum_key']]['row'];creator=f.get('creator_label')or''
            if f['source']=='nationalarchive' and mu['name']=='Byzantine and Christian Museum':
                inv=re.findall(r'ΒΧΜ\s*0*(\d+)',f['raw'].get('oldCode')or'')
                if len(set(inv))==1:f['accession']='ΒΧΜ '+str(int(inv[0]))
            if f['source']=='searchculture' and f['raw']['collection']=='benaki_collections':
                inv=re.findall(r'\((?:GE|ΓΕ)\s*(\d+)\)',str(f['raw']['fields'].get('Description')))
                if len(set(inv))==1:f['accession']='GE '+inv[0]
            sourceurls={f['source_url'].replace('http://','https://').rstrip('/')}
            if f.get('native_url'):sourceurls.add(f['native_url'].replace('http://','https://').rstrip('/'))
            if 'benaki.org/'in(f.get('native_url')or''):
                sourceurls.add('benaki:'+parse_qs(urlparse(f['native_url']).query)['id'][0])
            exact=set().union(*(source_index[u]for u in sourceurls))
            if not exact and f.get('accession'):
                exact={a['id']for x in current if (a:=x['artwork'])['current_institution_id']==mu['id'] and accession_key(a.get('accession_number'))==accession_key(f['accession'])}
            if len(exact)>1:
                held.append(dict(facts=f,reason='multiple_existing_source_identities',ids=sorted(exact)));continue
            before=by_id[next(iter(exact))]if exact else None
            names=[creator]+[re.sub(r'^.*\b(?:Painters|Engravers|Sculptors|Visual artists|Photographers|Icon painters|Artists|Architects|Educators)\s+', '',untag(x)) for x in f.get('creator_values',[]) if x.endswith('(EN)')]
            pids=set().union(*(creator_index[m.creator_key(re.sub(r'[, ]*\(?\d{3,4}\s*[-–]\s*\d{3,4}\)?$','',n))]for n in names))
            pid=next(iter(pids))if len(pids)==1 else None
            if re.search(r'\b(?:unknown|anonymous|attributed|workshop|school|after|copy|orphan)\b|αγνωστ',norm(creator)):pid=None
            life=re.search(r'\(?\b(\d{4})\s*[-–]\s*(\d{4})\)?',creator)
            if pid and life and any(artists[pid][k] and artists[pid][k]!=int(life[i])for k,i in [('birth_year',1),('death_year',2)]):pid=None
            if before:
                w=before['artwork']
                if w['status']!='review' or w['published_at'] or w['current_institution_id']not in [None,mu['id']]:
                    held.append(dict(facts=f,reason='existing_publication_or_holding_conflict',id=w['id']));continue
                if pid and before['artists'] and pid not in {a['id']for a in before['artists']}:
                    held.append(dict(facts=f,reason='existing_creator_conflict',id=w['id']));continue
                aid=w['id']
            else:
                relevant=[];ft={norm(v)for v in [f['title'],f.get('alternate_title'),f.get('original_title')]if v}
                for x in current:
                    w=x['artwork']
                    if not ft&{norm(w['title']),norm(w.get('alternate_title'))}:continue
                    if w['current_institution_id']==mu['id'] or pid in {a['id']for a in x['artists']} or (creator and m.creator_key(creator)==m.creator_key(w.get('unlinked_creator_label'))):relevant.append(w['id'])
                if relevant:
                    held.append(dict(facts=f,reason='same_title_creator_or_museum_needs_version_reconciliation',ids=relevant));continue
                aid=uid('artwork/'+f['scheme']+'/'+f['source_id'])
            f.update(artwork_id=aid,artist_id=pid,museum=mu,before=before,action='enrich'if before else'create')
            ready.append(f)
        used={f['museum_key']for f in ready};museum_plan={k:v for k,v in museum_plan.items()if k in used}
        result=dict(at=now(),records=ready,held=held,museums=museum_plan,places=list(new_places.values()),
                    artists={p:artists[p]for p in {f['artist_id']for f in ready}if p})
        save(RUN/PLAN,result);save(BACKUP/(PLAN+'.preimages.json.gz'),result)
    print('Plan:',collections.Counter(f['action']for f in ready),len(held),'holds;',len(museum_plan),'museums;',len(result['artists']),'painters',flush=True)


def cloud_backup():
    result=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791471559641','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True))
    assert result['status']=='SUCCESSFUL'
    if not(RUN/'cloud-backup.json').exists():save(RUN/'cloud-backup.json',result);save(BACKUP/'cloud-backup.json',result)


def apply():
    p=load(RUN/PLAN);digest=sha((RUN/PLAN).read_bytes())
    assert not(RUN/APPLIED).exists();cloud_backup();records=p['records'];sid=uid('source')
    with connect(readonly=False)as db,db.transaction():
        db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(RUN.name,))
        assert db.execute('SELECT current_database() name').fetchone()['name']=='artline'
        assert len({f['artwork_id']for f in records})==len(records)
        urls=[f['source_url']for f in records];expected={f['source_url']:f['artwork_id']for f in records}
        concurrent=db.execute("SELECT entity_id::text id,source_url url FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text,canonical_url FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall()
        assert all(expected[x['url']]==x['id']for x in concurrent),'Concurrent source identity conflict'
        for f in records:
            raw=gzip.decompress((ROOT/f['receipt']['body_path']).read_bytes());assert sha(raw)==f['receipt']['sha256']
            assert f['first'] is None and f['last'] is None if f['precision']=='unknown'else f['first']<=f['last']<=1970
            assert not(f['work_type']=='photograph'and f['last']is not None and f['last']<1826)
            if f['artist_id']and f['last']is not None and p['artists'][f['artist_id']]['birth_year']:
                assert f['last']>=p['artists'][f['artist_id']]['birth_year']
        for row in db.execute('SELECT to_jsonb(a) row FROM artists a WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE',(list(p['artists']),)):
            assert row['row']==p['artists'][row['row']['id']],'Artist authority changed'
        # Store source metadata separately from the user's source acceptance.
        source=db.execute('SELECT id::text FROM sources WHERE id=%s OR slug=%s',(sid,RUN.name)).fetchall()
        if source:assert len(source)==1 and source[0]['id']==sid
        else:m.insert(db,'sources',dict(id=sid,slug=RUN.name,name='Greek museums: Ministry of Culture and museum-supplied SearchCulture records',source_type='collection_page',base_url=g.PORTAL))
        usedplaces={mu['row']['place_id']for mu in p['museums'].values()}
        for place in p['places']:
            if place['id']in usedplaces:
                assert not db.execute('SELECT 1 FROM places WHERE id=%s',(place['id'],)).fetchone()
                m.insert(db,'places',place);m.audit_entry(db,'place',place['id'],None,place,'insert')
        for key,mu in p['museums'].items():
            row=mu['row'];prior=mu['before']
            if prior:
                current=db.execute('SELECT to_jsonb(i) row FROM institutions i WHERE id=%s FOR UPDATE',(row['id'],)).fetchone()['row'];assert current==prior
                if row['place_id']!=prior['place_id']:
                    db.execute('UPDATE institutions SET place_id=%s,updated_at=now() WHERE id=%s',(row['place_id'],row['id']))
                    m.audit_entry(db,'institution',row['id'],prior,row,'update')
            else:m.insert(db,'institutions',row);m.audit_entry(db,'institution',row['id'],None,row,'insert')
            evidence=mu['evidence'];url=evidence.get('source_url')or(evidence.get('directory')or{}).get('source_url')or next(f['source_url']for f in records if f['museum_key']==key)
            m.insert(db,'citations',dict(entity_type='institution',entity_id=row['id'],field_name='greek_museum_identity_20261008',source_id=sid,source_url=url,evidence_note=json.dumps(mu,ensure_ascii=False),retrieved_at=now(),created_by=ACTOR))
        for f in records:
            aid=f['artwork_id'];prior=f['before']['artwork']if f['before']else None
            actual=db.execute('SELECT to_jsonb(a) row FROM artworks a WHERE id=%s FOR UPDATE',(aid,)).fetchone()
            assert (actual['row']if actual else None)==prior,'Artwork drift: '+aid
            exact=db.execute("SELECT entity_id::text id FROM external_identifiers WHERE entity_type='artwork' AND scheme=%s AND external_id=%s",(f['scheme'],f['source_id'])).fetchall()
            assert not exact or all(x['id']==aid for x in exact)
            if not prior:
                row=dict(id=aid,slug='greek-museums-'+aid,title=f['title'],alternate_title=f.get('alternate_title'),normalized_title=norm(f['title']),
                    date_display=f['date_display'],creation_year_start=f['first'],creation_year_end=f['last'],date_precision=f['precision'],
                    work_type=f['work_type'],medium_text=f['medium'],dimensions_text=f['dimensions'],accession_number=f['accession'],
                    status='review',research_candidate=True,unlinked_creator_label=None if f['artist_id']else f['creator_label'],created_by=ACTOR,updated_by=ACTOR)
                m.insert(db,'artworks',row)
                if f['artist_id']:
                    link=dict(artwork_id=aid,artist_id=f['artist_id'],attribution_role='primary',representative_order=1,
                        attribution_note='Exact unique existing name/alias, with source lifespan consistency where stated; original creator label: '+f['creator_label']+'; '+f['source_url'])
                    m.insert(db,'artwork_artists',link);m.audit_entry(db,'artwork_creator_link',aid,None,link,'insert')
            if not exact:
                m.insert(db,'external_identifiers',dict(entity_type='artwork',entity_id=aid,scheme=f['scheme'],external_id=f['source_id'],canonical_url=f['source_url'],source_id=sid,retrieved_at=f['receipt']['retrieved_at']))
            m.insert(db,'citations',dict(entity_type='artwork',entity_id=aid,field_name='greek_museum_object_20261008',source_id=sid,source_record_id=f['source_id'],source_url=f['source_url'],
                evidence_note=json.dumps(dict(plan_sha256=digest,facts={k:v for k,v in f.items()if k not in ['before','museum']},policy='Source statements retained; unknowns remain unknown; no present-display or publication assertion.'),ensure_ascii=False),retrieved_at=f['receipt']['retrieved_at'],created_by=ACTOR))
            holdings=db.execute("SELECT institution_id::text FROM artwork_location_assertions WHERE artwork_id=%s AND claim_type='holding' AND review_state='accepted' AND superseded_by IS NULL",(aid,)).fetchall()
            assert all(h['institution_id']==f['museum']['id']for h in holdings)
            if not holdings:
                m.insert(db,'artwork_location_assertions',dict(artwork_id=aid,claim_type='holding',institution_id=f['museum']['id'],context='collection',source_id=sid,source_url=f['source_url'],evidence_note=f['holding_basis']+' Editorial confidence '+str(f['holding_confidence'])+' (not a calibrated probability).',checked_at=f['receipt']['retrieved_at'],review_state='accepted'))
            after=db.execute('SELECT to_jsonb(a) row,artline_has_selection_evidence(id) selected FROM artworks a WHERE id=%s',(aid,)).fetchone()
            assert after['row']['status']=='review' and after['row']['published_at']is None and after['selected']
            assert after['row']['current_institution_id']==f['museum']['id']
            if prior:assert all(after['row'][k]==prior[k]for k in ['title','creation_year_start','creation_year_end','date_precision','primary_media_id','status','published_at'])
            m.audit_entry(db,'artwork',aid,prior,after['row'],'update'if prior else'insert')
        after=full_rows(db,[f['artwork_id']for f in records]);save(BACKUP/AFTER,after)
    save(RUN/APPLIED,dict(at=now(),plan_sha256=digest,artwork_ids=[f['artwork_id']for f in records],created=sum(f['action']=='create'for f in records),enriched=sum(f['action']=='enrich'for f in records),new_museums=sum(not mu['before']for mu in p['museums'].values()),after_path=str(BACKUP/AFTER)))
    print('Catalogue applied',len(records),'objects',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['facts','plan','apply']);a=p.parse_args()
    {'facts':facts,'plan':plan,'apply':apply}[a.action]()
