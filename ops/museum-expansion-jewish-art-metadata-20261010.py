"""Individual fine-art source records and all eight existing comparators, metadatafirst."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-jewish-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN
fields=c.module('parser','museum-expansion-war-metadata-20261010.py').fields

def main():
    dest=RUN/'art-source-records-001.json.gz';assert not dest.exists();cards=m.load(RUN/'bounded-art-index-001.json.gz')['cards']
    old=m.load(RUN/'production-initial-scope-001.json.gz')['snapshot']['identifiers'];oldids={x['external_id']:x for x in old if x['scheme']=='searchculture-edm'};selected=[];excluded=[]
    for n,card in enumerate(cards,1):
        row=dict(card,number=n,historical_source_match=card['source_id'] in oldids,selection_reason='Visualart metadata candidate; individual date/version/medium/holdingreview pending.')
        date=card['index_date'];match=re.fullmatch(r'(\d{4})(?: - (\d{4}))?',date or '')
        if match and int(match[1])>1970 and not row['historical_source_match']:excluded.append(dict(row,selection_reason='Index creation range entirelyafter1970; no individual record/image selected.'))
        else:selected.append(row)
    allids={x['source_id'] for x in cards}
    for sid,v in sorted(oldids.items()):
        if sid not in allids:selected.append(dict(source_id=sid,url=v['canonical_url'],number=197+sum(x['number']>=197 for x in selected),historical_source_match=True,selection_reason='Existing catalogue comparator.'))
    selection=RUN/'art-metadata-selection-001.json';assert not selection.exists();m.save(selection,dict(at=m.now(),selected=selected,excluded=excluded,index_reference=c.ref(RUN/'bounded-art-index-001.json.gz'),policy='Metadatafirst. Broadcenturyranges and undatedworks are reviewleads, not confirmedpre1971creations. Photographyofart, moderncopies, details andoutsideinstitutionholdings must be reconciled.'))
    rows=[];held=[];failures=0
    for card in selected:
        sid=card['source_id'];suffix=sid.split('000141-')[1] if sid.startswith('jewishmuseum/') else sid.split('000192-')[1];key='object-'+suffix+'-001';rp=RUN/'captures'/(key+'.json')
        if failures>=3:held.append(dict(number=card['number'],source_id=sid,reason='Unattempted after3sourcefailures'));continue
        if rp.exists() and m.load(rp)['status']!=200:held.append(dict(number=card['number'],source_id=sid,reason='Priorfailedcapture,no retry',receipt=m.load(rp)));failures+=1;continue
        try:doc,rc=src.capture(key,card['url'])
        except Exception as exc:held.append(dict(number=card['number'],source_id=sid,reason=type(exc).__name__,receipt=m.load(rp) if rp.exists() else None));failures+=1;continue
        literal,enrichment,links=fields(doc);assert literal.get('Τίτλος') and literal.get('Πάροχος')==['Εβραϊκό Μουσείο της Ελλάδος']
        im=doc.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
        filelinks=sorted({urljoin(card['url'],a['href']) for a in doc.select('a[href]') if '/aggregator/edm/'+sid+'/files/' in a['href']})
        rights=sorted({a['href'] for a in doc.select('a[href]') if 'creativecommons.org/' in a['href'] or 'rightsstatements.org/' in a['href']})
        native=sorted({urljoin(card['url'],a['href']) for a in doc.select('a[href]') if 'artifacts.jewishmuseum.gr' in a['href'] and ('/artifacts/' in a['href'] or '/handle/' in a['href'])})
        rows.append(dict(number=card['number'],source_id=sid,source_url=card['url'],index=card,fields=literal,enrichment=enrichment,field_enrichment_links=links,thumbnail_url=urljoin(card['url'],im['src']) if im else None,file_links=filelinks,rights_links=rights,native_links=native,receipt=rc,decision='unreviewed_metadata'))
        if len(rows)%20==0:print(json.dumps(dict(captured=len(rows),selected=len(selected),held=len(held))),flush=True)
    m.save(dest,dict(at=m.now(),rows=rows,held=held,selection_reference=c.ref(selection),script_reference=c.ref(Path(__file__).resolve()),parser_reference=c.ref(Path(__file__).with_name('museum-expansion-war-metadata-20261010.py')),policy='Literal fields separated from aggregator enrichment. Maker versus sitter/prototype, creation versusdepiction/photograph, samephysicalworkviews andtruecollectionholding require explicitreview. No images or databasewrites.'))
    print(json.dumps(dict(captured=len(rows),old=sum(x['index']['historical_source_match'] for x in rows),held=len(held),later_index_only=len(excluded))),flush=True)

if __name__=='__main__':main()
