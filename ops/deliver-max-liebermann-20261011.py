#!/usr/bin/env python3
"""Reviewed museum-object expansion for Max Liebermann; production only."""
import argparse,collections,csv,gzip,hashlib,html,importlib.util,json,re,subprocess,uuid
from pathlib import Path
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    sp=importlib.util.spec_from_file_location(name,ROOT/'ops'/file);v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);return v
d=module('liebermann_research','research-max-liebermann-20261011.py')
b=module('liebermann_existing_tools','low-count-200-painters-20261008.py')
r=b.r;r.PORT=55448
RUN=d.RUN;OP='max-liebermann-20261011';AID='b05c66ac-a834-4677-857a-79ee9c321a08';ACTOR='local-european-research'
BACKUP=Path.home()/'Library/Application Support/Artline/backups'/OP
CONFIG={
'Hamburger Kunsthalle':('hamburg','caca0946-ccfc-4f41-becc-fc3b18dbeb34','hamburger-kunsthalle-object'),
'Städel Museum':('staedel','b71d242a-a538-441c-8d45-08a011570634','staedel-object'),
'ALBERTINA':('albertina','7521d69d-e419-538d-9d5c-2848dcebcf6e','albertina-object'),
'Staatliche Museen zu Berlin':('berlin','7f338394-6c07-5b37-9d63-7b85e66e9007','smb-object'),
'The Metropolitan Museum of Art':('met','a0673ec8-1b74-ebcb-0331-a1c021b793f6','met-object'),
'National Gallery of Art':('nga','4a7cf367-a105-f2bf-dc1c-a2210974752e','european-nga-object'),
'Art Institute of Chicago':('aic','', 'artic-object'),
'The Cleveland Museum of Art':('cleveland','', 'cleveland-object'),
'Rijksmuseum':('rijks','b6a5755d-157e-4ebe-a5a9-3bc52964ebf5','rijks-object'),
'SMK – National Gallery of Denmark':('smk','ee9976cf-63a1-48f7-9e34-eb5444e0486c','smk-object'),
'Bavarian State Painting Collections':('pinakothek','33916550-59e8-4316-92d5-39c66ca12dfa','pinakothek-artwork'),
'Museo Nacional Thyssen-Bornemisza':('thyssen','eb9e002b-1d26-4996-9b58-d34a4c372fc3','thyssen-artwork'),
'The Museum of Modern Art':('moma','038c9af4-f059-50ae-aae5-085fcabc8842','moma-object'),
}
FILES=['hamburg-records.json','staedel-records.json','albertina-records.json','berlin-records.json','us-open-data-records.json','us-api-records.json','rijks-records.json','smk-records.json','pinakothek-thyssen-records.json','moma-normalized.json']

def uid(key):return str(uuid.uuid5(uuid.NAMESPACE_URL,OP+'/'+key))
def load(name):return r.load(RUN/name)
def invkey(institution,accession):
    if institution=='caca0946-ccfc-4f41-becc-fc3b18dbeb34':accession=re.sub(r'^HK[-\s]*','',accession or'',flags=re.I)
    return institution,d.norm(accession)
def urlkey(url):
    if not url:return ''
    q=re.search(r'wikidata.org/(?:wiki|entity)/(Q\d+)',url)
    if q:return 'wikidata/'+q[1]
    u=urlsplit(url);host=u.hostname.removeprefix('www.')if u.hostname else'';path=unquote(u.path).rstrip('/')
    if 'hamburger-kunsthalle' in host and'/objekt/'in path:return 'hamburg/'+path.split('/objekt/')[1].split('/')[0].casefold()
    if host in ['id.smb.museum','search.smb.museum']and'/object/'in path:return 'berlin/'+path.split('/object/')[1].removeprefix('obj-')
    if host=='sammlung.pinakothek.de'and'/artwork/'in path:return 'pinakothek/'+path.split('/artwork/')[1].split('/')[0]
    if host=='sammlungenonline.albertina.at'and'/objects/'in path:return 'albertina/'+path.split('/objects/')[1].split('/')[0]
    if host=='nga.gov':
        q=re.search(r'art-object-page\.(\d+)|/artworks/(\d+)',path)
        if q:return 'nga/'+str(q[1]or q[2])
    if host=='metmuseum.org'and'/collection/search/'in path:return 'met/'+path.rsplit('/',1)[-1]
    if host=='artic.edu'and'/artworks/'in path:return 'aic/'+path.split('/artworks/')[1].split('/')[0]
    if host=='clevelandart.org'and'/art/'in path:return 'cleveland/'+path.split('/art/')[1].split('/')[0]
    if host=='open.smk.dk':return 'smk/'+path.rsplit('/',1)[-1]
    return host+path

def dates(value):
    v=html.unescape(str(value or'')).strip().replace('–','-').replace('—','-')
    v=re.sub(r'^Herstellung:\s*','',v)
    v=re.sub(r'^(um|circa|ca\.?|about|c\.)\s*','c. ',v,flags=re.I)
    match=re.fullmatch(r'(c\. )?(\d{4})\s*[-/]\s*(\d{2})',v)
    if match:v=(match[1]or'')+match[2]+'-'+match[2][:2]+match[3]
    dt=b.m.dates.creation_date(v)
    if dt:dt['date_display']=str(value).strip()
    return dt or dict(creation_year_start=None,creation_year_end=None,date_precision='unknown',date_display=str(value or'Unknown date').strip())

def kind(medium,typ):
    t=html.unescape((typ or'')+' '+(medium or'')).casefold()
    if re.search(r'lithograph|lithograf|litograf|radier|radering|kaltnadel|drypoint|etching|aquatint|engraving|woodcut|druck|^print|\bprint\b',t):return 'print'
    if re.search(r'aquarell|watercolou?r',t):return 'watercolor'
    if re.search(r'öl|oil|tempera|gouache|gemälde|painting|^bild\b',t):return 'painting'
    if re.search(r'zeichnung|drawing|tegning|blyant|\bkul\b|bleistift|kreide|kohle|charcoal|pencil|pastell?|tusche|feder|graphit|crayon|chalk',t):return 'drawing'
    return 'unknown'

def normalize(x):
    if 'error'in x:return None,'source_page_unavailable_or_unparsed'
    source=x['source'];y=dict(source=source,source_id=str(x.get('source_id')or''),source_url=x['source_url'],title=html.unescape(x['title']).strip(),creator=x.get('creator'),medium=x.get('medium'),dimensions=x.get('dimensions'),accession=x.get('accession'),work_type=x.get('work_type'),raw=x)
    date=x.get('date');reason=None
    if source=='Hamburger Kunsthalle':
        if not x['creator'].startswith('Max Liebermann'):reason='other_maker_after_Liebermann_or_qualified_authorship'
        if re.search('mechanische reproduktion|heliograv|lichtdruck|photograv|faksimile',x.get('medium')or'',re.I):reason='photomechanical_reproduction_not_original'
        if x['source_id'].lower().startswith('kb-'):reason='library_volume_component_requires_physical_unit_review'
        title,sep,last=x['title'].rpartition(', ')
        if sep and re.search(r'\d{4}|undatiert|o\. ?D\.',last):y['title']=title;date=last
        y['dimensions']=next((v for v in x['fields']['sidebar']if re.search(r'\d\s*(?:mm|cm)',v)),None)
        if x.get('verso_title'):y['physical_unit_note']='Source describes recto and verso together; one inventory object retained.'
    elif source=='Städel Museum':
        y['source_id']=x['fields'].get('Object Number')or x['source_id'];y['accession']=y['source_id']
        y['medium']=y['medium']or'; '.join(x['fields'].get(k,'')for k in ['Technique','Material']).strip('; ')
        y['dimensions']=y['dimensions']or x['fields'].get('Blatt')
        if x['creator']!='Max Liebermann':reason='creator_needs_review'
    elif source=='ALBERTINA':
        if x['creator']!='Max Liebermann':reason='creator_needs_review'
        if re.fullmatch(r'\d+v',y['accession']or''):reason='verso_same_sheet_review'
        if re.fullmatch(r'\d+r',y['accession']or''):y['physical_unit_note']='Recto retained as one sheet; separately catalogued verso preserved in research register, not counted twice.'
    elif source=='Staatliche Museen zu Berlin':
        creators=x['creator_roles'];own=[c for c in creators if c.get('searchLabel')=='Max Liebermann'and c.get('role')in ['Zeichner*in','Radierer*in','Lithograf*in','Lithograph*in','Stecher*in','Maler*in']and not re.search(r'nach|zugeschrieben|ehemals',c['nameLine'],re.I)]
        other=[c for c in creators if c.get('searchLabel')!='Max Liebermann'and c.get('role')in ['Zeichner*in','Radierer*in','Lithograf*in','Stecher*in','Maler*in']]
        if not own or other:reason='depicted_person_designer_or_other_creator_needs_review'
        if re.search(r'Seite|Rückseite|Skizzenbuch|Einband|Buch|Fotografie',x.get('work_type')or'',re.I):reason='book_page_verso_or_nonart_physical_unit_review'
        y['source_id']=y['source_id'].removeprefix('obj-')
    elif source=='National Gallery of Art':
        if not any(c['roletype']=='artist'for c in x['creator_roles']):reason='former_owner_not_creator'
        if x['raw']['accessioned']!='1'or x['raw']['isvirtual']!='0':reason='not_accessioned_or_virtual_record'
        if x['raw']['classification']not in ['Print','Painting','Drawing']:reason='bound_volume_or_other_unit_review'
    elif source=='The Metropolitan Museum of Art':
        raw=x['raw'];names=raw['Artist Display Name'].split('|');prefix=raw['Artist Prefix'].split('|')
        if len(prefix)==len(names)and any(prefix[i].strip()for i,n in enumerate(names)if n=='Max Liebermann'):reason='qualified_after_creator_role'
        if x['work_type']not in ['Prints','Paintings','Drawings']or re.search('book|album|portfolio|leaf|folio',x.get('object_name')or'',re.I):reason='book_portfolio_or_component_unit_review'
    elif source=='Rijksmuseum':
        if len(x['creator'].split('; '))!=1:reason='multiple_creators_require_role_review'
        if any(re.fullmatch(r'https://id\.rijksmuseum\.nl/20\d+',p or'')for p in x['parents']):reason='physical_parent_component_review'
        if re.search(r'\((?:V|VERSO)\)\s*$',y['accession']or'',re.I):reason='verso_same_sheet_review'
        y['work_type']=' '.join(x['types'])
    elif source=='SMK – National Gallery of Denmark':
        if any(c.get('creator_role')for c in x['creator_roles']):reason='qualified_creator_role_review'
        if any(re.search(r'bog|book|mappe|album',v,re.I)for v in x.get('work_status')or[]):reason='book_or_portfolio_unit_review'
        if 'bog'in x['accession'].lower():reason='book_or_portfolio_unit_review'
        y['work_type']=' '.join(v['name']for v in x['object_names']);y['dimensions']='; '.join(v['type']+' '+v['value']+' '+v['unit']for v in x['raw'].get('dimensions',[]))
    elif source=='Bavarian State Painting Collections':
        raw=gzip.decompress((ROOT/x['receipt']['body_path']).read_bytes());s=d.BeautifulSoup(raw,'html.parser');f={}
        for label in s.select('.content__item .label-header'):
            text=label.parent.get_text(' ',strip=True);key=label.get_text(' ',strip=True);f[key]=text.removeprefix(key).strip()
        y['title']=y['title'].rstrip(', ');date=s.select_one('h1').parent.select_one('.artwork__dates').get_text(' ',strip=True)
        y.update(medium=f.get('Material / Technik / Bildträger'),dimensions=f.get('Maße des Objekts'),accession=f.get('Inventarnummer'),work_type='painting');y['raw']=dict(x,parsed_fields=f)
        if 'Neue Pinakothek'not in f.get('Bestand',''):reason='holding_branch_requires_review'
    elif source=='Museo Nacional Thyssen-Bornemisza':
        raw=gzip.decompress((ROOT/x['receipt']['body_path']).read_bytes());s=d.BeautifulSoup(raw,'html.parser');h=s.select_one('h1').parent;date=s.select_one('.field--FechasThyssen').get_text(' ',strip=True)
        label=h.find(string=re.compile('Inv. no.'));inv=label.parent if label else None;y['accession']=inv.get_text(' ',strip=True).replace('Inv. no.','').strip(' ()')if inv else None
        box=h.select_one('.u-font-size-sm');parts=[c.get_text(' ',strip=True)for c in box.find_all('div',recursive=False)]if box else[]
        literal=parts[0]if parts else '';match=re.fullmatch(r'(.+?)\.\s+(\d.+?\bcm)',literal)
        y['medium']=match[1]if match else literal or None;y['dimensions']=match[2]if match else None
    elif source=='The Museum of Modern Art':
        if x['creator']!='Max Liebermann':reason='creator_needs_review'
        if x['work_type']!='Print' or not re.fullmatch(r'\d+\.\d{4}',x['accession']):reason='book_or_periodical_component_unit_review'
    y.update(dates(date));y['normalized_title']=b.q.norm(y['title']);y['work_type']=kind(y['medium'],y['work_type'])
    years=[int(v)for v in re.findall(r'(?<!\d)(\d{4})(?!\d)',str(date or''))]
    if any(v>1970 for v in years):reason='source_date_after_or_crossing_1970'
    if y['work_type']in ['painting','drawing','watercolor']and y['creation_year_start']and y['creation_year_start']>1935:reason='original_creation_postdates_artist_life_requires_review'
    if not y['title']or not y['accession']or not y['source_id']:reason='native_object_identity_incomplete'
    if y['work_type']=='unknown':reason=reason or'object_type_requires_review'
    return y,reason

def plan():
    rows=[];held=[]
    for file in FILES:
        for x in load(file):
            y,reason=normalize(x)
            if reason:held.append(dict(source=x['source'],source_url=x['source_url'],reason=reason,record=y or x))
            else:rows.append(y)
    # Check physical parent associations supplied by NGA, not only title wording.
    inseparable=set()
    with (d.DATA/'nga/object_associations.csv').open(newline='',encoding='utf-8-sig')as f:
        for rel in csv.DictReader(f):
            if rel['relationship']=='inseparable':inseparable.add(rel['childobjectid'])
    clear=[]
    for y in rows:
        if y['source']=='National Gallery of Art'and y['source_id']in inseparable:held.append(dict(source=y['source'],source_url=y['source_url'],reason='inseparable_child_record',record=y))
        else:clear.append(y)
    rows=clear
    if (RUN/'scoped-collision-snapshot.json.gz').exists() and (RUN/'plan-draft.json.gz').exists():
        previous=load('plan-draft.json.gz');artist=previous['artist'];CONFIG.update(previous['configuration'])
        snap=load('scoped-collision-snapshot.json.gz');existing=snap['existing'];refs=snap['refs'];cites=snap['cites'];links=snap['links']
    else:
        with r.connect('production')as db,db.transaction():
            db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            artist=db.execute('SELECT to_jsonb(a) a FROM artists a WHERE id=%s',(AID,)).fetchone()['a'];assert artist['display_name']=='Max Liebermann'and artist['birth_year']==1847 and artist['death_year']==1935
            for source in ['Art Institute of Chicago','The Cleveland Museum of Art']:
                matching=db.execute('SELECT id::text,name FROM institutions WHERE name=%s',(source,)).fetchall();assert len(matching)==1
                c=CONFIG[source];CONFIG[source]=(c[0],matching[0]['id'],c[2])
            mids=sorted({v[1]for v in CONFIG.values()});existing=db.execute("SELECT to_jsonb(a) a FROM artworks a WHERE a.id IN(SELECT artwork_id FROM artwork_artists WHERE artist_id=%s) OR unlinked_creator_label ILIKE %s OR current_institution_id=ANY(%s::uuid[])",(AID,'%liebermann%',mids)).fetchall()
            ids=[x['a']['id']for x in existing];refs=[];cites=[];links=[]
            for i in range(0,len(ids),2000):
                batch=ids[i:i+2000]
                refs+=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])",(batch,)).fetchall()
                cites+=db.execute("SELECT entity_id::text,source_url FROM citations WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])",(batch,)).fetchall()
                links+=db.execute('SELECT artwork_id::text,artist_id::text FROM artwork_artists WHERE artwork_id=ANY(%s::uuid[])',(batch,)).fetchall()
            r.save_gz(RUN/'scoped-collision-snapshot.json.gz',dict(existing=existing,refs=refs,cites=cites,links=links))
            r.save(RUN/'scope-query-plan.json',db.execute('EXPLAIN (FORMAT JSON) SELECT id FROM artworks WHERE current_institution_id=ANY(%s::uuid[])',(mids,)).fetchone())
    byurl=collections.defaultdict(set);byacc=collections.defaultdict(set);bytitle=collections.defaultdict(list);byid={x['a']['id']:x['a']for x in existing};linked={x['artwork_id']for x in links if x['artist_id']==AID}
    for x in refs:byurl[urlkey(x['canonical_url'])].add(x['entity_id'])
    for x in cites:byurl[urlkey(x['source_url'])].add(x['entity_id'])
    for a in byid.values():
        if a['current_institution_id']and a['accession_number']:byacc[invkey(a['current_institution_id'],a['accession_number'])].add(a['id'])
        if a['id']in linked or'liebermann'in(a['unlinked_creator_label']or'').lower():bytitle[b.q.norm(a['title'])].append(a)
    # Authoritative described-at URLs add translation-independent identity leads.
    q_byurl=collections.defaultdict(set)
    for x in load('wikidata-records.json'):
        for url in x['described_at']:q_byurl[urlkey(url)].add(x['source_id'])
    accepted=[];present=[];seen=set()
    for row in rows:
        config=CONFIG[row['source']];key=urlkey(row['source_url']);qids=q_byurl[key]
        matches=set(byurl[key])|byacc[invkey(config[1],row['accession'])]
        # Same translated title, creator, date, and Pinakothek collection; do not
        # create a second painting merely because the earlier row has no inventory.
        known_translations={'pinakothek/A9xlemlLWv':'81d4e661-38c4-55e2-b401-2b9d2e574ce7','pinakothek/JzG6zKEGWO':'1689d74f-f07e-51d5-be72-b7eca3584448'}
        if key in known_translations:
            target=known_translations[key];assert target in byid
            assert byid[target]['creation_year_start']==row['creation_year_start']
            matches.add(target)
        for qid in qids:matches|=byurl['wikidata/'+qid]
        row.update(institution_id=config[1],source_scheme=config[2],provider=config[0],wikidata_identity_leads=sorted(qids))
        if matches:
            present.append(dict(record=row,existing_ids=sorted(matches),reason='existing_native_identity'if len(matches)==1 else'identity_conflict'));continue
        repeats=[a for a in bytitle[row['normalized_title']]if not a['accession_number']and a['work_type']==row['work_type']and(a['creation_year_start']is None or row['creation_year_start']is None or a['creation_year_start']<=row['creation_year_end']and row['creation_year_start']<=a['creation_year_end'])]
        if repeats:
            held.append(dict(source=row['source'],source_url=row['source_url'],reason='same_creator_title_version_needs_review',existing_ids=[a['id']for a in repeats],record=row));continue
        unit=invkey(config[1],row['accession'])
        if unit in seen:
            held.append(dict(source=row['source'],source_url=row['source_url'],reason='same_native_inventory_in_source',record=row));continue
        seen.add(unit);row.update(id=uid('artwork/'+config[0]+'/'+row['source_id']),slug='liebermann-'+config[0]+'-'+re.sub('[^a-zA-Z0-9]+','-',row['source_id']).strip('-').lower())
        accepted.append(row)
    p=dict(at=d.now(),artist=artist,rows=accepted,present=present,held=held,configuration=CONFIG,local_database_connected=False,policy='Direct museum object pages/open-data records; exact creator roles; native IDs and inventory numbers; review status. Reproductions, other makers, owned/depicted-only records and inseparable book/verso units held. Original dates and unknowns retained. No images downloaded or attached. No on-view claims.')
    r.save_gz(RUN/'plan-reviewed-draft-v3.json.gz',p)
    print(json.dumps(dict(accepted=len(accepted),by_source=collections.Counter(x['source']for x in accepted),present=len(present),held=collections.Counter(x['reason']for x in held),unknown_dates=sum(x['creation_year_start']is None for x in accepted)),ensure_ascii=False),flush=True)

def validate(p):
    rows=p['rows'];assert rows and len({x['id']for x in rows})==len(rows)
    assert len({(x['institution_id'],d.norm(x['accession']))for x in rows})==len(rows)
    for x in rows:
        assert x['source_url'].startswith('https://')and x['title']and x['accession']
        assert x['date_display']!='(1847-1935)'
        assert x['creation_year_end']is None or x['creation_year_end']<=1970
        assert x['work_type']in ['painting','drawing','watercolor','print']
        _,reason=normalize(x['raw']);assert reason is None,(x['source_url'],reason)
        if x['source']=='Hamburger Kunsthalle':assert not x['source_id'].startswith('kb-')
        if x['source']=='ALBERTINA':assert not re.fullmatch(r'\d+v',x['accession'])
    assert len({x['artwork_id']for x in p['link_existing']})==len(p['link_existing'])

def review():
    p=load('plan-reviewed-draft-v3.json.gz');e=load('existing.json.gz');wd=load('wikidata-details.json')['entities'];cites=load('unlinked-citations.json.gz');snaps=load('unlinked-snapshots.json.gz')
    p['link_existing']=[]
    for item in e['raw_labels']:
        a=item['artwork'];wid=a['id']
        if a['status']=='archived'or(a['unlinked_creator_label']or'').lower().strip()!='max liebermann':continue
        if snaps[wid]['creators']:continue
        for cite in cites:
            if cite['entity_id']!=wid:continue
            qid=cite['source_url'].rsplit('/',1)[-1];claims=wd.get(qid,{}).get('claims',{}).get('P170',[])
            if len(claims)!=1 or claims[0].get('qualifiers')or claims[0].get('rank')=='deprecated':continue
            if claims[0]['mainsnak'].get('datavalue',{}).get('value',{}).get('id')!='Q158062':continue
            p['link_existing'].append(dict(artwork_id=wid,title=a['title'],source_url=cite['source_url'],qid=qid,claim=claims[0],before=snaps[wid]));break
    assert len(p['link_existing'])==10
    p['review_notes']=['Library volume components and separately indexed verso records held; no count inflation.', 'Pinakothek dates taken from artwork title block, never artist life dates.', 'Two translated Pinakothek titles reconciled to existing WikiArt records.', 'Ten unlinked records have one unqualified Wikidata creator claim Q158062 and no existing artist links.', 'Prints with distinct museum inventories remain separate physical impressions; this is not a count of unique compositions.']
    validate(p);r.save_gz(RUN/'reviewed-plan.json.gz',p)
    BACKUP.mkdir(parents=True,exist_ok=True);backup=json.loads(Path('/tmp/artline-liebermann-20261011/cloud-backup.json').read_text());assert backup['status']=='SUCCESSFUL'and backup['description']==OP.replace('20261011','artwork-expansion-20261011')
    r.save(BACKUP/'cloud-backup.json',backup)
    print(json.dumps(dict(new=len(p['rows']),link_existing=len(p['link_existing']),types=collections.Counter(x['work_type']for x in p['rows']),unknown_dates=sum(x['creation_year_start']is None for x in p['rows'])),ensure_ascii=False),flush=True)

def collisions(db,rows):
    ids=[x['id']for x in rows];urls=[x['source_url']for x in rows];slugs=[x['slug']for x in rows]
    direct=db.execute('SELECT id::text,slug FROM artworks WHERE id=ANY(%s::uuid[]) OR slug=ANY(%s)',(ids,slugs)).fetchall()
    refs=db.execute("SELECT entity_id::text,scheme,external_id,canonical_url FROM external_identifiers WHERE entity_type='artwork'AND canonical_url=ANY(%s)",(urls,)).fetchall()
    native=db.execute("SELECT e.entity_id::text,e.scheme,e.external_id FROM unnest(%s::text[],%s::text[]) q(scheme,native) JOIN external_identifiers e ON e.scheme=q.scheme AND e.external_id=q.native",([x['source_scheme']for x in rows],[x['source_id']for x in rows])).fetchall()
    acc=db.execute('SELECT a.id::text,a.title,a.current_institution_id::text,a.accession_number FROM artworks a JOIN unnest(%s::uuid[],%s::text[]) q(institution,inventory) ON a.current_institution_id=q.institution AND a.accession_number=q.inventory',([x['institution_id']for x in rows],[x['accession']for x in rows])).fetchall()
    return dict(direct=direct,urls=refs,native=native,inventory=acc)

def preflight():
    p=load('reviewed-plan.json.gz');validate(p);pin=r.sha((RUN/'reviewed-plan.json.gz').read_bytes())
    with r.connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        conflicts=collisions(db,p['rows']);assert not any(conflicts.values()),conflicts
        old=load('existing.json.gz');ids=[x['artwork']['id']for x in old['rows']]
        current=b.s.snapshots(db,ids);assert len(current)==p.get('baseline_count',109)
        for item in old['rows']:assert current[item['artwork']['id']]['artwork']==item['artwork']
        for item in p['link_existing']:assert b.s.snapshots(db,[item['artwork_id']])[item['artwork_id']]==item['before']
        count=db.execute("SELECT count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'",(AID,)).fetchone()['n'];assert count==p.get('baseline_count',109)
        r.save_gz(BACKUP/'preflight-existing.json.gz',current)
        query_plan=db.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) SELECT a.id FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s',(AID,)).fetchone()
    r.save(RUN/'preflight.json',dict(at=d.now(),plan_sha256=pin,conflicts=conflicts,existing_count=count,query_plan=query_plan,local_database_connected=False))
    print('Preflight passed; pinned plan '+pin,flush=True)

def evidence(row,pin):
    x=row['raw'];return dict(operation=OP,plan_sha256=pin,identity_basis='Exact museum object and creator role; native inventory and source URL checked against existing catalogue.',source_creator=x.get('creator'),source_creator_roles=x.get('creator_roles'),native_inventory=row['accession'],literal_date=row['date_display'],original_object_type=x.get('work_type'),physical_unit_note=row.get('physical_unit_note'),source_receipt=x.get('receipt'),source_rights_label=x.get('rights_label')or x.get('rights'),selection='Documented museum object. Review status, unknown dates retained; no masterpiece or current-display assertion. No image attached.')

def apply():
    from psycopg.types.json import Jsonb
    p=load('reviewed-plan.json.gz');validate(p);pin=r.sha((RUN/'reviewed-plan.json.gz').read_bytes());assert load('preflight.json')['plan_sha256']==pin
    assert r.load(BACKUP/'cloud-backup.json')['status']=='SUCCESSFUL'
    ids=[x['id']for x in p['rows']];old=r.load(BACKUP/'preflight-existing.json.gz');marker=uid('applied');linkids=[x['artwork_id']for x in p['link_existing']]
    with r.connect('production',readonly=False)as db,db.transaction():
        db.execute("SET LOCAL lock_timeout='90s'");db.execute("SELECT pg_advisory_xact_lock(hashtext('artline-curated-ingestion'))")
        db.execute("SELECT set_config('artline.actor_user_id',%s,true)",(ACTOR,))
        previous=db.execute('SELECT after_json FROM audit_log WHERE id=%s',(marker,)).fetchone()
        if previous:
            result=previous['after_json'];assert result['plan_sha256']==pin
        else:
            assert not any(collisions(db,p['rows']).values())
            assert db.execute('SELECT to_jsonb(a) a FROM artists a WHERE id=%s FOR SHARE',(AID,)).fetchone()['a']==p['artist']
            assert b.s.snapshots(db,list(old))==old
            for x in p['link_existing']:
                db.execute('SELECT id FROM artworks WHERE id=%s FOR UPDATE',(x['artwork_id'],))
                assert b.s.snapshots(db,[x['artwork_id']])[x['artwork_id']]==x['before']
            r.save_gz(BACKUP/'locked-link-preimages.json.gz',{x['artwork_id']:x['before']for x in p['link_existing']})
            for source,config in p['configuration'].items():
                provider=config[0];row=next((x for x in p['rows']if x['source']==source),None)
                if row:db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page',%s)",(uid('source/'+provider),OP+'-'+provider,source+' — Max Liebermann source review, 11 October 2026',urlsplit(row['source_url'])._replace(path='',query='',fragment='').geturl()+'/'))
            db.execute("INSERT INTO sources(id,slug,name,source_type,base_url) VALUES(%s,%s,%s,'collection_page','https://www.wikidata.org/')",(uid('source/wikidata'),OP+'-wikidata','Wikidata — Max Liebermann creator reconciliation, 11 October 2026'))
            with db.pipeline():
                for x in p['rows']:
                    wid=x['id'];sid=uid('source/'+x['provider']);note=json.dumps(evidence(x,pin),ensure_ascii=False)
                    db.execute("""INSERT INTO artworks(id,slug,title,normalized_title,date_display,creation_year_start,creation_year_end,date_precision,work_type,medium_text,dimensions_text,accession_number,current_institution_id,status,research_candidate,created_by,updated_by)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'review',true,%s,%s)""",tuple(x[k]for k in ['id','slug','title','normalized_title','date_display','creation_year_start','creation_year_end','date_precision','work_type','medium','dimensions','accession','institution_id'])+(ACTOR,ACTOR))
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(wid,AID,'Direct museum creator attribution; native object and original creator roles preserved in source citation.'))
                    db.execute("INSERT INTO external_identifiers(entity_type,entity_id,scheme,external_id,canonical_url,source_id,retrieved_at) VALUES('artwork',%s,%s,%s,%s,%s,%s)",(wid,x['source_scheme'],x['source_id'],x['source_url'],sid,p['at']))
                    db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'museum_object_identity_and_holding',%s,%s,%s,%s,%s)",(uid('citation/'+wid),wid,sid,x['source_id'],x['source_url'],note,p['at'],ACTOR))
                    db.execute("INSERT INTO artwork_location_assertions(id,artwork_id,claim_type,institution_id,context,source_id,source_url,evidence_note,checked_at,review_state) VALUES(%s,%s,'holding',%s,'collection',%s,%s,%s,%s,'accepted')",(uid('holding/'+wid),wid,x['institution_id'],sid,x['source_url'],'Museum catalogue inventory '+x['accession']+'. Collection association only; current display is unknown.',p['at']))
                for x in p['link_existing']:
                    db.execute("INSERT INTO artwork_artists(artwork_id,artist_id,attribution_role,attribution_note) VALUES(%s,%s,'primary',%s)",(x['artwork_id'],AID,'Existing literal Max Liebermann label reconciled to Q158062 using the same object Wikidata creator statement.'))
                    db.execute("INSERT INTO citations(id,entity_type,entity_id,source_id,field_name,source_record_id,source_url,evidence_note,retrieved_at,created_by) VALUES(%s,'artwork',%s,%s,'verified_creator_reconciliation',%s,%s,%s,%s,%s)",(uid('link-citation/'+x['artwork_id']),x['artwork_id'],uid('source/wikidata'),x['qid'],x['source_url'],json.dumps(dict(operation=OP,plan_sha256=pin,claim=x['claim'],original_creator_label='Max Liebermann',changes='Added artist relationship only; metadata, image, status and holdings retained.'),ensure_ascii=False),p['at'],ACTOR))
            assert b.s.snapshots(db,list(old))==old
            post=b.s.snapshots(db,ids+linkids);assert len(post)==len(ids)+len(linkids)
            for x in p['rows']:
                a=post[x['id']]['artwork'];assert a['status']=='review'and a['research_candidate']and a['primary_media_id']is None and a['published_at']is None
                assert a['current_institution_id']==x['institution_id']and a['creation_year_start']==x['creation_year_start']and a['creation_year_end']==x['creation_year_end']
                assert len(post[x['id']]['creators'])==1 and post[x['id']]['creators'][0]['artist_id']==AID
                assert len(post[x['id']]['locations'])==1 and not post[x['id']]['attachments']
            for x in p['link_existing']:
                a=post[x['artwork_id']];before=x['before'];assert a['artwork']==before['artwork']and a['locations']==before['locations']and a['attachments']==before['attachments']
                assert len(a['creators'])==1 and a['creators'][0]['artist_id']==AID
            count=db.execute("SELECT count(DISTINCT a.id) n FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=%s AND a.status<>'archived'",(AID,)).fetchone()['n'];assert count==p.get('baseline_count',109)+len(ids)+len(linkids)
            r.save_gz(BACKUP/'transaction-postimages.json.gz',post)
            result=dict(at=d.now(),plan_sha256=pin,artist_id=AID,slug=p['artist']['slug'],before=p.get('baseline_count',109),added=len(ids),linked_existing=len(linkids),after=count,new_ids=ids,linked_ids=linkids,images_attached=0,local_database_connected=False,existing_records_preserved=True)
            db.execute("INSERT INTO audit_log(id,actor_user_id,action,entity_type,entity_id,after_json) VALUES(%s,%s,'verified_museum_creator_expansion','artist',%s,%s)",(marker,ACTOR,AID,Jsonb(result)))
    r.save(RUN/'applied.json',result);print(json.dumps({k:v for k,v in result.items()if k not in ['new_ids','linked_ids']},ensure_ascii=False),flush=True)

def verify():
    import requests
    p=load('reviewed-plan.json.gz');a=load('applied.json');validate(p);assert a['plan_sha256']==r.sha((RUN/'reviewed-plan.json.gz').read_bytes())
    with r.connect('production')as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        post=b.s.snapshots(db,a['new_ids']+a['linked_ids']);assert post==r.load(BACKUP/'transaction-postimages.json.gz')
        old=r.load(BACKUP/'preflight-existing.json.gz');assert b.s.snapshots(db,list(old))==old
        cites=db.execute("SELECT entity_id::text,source_record_id,source_url,evidence_note FROM citations WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])",(a['new_ids'],)).fetchall();assert len(cites)==a['added']
        for c in cites:assert json.loads(c['evidence_note'])['plan_sha256']==a['plan_sha256']
    found={};pages=[];cursor=None
    for _ in range(50):
        params=dict(limit=50)
        if cursor:params['cursor']=cursor
        res=requests.get('https://artlines.org/api/backend/v1/artists/'+a['slug']+'/works',params=params,timeout=(15,90));res.raise_for_status();data=res.json();assert len(data['items'])<=50
        pages.append(dict(url=res.url,status=res.status_code,data=data))
        for item in data['items']:assert item['id']not in found;found[item['id']]=item
        nxt=data.get('next_cursor')
        if not nxt:break
        assert nxt!=cursor;cursor=nxt
    else:raise AssertionError('Unbounded pagination')
    assert len(found)==a['after']and set(a['new_ids']+a['linked_ids'])<=set(found)
    for x in p['rows']:
        item=found[x['id']];assert item['title']==x['title']and item['creation_year_start']==x['creation_year_start']and item['creation_year_end']==x['creation_year_end']and item['status']=='review'
    r.save_gz(RUN/'public-verification-pages.json.gz',pages)
    proof=dict(at=d.now(),before=a['before'],added=a['added'],linked_existing=a['linked_existing'],after=a['after'],api_pages=len(pages),public_ids_verified=len(found),existing_metadata_images_and_status_preserved=True,new_images=0,local_database_connected=False)
    r.save(RUN/'verification.json',proof);print(json.dumps(proof),flush=True)

def report():
    p=load('reviewed-plan.json.gz');proof=load('verification.json');a=load('applied.json');register=[];pages_file='public-verification-pages.json.gz'
    if (RUN/'smk-supplement/verification.json').exists():
        supplemental=load('smk-supplement/reviewed-plan.json.gz');resolved={x['source_url']for x in supplemental['rows']}
        p['rows']+=supplemental['rows'];p['held']=[x for x in p['held']if x['source_url']not in resolved]
        proof=load('smk-supplement/verification.json');pages_file='smk-supplement/public-verification-pages.json.gz'
    for x in p['rows']:register.append(dict(record=x,decision='added_to_production',artline_ids=x['id'],reason='Verified direct museum object and creator role'))
    for x in p['present']:register.append(dict(record=x['record'],decision='existing_record',artline_ids='; '.join(x['existing_ids']),reason=x['reason']))
    for x in p['held']:register.append(dict(record=x['record'],decision='held_for_research',artline_ids='; '.join(x.get('existing_ids',[])),reason=x['reason']))
    for file in ['wikiart-records.json','wikidata-records.json','buchheim-records.json']:
        for x in load(file):register.append(dict(record=x,decision='discovery_register',artline_ids='',reason=x.get('error')or'Cross-source identity or physical unit requires reconciliation; not an additional unique-work count'))
    columns=['source','source_id','title','source_date','museum_or_collection','accession','source_url','decision','reason','artline_ids']
    entities=load('wikidata-details.json')['entities']
    with (RUN/'source-records.csv').open('w',newline='',encoding='utf-8-sig')as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
        for entry in register:
            x=entry['record'];date=x.get('date_display')or x.get('date')or''
            if x['source']=='Wikidata':date=json.dumps([v['mainsnak'].get('datavalue',{}).get('value')for v in entities.get(x['source_id'],{}).get('claims',{}).get('P571',[])],ensure_ascii=False)
            writer.writerow(dict(source=x['source'],source_id=x.get('source_id',''),title=x.get('title',''),source_date=date,museum_or_collection='; '.join(x.get('collections',[]))or x.get('collection_label')or(x['source']if x['source']not in ['WikiArt','Wikidata']else''),accession=x.get('accession')or'; '.join(x.get('accessions',[])),source_url=x['source_url'],decision=entry['decision'],reason=entry['reason'],artline_ids=entry['artline_ids']))
    public=[x for page in load(pages_file)for x in page['data']['items']];assert len(public)==proof['after']
    with (RUN/'artline-artworks.csv').open('w',newline='',encoding='utf-8-sig')as f:
        writer=csv.DictWriter(f,fieldnames=['id','title','date','work_type','medium','dimensions','inventory','artline_url','source_urls','has_image']);writer.writeheader()
        for x in sorted(public,key=lambda x:x['title'].casefold()):writer.writerow(dict(id=x['id'],title=x['title'],date=x['date_display'],work_type=x['work_type'],medium=x.get('medium_text'),dimensions=x.get('dimensions_text'),inventory=x.get('accession_number'),artline_url='https://artlines.org/artists/'+a['slug']+'/works/'+x['id'],source_urls='; '.join(sorted({c['source_url']for c in x['citations']})),has_image=bool(x.get('media_url'))))
    coverage=collections.defaultdict(collections.Counter)
    for x in register:coverage[x['record']['source']][x['decision']]+=1
    r.save(RUN/'coverage.json',dict(source_records=len(register),sources={k:dict(v)for k,v in coverage.items()},new_types=dict(collections.Counter(x['work_type']for x in p['rows'])),public_records=len(public),public_illustrated=sum(bool(x.get('media_url'))for x in public),new_images=0,unknown_dates_added=sum(x['creation_year_start']is None for x in p['rows'])))
    print(json.dumps(dict(source_records=len(register),artline_records=len(public),sources=len(coverage)),ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['plan','review','preflight','apply','verify','report']);args=parser.parse_args();globals()[args.action]()
