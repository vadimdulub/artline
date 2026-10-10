"""Capture151 new undated-index artwork leads, preserving all descriptive date evidence."""
import collections
import importlib.util
import json
import time
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-zongolopoulos-paintings-source-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
m,q,RUN=d.m,d.q,d.RUN


def main():
    cards=[v for p in m.load(RUN/'bounded-painting-index-001.json.gz')['pages']for v in p['cards']]
    selected=[v for v in cards if not v['prior_source_review']and v['index_date_scope']in ['unknown','eligible']]
    other=[v for v in cards if v not in selected]
    assert len(selected)==151 and all(v['index_date_scope']=='unknown'for v in selected)
    assert collections.Counter('prior'if v['prior_source_review']else v['index_date_scope']for v in other)==dict(prior=9,post_1970=20)
    m.save(RUN/'object-selection-001.json',dict(at=m.now(),selected=selected,deferred_or_excluded=other,
        policy='151 new undated-index painting-category leads only. Object descriptions can identify dates, prints, reproductions or attributions; the index category and lack of date do not establish final type or eligibility. Nine previously reviewed sources and20post1970 leads excluded from capture.',
        index_reference=q.s.ref(RUN/'bounded-painting-index-001.json.gz')))
    rows=[]
    for number,card in enumerate(selected,1):
        sid=card['source_id'].rsplit('-',1)[1]
        soup,receipt=q.q.capture('selected-'+sid+'-001',card['url'])
        fields,enrichment=q.fields(soup);assert fields.get('Τίτλος')and fields.get('Δημιουργός')
        image=soup.find('img',src=lambda u:u and '/thumbnails/edm-record/'+card['source_id']in u);assert image is not None
        rows.append(dict(number=number,source_id=card['source_id'],source_url=card['url'],role='candidate',index=card,
            fields=fields,enrichment=enrichment,receipt=receipt,thumbnail_url=urljoin(card['url'],image['src']),
            rights_links=sorted({a['href']for a in soup.select('a[href]')if 'creativecommons.org/licenses/'in a['href']})))
        if number%20==0:print(json.dumps(dict(objects=number,total=151)),flush=True)
        time.sleep(.08)
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=rows,
        selection_reference=q.s.ref(RUN/'object-selection-001.json'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='Literal foundation metadata via SearchCulture preserved separately from EKT enrichment. No assigned dates, physical artwork counts, verified painter IDs, images or DB writes yet.'))


if __name__=='__main__':main()
