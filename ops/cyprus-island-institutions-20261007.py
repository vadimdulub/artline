#!/usr/bin/env python3
"""Reconciled island-wide identities, geographic evidence and guarded writes."""
import argparse,collections,gzip,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('island',Path(__file__).with_name('cyprus-island-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
h,d,n,R,B=x.h,x.d,x.n,x.R,x.B
EXISTING={779307:'archbishop-kyprianos-museum-strovolos',493672:'ledroi-archaeological-museum-nicosia',493669:'hambis-municipal-printmaking-museum-nicosia',477706:'fairy-tale-museum-nicosia',469063:'hadjigeorgakis-kornesios-museum-nicosia',468835:'kykkos-monastery-museum',468750:'saint-neophytos-monastery',468670:'national-struggle-museum-nicosia',468664:'nimac-nicosia',468658:'leventis-gallery',468652:'pancyprian-gymnasium-museums-nicosia',468646:'leventis-municipal-museum-nicosia',468640:'cyprus-classic-motorcycle-museum-nicosia',468634:'state-gallery-cyprus',468616:'cypriot-coinage-museum-nicosia',468610:'giabra-pierides-collection-museum-nicosia',468603:'cyprus-folk-art-museum-nicosia',468597:'cyprus-postal-museum-nicosia',468591:'cyprus-police-museum-nicosia',468585:'cyprus-natural-history-museum-latsia',468573:'cvar-nicosia',468567:'makarios-byzantine-museum-nicosia',468561:'makarios-byzantine-museum-nicosia',468555:'cyprus-museum-nicosia'}
TOWNS={783014:'Limassol',782907:'Latchi',749446:'Paralimni',560579:'Agglisides',494065:'Limassol',493994:'Mazotos',493675:'Dali',489739:'Kampos',489717:'Limassol',479451:'Trachoni',477659:'Episkopeio',472395:'Sotira',468841:'Spilia',468835:'Kykkos Monastery',468829:'Palaichori',468823:'Koilani',468817:'Fikardou',468811:'Arsos',468805:'Steni',468798:'Paphos',468792:'Polis Chrysochous',468780:'Geroskipou',468774:'Fyti',468768:'Paphos',468762:'Geroskipou',468756:'Peristerona (Paphos district)',468750:'Paphos',468744:'Limassol',468738:'Episkopi (Limassol district)',468732:'Limassol',468726:'Limassol',468720:'Limassol',468714:'Limassol',468708:'Fasoula',468702:'Erimi',468696:'Limassol',468690:'Kato Polemidia',468684:'Limassol',468676:'Limassol',468628:'Agia Varvara (Nicosia district)',468548:'Larnaca',468542:'Larnaca',468536:'Larnaca',468530:'Larnaca',468525:'Larnaca',468520:'Larnaca',468514:'Athienou',468508:'Aradippou',468502:'Larnaca',468496:'Paralimni',468490:'Deryneia',468484:'Ayia Napa',468478:'Avgorou'}
NORTH=[
 ('StBarnabas-Arkeoloji','Saint Barnabas Icon and Archaeological Museum','Salamis','saint-barnabas-icon-archaeological-museum'),
 ('Namık-Kemal','Namık Kemal Dungeon and Museum','Famagusta','namik-kemal-museum-famagusta'),
 ('Canbulat','Canbulat Museum','Famagusta','canbulat-museum-famagusta'),
 ('Kral-Mezarları','Salamis Royal Tombs Museum','Salamis','salamis-royal-tombs-museum'),
 ('İkon-Müzesi-Yeni','İskele Icon Museum','İskele (Trikomo)','iskele-icon-museum'),
 ('İskele-Arkeoloji','İskele Archaeology Museum','İskele (Trikomo)','iskele-archaeology-museum'),
 ('Girne-Kalesi','Kyrenia Castle and Shipwreck Museum','Kyrenia','kyrenia-castle-shipwreck-museum'),
 ('Kıbrıs-Evi','Cyprus House and Carob Store Museum','Kyrenia','cyprus-house-museum-kyrenia'),
 ('Barış-ve-Özgürlük','Peace and Freedom Museum','Kyrenia region','peace-freedom-museum-kyrenia'),
 ('Archangelos','Archangelos Michael Icon Museum','Kyrenia','archangelos-michael-icon-museum-kyrenia'),
 ('Taşkent','Taşkent Martyrs Museum','Taşkent (Kyrenia district)','taskent-martyrs-museum'),
 ('G%C3%BCzelyurt-Do','Güzelyurt Archaeology and Nature Museum','Güzelyurt (Morphou)','guzelyurt-archaeology-nature-museum'),
 ('Güzelyurt-Tren','Güzelyurt Railway Station Museum','Güzelyurt (Morphou)','guzelyurt-railway-station-museum'),
 ('Lefke-Maden','Lefke Mining Museum — Vasıf Palas','Lefke','lefke-mining-museum'),
]
LARNAKA=[
 ('ecclesiastical-museum-athienou-archbishop-georgios','Ecclesiastical Museum of Athienou — Archbishop Georgios','Athienou'),
 ('larnaka-municipal-gallery-christoforou-collection','Larnaka Municipal Gallery — Christoforou Collection','Larnaca'),
 ('kato-drys-bee-embroidery-museum','Kato Drys Bee and Embroidery Museum','Kato Drys'),
 ('craft-caning-museum-livadia','Craft of Caning Museum, Livadia','Livadia'),
 ('local-agricultural-museum-kato-drys','Local Rural Museum of Kato Drys','Kato Drys'),
 ('museum-platini-musee-de-platini','Museum of Platini','Mosfiloti'),
 ('tochni-ecclesiastical-museum','Ecclesiastical Museum of Saints Constantine and Helen, Tochni','Tochni'),
 ('municipal-art-gallery','Larnaka Municipal Gallery','Larnaca'),
 ('salt-pepper-museum','Salt and Pepper Museum, Larnaca','Larnaca'),
 ('local-museum-traditional-embroidery-and-silversmith-work-lefkara','Local Museum of Traditional Embroidery and Silversmith-work, Lefkara','Lefkara'),
 ('museum-christian-art-christoforou-collection','Museum of Christian Art — Christoforou Collection','Aradippou'),
 ('aradippou-toy-museum','Aradippou Toy Museum','Aradippou'),
 ('jewish-museum-cyprus','Jewish Museum Cyprus','Larnaca'),
]
EXTRAS=[
 ('palaipafos','Local Archaeological Museum of Palaipafos (Kouklia)','Kouklia','palaipafos-archaeological-museum-kouklia','Palaipafos'),
 ('railways','Cyprus Railways Museum','Evrychou','cyprus-railways-museum-evrychou','Railways Museum'),
 ('akourdalia','Akourdalia Folk Art Museum','Akourdalia','akourdalia-folk-art-museum','Akourdalia'),
 ('nicosia-district','Linos Museum, Kakopetria','Kakopetria','linos-museum-kakopetria','Linos Museum'),
 ('nicosia-district','Eliomilos Olive Oil Museum, Kakopetria','Kakopetria','eliomilos-museum-kakopetria','Eliomilos Museum'),
 ('nicosia-district','Pedoulas Folkloric Museum','Pedoulas','pedoulas-folkloric-museum','Folkloric Museum in Pedoulas'),
 ('nicosia-district','Pedoulas Byzantine Museum','Pedoulas','pedoulas-byzantine-museum','Pedoulas Byzantine Museum'),
 ('nicosia-district','Saint John Lampadistis Byzantine Museum','Kalopanagiotis','saint-john-lampadistis-museum','Monastery of St John Lampadistis'),
 ('nicosia-district','Nikos Kouroussis Foundation Museum','Mitsero','nikos-kouroussis-museum-mitsero','Museum of Nikos Kouroussis'),
 ('nicosia-district','Museum of Folk Art, Tradition and Heritage, Platanistasa','Platanistasa','platanistasa-folk-art-museum','Museum of Folk Art, Tradition and Heritage in Platanistasa'),
 ('famagusta-directory','Museum of Ayia Anna, Paralimni','Paralimni','ayia-anna-museum-paralimni','Museum of Ayia Anna'),
]
def proof(page,label,identifier=None):
    rc=page['receipt'];assert rc['status']==200 and h.sha(gzip.decompress((n.REPO/rc['body_path']).read_bytes()))==rc['sha256']
    return dict(receipt=rc,url=page['url'],label=label,identifier=identifier,limitation='Institution identity/geographic evidence; no opening, artwork-count, object-holding or current-display claim inferred.')
def registry():
    source=h.load(R/'indexes/visitcyprus-museums.json');records=[];holds=[]
    for item in source['records']:
        iid=item['id'];name=h.plain(item['title']['rendered']);text=x.BeautifulSoup(item['content']['rendered'],'html.parser').get_text(' ',strip=True)
        if iid in [557945,468579]:holds.append(dict(source_id=iid,name=name,reason='Sculpture park/studio or handicraft retail centre; reconcile a present museum identity separately.'));continue
        m=re.search(r'Region:\s*(.*?)\s*Address:\s*(.*?)(?:GPS|Contact|Operating)',text);assert m
        town=TOWNS.get(iid,'Nicosia'if iid in EXISTING else None);assert town,(iid,name)
        row=dict(slug=EXISTING.get(iid,'cyprus-'+item['slug']),existing_slug=EXISTING.get(iid),name=name,place=town,region=m[1],address=m[2],kind='foundation'if iid==494065 else'museum',sources=[proof(dict(url=item['link'],receipt=source['receipt']),name,str(iid))])
        if iid==468823:
            for suffix,label in [('ecclesiastical','Ecclesiastical Museum, Koilani'),('viticulture','Viticulture Museum, Koilani')]:records.append(dict(row,slug='koilani-'+suffix+'-museum',name=label,notes='The primary directory explicitly describes two museums in Koilani; keep their object holdings separate.'))
        else:records.append(row)
    directory=h.load(R/'pages/north-department.json')
    for part,name,town,slug in NORTH:
        links=[a for a in directory['links']if part in a['url']];assert len(links)==1,(part,links)
        a=links[0];p=h.load(R/'pages'/('north-'+h.sha(a['url'].encode())[:20]+'.json'))
        records.append(dict(slug=slug,name=name,place=town,region='Northern Cyprus; primary departmental region retained in source URL',address=None,kind='museum',existing_slug=None,sources=[proof(p,a['text'])]))
    for key,name,town in LARNAKA:
        p=h.load(R/'pages'/('larnaka-'+key+'.json'))
        records.append(dict(slug='cyprus-'+key,name=name,place=town,region='Larnaca district',address=None,kind='museum',existing_slug=None,sources=[proof(p,p['title'])]))
    for key,name,town,slug,needle in EXTRAS:
        p=h.load(R/'pages'/(key+'.json'));assert h.norm(needle)in h.norm(p['text']),(key,needle)
        records.append(dict(slug=slug,name=name,place=town,region='Cyprus; locality and region retained in cited primary page',address=None,kind='museum',existing_slug=None,sources=[proof(p,needle)]))
    merged={}
    for row in records:
        if row['slug']in merged:merged[row['slug']]['sources']+=row['sources']
        else:merged[row['slug']]=row
    result=dict(at=h.now(),records=list(merged.values()),held=holds,minimum=500,upper_target=1000)
    h.save(R/'institution-registry.json',result);print('Registry',len(merged),'institutions,',len(holds),'held leads',flush=True)
def plan():
    reg=h.load(R/'institution-registry.json')
    with d.connect()as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        live=[r['v']for r in db.execute('SELECT to_jsonb(i)v FROM institutions i ORDER BY id')]
        places=[r['v']for r in db.execute("SELECT to_jsonb(p)v FROM places p WHERE country_code='CY' ORDER BY id")]
    rows=[];planned_places={};used=set()
    for row in reg['records']:
        candidates=[i for i in live if i['slug']==row['slug']or h.norm(i['name'])==h.norm(row['name'])];assert len(candidates)<=1,(row['name'],candidates)
        before=candidates[0]if candidates else None
        matches=[p for p in places if p['normalized_name']==h.norm(row['place'])];assert len(matches)<=1
        place=matches[0]if matches else planned_places.setdefault(row['place'],dict(id=n.uid('place/'+row['place']),name=row['place'],normalized_name=h.norm(row['place']),country_code='CY'))
        if before:
            obj=dict(before)
            if obj['place_id']is None:obj['place_id']=place['id']
        else:obj=dict(id=n.uid('institution/'+row['slug']),slug=row['slug'],name=row['name'],normalized_name=h.norm(row['name']),kind=row['kind'],place_id=place['id'],website_url=row['sources'][0]['url'],status='review',description='Institution in '+row['place']+', Cyprus, documented by the cited primary museum or regional/national directory. '+row.get('notes',''))
        assert obj['id']not in used;used.add(obj['id']);rows.append(dict(institution=obj,before=before,facts=row,editorial_confidence=.95,confidence_basis='Named primary institutional/directory entry, reviewed geography and duplicate identities; editorial assessment, not calibrated probability.'))
    value=dict(at=h.now(),target='production',records=rows,new_places=list(planned_places.values()),existing_places=places,all_institution_identities=live,registry_sha256=h.sha((R/'institution-registry.json').read_bytes()))
    h.save(R/'institution-plan.json.gz',value);h.save(B/'institution-plan-preimages.json.gz',value)
    print('PLAN',sum(r['before']is None for r in rows),'new institutions;',sum(r['before']is not None for r in rows),'existing;',len(planned_places),'new geographic places',flush=True)
def apply():
    p=h.load(R/'institution-plan.json.gz');digest=h.sha((R/'institution-plan.json.gz').read_bytes());assert not(R/'institutions-applied.json').exists()
    b=h.load(R/'production-backup.json')['production'];assert b['status']=='SUCCESSFUL'and b['instance']=='artline-postgres'and '/projects/artline-508319/'in b['selfLink']
    assert h.sha((R/'institution-registry.json').read_bytes())==p['registry_sha256']
    for row in p['records']:
        for s in row['facts']['sources']:
            rc=s['receipt'];assert h.sha(gzip.decompress((n.REPO/rc['body_path']).read_bytes()))==rc['sha256']
    ids=[r['institution']['id']for r in p['records']];sid=n.uid('institution-source')
    with d.connect(readonly=False)as db,db.transaction():
        assert db.execute('SELECT current_database()name').fetchone()['name']=='artline'
        db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))");db.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(R.name,))
        actual={r['v']['id']:r['v']for r in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=ANY(%s::uuid[])ORDER BY id FOR UPDATE',(ids,))}
        for row in p['records']:assert actual.get(row['institution']['id'])==row['before'],'Institution version changed'
        places=[r['v']for r in db.execute("SELECT to_jsonb(p)v FROM places p WHERE country_code='CY' ORDER BY id FOR UPDATE")];assert places==p['existing_places'],'Cyprus places changed'
        new=[r['institution']for r in p['records']if r['before']is None]
        assert not db.execute('SELECT id FROM institutions WHERE slug=ANY(%s)',([r['slug']for r in new],)).fetchall()
        for i in new:assert not db.execute('SELECT id FROM institutions WHERE normalized_name=%s AND place_id=%s',(i['normalized_name'],i['place_id'])).fetchall()
        h.save(B/'institution-transaction-preimages.json.gz',dict(at=h.now(),institutions=actual,places=places,absent_institution_ids=[r['id']for r in new],new_place_ids=[r['id']for r in p['new_places']],plan_sha256=digest))
        for place in p['new_places']:h.insert(db,'places',place);h.audit_entry(db,'place',place['id'],None,place,'insert')
        h.insert(db,'sources',dict(id=sid,slug=R.name+'-museum-identities',name='Cyprus island-wide museums: primary institutional and regional/national directory evidence',source_type='authority_data'))
        for row in p['records']:
            obj=row['institution'];before=row['before']
            if before is None:h.insert(db,'institutions',obj)
            elif before['place_id']!=obj['place_id']:db.execute('UPDATE institutions SET place_id=%s WHERE id=%s',(obj['place_id'],obj['id']))
            for index,s in enumerate(row['facts']['sources']):
                evidence=dict(facts=row['facts'],source=s,editorial_confidence=row['editorial_confidence'],confidence_basis=row['confidence_basis'],plan_sha256=digest)
                h.insert(db,'citations',dict(id=n.uid('institution-citation/'+obj['id']+'/'+str(index)),entity_type='institution',entity_id=obj['id'],field_name='verified_museum_identity_and_geography',source_id=sid,source_url=s['url'],source_record_id=s.get('identifier'),evidence_note=json.dumps(evidence,ensure_ascii=False),retrieved_at=s['receipt']['retrieved_at'],created_by=h.ACTOR))
            after=db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=%s',(obj['id'],)).fetchone()['v']
            assert all(after[k]==v for k,v in obj.items()if k!='updated_at')
            if before is None or before!=after:h.audit_entry(db,'institution',obj['id'],before,after,'insert'if before is None else'update')
        after={r['v']['id']:r['v']for r in db.execute('SELECT to_jsonb(i)v FROM institutions i WHERE id=ANY(%s::uuid[])',(ids,))}
        h.save(B/'institution-transaction-after.json.gz',dict(at=h.now(),institutions=after,plan_sha256=digest))
    receipt=dict(at=h.now(),target='production',new_institutions=len(new),existing_institutions=len(ids)-len(new),new_places=len(p['new_places']),geography_enrichments=sum(r['before']is not None and r['before']['place_id']!=r['institution']['place_id']for r in p['records']),institution_ids=ids,plan_sha256=digest,new_publications=0,local_database_writes=0)
    h.save(R/'institutions-applied.json',receipt);print('COMMITTED',{k:v for k,v in receipt.items()if k!='institution_ids'},flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['registry','plan','apply']);a=p.parse_args();globals()[a.phase]()
