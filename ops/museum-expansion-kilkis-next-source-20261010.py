"""Capture two observed Athens City collection entry points; no object/image import."""
import importlib.util
import json
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-kilkis-common-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
q=c.module('q','museum-expansion-kazantzakis-source-20261009.py')
m,RUN=c.m,c.RUN
q.RUN=RUN;q.CAP=RUN/'captures';q.CAP.mkdir(parents=True,exist_ok=True)

def main():
    destination=RUN/'next-source-discovery-001.json.gz';assert not destination.exists()
    source='https://www.searchculture.gr/aggregator/portal/collections/DigAthensMuseum?language=en'
    soup,receipt=q.capture('athens-city-searchculture-profile-001',source)
    native=next(urljoin(source,a['href']) for a in soup.select('a[href]') if 'portal.athenscitymuseum.gr/artworks' in a['href'])
    rows=[]
    for key,url,doc,rc in [('searchculture',source,soup,receipt),('native',native,None,None)]:
        if doc is None:doc,rc=q.capture('athens-city-native-index-001',url)
        links=[dict(title=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in doc.select('a[href]')]
        forms=[dict(action=f.get('action'),method=f.get('method'),controls=[dict(tag=x.name,name=x.get('name'),value=x.get('value'),type=x.get('type'),text=x.get_text(' ',strip=True)) for x in f.select('input,select,option')]) for f in doc.select('form')]
        rows.append(dict(key=key,receipt=rc,text=doc.get_text(' ',strip=True),links=links,forms=forms))
        print(json.dumps(dict(key=key,status=rc['status'],bytes=rc['bytes'],text=doc.get_text(' ',strip=True)[:5500]),ensure_ascii=False),flush=True)
    m.save(destination,dict(at=m.now(),institution_id='f575847e-47eb-59e4-b558-32d8723bc3c9',last_verified_catalogue_count=18,last_verified_dateeligible_count=16,last_verified_counts_at='2026-10-09',fresh_production_counts=False,rows=rows,object_details_reviewed=0,images_downloaded=0,applied=False,script_reference=c.ref(Path(__file__).resolve()),policy='Two observed public entry points only. The approximately2400 collection objects include photographs, furnishings, documents, reproductions and later works; none is automatically an eligible original artwork. Next use bounded metadata selection and reconcile existing18 identities. No invented creation dates or mass image download.'))

if __name__=='__main__':main()
