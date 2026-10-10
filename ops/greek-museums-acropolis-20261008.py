#!/usr/bin/env python3
"""Selected official Acropolis highlights, retaining qualified artists and source dates."""
import concurrent.futures, importlib.util, re
from pathlib import Path
from urllib.parse import urljoin
spec=importlib.util.spec_from_file_location('d',Path(__file__).with_name('greek-museums-delivery-20261008.py'))
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
SITE='https://www.theacropolismuseum.gr'


def main():
    soup,rc=d.g.page(SITE+'/en/exhibit-highlights');items=[]
    for a in soup.select('a[href]'):
        im=a.select_one('img.deltia_tupou_img')
        if im:items.append(dict(url=urljoin(SITE,a['href']),index_image=im['src'],index_text=d.g.clean(a)))
    def one(index):
        s,receipt=d.g.page(index['url']);fields={}
        for label in s.select('.popular_exhibitions_inside_container_paddings .col-lg-5'):
            value=label.find_next_sibling('div');fields[d.g.clean(label)]=d.g.clean(value)
        title=d.g.clean(s.select_one('h2.title'));assert title and fields.get('Inventory number')
        dt=fields.get('Date');text=re.sub(r'^AD\s+(.+)$',r'\1 AD',dt or'')
        parsed=d.date(text);parsed['date_display']=dt or'Creation date unknown'
        category=fields.get('Category');material=fields.get('Material')or''
        kind='sculpture'if category in ['Sculpture','Architectural sculpture','Funerary monument']else'ceramic'if 'Clay'in material else'metalwork'if material in ['Silver','Bronze','Lead']else'unknown'
        images=[urljoin(SITE,a['href'])for a in s.select('a[data-external-thumb-image]')]
        assert index['index_image']in images
        return dict(source='acropolis',scheme='acropolis-museum-object',source_id=index['url'].split('/en/')[1],source_url=index['url'],native_url=index['url'],
            receipt=receipt,museum_key='acropolis-museum',title=title,alternate_title=None,creator_label=fields.get('Artist'),creator_values=[],**parsed,
            work_type=kind,medium=material or None,dimensions=fields.get('Dimensions'),accession=fields['Inventory number'],
            raw=dict(fields=fields,index=index,image_urls=images,source_text=d.g.clean(s)),image_url=index['index_image'],holding_confidence=0.99,
            holding_basis='Exact accession and individual object page in the official Acropolis Museum highlights catalogue. Qualified artist wording preserved. Collection association only; no current-display assertion.')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:records=list(pool.map(one,items))
    d.save(d.RUN/'acropolis-object-facts.json',dict(at=d.now(),index_receipt=rc,records=records))
    p=d.load(d.RUN/'delivery-plan-v2.json.gz');held=[];ready=[]
    with d.connect()as db:
        assert not db.execute("SELECT 1 FROM institutions WHERE name ILIKE '%Acropolis%' OR website_url LIKE '%theacropolismuseum.gr%'").fetchone()
        place=db.execute("SELECT to_jsonb(p) row FROM places p WHERE country_code='GR' AND name='Athens'").fetchall();assert len(place)==1;place=place[0]['row']
        mu=dict(id=d.uid('institution/acropolis-museum'),slug='acropolis-museum-athens',name='Acropolis Museum',normalized_name='acropolis museum',kind='museum',status='review',place_id=place['id'],website_url=SITE+'/en')
        ids=[r['id']for r in db.execute("SELECT id::text FROM artworks WHERE normalized_title=ANY(%s) AND status<>'archived'",([d.norm(f['title'])for f in records],))]
        collisions=d.full_rows(db,ids);d.save(d.BACKUP/'acropolis-identity-preimages.json.gz',collisions)
        urls=[f['source_url']for f in records]
        hits=db.execute("SELECT entity_id::text FROM citations WHERE entity_type='artwork' AND source_url=ANY(%s) UNION SELECT entity_id::text FROM external_identifiers WHERE entity_type='artwork' AND canonical_url=ANY(%s)",(urls,urls)).fetchall()
        assert not hits,'Native source already present, needs reconciliation'
        for f in records:
            if any(d.norm(f['title'])==x['artwork']['normalized_title']for x in collisions):
                held.append(dict(facts=f,reason='same_title_requires_version_reconciliation'));continue
            if f['work_type']=='unknown':held.append(dict(facts=f,reason='highlight_outside_selected_artwork_types'));continue
            if 'After 'in f['date_display']:held.append(dict(facts=f,reason='open_ended_creation_date'));continue
            f.update(artwork_id=d.uid('artwork/'+f['scheme']+'/'+f['source_id']),artist_id=None,museum=mu,before=None,action='create');ready.append(f)
    p['records']+=ready;p['held']+=held
    p['museums']['acropolis-museum']=dict(row=mu,before=None,place=place,evidence=dict(name=mu['name'],city='Athens',source_url=SITE+'/en/exhibit-highlights',receipt=rc))
    p['at']=d.now();d.save(d.RUN/'delivery-plan-v3.json.gz',p);d.save(d.BACKUP/'delivery-plan-and-preimages-v3.json.gz',p)
    print('Acropolis',len(ready),'ready',len(held),'held',flush=True)


if __name__=='__main__':main()
