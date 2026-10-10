"""Select 110 pre-1971 leads and 18 existing comparators before image retrieval."""
import collections
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('z',Path(__file__).with_name('museum-expansion-zongolopoulos-source-20261010.py'))
z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
m,q,RUN=z.m,z.q,z.RUN


def main():
    cards=[v for p in m.load(RUN/'bounded-index-001.json.gz')['pages']for v in p['cards']]
    selected=[];deferred=[]
    for card in cards:
        years=[int(v)for v in re.findall(r'\d{4}',card['index_date']or'')]
        assert years and len(years)<=2
        kind='existing_comparator'if card['historical_source_match']else'excluded_document'if card['index_type']=='Document'else'hold_date_crosses_1970'if years[0]<=1970<years[-1]else'excluded_post_1970'if years[0]>1970 else'candidate'
        record=dict(card,selection_state=kind)
        (selected if kind in ['existing_comparator','candidate']else deferred).append(record)
    assert collections.Counter(v['selection_state']for v in selected)==dict(existing_comparator=18,candidate=110)
    m.save(RUN/'object-selection-001.json',dict(at=m.now(),selected=selected,deferred=deferred,
        policy='110 eligible-date artwork leads and all18 historical source comparators.29 crossing ranges,20 post-1970 records and3 archival documents not fetched as artwork candidates. Multiple source pages may represent different views of one physical object; source count is not artwork count.',
        index_reference=q.s.ref(RUN/'bounded-index-001.json.gz')))
    rows=[]
    for number,card in enumerate(selected,1):
        sid=card['source_id'].rsplit('-',1)[1]
        soup,receipt=q.q.capture('selected-'+sid+'-001',card['url'])
        fields,enrichment=q.fields(soup)
        assert fields.get('Τίτλος')and fields.get('Δημιουργός')and fields.get('Ημερομηνία')
        image=soup.find('img',src=lambda u:u and '/thumbnails/edm-record/'+card['source_id']in u)
        assert image is not None
        rows.append(dict(number=number,source_id=card['source_id'],source_url=card['url'],role=card['selection_state'],
            index=card,fields=fields,enrichment=enrichment,receipt=receipt,
            links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(card['url'],a['href']))for a in soup.select('a[href]')if 'zongolopoulos.gr'in a['href']],
            thumbnail_url=urljoin(card['url'],image['src']),
            rights_links=sorted({a['href']for a in soup.select('a[href]')if 'creativecommons.org/licenses/'in a['href']})))
        if number%16==0:print(json.dumps(dict(objects=number,total=128)),flush=True)
        time.sleep(.08)
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,
        selection_reference=q.s.ref(RUN/'object-selection-001.json'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Literal museum-supplied SearchCulture object metadata, separate from EKT enrichment. No object identity, edition, inventory normalization or physical-work count inferred yet. No database writes.'))


if __name__=='__main__':main()
