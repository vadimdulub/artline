#!/usr/bin/env python3
"""Exact WikiArt object/location reconciliation under the approved source policy."""
import collections,gzip,html,importlib.util,json,re,unicodedata,uuid
from pathlib import Path
from urllib.parse import unquote
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('task',ROOT/'ops/random-5000-museum-research-20261006.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r;RUN=m.RUN
def norm(v):return ' '.join(re.findall(r'[^\W_]+',''.join(c for c in unicodedata.normalize('NFKD',html.unescape(v or '').casefold())if not unicodedata.combining(c))))
def key(v):return re.sub(r'^the ','',norm(v))
def uid(v):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://artline.local/random-5000-museums-20261006/'+v))
def urlkey(v):return unquote(v or '').rstrip('/')

# Reviewed alternate forms of the same named creator; not fuzzy name matching.
CREATOR_ALIASES=[('Martiros Saryan','Martiros Sarian'),('Luis de Madrazo','Luis de Madrazo y Kuntz'),('Bronzino','Agnolo Bronzino'),('Élisabeth Vigée Le Brun','Louise Elisabeth Vigee Le Brun'),('Ivan Kramskoi','Ivan Kramskoy'),('Alexei Savrasov','Aleksey Savrasov'),('P. S. Krøyer','Peder Severin Kroyer'),('Giotto di Bondone','Giotto'),('Dieric Bouts','Dirk Bouts'),('Kunisada','Utagawa Kunisada'),('Andrea Solari','Andrea Solario')]
def creator_match(source,names):
    n=norm(source)
    return n in names or any(n in {norm(a),norm(b)} and bool(names & {norm(a),norm(b)})for a,b in CREATOR_ALIASES)

REVIEWED_MUSEUM_LABELS={'Barber Institute of Fine Arts, Birmingham, UK','Bavarian State Painting Collections, Munich, Germany','Broad MSU (Michigan State University), East Lansing, MI, US','Dayton Art Institute (DAI), Dayton, OH, US','Galleria Doria Pamphilj, Rome, Italy','Montgomery Musuem of  Fine Arts, Montgomery, AL, US','Museu Picasso, Barcelona, Spain','Staatliche Kunstsammlungen Dresden, Dresden, Germany','Wadsworth Atheneum, Hartford, CT, US'}
# Exact source museum labels independently reviewed; institutional primary sources
# are retained in wikiart-authority-review-*.json. No branch/display inference.
# Explicit translations, historical names and branch-to-collection identities.
ALIASES={
'Washington University Gallery of Art':'fc6130ff-fe94-57c7-8d2a-bcbc3895ed32',
'Château de Versailles':'f4eea5e8-e7ba-4843-b2c2-bda64513cfd1',
'Château de Compiègne':'299d2a0f-f9ac-4149-97a6-21cd980e853d',
"Galleria dell’Accademia":'135e0e91-2240-4466-96ff-243e8fc735ca',
"Galleria dell'Accademia, Venice":'135e0e91-2240-4466-96ff-243e8fc735ca',
'Musee des Beaux-Arts de Pau':'ca02311e-90c0-4715-b165-753d3b38de86',
'Museu de Belles Arts de València':'67a919aa-d026-4251-820b-4feb3152c0ab',
'Palais des Beaux-Arts de Lille':'64bc0dba-0ce8-4ed5-bd1f-3aec5433c767',
'Sukiennice Museum':'05e061a0-727a-567f-bd69-a4a7af2174d6',
'Art Museum of Georgia':'10206a6d-cc93-50af-b5b8-6359df746dc6',
'National Museum of Ancient Art':'e0b889ef-7ea0-4842-a33e-f830eb93ae20',
'Tula Regional Museum of Fine Arts':'62c42078-ddfb-5edf-a2eb-ade24253fe54',
'Beyeler Foundation':'96f44fc7-ef57-4633-86a4-674be51a3298',
'El Greco Museum':'298fc2b0-4bb9-4f34-9651-adef51ffeabf',
'Fogg Museum':'f94d0f6b-d6a7-5da2-afdf-e35a294b4e31',
'Kunsthalle Hamburg':'caca0946-ccfc-4f41-becc-fc3b18dbeb34',
'Lenbachhaus':'f0ffee7e-c66e-5dcf-9b10-5a8519849c7a',
'Lille Métropole Museum of Modern':'a7c167a4-ca30-4df6-a870-50af7ae5cb4e',
'Museum of Fine Arts, Ghent':'ee490c87-6dc6-4a7c-8f34-e70d2932a18b',
'National Art Gallery':'052007aa-11f7-4d57-90e6-d3b62bb0bf4b',
'National Gallery, London':'2c909ffb-2614-4273-b76b-a0daa2a74833',
'National Gallery, Oslo':'5f550b6e-7d78-4fab-89f5-5f54a9bc1241',
'National Museum, Kraków':'05e061a0-727a-567f-bd69-a4a7af2174d6',
'Ateneum':'688a05df-a339-5dde-9fd0-4263559553f1',
'Borghese Gallery':'9478435a-4e29-400c-9fa4-1878df5f570a',
'Budapest Museum of Fine Arts':'bd5b7c44-fc24-51a7-87d2-d6da437325fa',
'Christchurch Art Gallery Te Puna o Waiwhetū':'63c94333-5256-5816-9a06-b7d33a3c7bca',
'Courtauld Gallery':'918386ff-6ddd-4244-a2c0-c54f3a9cad97',
'Courtauld Institute of Art':'918386ff-6ddd-4244-a2c0-c54f3a9cad97',
'Gemäldegalerie, Berlin':'f6213ff5-c42a-4637-8dff-8d7d3f0c7a96',
'Georges Pompidou Center':'0e18909a-b205-5422-a72d-3e629b6bbd69',
'Groeningemuseum':'9d14eb57-dfe6-4170-ab36-63fde4ee12ba',
'Guimet Museum':'d08f1829-5457-4ba2-a27b-31e4c98fb43e',
'Imperial War Museum, London':'e147c124-583e-58d9-876f-d98f7ed0b5e2',
'Kunsthistorisches Museum':'fbc55862-f61c-4561-a0a0-eedf65674f62',
'Louvre':'355fdf89-aee5-4066-a0f3-fd4cfc2a13ae',
'Metropolitan Museum of Art':'a0673ec8-1b74-ebcb-0331-a1c021b793f6',
'Museo del Prado':'008d3646-ed41-4691-9a37-25a9fff40e51',
'Museum of Fine Arts (MFA), Boston':'e817808a-be18-5348-896e-358bed088ac3',
'Musée Bonnat':'15a692d3-dbd1-5540-a604-5d358ff8265f',
'Musée Condé':'4ea70372-bc67-4e43-bb4b-d3c00acf9cc9',
'Musée Rodin':'c6449110-59c8-435e-8af4-0ccf78008769',
"Musée d'Art Moderne de la Ville de Paris":'3bc44a21-55f7-58e7-acc3-2ae4d6184be5',
'Musée des Beaux-Arts de Dijon':'2fe6529c-3fe7-4d78-8f57-c1ff1b940951',
'Musée des Beaux-Arts de Nantes':'96bb93ac-60cf-4efa-923e-59929b640e10',
'National Gallery of Denmark':'ee9976cf-63a1-48f7-9e34-eb5444e0486c',
'National Museum of Capodimonte':'6ef6013f-6d3d-5aae-8666-621dcb83b401',
'National Museum, Warsaw':'6c8ae01a-f6a5-5591-9635-a4af407cd2dc',
'Neue Pinakothek':'33916550-59e8-4316-92d5-39c66ca12dfa',
'Palazzo Brera':'735f66cb-4b8b-4fbe-b238-d8cce44c845a',
'Petit Palais, Paris':'af70188f-bda2-5af1-8c5e-b323d987a0c3',
'Philips Collection':'45fba194-c280-51f1-965f-a135449ee1ad',
'Phillips Collection':'45fba194-c280-51f1-965f-a135449ee1ad',
'Sabauda Gallery':'96f06fb0-ff0c-5f84-bc6f-a3968a2c06f8',
'Stedelijk Museum':'f416ec8a-5aa6-5712-84c7-a5a88c38b185',
'Städel':'b71d242a-a538-441c-8d45-08a011570634',
'Tate Britain':'a1976c92-e516-4585-9c6e-c4e640f6a8e9',
'Tate Modern':'a1976c92-e516-4585-9c6e-c4e640f6a8e9',
'Thyssen-Bornemisza Museum':'eb9e002b-1d26-4996-9b58-d34a4c372fc3',
'Uffizi Gallery':'b18ea8d3-6192-1f8f-52e4-9db84250dffb',
'Yale Centre For British Art':'4effcd74-dc05-5866-923e-f7f3a4631d9d'}

def main():
    rows=r.load(RUN/'baseline.json.gz');wiki=r.load(RUN/'cached-wikiart-results-supplement.json.gz');institutions=r.load(RUN/'institutions.json.gz');byid={x['id']:x for x in institutions};auth=r.load(RUN/'cached-institution-authorities.json.gz');artists=r.load(RUN/'artists.json.gz');artisturls=collections.defaultdict(set)
    for x in artists['identifiers']:
        if x.get('canonical_url'):artisturls[x['entity_id']].add(x['canonical_url'].rstrip('/'))
    aliases={norm(k):v for k,v in ALIASES.items()};resolved={};heldinstitutions=[];new={}
    labels=sorted({p['fields']['Location']for x in wiki.values()for p in x['pages']if p['fields'].get('Location')})
    for label in labels:
        clean=re.sub(r'\([^)]*\)','',label);prefix=clean.split(',')[0].strip();reason=None;matches=[];basis=''
        if label.startswith('Hillman Family Foundation'):reason='documented_non_museum_private_foundation'
        elif label.startswith(('New Hermitage Gallery','Galerie Rosengart')):reason='museum_versus_commercial_gallery_identity_not_established'
        elif label.count(',')>=4:reason='multiple_museums_in_literal_source_label'
        elif re.search(r'private|unknown|destroyed',label,re.I):reason='private_collection_or_unknown_or_destroyed'
        elif re.search(r'\bchurch\b|chapel|basilica|cathedral|monastery|mausoleum|santa maria|secretariat|palazzo apostolico|palazzo grimani|prague castle|royal castle|vorontsov|biblioteca',label,re.I):reason='documented_non_museum_site_or_collection_requires_separate_site_review'
        elif re.search(r'oskar reinhart',label,re.I):reason='institution_branch_identity_requires_individual_review'
        elif re.search(r'horlivka|sevastopol|roerich museum, moscow|rudolph staechelin',label,re.I):reason='historical_or_changed_collection_custody_requires_current_authority_review'
        if not reason:
            chosen=[(a,i)for a,i in aliases.items()if norm(clean)==a or norm(clean).startswith(a+' ')or norm(label)==a or norm(label).startswith(a+' ')]
            if chosen:
                chosen.sort(key=lambda x:-len(x[0]));matches=[byid[chosen[0][1]]];basis='Reviewed source-name translation or branch-to-collection identity; literal WikiArt label retained.'
            else:
                generic=key(prefix)in {'national gallery','national portrait gallery','national museum','museum of fine arts'}
                matchkeys={key(clean),key(label)}if generic else {key(clean),key(prefix),key(label),key(label.split(',')[0])}
                exact={x['id']:x for x in institutions if key(x['name'])in matchkeys}
                if len(exact)==1:matches=list(exact.values());basis='Exact normalized institution name; source city/country retained.'
                elif len(exact)>1:reason='multiple_existing_institution_name_matches'
            if not matches and not reason:
                # A full label with city/country disambiguates a new authority;
                # it does not supply invented coordinates, website or Wikidata ID.
                museum=label in REVIEWED_MUSEUM_LABELS or bool(re.search(r'museum|musée|museo|gallery|galerie|pinakothek|kunsthalle|kunsthistor|lenbachhaus|sprengel|guggenheim|fondation|foundation|beyeler|menil|frick|gemeentemuseum|palazzo colonna',label,re.I))
                if not museum:reason='institution_identity_requires_individual_review'
                else:
                    possibilities=[]
                    for q,v in auth.items():
                        e=v['entity'];names={key(z['value'])for z in e.get('labels',{}).values()}|{key(z['value'])for zz in e.get('aliases',{}).values()for z in zz}
                        generic=key(prefix)in {'national gallery','national portrait gallery','national museum','museum of fine arts'}
                        if (not generic and key(prefix)in names)or key(clean)in names:possibilities.append(q)
                    existing=[x for x in institutions if x.get('wikidata_id')in possibilities]
                    if len(existing)==1:matches=existing;basis='Exact source museum-name/alias reconciled through cached Wikidata authority to existing institution ID.'
                    elif existing:reason='multiple_institution_authorities_match'
                    else:
                        i={'id':uid('institution/'+norm(label)),'slug':'museum-source-'+r.sha(label.encode())[:20],'name':label,'normalized_name':norm(label),'website_url':None,'wikidata_id':None,'kind':'foundation'if re.search(r'foundation|beyeler',label,re.I)else 'museum','status':'review','description':'Named museum collection documented by the approved WikiArt source. Literal source city/country retained in the name; no physical whereabouts or current-display claim. Institution authority remains in review.','canonical_institution_id':None}
                        matches=[i];new[i['id']]=i;basis='New review institution using the full explicit source museum label; no guessed website, coordinates or external authority.'
            if matches:
                i=matches[0];i=byid.get(i.get('canonical_institution_id'),i);resolved[label]={'institution':i,'basis':basis}
        if reason:heldinstitutions.append({'label':label,'reason':reason})
    claims=[];outcomes=[]
    for aid,row in rows.items():
        a=row['artwork'];pages=wiki[aid]['pages'];found=[];issues=[]
        for p in pages:
            loc=p['fields'].get('Location')
            if not loc:continue
            if loc not in resolved:issues.append(next(x['reason']for x in heldinstitutions if x['label']==loc));continue
            if loc.startswith('Kunsthistorisches Museum') and p['fields'].get('Genre')=='sculpture':issues.append('museum_department_authority_requires_review');continue
            ids={e['external_id']for e in row['identifiers']if e['scheme']=='wikiart-artwork'and urlkey(e.get('canonical_url'))==urlkey(p['url'])}
            raw=(ROOT/p['capture']['body_path']).read_bytes();raw=gzip.decompress(raw)if p['capture']['body_path'].endswith('.gz')else raw;text=raw.decode('utf-8','replace')
            native=set(re.findall(r"trackPageView\('painting',\s*'([a-f0-9]{24})'",text))
            names={norm(x['name'])for x in row['creator_keys']}|{norm(a.get('unlinked_creator_label'))};artisturl=p['url'].rsplit('/',1)[0]
            titleok=norm(p['title'])in {norm(a['title']),norm(a.get('alternate_title'))}
            tradition=not row['creators'] and a.get('unlinked_creator_label')=='Creator not recorded' and p['artist'] in {'Fayum portrait','Orthodox Icons'}
            creatorok=creator_match(p['artist'],names) or any(artisturl in artisturls[x['artist_id']]for x in row['creators']) or tradition
            if len(ids)!=1 or ids!=native or urlkey(p['canonical'])!=urlkey(p['url'])or not titleok or not creatorok:issues.append('exact_source_object_title_creator_identity_requires_review');continue
            if re.search(r'\bprint\b|etching|engraving|lithograph|woodcut|woodblock|screenprint|linocut|aquatint',p['fields'].get('Media',''),re.I)or a['work_type']=='print':issues.append('specific_print_impression_requires_inventory_or_version_evidence');continue
            if aid in {'2c89d7b8-94e1-5424-a753-9d62790d8173','432c03e8-6ca6-5a47-8710-2b372098d1f9','5e6930b3-9bb4-582e-b7af-ad1e76c07808'}:issues.append('replica_or_maquette_version_not_resolved');continue
            info=resolved[loc];rc=r.load(ROOT/p['capture']['receipt_path']);assert rc.get('status',rc.get('status_code',200))==200
            evidence={'artwork_id':aid,'page':p,'institution_resolution':info['basis'],'source_policy':'WikiArt source approval, AGENTS.md and docs/ARTLINE_IMAGE_USE.md, 6 October 2026','native_id_verified':next(iter(ids)),'title_and_creator_verified':True,'unknown_or_conflicting_dates_preserved':True}
            found.append({'artwork_id':aid,'title':a['title'],'scheme':'wikiart-artwork','external_id':next(iter(ids)),'institution':info['institution'],'source_url':p['url'],'checked_at':p['capture']['retrieved_at'],'location_text':info['institution']['name'],'identity_basis':'Exact existing WikiArt native ID, canonical object URL, title and creator; explicit source Location matched to reviewed museum authority.','source_class':'user_approved_wikiart_catalogue','source_receipt':rc,'object_evidence':evidence,'claim_type':'holding','review_state':'accepted','limitation':'Source-documented museum collection connection only. Literal WikiArt location label retained; no physical whereabouts, legal ownership or current-display claim. Original artwork dates, creators, images and publication state preserved.'})
        if len({c['institution']['id']for c in found})>1:issues.append('conflicting_museums_on_exact_source_pages');found=[]
        if found:claims.append(found[0]);code='supported_wikiart_museum_holding'
        elif issues:code=issues[0]
        elif pages:code='wikiart_page_has_no_location'
        elif wiki[aid]['known_wikiart_urls']:code='known_wikiart_page_not_in_captured_sources'
        else:code='no_existing_wikiart_object_crosswalk'
        outcomes.append({'artwork_id':aid,'outcome':code,'issues':issues,'source_urls':[p['url']for p in pages],'source_locations':[p['fields']['Location']for p in pages if p['fields'].get('Location')]})
    r.save_gz(RUN/'wikiart-holding-plan-v5.json.gz',{'at':r.now(),'claims':claims,'outcomes':outcomes,'new_institutions':[i for i in new.values()if any(c['institution']['id']==i['id']for c in claims)],'institution_resolutions':resolved,'institution_holds':heldinstitutions,'supersedes':'wikiart-holding-plan-v4.json.gz; official Museofile and MNK branch evidence resolves Lille and Sukiennice; sculpture excluded from painting-department authority. See manual-primary-and-authority-review.json.'})
    print('WikiArt candidates',len(claims),'new institution authorities',len({c['institution']['id']for c in claims if c['institution']['id']in new}),'outcomes',dict(collections.Counter(x['outcome']for x in outcomes)),flush=True)

if __name__=='__main__':main()
