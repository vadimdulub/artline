#!/usr/bin/env python3
"""Bounded, individually reviewed museum selections across historical presets.

No collection crawl, publication, artist invention or current-display assertions.
Preserves source intervals/qualifiers, checks exact identities and parent accessions,
and uses the shared pinned-plan, image-review, backup and atomic-import workflow.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('core', Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
core.CAMPAIGN = 'period-images-20260926'
core.SOURCE_LABEL = 'Historical period artwork selections'
core.RUN = core.ROOT / 'docs/research' / core.CAMPAIGN
core.BACKUP = core.DATA / 'backups' / core.CAMPAIGN
core.ORIGINALS = core.DATA / 'source-images' / core.CAMPAIGN
core.MIGRATION = '0029_textile_photograph_types.sql'
core.PROVIDERS = {'cleveland': core.PROVIDERS['cleveland'],
    'nga': {'name': 'National Gallery of Art, Washington', 'slug': 'national-gallery-of-art',
        'api': 'https://www.nga.gov/', 'policy': 'https://www.nga.gov/terms-and-notices', 'source_type': 'collection_page'}}
core.COUNTRIES = {
    'IQ': ('Iraq','western-asia'), 'IT': ('Italy','southern-europe'), 'GR': ('Greece','southern-europe'),
    'PK': ('Pakistan','southern-asia'), 'AF': ('Afghanistan','southern-asia'), 'IN': ('India','southern-asia'),
    'JP': ('Japan','eastern-asia'), 'TH': ('Thailand','south-eastern-asia'), 'CN': ('China','eastern-asia'),
    'EG': ('Egypt','northern-africa'), 'TR': ('Türkiye','western-asia'), 'IR': ('Iran','southern-asia'),
    'ML': ('Mali','western-africa'), 'DE': ('Germany','western-europe'), 'NL': ('Netherlands','western-europe'),
    'GB': ('United Kingdom','northern-europe'), 'FR': ('France','western-europe'), 'US': ('United States','northern-america'),
    'PE': ('Peru','south-america'), 'MX': ('Mexico','central-america')}
# Geographic assignments are reviewed here, never inferred from an artist's life.
# Classical cultural labels with no unambiguous modern origin remain unassigned.
GROUPS = [
 ('writing', 'IQ', [151962,145396,138765,150548,154651,155583], 'Sumerian sculpture and ritual objects from the early urban societies of Mesopotamia.'),
 ('classical', 'IT', [155665,110232], 'Classical vase painting and funerary sculpture from southern Italy and Rome.'),
 ('classical', 'GR', [130360], 'Archaic Greek figure sculpture.'),
 ('classical', None, [146147,124135,161695], 'Greek and Etruscan visual culture; cultural identity does not establish a modern manufacture country.'),
 ('buddhism', 'PK', [147010,135485], 'Gandharan Buddhist figures and narrative relief.'),
 ('buddhism', 'AF', [143465], 'Buddhist sculpture from Hadda; the museum qualifies the precise site as probable.'),
 ('buddhism', 'IN', [144058,145408], 'Buddhist figure sculpture from Uttar Pradesh and Mathura.'),
 ('buddhism', 'JP', [128067], 'Asuka-period Japanese Miroku, showing the spread of Buddhist imagery.'),
 ('buddhism', 'TH', [147403], 'Dvaravati-style Buddhist sculpture; Shri Thep is a probable origin.'),
 ('byzantium', 'EG', [143165,151044,128462], 'Byzantine Egyptian textiles with Christian subjects; Egypt remains the recorded object origin.'),
 ('byzantium', 'TR', [107310,145192,106709], 'Byzantine ivory carving and metalwork from Constantinople, modern Istanbul.'),
 ('islamic-learning', 'IR', [124071,98300,128300], 'Seljuq ceramic decoration: courtly figures, luster and mina’i painting.'),
 ('mongol', 'IR', [106697,95046,117487,152587], 'Ilkhanid-period Iranian ceramics, carved decoration and patterned textile.'),
 ('mongol', 'CN', [137198], 'Yuan-dynasty Jingdezhen ceramic with lion-head handles.'),
 ('tang-song', 'CN', [147576,159163,147003,145411,151541,139824,135836,113945,149956], 'Tang and Song visual culture: mirrors, Buddhist sculpture, courtly life, poetry and landscape painting.'),
 ('sahel', 'ML', [152343], 'Inland Niger Delta figure, possibly 1300s–1600s; the museum’s probable Djenné-Djenno attribution is retained.'),
 ('mughal', 'IN', [170835,146184,170812,170849,170851,170786,170803], 'Mughal court painting, historical narrative and Persianate literary subjects; source creator labels and date ranges preserved.'),
 ('silk-roads', 'IR', [127878], 'Iranian samite textile with patterned roundels, relevant to the exchange of luxury textiles.'),
 ('silk-roads', 'CN', [156106], 'Jin-dynasty brocade, relevant to the textile traditions of the overland exchange routes.'),
 ('reformation', 'DE', [135428,130377,107161], 'Cranach’s court and biblical subjects in the visual world of the northern Renaissance and Reformation.'),
 ('science', 'NL', [329329], 'Merian’s close observation of plant and insect life; the museum’s different display and numeric date forms are both preserved.'),
 ('enlightenment', 'GB', [158152,159273], 'Mezzotints after Joseph Wright: scientific discovery and skilled industrial labor. Engravers and the source painter retain distinct roles.'),
 ('french-revolution', 'FR', [162396], 'A study by David from the Napoleonic aftermath, contextual work by the selected Revolutionary artist, not a depiction of the Revolution.'),
 ('romanticism', 'FR', [114161,144964], 'Delacroix studies of the figure and costume; both sides of one sheet remain one accession.'),
 ('empire', 'FR', [149536], 'Gérôme’s Orientalist sculpture, presented as a European representation rather than an unmediated record of its subject.'),
 ('modernism', 'US', [166893], 'Cassatt’s study of modern domestic life, one sheet including its reverse.'),
 ('edo', 'JP', [126723,153622], 'Hokusai print and figure painting; the broad museum date interval of the painting is retained.'),
 ('first-world-war', 'DE', [138356], 'Kollwitz’s study of hardship in the interwar aftermath, preserving both sides as one work.'),
 ('second-world-war', 'GB', [166755], 'Nash’s 1934 photograph, contextual work by a selected war artist; not described as a wartime image.'),
 ('atlantic', 'PE', [441846], 'Chimú-Inka ceramic from the Central Andean north coast, spanning the era of Atlantic encounters.'),
 ('atlantic', 'MX', [155486], 'Pre-Columbian Mexican pendant, dated by the museum to before 1519; local visual culture at the time of European contact.'),
]
ARTISTS = {1280:'j-m-w-turner-q159758', 1643:'jacques-louis-david-q83155', 11961:'adolph-menzel-nga-2430',
    27479:'wikimedia-painter-q3568880'}
# Source IDs for the remaining linked artists are extracted from the reviewed
# exact selected records, then checked against these explicit identity pairs.
IDENTITIES = {'Lucas Cranach':'lucas-cranach-the-elder-q191748', 'Maria Sibylla Merian':'wikiart-artist-maria-sibylla-merian',
    'Eugène Delacroix':'eugene-delacroix-q33477', 'Mary Cassatt':'mary-cassatt-q173223',
    'Käthe Kollwitz':'kathe-kollwitz-nga-2141', 'Paul Nash':'paul-nash-nga-5074'}
TYPE = {'Painting':'painting','Drawing':'drawing','Print':'print','Sculpture':'sculpture','Ceramic':'ceramic',
    'Textile':'textile','Silver':'metalwork','Metalwork':'metalwork','Ivory':'sculpture','Photograph':'photograph','Jewelry':'unknown'}
OWNER_CHOICES = {441846,155486,158152,159273,149536,144964}


def plan():
    objects = {}
    for f in sorted((core.RUN/'captures').glob('cma-*.json')):
        if f.name.endswith('.receipt.json'): continue
        receipt = json.loads(f.with_suffix(f.suffix+'.receipt.json').read_bytes())
        assert core.sha(f.read_bytes()) == receipt['sha256']
        for o in json.loads(f.read_bytes()).get('data',[]): objects.setdefault(o['id'], (o,receipt))
    records = []
    with core.connect() as db:
        institutions = {k: db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE slug=%s', (v['slug'],)).fetchone()['record'] for k,v in core.PROVIDERS.items()}
        artist_slugs = sorted(set(ARTISTS.values())|set(IDENTITIES.values())|{'kazimir-malevich-q130777'})
        artists = db.execute('SELECT to_jsonb(a) record FROM artists a WHERE slug=ANY(%s) ORDER BY slug',(artist_slugs,)).fetchall()
        artist_ids = {r['record']['slug']:r['record']['id'] for r in artists}
        assert set(artist_slugs) == set(artist_ids)
        for preset,country,ids,reason in GROUPS:
            for oid in ids:
                o,receipt = objects[oid]
                assert o['share_license_status']=='CC0' and not o.get('copyright') and not o.get('rights_and_reproductions')
                assert o['legal_status']=='accessioned' and o['on_loan'] is False
                assert not o.get('cover_accession_number') and o['record_type'] in ('object','cover'), 'Child accession requires reconciliation'
                lo,hi = o['creation_date_earliest'],o['creation_date_latest']
                assert type(lo)==type(hi)==int and lo<=hi<=1970
                assert o['creation_date'] and 'not dated' not in o['creation_date']
                creators = [x for x in o.get('creators',[]) if x.get('use_in_caption') and x.get('role') != 'publisher']
                maker = '; '.join(' '.join(x for x in [cr.get('qualifier'),cr['description'].split(' (')[0],('('+cr['role']+')') if cr.get('role') not in (None,'artist') else None] if x) for cr in creators) or None
                linked = None
                primaries = [x for x in creators if not x.get('qualifier') and x.get('role')=='artist']
                if len(primaries)==1:
                    cr=primaries[0]; slug = ARTISTS.get(cr['id']) or IDENTITIES.get(cr['description'].split(' (')[0])
                    if slug: linked=artist_ids[slug]
                date=o['creation_date']; approximate=any(x in date for x in ('c.','probably','possibly'))
                key='cleveland-'+str(oid)
                c={'key':key,'provider':'cleveland','object_id':str(oid),'accession':o['accession_number'],'preset':preset,
                    'title':o['title'],'lo':lo,'hi':hi,'date_display':date,
                    'precision':('circa' if lo==hi else 'circa_range') if approximate else ('exact' if lo==hi else 'range'),
                    'type':TYPE[o['type']],'country':country,'culture':'; '.join(o['culture']),'place_display':'; '.join(o['culture']),
                    'maker':maker,'artist_id':linked,'url':o['url'],'image_url':o['images']['web']['url'],
                    'medium':o['technique'],'dimensions':o.get('measurements'),'credit':o['creditline'],'reason':reason,'object':o,'capture':receipt,
                    'institution_id':institutions['cleveland']['id'],'artwork_id':core.uid(key),'slug':'period-'+key,
                    'geography_note':'Country-level catalogue association from museum geography. Historical labels and qualified localities retained verbatim; no creator nationality or modern citizenship inferred.',
                    'scope_note':'One accession per object; no duplicate parts. Source attribution qualifiers and creator roles retained in object label and citation. Only an unqualified reconciled primary maker receives a primary artist link.'}
                assert not core.duplicate(db,c), 'Existing object '+key
                # Parent accessions must not already be represented by children.
                assert not db.execute("SELECT 1 FROM artworks WHERE current_institution_id=%s AND accession_number LIKE %s LIMIT 1",(c['institution_id'], c['accession']+'.%')).fetchone(), 'Existing accession parts '+key
                records.append(c)
        web=core.load('captures/nga-barnes-web.json'); policy=core.load('captures/nga-policy-image-web.json')
        assert '1995.77.6' in json.dumps(web) and 'public domain' in json.dumps(web) and 'Creative Commons Zero' in json.dumps(policy)
        key='nga-93945'
        c={'key':key,'provider':'nga','object_id':'93945','accession':'1995.77.6','preset':'russian-revolution',
            'title':'A Peasant Woman Goes for Water','lo':1913,'hi':1913,'date_display':'1913','precision':'exact','type':'print',
            'country':None,'culture':None,'place_display':None,'maker':None,'artist_id':artist_ids['kazimir-malevich-q130777'],
            'url':'https://www.nga.gov/artworks/93945-peasant-woman-goes-water',
            'image_url':'https://api.nga.gov/iiif/bb5f84a1-ca03-43b3-9b2f-d8902c39dd4a/full/%21800%2C800/0/default.jpg',
            'medium':'lithograph in black on wove paper','dimensions':'sheet: 13 x 12 cm (5 1/8 x 4 3/4 in.)',
            'credit':'Gift of Frank R. and Jeannette H. Eyerly; Courtesy National Gallery of Art, Washington',
            'reason':'Malevich’s pre-Revolution avant-garde print, dated 1913, within the preset’s documented earlier context.',
            'object':{'source_capture':'captures/nga-barnes-web.json','metadata':web},
            'capture':{'at':core.now(),'url':'https://www.nga.gov/artworks/93945-peasant-woman-goes-water','sha256':core.sha((core.RUN/'captures/nga-barnes-web.json').read_bytes()),'transport':'web indexed primary page; direct HTTP 403'},
            'institution_id':institutions['nga']['id'],'artwork_id':core.uid(key),'slug':'period-'+key}
        assert not core.duplicate(db,c);records.append(c)
        countries=db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code',(list(core.COUNTRIES),)).fetchall()
        places={}
        for code,(name,_) in core.COUNTRIES.items():
            matches=db.execute('SELECT to_jsonb(p) record FROM places p WHERE country_code=%s AND name=%s',(code,name)).fetchall()
            assert len(matches)<=1
            if matches: places[code]=matches[0]['record']
        collections=db.execute('SELECT to_jsonb(c) record FROM curated_collections c WHERE institution_id=%s ORDER BY curator_kind',(institutions['cleveland']['id'],)).fetchall()
        curated=[]; preimages=[]
        for item in collections:
            coll=item['record']; position=db.execute('SELECT COALESCE(max(position),0) n FROM curated_collection_items WHERE collection_id=%s',(coll['id'],)).fetchone()['n']
            selected=[c for c in records if c['provider']=='cleveland' and (c['object']['is_highlight'] if coll['curator_kind']=='museum' else int(c['object_id']) in OWNER_CHOICES)]
            if not selected:continue
            preimages.append({**item,'max_position':position})
            for n,c in enumerate(selected,position+1):
                curated.append({'collection_id':coll['id'],'artwork_id':c['artwork_id'],'position':n,
                    'reason':('Museum API explicitly marks this object as a highlight. ' if coll['curator_kind']=='museum' else 'Artline editorial selection for historical context; not a museum highlight claim. ')+c['reason']})
    _,cleveland_policy=core.fetch(core.PROVIDERS['cleveland']['policy'],core.RUN/'captures/cleveland-policy.html')
    policies={'cleveland':cleveland_policy,'nga':{'url':core.PROVIDERS['nga']['policy'],'capture':'captures/nga-policy-image-web.json','sha256':core.sha((core.RUN/'captures/nga-policy-image-web.json').read_bytes())}}
    core.save(core.RUN/'plan.json',{'records':records,'institutions':institutions,'artist_preimages':artists,'country_preimages':countries,'places':places,
        'collection_preimages':preimages,'curated_items':curated,'policies':policies,
        'selection_bound':'Individually listed museum objects selected from bounded metadata searches before downloading images. Existing accessions, parts and exact source identities excluded. No publication or current-display assertions.'})
    core.save(core.RUN/'plan-pin.json',{'sha256':core.sha((core.RUN/'plan.json').read_bytes())})
    print('Pinned',len(records),'museum objects,',len(curated),'explicit editorial/museum selections.')


def verify():
    core.verify()
    p=core.pinned()
    with core.connect() as db:
        for c in p['curated_items']:
            got=db.execute('SELECT artwork_id::text,collection_id::text,position,reason FROM curated_collection_items WHERE collection_id=%s AND artwork_id=%s',(c['collection_id'],c['artwork_id'])).fetchone()
            assert got==c
    print('Explicit curation verified; museum and editorial choices remain distinct.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['plan','prepare','backup','apply','verify'])
    phase=parser.parse_args().phase
    (globals().get(phase) or getattr(core,phase))()
