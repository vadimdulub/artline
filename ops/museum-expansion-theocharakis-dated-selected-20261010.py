"""Sixty selected dated paintings/studies, reconciled to native object metadata."""
import importlib.util
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('museum-expansion-theocharakis-dated-source-20261010.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
spec=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-theocharakis-native-20261010.py'))
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
m,q,RUN=d.m,d.q,d.RUN
# The helper import has its own old run; restore capture destination explicitly.
q.q.RUN=RUN;q.q.CAP=RUN/'captures';q.q.CAP.mkdir(parents=True,exist_ok=True)


def main():
    index=m.load(RUN/'dated-index-001.json.gz')
    cards=[r for page in index['pages']for r in page['cards']]
    for card in cards:
        card['index_type']=re.search(r' Item type (.*?) Creator ',card['text'])[1]
    paintings=[v for v in cards if not v['prior_source_review']and v['index_type']=='Painting']
    sketches=[v for v in cards if not v['prior_source_review']and v['index_type']=='Sketch'
              and re.fullmatch(r'\d{4}(?: - \d{4})?',v['index_date'])and int(v['index_date'].split(' - ')[-1])<=1955][:13]
    ids={v['source_id']for v in paintings+sketches}
    selected=[v for v in cards if v['source_id']in ids]
    assert len(paintings)==47 and len(sketches)==13 and len(selected)==60
    deferred=[v for v in cards if v['source_id']not in ids]
    m.save(RUN/'object-selection-001.json',dict(at=m.now(),rows=selected,deferred=deferred,
        rationale='All 47 index-labelled paintings in the bounded 90-card dated sample, plus 13 new studies with explicit index ranges ending by 1955. Includes eligible 1956 artwork metadata; production image policy is separate. Remaining 29 new leads are deferred, and one already-reviewed source is not duplicated.',
        index_reference=q.s.ref(RUN/'dated-index-001.json.gz')))
    sources=[];natives=[]
    for number,card in enumerate(selected,1):
        sid=card['source_id'].rsplit('-',1)[1]
        soup,receipt=q.q.capture('selected-'+sid+'-001',card['url'])
        fields,enrichment=q.fields(soup)
        links=sorted({urljoin(card['url'],a['href'])for a in soup.select('a[href]')if re.search(r'exhibition\.thfdigital\.gr/projects/\d+',a['href'])})
        assert len(links)==1 and fields.get('Τίτλος')and fields.get('Δημιουργός')
        image=soup.find('img',src=lambda u:u and '/thumbnails/edm-record/'+card['source_id']in u)
        assert image is not None
        rights=sorted({a['href']for a in soup.select('a[href]')if 'creativecommons.org/licenses/'in a['href']})
        sources.append(dict(number=number,source_id=card['source_id'],source_url=card['url'],role='candidate',index=card,
            fields=fields,enrichment=enrichment,native_url=links[0],receipt=receipt,thumbnail_url=urljoin(card['url'],image['src']),rights_links=rights))
        native,nreceipt=q.q.capture('native-'+sid+'-001',links[0]);main,nfields,creators=n.native_fields(native)
        assets=sorted({urljoin(links[0],a['href'])for a in main.select('a[href]')if '/wp-content/uploads/'in a['href']and not a['href'].endswith('.svg')})
        assert len(assets)==1
        comparisons=dict(title=nfields['τίτλος']in fields['Τίτλος'],medium=nfields['τεχνική']in fields['Υλικό'],
            date=nfields['έτος']in fields['Ημερομηνία δημιουργίας'],dimensions=nfields.get('διαστάσεις')in fields['Έκταση (μέγεθος ή διάρκεια)'],
            creator=bool(creators)and all(v in fields['Δημιουργός']for v in creators))
        natives.append(dict(number=number,source_id=card['source_id'],role='candidate',native_url=links[0],fields=nfields,creators=creators,
            full_image_url=assets[0],receipt=nreceipt,source_comparison=comparisons,text=q.clean(main.get_text(' ',strip=True))))
        if number%10==0:print(json.dumps(dict(objects=number,total=60,source_native_conflicts=sum(not all(v['source_comparison'].values())for v in natives))),flush=True)
        time.sleep(.08)
    m.save(RUN/'selected-source-records-001.json.gz',dict(at=m.now(),rows=sources,selection_reference=q.s.ref(RUN/'object-selection-001.json'),script_reference=q.s.ref(Path(__file__).resolve())))
    m.save(RUN/'native-object-records-001.json.gz',dict(at=m.now(),rows=natives,source_reference=q.s.ref(RUN/'selected-source-records-001.json.gz'),
        policy='Literal native artwork metadata, separate from index and EKT enrichment. No created accessions, inferred creation years or database mutations. Full asset URLs are observed references only.'))


if __name__=='__main__':main()
