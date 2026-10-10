"""Reconcile captured literal/native metadata before selecting authentic visual evidence."""
import collections,gzip,importlib.util,json,re
from pathlib import Path
from urllib.parse import unquote,urljoin
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('t',Path(__file__).with_name('museum-expansion-jewish-textile-metadata-20261010.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
c,m,RUN=t.c,t.m,t.RUN

def main():
    dest=RUN/'selected-source-records-002.json.gz';assert not dest.exists()
    art=m.load(RUN/'art-source-records-001.json.gz')['rows'];textile=m.load(RUN/'textile-source-records-002.json.gz')['rows'];native={x['number']:x['native'] for x in m.load(RUN/'selected-art-native-evidence-001.json.gz')['rows']}
    cards={x['number']:x for x in m.load(RUN/'textile-metadata-selection-001.json')['selected']}
    for n in [1194,1195]:
        card=cards[n];sid=card['source_id'];key='object-'+sid.split('000141-')[1]+'-001';assert (t.src.CAP/(key+'.json')).exists()
        doc,rc=t.src.capture(key,card['url']);literal,enrichment,links=t.fields(doc);im=doc.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
        row=dict(number=n,source_id=sid,source_url=card['url'],index=card,fields=literal,enrichment=enrichment,field_enrichment_links=links,thumbnail_url=urljoin(card['url'],im['src']),rights_links=sorted({a['href'] for a in doc.select('a[href]') if 'creativecommons.org/' in a['href'] or 'rightsstatements.org/' in a['href']}),native_links=sorted({a['href'] for a in doc.select('a[href]') if 'artifacts.jewishmuseum.gr/artifacts/' in a['href']}),receipt=rc)
        row['native']=t.native(row);textile.append(row)
    rows=art+textile;assert len(rows)==311
    groups=collections.defaultdict(list);selection=[]
    for row in rows:
        n=row['number'];f=row['fields'];old=row['index']['historical_source_match']
        if n in native:row['native']=native[n]
        if row.get('native'):
            v=row['native'];raw=gzip.decompress((m.ROOT/v['receipt']['body_path']).read_bytes());doc=BeautifulSoup(raw,'html.parser');im=doc.select_one('img.object-contain');assert im
            v['primary_image_url']=im['src'];v['file_name']=unquote(im['src'].rsplit('/',1)[1]);v['literal_date']=re.search(r' Date: (.*?) Creator:',v['text'])[1]
            # File tokens aid identity review; they are not asserted accession numbers.
            name=re.sub(r'-\d+(?=\.jpg$)','',v['file_name'],flags=re.I)
            match=re.search(r'(\d{2,4}\.\d+(?:\.[\da-z]+)*[a-z]?)\.jpg$',name,re.I)
            v['file_identity_token']=match[1] if match else None
            if match:groups[match[1]].append(n)
        external=any('Municipality Museum of Ioannina' in x or 'Epirotic Studies' in x for x in f.get('Επιμέρους συλλογή',[])) or 'Municipality Museum of Ioannina' in row.get('native',{}).get('text','').split('Visit the Museum Website ')[-1]
        if old:decision='existing_comparator'
        elif external:decision='external_collection_hold'
        elif n>=1001 or n in t.ART_NUMBERS:decision='visual_review_candidate'
        elif n in [176,177]:decision='post1970_depicted_event_hold'
        elif '000141-photograph-' in row['source_id']:decision='photographic_surrogate_hold'
        else:decision='unresolved_date_or_version_lead'
        row['decision']=decision
        if decision in ['visual_review_candidate','existing_comparator']:
            selection.append(dict(number=n,source_id=row['source_id'],decision=decision,thumbnail_url=row['thumbnail_url'],native_image_url=row.get('native',{}).get('primary_image_url'),native_file_identity=row.get('native',{}).get('file_identity_token')))
    assert len(selection)>130 and sum(x['decision']=='external_collection_hold' for x in rows)<30
    m.save(dest,dict(at=m.now(),rows=rows,dependencies=[c.ref(RUN/f) for f in ['art-source-records-001.json.gz','textile-source-records-002.json.gz','selected-art-native-evidence-001.json.gz']],script_reference=c.ref(Path(__file__).resolve()),policy='311 captured metadata records, including128 textile entries. Corrected collection test uses object body after navigation, not the global category menu; V1 overheld every native object and is superseded. Two earlier successfullycachedcanopyrecords integratedwithout HTTP retry. Native primary image selector corrected to img.object-contain for2017/09contemporaryartimages; priorcaptures unchanged. ExternalIoannina collections held, photographic surrogates notheldoriginalartworks, publication andcurrentdisplayunchanged.'))
    m.save(RUN/'metadata-visual-selection-002.json',dict(at=m.now(),rows=selection,counts=dict(collection_records=len(rows),decisions=dict(collections.Counter(x['decision'] for x in rows)),visual_candidates=len(selection)),file_identity_groups=[dict(token=k,numbers=v) for k,v in groups.items() if len(v)>1],script_reference=c.ref(Path(__file__).resolve()),policy='Only these capturedmetadata-selectedobjects may have authentic visualreferences downloaded. No exhaustive13533record image download. Literalcreation dates andwholeobject boundaries stillunderreview; publicimagecutoff1955 appliesafter review. Nativefilenames are identityleads, notverifiedinventorynumbers.'))
    print(json.dumps(dict(counts=collections.Counter(x['decision'] for x in rows),visual=len(selection),groups={k:v for k,v in groups.items() if len(v)>1})),flush=True)

if __name__=='__main__':main()
