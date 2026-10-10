"""Bounded collection-page discovery for the next unfilled Greek museums."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin,urlparse
spec=importlib.util.spec_from_file_location('src',Path(__file__).with_name('museum-expansion-jewish-source-20261010.py'))
src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
c,m,RUN=src.c,src.m,src.RUN

def main():
    dest=RUN/'next-source-discovery-001.json.gz';assert not dest.exists();queue=m.load(c.checked(m.load(c.CP)['priority_museum_queue_reference']))['rows'];rows=[]
    for key,iid in [('momus','fbb86dfe-de37-5942-b762-0585ae753b31'),('faltaits','4c0f86b1-db26-5bac-b996-af97707fce2c'),('agrinio','d320a1d9-e80c-5205-823d-fefe07394a03')]:
        museum=next(x for x in queue if x['id']==iid);url=museum['website_url']
        try:doc,rc=src.capture('next-'+key+'-collection-001',url)
        except Exception as exc:rows.append(dict(institution_id=iid,name=museum['name'],error=type(exc).__name__,url=url));continue
        text=src.clean(doc.get_text(' ',strip=True));cards=[]
        for el in doc.select('.edm-entity-result'):
            pairs=[(a,urljoin(url,a['href'])) for a in el.select('a[href]') if '/aggregator/edm/' in a['href'] and a.get_text(' ',strip=True)]
            if pairs:
                a,u=pairs[0];cards.append(dict(title=src.clean(a.get_text(' ',strip=True)),url=u,text=src.clean(el.get_text(' ',strip=True))))
        external=sorted({urljoin(url,a['href']) for a in doc.select('a[href]') if urlparse(urljoin(url,a['href'])).hostname not in ['www.searchculture.gr',None]})
        links=[dict(title=src.clean(a.get_text(' ',strip=True)),url=urljoin(url,a['href'])) for a in doc.select('a[href]') if 'advancedSearch' in a['href'] or '/collections/' in a['href']]
        pager=doc.select_one('.results-pagination .text-muted');pagination=src.clean(pager.get_text(' ',strip=True)) if pager else None
        row=dict(institution_id=iid,name=museum['name'],last_catalogue_count=museum['catalogue_count_to_200'],receipt=rc,text=text,first_cards=cards,external_links=external,navigation=links,pagination=pagination);rows.append(row)
        print(json.dumps(dict(name=museum['name'],pagination=pagination,text=text[:1500],cards=cards[:3],external_links=external[:12]),ensure_ascii=False),flush=True)
    m.save(dest,dict(at=m.now(),rows=rows,script_reference=c.ref(Path(__file__).resolve()),policy='Only three public collection landingpages and first visible30metadata cards per source. No individual objects, images or databasewrites. Source totals are mixedrecords, not eligible artworks; fresh baseline and date/art/unit review needed. EarlierNikaia101mixedentries remain in inheriteddiscovery.'))

if __name__=='__main__':main()
