#!/usr/bin/env python3
"""Read-only, bounded reconciliation of existing Louvre image leads.

No fixture records, image downloads, publication or catalogue mutations.
Preserve captured source responses and identity candidates for separate review.
"""
import argparse
import importlib.util
import json
import re
import time
from pathlib import Path

spec = importlib.util.spec_from_file_location('location_research', Path(__file__).with_name('research-artwork-locations-20261004.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r);r.PORT=55445
r.RUN = r.ROOT / 'docs/research/louvre-image-coverage-20261005'


def snapshot():
    with r.connect() as db:
        selected = db.execute('''SELECT to_jsonb(a) artwork,to_jsonb(m) media,c.evidence_note::jsonb lead,
          COALESCE((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role,
            'identifiers',(SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artist' AND e.entity_id=ar.id)))
            FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists
          FROM citations c JOIN artworks a ON a.id=c.entity_id JOIN media_assets m ON m.id=a.primary_media_id
          WHERE c.entity_type='artwork' AND c.field_name='museum_location_lead_review'
          AND c.evidence_note ILIKE '%louvre%' AND a.current_institution_id IS NULL AND a.status<>'archived'
          ORDER BY a.id,c.id''').fetchall()
        native = db.execute('''SELECT to_jsonb(a) artwork,
          COALESCE((SELECT jsonb_agg(jsonb_build_object('id',ar.id,'name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role))
            FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists,
          COALESCE((SELECT jsonb_agg(to_jsonb(c)) FROM citations c WHERE c.entity_type='artwork' AND c.entity_id=a.id),'[]') citations,
          COALESCE((SELECT jsonb_agg(to_jsonb(e)) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers
          FROM artworks a WHERE a.current_institution_id=(SELECT id FROM institutions WHERE slug='musee-du-louvre')
          AND a.status<>'archived' ORDER BY a.id''').fetchall()
    r.save_gz(r.RUN/'selected-existing-images.json.gz', selected)
    r.save_gz(r.RUN/'louvre-existing-records.json.gz', native)
    print(json.dumps({'selected_image_leads':len(selected),'existing_museum_records':len(native),'current_images':sum(bool(x['artwork']['primary_media_id']) for x in native)}),flush=True)


def crosswalk():
    selected=r.load(r.RUN/'selected-existing-images.json.gz')
    ids=sorted({x['lead']['source_url'].split('/en/',1)[1] for x in selected if '/en/' in x['lead']['source_url']})
    for offset in range(0,len(ids),35):
        dest=r.RUN/'wikiart-crosswalk'/f'{offset:03d}.json.gz'
        if dest.exists():continue
        query='SELECT ?item ?wikiart ?ark ?joconde ?creator ?en ?fr WHERE { VALUES ?wikiart { '+ ' '.join(json.dumps(v)for v in ids[offset:offset+35])+''' } ?item wdt:P6002 ?wikiart .
 OPTIONAL { ?item wdt:P9394 ?ark } OPTIONAL { ?item wdt:P347 ?joconde } OPTIONAL { ?item wdt:P170 ?creator }
 OPTIONAL { ?item rdfs:label ?en FILTER(LANG(?en)="en") } OPTIONAL { ?item rdfs:label ?fr FILTER(LANG(?fr)="fr") } }'''
        raw,receipt=r.capture('https://query.wikidata.org/sparql',{'query':query,'format':'json'},tag='wikidata-crosswalk',timeout=45)
        assert receipt['status']==200,receipt['status']
        rows=[{k:v['value']for k,v in row.items()}for row in json.loads(raw)['results']['bindings']]
        r.save_gz(dest,{'receipt':receipt,'rows':rows})
        print(json.dumps({'batch':offset,'selected':len(ids),'matches':len(rows)}),flush=True)
        time.sleep(1)

def reconcile():
    selected={x['artwork']['id']:x for x in r.load(r.RUN/'selected-existing-images.json.gz')};native=r.load(r.RUN/'louvre-existing-records.json.gz')
    ready=[];held=[]
    for m in r.load(r.RUN/'identity-candidates.json.gz')['matched']:
     arks={c['ark']for c in m['crosswalks']};c=m['crosswalks'][0];p=r.load(r.RUN/'primary-records'/(c['ark']+'.json.gz'));o=p['object'];src=selected[m['id']];w=src['artwork'];reason=None
     ns=[x for x in native if any((c.get('joconde') and z['source_record_id']==c['joconde']) or c['ark'] in (z['source_url']or '')for z in x['citations'])]
     ds=o.get('dateCreated',[]);current=[z for z in o.get('creator',[]) if z.get('attributionLevel','').casefold()=='attribution actuelle' and z.get('wikidata')]
     source_q={z['external_id'] for ar in src['artists'] for z in ar.get('identifiers')or[] if z['scheme']=='wikidata'}
     h=next((float(z['value'].replace(',','.'))for z in o.get('dimension',[])if z['type']=='Hauteur'),None);width=next((float(z['value'].replace(',','.'))for z in o.get('dimension',[])if z['type']=='Largeur'),None)
     if len(arks)!=1:reason='Ambiguous object crosswalk'
     elif not ns:reason='No native object matched by primary/Joconde identifier'
     elif len(ns)>1:reason='Multiple native records need separate duplicate review'
     elif ns[0]['artwork']['primary_media_id']:reason='Native image already exists; preserved'
     elif len(ds)!=1 or not isinstance(ds[0].get('startYear'),int):reason='Primary date needs review'
     elif len(current)!=1 or current[0]['wikidata'] not in source_q:reason='Current primary creator needs review'
     elif current[0].get('doubt') or current[0].get('linkType') or current[0].get('authenticationType'):reason='Qualified primary attribution'
     elif not o.get('heldBy','').startswith('Musée du Louvre'):reason='Holding needs review'
     elif any(term in w['title'].lower() for term in ['(detail)','sketch','study']):reason='Partial composition'
     elif not h or not width or abs((width/h)/(src['media']['width']/src['media']['height'])-1)>.09:reason='Image/primary dimensions need visual review'
     else:
      n=ns[0]['artwork'];start=ds[0]['startYear'];end=ds[0].get('endYear')or start
      if not all(isinstance(v,int)for v in [end,w['creation_year_start'],w['creation_year_end']]):reason='Missing/unknown date'
      elif end>1970 or max(start,w['creation_year_start'],n['creation_year_start'] if n['creation_year_start'] is not None else start)>min(end,w['creation_year_end'],n['creation_year_end'] if n['creation_year_end'] is not None else end):reason='Different dated version'
      elif {ar['id']for ar in ns[0]['artists']}!={ar['id']for ar in src['artists']} and not (not ns[0]['artists'] and len(src['artists'])==1 and r.namekey(n['unlinked_creator_label']or'')==r.namekey(src['artists'][0]['name'])):reason='Native creator relationship differs'
      elif src['media']['rights_status'] not in ['public_domain','cc0','cc_by','cc_by_sa']:reason='Rights need review'
      elif src['media']['byte_size']>100000:reason='Oversize existing asset'
     if reason:held.append({'source_id':w['id'],'title':w['title'],'reason':reason});print('HOLD',w['title'],reason)
     else:
      item={'source_id':w['id'],'source_title':w['title'],'target_id':ns[0]['artwork']['id'],'target_title':ns[0]['artwork']['title'],'media_id':src['media']['id'],'ark':c['ark'],'joconde':c.get('joconde'),'crosswalk':c,'source_receipt':p['source_receipt'],'source_url':'https://collections.louvre.fr/en/ark:/53355/cl'+c['ark'],'primary_dates':[start,end],'primary_inventory':o['objectNumber'],'primary_title':o['title'],'primary_dimensions':o['dimension']}
      ready.append(item);print('READY',w['title'],'→',item['target_title'])
    r.save_gz(r.RUN/'reviewed-image-matches-v2.json.gz',{'ready':ready,'held':held})
    print('Ready',len(ready),'Held',len(held))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['snapshot','crosswalk','reconcile']);args=p.parse_args()
    globals()[args.command]()
