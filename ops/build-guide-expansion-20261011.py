"""Assemble authored English editions in staging. Does not publish drafts."""
import copy
import gzip
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'docs/research/museum-guides-80-20261011'
STAGE=Path('/tmp/artline-80-guides-20261011/editions')
PUBLIC=ROOT/'apps/web/content/articles/museum-guides'

def load(path):return json.loads(path.read_text())
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def normal(value):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',value.casefold()).encode('ascii','ignore').decode())
def creator_name(value):
    # Display cleanup only; the supplied label stays in the selection evidence.
    value=re.sub(r'\s*\[qualified attribution: malarka; ; \]','',value)
    value=re.sub(r'^\d{4}[-–]\d{4},\s*','',value)
    value=re.sub(r'\s*\([^()]*(?:\d{3,4})[^()]*\)$','',value).strip()
    aliases={'Rembrandt Harmensz. van Rijn':'Rembrandt van Rijn','Krafft Barbara':'Barbara Krafft',
      'Francisco José de Goya y Lucientes (Francisco de Goya)':'Francisco Goya',
      'Anna Bilińska-Bohdanowiczowa':'Anna Bilińska',
      'Robert, Martin Henry':'Martin Henry Robert','Artizzone, Charlotte':'Charlotte Artizzone',
      'Crawford, Catherine Betty':'Catherine Betty Crawford','Scott-Stevenson, Esme':'Esmé Scott-Stevenson',
      'Balfour, Allan E.':'Allan E. Balfour','Pritchard, T. H.':'T. H. Pritchard',
      'Arundale, Francis Vyvyan Jago':'Francis Vyvyan Jago Arundale',
      'zugeschrieben: Gao Qipei':'Attributed to Gao Qipei','Unknown':'Unknown artist'}
    return aliases.get(value,value)
def date_english(value):
    value=value or 'Date not established'
    value=re.sub(r'^\(([^()]+)\)$',r'\1',value)
    value=re.sub(r'^(?:circa|Circa|ca\.?|um|vers|ok\.)\s+', 'c. ', value)
    value=re.sub(r'^(\d{4}) vers$',r'c. \1',value)
    value=re.sub(r'^entre (\d{4}) et (\d{4})$',r'\1–\2',value)
    value=re.sub(r'^2e moitié (\d+)e siècle$',r'Second half of the \1th century',value)
    value=re.sub(r'^(Made|Executed) ', '', value)
    value=re.sub(r'^Sign\. ', 'Signed ', value)
    value=value.replace('Ming- oder Qing-Dynastie','Ming or Qing dynasty').replace('Ming-Dynastie','Ming dynasty').replace('Qing-Dynastie','Qing dynasty').replace('datiert ','dated ').replace(', um ', ', c. ').replace('17. Jh.','17th century')
    value=value.replace('[Peint entre le 4 et le 8 juin 1890.]','(painted 4–8 June 1890)').replace('[novembre-décembre]','(November–December)').replace('preferred intorno al 1504','usually dated c. 1504')
    value=re.sub(r'(\d{4})--(\d{2})--(\d{2})',r'\1-\2-\3',value)
    value=value.replace('Unverified date:','Date unverified:').replace('1897 vers','c. 1897').replace('1509 vers,1510 et','c. 1509–1510')
    return value
def medium_english(value):
    if not value:return ''
    aliases={
      'olej; płótno':'Oil on canvas','pastel; kredka pastelowa; papier żeberkowy':'Pastel on laid paper',
      'rysunek; kredka; papier':'Crayon drawing on paper','technika mieszana; kredka pastelowa; farba temperowa; płótno':'Pastel and tempera on canvas',
      "peinture à l'huile;peuplier":"Oil on poplar","tempera;bois":"Tempera on wood",
      'tüchlein; leinengewebe in leinwandbindung':'Tüchlein painting on plain-weave linen','oil; canvas (painting support)':'Oil on canvas',
      "huile sur toile":"Oil on canvas", "peinture à l'huile;toile":"Oil on canvas", "toile;peinture à l'huile":"Oil on canvas", "toile (peinture à l’huile)":"Oil on canvas", "peinture à l'huile, toile":"Oil on canvas",
      "olieverf op doek":"Oil on canvas", "olieverf op paneel":"Oil on panel", "olieverf op ivoor":"Oil on ivory",
      "technika olejna; farba olejna; płótno":"Oil on canvas", "technika olejna; płótno; farba olejna":"Oil on canvas",
      "tusche und farben auf papier":"Ink and colour on paper", "tusche auf papier":"Ink on paper", "tusche und leichte farben auf papier":"Ink and light colour on paper",
      "tusche und farben auf papier; seide (montierung)":"Ink and colour on paper with silk mounting", "tusche auf goldgrundpapier":"Ink on gold-ground paper",
      "fächerblatt, tusche und farben auf goldgrundpapier":"Fan leaf, ink and colour on gold-ground paper", "lindenholz (tilia sp.)":"Limewood (Tilia species)",
      "ölfarbe; leinwand":"Oil on canvas", "öl auf leinwand":"Oil on canvas", "ölfarbe; eichenholz":"Oil on oak",
      "olie på træ":"Oil on wood", "olie på lærred":"Oil on canvas", "tempera; olej; deska lipowa":"Tempera and oil on limewood panel",
      "pastel; kredka pastelowa; papier":"Pastel on paper", "peinture à l'huile;bois":"Oil on wood", "peinture à l’huile;contreplaqué":"Oil on plywood",
      "peinture à l'huile;verre":"Oil on glass", "peinture à l'huile;emploi d'or;résineux":"Oil and gold on softwood",
      "peinture à l'huile;papier (blanc);toile;matériaux collés l'un sur l'autre":"Oil on white paper mounted on canvas",
      "peinture à l'huile;toile;bois;matériaux collés l'un sur l'autre":"Oil on canvas mounted on wood",
      "canvas; paint binder not exposed by the reviewed object/iiif metadata":"Canvas; paint medium not specified", "canvas; paint binder not specified in reviewed source":"Canvas; paint medium not specified",
      "wood (plant material); textile materials; oil paint (paint)":"Oil, wood and textile", "oil on isorel":"Oil on hardboard",
    }
    key=value.casefold().strip()
    if key in aliases:return aliases[key]
    key=key.replace('oil paint (paint)','oil').replace('oil paint','oil').replace('watercolor','watercolour').replace('color','colour')
    if ','in key or ';'in key:
        parts=[p.strip()for p in re.split('[,;]',key)]
        supports={'canvas','paper','panel','board','wood','oak','copper','cardboard','plaster','plywood'}
        media=[p for p in parts if p not in supports];support=[p for p in parts if p in supports]
        if len(support)==1 and all(p in {'oil','tempera','pastel','chalk','pencil','ink','charcoal','crayon','gouache','watercolour','graphite','enamel','sand','collage'}for p in media):
            def join(xs):return ', '.join(xs[:-1])+' and '+xs[-1]if len(xs)>1 else xs[0]
            key=join(media)+' on '+support[0] if media else support[0]
    return key[0].upper()+key[1:] if key else ''
def assemble(slugs):
    base=load(PUBLIC/'louvre/en.json');books=load(RUN/'books.json')
    artist_candidates={}
    for file in (RUN/'catalogue').glob('*.json.gz'):
        for work in json.loads(gzip.decompress(file.read_bytes()))['works']:
            for a in work['artists']:
                if a['role']in ['primary','artist']:
                    artist_candidates.setdefault(normal(creator_name(a['name'])),{})[a['slug']]=a
    lookup=RUN/'creator-label-lookup.json'
    if lookup.exists():
        for a in load(lookup)['artists']:
            artist_candidates.setdefault(normal(creator_name(a['display_name'])),{})[a['slug']]={'name':creator_name(a['display_name']),'slug':a['slug'],'role':'primary'}
    overrides=load(RUN/'field-overrides.json') if (RUN/'field-overrides.json').exists()else{}
    files=[RUN/'copy'/(s+'.json')for s in slugs]if slugs else sorted((RUN/'copy').glob('*.json'))
    for file in files:
        slug=file.stem;authored=load(file);selection=load(RUN/'selections'/(slug+'.json'));meta=selection['candidate']
        assert len(selection['works'])==len(authored['works'])==20
        guide={k:copy.deepcopy(base[k])for k in ['selectionNote','labels']}
        guide.update({k:meta[k]for k in ['slug','museum','city','country']})
        guide.update({k:authored[k]for k in ['title','subtitle','introduction','visitNote']})
        website=selection['institution'].get('website_url')or''
        guide.update(locale='en',website=authored.get('website',website),officialGuide=authored.get('officialGuide',website),updated='2026-10-11')
        guide['books']=[dict(books[authored['bookKey']],note=authored['bookNote'])]+authored.get('extraBooks',[])
        ws=[];resolutions=[]
        for original,prose in zip(selection['works'],authored['works']):
            title,description,importance=prose
            assert all(isinstance(s,str) and len(s)>0 for s in prose)
            assert len(description.split())>=15 and len(importance.split())>=15,(slug,title)
            m=original['media'];artists=copy.deepcopy(original['artists'])
            label=creator_name(original['unlinked_creator_label']or'')
            for a in artists:a['name']=creator_name(a['name'])
            # Exact normalized, unqualified name matches only. Ambiguities stay explicit.
            if not artists and label:
                candidates=artist_candidates.get(normal(label),{})
                if len(candidates)==1:
                    a=copy.deepcopy(next(iter(candidates.values())));a['role']='primary';artists=[a]
                    resolutions.append({'artwork':original['id'],'suppliedLabel':label,'linkedArtist':a,'basis':'Unique exact normalized name among source-linked production artists; guide filter only, no database mutation.'})
            artist='; '.join(a['name']+(' ('+a['role'].replace('_',' ')+')'if a['role']not in ['primary','artist']else'')for a in artists)or label or'Unknown artist'
            image='https://artlines.org'+m['storage_path']if m['storage_kind']=='local'else m['delivery_url']
            date=date_english(original['date_display'])
            work=dict(id=original['id'],title=title,catalogueTitle=original['title'],artist=artist,artists=artists,date=date,
                start=original['creation_year_start'],end=original['creation_year_end'],medium=medium_english(original['medium_text']),accession=original['accession_number']or'',
                image=image,imageSource=m['source_page_url']or original['holdings'][0]['url'],credit=m['attribution_text']or m['creator_credit']or m['provider_name'],
                license=m['license_label']or m['rights_status'],licenseUrl=m['license_url']or'',source=original['holdings'][0]['url'],
                description=description,importance=importance,museum=meta['museum'])
            for key,value in overrides.get(original['id'],{}).items():
                if key!='evidence':work[key]=value
            if not original['artists'] and work['artists']:
                work['catalogueArtistSlug']=None
            ws.append(work)
        guide['works']=ws
        dated=[w for w in ws if w['start']is not None and w['end']is not None]
        assert dated,slug
        guide['context']={'start':max(1100,min(w['start']for w in dated)),'end':min(1970,max(w['end']for w in dated))}
        save(STAGE/slug/'en.json',guide)
        save(RUN/'assembly'/(slug+'.json'),{'selectionSha256':hashlib.sha256((RUN/'selections'/(slug+'.json')).read_bytes()).hexdigest(),'copySha256':hashlib.sha256(file.read_bytes()).hexdigest(),'guideSha256':hashlib.sha256((STAGE/slug/'en.json').read_bytes()).hexdigest(),'artistResolutions':resolutions})
        print(slug,'English assembled in staging',flush=True)

if __name__=='__main__':assemble(sys.argv[1:])
