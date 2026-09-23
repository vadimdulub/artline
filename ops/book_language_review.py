"""Conservative parsing of explicit Wikipedia book-language fields."""
import collections,re,unicodedata
import mwparserfromhell as mw

BOOK_BOXES={'infobox book','infobox short story','infobox poem','infobox play','infobox religious text','infobox ancient text','infobox manuscript','infobox scripture','infobox literary work','infobox encyclopedia','infobox novel','infobox graphic novel'}
NOTE_TEMPLATES={'refn','efn','sfn','sfnm','sfnp','harv','harvnb','harvtxt','cn','citation needed','ref label','refn','rp','r','fn','note','efn-ua'}
LIST_TEMPLATES={'plainlist','plain list','ubl','unbulleted list','unbulletedlist','hlist','flatlist','flat list','bulleted list'}

def norm(value):
    text=unicodedata.normalize('NFKC',str(value)).lower().replace('_',' ').replace('’',"'").strip()
    text=re.sub(r'\s+',' ',text)
    return text[:-9].strip() if text.endswith(' language') else text

def aliases_for(terms):
    aliases=collections.defaultdict(set);canonical=collections.defaultdict(set)
    for q,e in terms.items():
        names=[v['value'] for k,v in e.get('labels',{}).items() if k in ('en','mul')]
        if 'enwiki' in e.get('sitelinks',{}):names.append(e['sitelinks']['enwiki']['title'])
        for name in names:canonical[norm(name)].add(q)
        names.extend(v['value'] for v in e.get('aliases',{}).get('en',[]))
        for name in names:aliases[norm(name)].add(q)
    result={key:next(iter(ids)) for key,ids in aliases.items() if len(ids)==1}
    # An old/historical variety may alias the modern language's exact name.
    # Prefer a unique canonical label/title over such a broad alias.
    result.update({key:next(iter(ids)) for key,ids in canonical.items() if len(ids)==1})
    return result

def field_text(raw):
    code=mw.parse(raw)
    for node in list(code.filter_comments()):code.remove(node)
    for tag in list(code.filter_tags()):
        name=norm(tag.tag)
        if name=='ref':code.remove(tag)
        elif name in ('br','hr'):code.replace(tag,';')
        elif name in ('small','span','div'):code.replace(tag,str(tag.contents or ''))
    for template in reversed(list(code.filter_templates())):
        name=norm(template.name).removeprefix('template:')
        try:
            if name in NOTE_TEMPLATES or name.startswith('cite '):code.remove(template)
            elif name in LIST_TEMPLATES:code.replace(template,';'.join(str(p.value) for p in template.params if str(p.name).strip().isdigit()))
            elif name in ('nowrap','nobreak') and template.has(1):code.replace(template,str(template.get(1).value))
            elif name in ('lang','langx') and template.has(2):code.replace(template,str(template.get(2).value))
            else:code.replace(template,' [unresolved template: '+str(template.name).strip()+'] ')
        except ValueError:
            # A parent reference may already have removed its nested template.
            pass
    return code.strip_code(normalize=True,collapse=False).strip()

def parse_field(raw,aliases):
    text=field_text(raw)
    if not text:return {'raw':raw,'text':text,'languages':[],'unresolved':[]}
    parts=[v.strip().strip('*').strip() for v in re.split(r'[,;/\n]|\s+(?:and|&)\s+',text) if v.strip().strip('*').strip()]
    languages=[];unknown=[]
    for part in parts:
        q=aliases.get(norm(part))
        if q:languages.append(q)
        else:unknown.append(part)
    return {'raw':raw,'text':text,'languages':sorted(set(languages)),'unresolved':unknown}

def wikipedia_language(capture,qid,aliases):
    page=capture['page'];identity=page.get('pageprops',{}).get('wikibase_item')
    result={'page_title':page.get('title'),'page_id':page.get('pageid'),'wikidata_item':identity,'fields':[],'languages':[],'state':'missing_language_field'}
    if identity!=qid:result['state']='page_identity_mismatch';return result
    revisions=page.get('revisions',[])
    if not revisions:result['state']='missing_revision';return result
    revision=revisions[0];result['revision_id']=revision['revid']
    result['url']='https://en.wikipedia.org/w/index.php?oldid='+str(revision['revid'])
    text=revision.get('slots',{}).get('main',{}).get('content','')
    result['lead']=mw.parse(text.split('\n==',1)[0]).strip_code()[:20000]
    boxes=[]
    for template in mw.parse(text).filter_templates(recursive=False):
        if norm(template.name).removeprefix('template:') not in BOOK_BOXES:continue
        fields=[]
        for name in ('language','original_language','original_languages'):
            if template.has(name):
                value=str(template.get(name).value).strip()
                if value:fields.append(dict(parse_field(value,aliases),name=name,template=str(template.name).strip()))
        if fields:boxes.append(fields)
    result['fields']=[f for box in boxes for f in box]
    if not result['fields']:return result
    if any(f['unresolved'] or not f['languages'] for f in result['fields']):result['state']='qualified_or_unmapped_language';return result
    sets={tuple(f['languages']) for f in result['fields']}
    if len(sets)!=1:result['state']='conflicting_infobox_languages';return result
    result['languages']=list(next(iter(sets)));result['state']='explicit_language_field'
    return result

def source_language_claims(entity):
    rows=[c for c in entity.get('claims',{}).get('P407',[]) if c.get('rank')!='deprecated' and c.get('mainsnak',{}).get('snaktype')=='value']
    return [c for c in rows if c.get('rank')=='preferred'] or rows

def claim_language_ids(entity):
    return sorted({c['mainsnak']['datavalue']['value']['id'] for c in source_language_claims(entity) if c['mainsnak']['datavalue']['value'].get('id')})

def ancestors(q,terms):
    result=set();pending=[q]
    while pending:
        current=pending.pop()
        for prop in ('P279',):
            for c in terms.get(current,{}).get('claims',{}).get(prop,[]):
                value=c.get('mainsnak',{}).get('datavalue',{}).get('value',{})
                parent=value.get('id') if isinstance(value,dict) else None
                if c.get('rank')!='deprecated' and parent and parent not in result and parent!=q:result.add(parent);pending.append(parent)
    return result

def compatible_varieties(qids,explicit,terms):
    """Retain supplied varieties only where a sourced subtype path connects them."""
    result=set(explicit)
    for q in qids:
        if any(v in ancestors(q,terms) or q in ancestors(v,terms) for v in explicit):result.add(q)
    return sorted(result)
