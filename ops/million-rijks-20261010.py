#!/usr/bin/env python3
"""Select physical fine-art metadata from a bounded, immutable OAI page window."""
import argparse,collections,fcntl,importlib.util,json,re,xml.etree.ElementTree as ET
from pathlib import Path
s=importlib.util.spec_from_file_location('nga',Path(__file__).with_name('million-nga-20261010.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
m=n.m;RUN=m.RUN/'rijks';MID='b6a5755d-157e-4ebe-a5a9-3bc52964ebf5'
SELECTION='selection-00000-01000-v3.json.gz'
NS={'o':'http://www.openarchives.org/OAI/2.0/','d':'http://purl.org/dc/elements/1.1/','t':'http://purl.org/dc/terms/','e':'http://www.europeana.eu/schemas/edm/','s':'http://www.w3.org/2004/02/skos/core#','r':'http://www.w3.org/1999/02/22-rdf-syntax-ns#','g':'http://rdvocab.info/ElementsGr2/','owl':'http://www.w3.org/2002/07/owl#','ore':'http://www.openarchives.org/ore/terms/'}
ABOUT='{'+NS['r']+'}about';RESOURCE='{'+NS['r']+'}resource';LANG='{http://www.w3.org/XML/1998/namespace}lang'
TYPE={'painting':'painting','drawing':'drawing','print':'print','photograph':'photograph','sculpture':'sculpture','pastel':'drawing','watercolour':'watercolor','watercolor':'watercolor','miniature (painting)':'painting'}
def literal(node,path):
    if node is None:return ''
    xs=node.findall(path,NS)
    return next((x.text for x in xs if x.get(LANG)=='en' and x.text),next((x.text for x in xs if x.text),''))
def date(text):
    # Keep original literal in metadata; project complete calendar dates to years.
    value=re.sub(r'\b(\d{4})-\d{2}-\d{2}\b',r'\1',text.strip())
    value=re.sub(r'(?<= )-\s*c\.\s*(?=\d)','- ',value)
    if 'c.' in text and not value.startswith('c.'):value='c. '+value
    return n.dates(value)
def lifeyear(text):
    match=re.fullmatch(r'((?:c\.|ca\.)\s*)?(\d{3,4})(?:-\d{2}-\d{2})?',text.strip())
    return ('c. ' if match[1] else '')+match[2] if match else None
def selection(start,end):
    RUN.mkdir(parents=True,exist_ok=True)
    with (RUN/'selection.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return selection_once(start,end)
def selection_once(start,end):
    dest=RUN/('selection-'+str(start).zfill(5)+'-'+str(end).zfill(5)+'-v3.json.gz')
    if dest.exists():return
    rows=[];held=[];people=collections.defaultdict(list);receipts=[];seen=set()
    for page in range(start,end):
        key='rijks/ListRecords.xml' if page==0 else 'rijks/pages/'+str(page).zfill(5)+'.xml';path=m.DATA/key;rc=m.load(m.RUN/'sources'/(key+'.receipt.json'));assert m.sha(path.read_bytes())==rc['sha256'];receipts.append(rc)
        for node in ET.parse(path).findall('.//o:record',NS):
            cho=node.find('.//e:ProvidedCHO',NS);oid=literal(node,'o:header/o:identifier').rsplit('/',1)[-1]
            if cho is None:held.append(dict(native_id=oid,reason='deleted_or_missing_metadata'));continue
            if oid in seen:held.append(dict(native_id=oid,reason='repeated_native_id'));continue
            seen.add(oid);concepts={c.get(ABOUT):literal(c,'s:prefLabel') for c in node.findall('.//s:Concept',NS)};type_labels=[concepts.get(x.get(RESOURCE),'') for x in cho.findall('d:type',NS)]
            title=literal(cho,'d:title');accession=literal(cho,'d:identifier');dt=literal(cho,'t:created');parsed=date(dt);worktype=next((TYPE[t] for t in type_labels if t in TYPE),None);reason=None
            parents=[x.get(RESOURCE,'') for x in cho.findall('t:isPartOf',NS)]
            if not worktype:reason='type_needs_review'
            elif any(re.fullmatch(r'https://id\.rijksmuseum\.nl/20\d+',u) for u in parents):reason='physical_parent_or_album_component_review'
            elif any(re.search(r'album|book|portfolio|fragment|negative',t,re.I) for t in type_labels):reason='physical_unit_review'
            elif not parsed or parsed[1]==1970 and 'circa' in parsed[2]:reason='date_needs_review_or_after_1970'
            elif not title or not accession:reason='identity_incomplete'
            if reason:held.append(dict(native_id=oid,reason=reason));continue
            agents={a.get(ABOUT):a for a in node.findall('.//e:Agent',NS)};creators=[]
            for c in cho.findall('d:creator',NS):
                uri=c.get(RESOURCE);a=agents.get(uri)
                if not uri or a is None:continue
                name=literal(a,'s:prefLabel');b=lifeyear(literal(a,'g:dateOfBirth'));d=lifeyear(literal(a,'g:dateOfDeath'));label=(b+' - '+d) if b and d else ('born '+b if b else ('died '+d if d else ''))
                qs=[x.get(RESOURCE,'').rsplit('/',1)[-1] for x in a.findall('owl:sameAs',NS) if 'wikidata.org/' in x.get(RESOURCE,'')];qid=qs[0] if len(qs)==1 and re.fullmatch('Q[0-9]+',qs[0]) else ''
                person=dict(constituentid=uri.rsplit('/',1)[-1],forwarddisplayname=name,preferreddisplayname=name,displaydate=label,wikidataid=qid,constituenttype='individual',role='Artist',prefix='',suffix='',source_birth=literal(a,'g:dateOfBirth'),source_death=literal(a,'g:dateOfDeath'),source_uri=uri)
                creators.append(person)
                if person not in people[person['constituentid']]:people[person['constituentid']].append(person)
            agg=node.find('.//ore:Aggregation',NS);shown=agg.find('e:isShownAt',NS) if agg is not None else None;source_url=shown.get(RESOURCE) if shown is not None else cho.get(ABOUT)
            source_images=[x.get(RESOURCE) for x in agg.findall('e:isShownBy',NS)] if agg is not None else [];rights=[x.get(RESOURCE) for x in agg.findall('e:rights',NS)] if agg is not None else []
            medium='; '.join(concepts.get(x.get(RESOURCE),'') for x in cho.findall('t:medium',NS)).strip('; ');creator_label='; '.join(c['forwarddisplayname'] for c in creators)
            raw=dict(native_id=oid,accession=accession,title=title,date_literal=dt,types=type_labels,creator_nodes=creators,source_images=source_images,rights=rights,parent_references=parents,page_receipt=rc,record_xml_sha256=m.sha(ET.tostring(node)),catalogue_unit_note='Native museum inventory object. Physical parent/album component references held; not an assertion that every print is a unique composition.')
            rows.append(dict(native_id=oid,artwork_id=m.uid('artwork/rijks/'+oid),title=title,normalized_title=m.norm(title),source_url=source_url,accession_number=accession,date_display=dt,first=parsed[0],last=parsed[1],precision=parsed[2],work_type=worktype,medium=medium,dimensions=literal(cho,'t:extent'),creator_label=creator_label,creators=creators,cultural_context='',wikidata_id='',raw=raw))
    manifest=dict(at=m.now(),pages=receipts);manifest_path=RUN/('manifest-'+str(start).zfill(5)+'-'+str(end).zfill(5)+'-v3.json');m.save(manifest_path,manifest)
    rc=dict(url='https://data.rijksmuseum.nl/oai?verb=ListRecords&metadataPrefix=edm',retrieved_at=m.now(),sha256=m.sha(manifest_path.read_bytes()),capture_kind='Manifest digest of individual immutable OAI response receipts',manifest_path=str(manifest_path))
    m.save(dest,dict(at=m.now(),source_receipt=rc,selected=rows,people=dict(people),held=held,page_range=[start,end],policy='Only explicitly typed fine-art physical inventory records with parsable literal dates through 1970. No library data, no images downloaded. OAI dc:creator retained as source attribution, life fields only from explicit birth/death predicates. No current-display inference.'))
    print(json.dumps(dict(page_range=[start,end],selected=len(rows),held=collections.Counter(r['reason'] for r in held),artists=len(people),types=collections.Counter(r['work_type'] for r in rows))),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('start',type=int);ap.add_argument('end',type=int);a=ap.parse_args();selection(a.start,a.end)
