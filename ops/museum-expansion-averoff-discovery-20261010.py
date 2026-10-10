"""Observe the next museum's public source coverage; no object/image ingestion."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('q',Path(__file__).with_name('museum-expansion-kazantzakis-selection-20261009.py'))
q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
m=q.m;RUN=m.RUN/'native/kazantzakis-more-delivery-20261010'
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)

def main():
    rows=[]
    urls=[('averoff-profile-001','https://www.searchculture.gr/aggregator/portal/collections/AveroffMuseum?language=en'),
        ('averoff-homepage-001','https://www.averoffmuseum.gr/')]
    for label,url in urls:
        soup,rc=q.q.capture(label,url);links=[dict(title=q.clean(a.get_text(' ',strip=True)),url=urljoin(rc['final_url'],a['href']))for a in soup.select('a[href]')]
        forms=[]
        for form in soup.select('form'):
            forms.append(dict(action=form.get('action'),method=form.get('method'),id=form.get('id')))
        text=q.clean(soup.get_text(' ',strip=True));rows.append(dict(receipt=rc,text=text,links=links,forms=forms))
        print(json.dumps(dict(source=url,text=text[:4000],collection_links=[x for x in links if any(t in(x['title']+' '+x['url']).lower()for t in ['συλλογ','collection','καλλιτεχν','artist'])][:25]),ensure_ascii=False),flush=True)
    m.save(RUN/'next-source-discovery-001.json.gz',dict(at=m.now(),institution_id='ea977842-2f6e-5020-a853-d300b507aca0',last_verified_catalogue_count=18,last_verified_dateeligible_count=9,
        last_verified_counts_at='2026-10-09',rows=rows,object_details_reviewed=0,images_downloaded=0,applied=False,
        policy='Public collection discovery only. Source-record counts are not eligible-artwork counts; current-display claims require separate dated evidence. Prioritize reviewed pending deliveries before additional museum research.',script_reference=q.s.ref(Path(__file__).resolve())))

if __name__=='__main__':main()
