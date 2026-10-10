"""Capture55selected photograph leads and10existing source comparators, no images."""
import importlib.util,json,re
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-athens-city-photographs-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
q=c.module('q','museum-expansion-kazantzakis-selection-20261009.py');q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)

def main():
    assert not(RUN/'selected-source-records-001.json.gz').exists();index=m.load(c.PREVIOUS/'next-photograph-index-001.json.gz');old=m.load(c.PREVIOUS/'production-initial-scope-001.json.gz')['snapshot'];photos={x['id']:x for x in old['artworks'] if x['work_type']=='photograph'};assert len(photos)==10
    oldids={x['external_id']:x for x in old['identifiers'] if x['entity_id'] in photos and x['scheme']=='searchculture-edm'};assert len(oldids)==10
    selected=[dict(x,number=i+1,historical_source_match=x['source_id'] in oldids,selection_state='selected_metadata_review') for i,x in enumerate(index['cards'])];sids={x['source_id'] for x in selected}
    for sid,v in sorted(oldids.items()):
        if sid in sids:continue
        art=photos[v['entity_id']];selected.append(dict(number=len(selected)+1,source_id=sid,url=v['canonical_url'],title=art['title'],index_date=art['date_display'],historical_source_match=True,selection_state='additional_existing_comparator',existing_artwork_id=v['entity_id']))
    assert len(selected)==65 and sum(x['historical_source_match'] for x in selected)==10
    sp=RUN/'metadata-selection-001.json'
    if not sp.exists():m.save(sp,dict(at=m.now(),selected=selected,index_reference=c.ref(c.PREVIOUS/'next-photograph-index-001.json.gz'),existing_reference=c.ref(c.PREVIOUS/'production-initial-scope-001.json.gz'),policy='55uncatalogued source IDs and all10existing museum photographs, metadata only.1960index date versus65–70title discrepancies require explicit review; no event/title-to-creation inference. No image download or production changes.'))
    else:assert m.load(sp)['selected']==selected
    rows=[]
    for card in selected:
        sid=card['source_id'];url=card['url'];uuid=sid.split('000190-')[1];soup,rc=q.q.capture('object-'+uuid+'-001',url);literal,enrichment=q.fields(soup);assert literal.get('Τίτλος') and literal.get('Πάροχος')==['Μουσείον της Πόλεως των Αθηνών – Ίδρυμα Βούρου – Ευταξία']
        native=sorted({urljoin(url,a['href']) for a in soup.select('a[href]') if a['href'].startswith('https://portal.athenscitymuseum.gr/artworks/')});assert len(native)==1
        image=soup.find('img',src=lambda x:x and '/thumbnails/edm-record/'+sid in x)
        rows.append(dict(number=card['number'],source_id=sid,source_url=url,native_url=native[0],index=card,fields=literal,enrichment=enrichment,thumbnail_url=urljoin(url,image['src']) if image else None,receipt=rc,decision='unreviewed_metadata'))
        if len(rows)%10==0:print(json.dumps(dict(captured=len(rows),selected=65)),flush=True)
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,selection_reference=c.ref(sp),script_reference=c.ref(Path(__file__).resolve()),policy='Museum-supplied literal metadata and EKT enrichment kept separate. Complete selected physical/version/date review is pending. No photographs or production changes.'))
    print(json.dumps(dict(captured=65,new_leads=55,existing_comparators=10)),flush=True)

if __name__=='__main__':main()
