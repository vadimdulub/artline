#!/usr/bin/env python3
"""Read-only, metadata-only review of nineteen selected priority artwork gaps."""
import collections,importlib.util,json
from pathlib import Path

s=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(s);s.loader.exec_module(base);core=base.core
RUN=core.ROOT/'docs/research/local-open-museum-priority-images-20261006'

def select():
 if (RUN/'candidates.json').exists():return
 leads=json.loads(Path('/private/tmp/artline-open-museum-priority-gaps.json').read_bytes());counts=collections.Counter();ids=[]
 for x in leads:
  if not x['artists'] or not any(n in x['artists'] for n in ['Repin','Shishkin','Orłowski','Kandinsky','Jawlensky','Korovin','Bakst']):continue
  key=(x['slug'],x['artists']);counts[key]+=1
  if counts[key]<=3:ids.append(x['id'])
 with base.connect() as db:
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.date_display,a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,a.accession_number,to_jsonb(a) before_record,i.slug institution_slug,i.name museum,i.website_url,i.wikidata_id institution_qid,e.scheme,e.external_id,e.source_id::text,e.canonical_url page,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   (SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'death',ar.death_year,'qid',(SELECT ae.external_id FROM external_identifiers ae WHERE ae.entity_type='artist' AND ae.entity_id=ar.id AND ae.scheme='wikidata')) ORDER BY ar.id) FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id) creators,
   (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
   (SELECT jsonb_agg(to_jsonb(ei) ORDER BY ei.id) FROM external_identifiers ei WHERE ei.entity_type='artwork' AND ei.entity_id=a.id) identifiers
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id JOIN external_identifiers e ON e.entity_type='artwork' AND e.entity_id=a.id WHERE a.id=ANY(%s::uuid[]) AND e.scheme=ANY(%s) AND a.primary_media_id IS NULL AND a.status='review' AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id) ORDER BY a.id''',(ids,['european-met-the-met-object','met-object','european-cleveland-cleveland-museum-of-art-object','european-chicago-art-institute-of-chicago-object'])).fetchall()
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 for x in rows:x.update(artist='; '.join(a['name'] for a in x['creators']),target_ids={'local':x['artwork_id']},provider={'the-met':'met','art-institute-of-chicago':'chicago','cleveland-museum-of-art':'cleveland'}[x['institution_slug']])
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows))

def audit():
 select();f=core.Fetcher(RUN/'metadata');events=core.latest_events(RUN)
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  if c['artwork_id'] in events:continue
  provider=c['provider'];oid=c['external_id'];url={'met':'https://collectionapi.metmuseum.org/public/collection/v1/objects/','cleveland':'https://openaccess-api.clevelandart.org/api/artworks/','chicago':'https://api.artic.edu/api/v1/artworks/'}[provider]+oid
  try:
   d=f.metadata(url);raw=d.get('data',d)
   if str(raw.get('objectID') if provider=='met' else raw.get('id'))!=oid:raise ValueError('Native object ID differs')
   accession=raw.get({'met':'accessionNumber','cleveland':'accession_number','chicago':'main_reference_number'}[provider])
   if accession!=c['accession_number']:raise ValueError('Native inventory differs')
   if provider=='met':grant=raw.get('isPublicDomain') is True and not raw.get('rightsAndReproduction');image=bool(raw.get('primaryImageSmall'));notice=raw.get('rightsAndReproduction')
   elif provider=='cleveland':grant=raw.get('share_license_status')=='CC0' and not raw.get('copyright');image=bool(raw.get('images',{}).get('web',{}).get('url'));notice=raw.get('copyright') or raw.get('share_license_status')
   else:grant=raw.get('is_public_domain') is True and not raw.get('copyright_notice');image=bool(raw.get('image_id'));notice=raw.get('copyright_notice')
   result=dict(provider=provider,artwork_id=c['artwork_id'],outcome='native_open_image_lead' if grant and image else 'manual_review',reason='Native image needs full identity, rights and visual review before download' if grant and image else 'Current native record does not expose an explicitly open primary image',native_url=url,native_inventory=accession,open_grant=grant,primary_image_available=image,notice=notice,capture=str((f.cache/(core.sha(url.encode())+'.json')).relative_to(core.ROOT)))
  except Exception as error:result=dict(provider=provider,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(error)[:350],native_url=url)
  core.event(RUN,result);print(c['artist'],c['title'],result['outcome'],result.get('open_grant'),result.get('primary_image_available'),flush=True)

if __name__=='__main__':audit()
