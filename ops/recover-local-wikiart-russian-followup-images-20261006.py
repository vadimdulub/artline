#!/usr/bin/env python3
"""Nine existing Russian Museum gaps, with explicit alternative-version review."""
import argparse
import collections
import copy
import importlib.util
import json
import uuid
from pathlib import Path
from urllib.parse import urlparse

s=importlib.util.spec_from_file_location('russian',Path(__file__).with_name('recover-local-wikiart-russian-images-20261006.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
wiki,base,core=r.wiki,r.base,r.core
RUN=core.ROOT/'docs/research/local-wikiart-russian-followup-images-20261006'
r.RUN=wiki.RUN=base.RUN=wiki.chicago.RUN=RUN
core.VERSION='local-wikiart-russian-alternatives-v1'
IDS=['da8e749f-92f8-409d-9a8c-499266320f1b','9a97dfc8-9ba7-4cae-a7c1-6e8742b613cf','98b24772-759e-4608-8049-f572be079b5d','1ddd2d3b-c2cf-401b-b94b-66759eb269e2','55f7c6ed-df4e-46fd-b1f3-383907ec4f27','4ebec1df-9151-40f9-8d04-fe6c7975e738','ffa60685-732d-4a80-9b6a-69d167a7b6b9','15f33735-0fee-4739-a5d7-c78a2707754b','7aa750dc-cea8-488a-9ef3-d29fb3128142']
MAX_SOURCE_OPTIONS=3
DATE_VARIANT_IDS=set()
SOURCE_OPTION_TRANSFORM=None
SELECTION='Nine existing Russian Museum gaps with bounded same-title WikiArt alternatives. Initial page is a metadata lead only. Freeze one reviewed physical version before image preparation. Preserve catalogue dates, unknown fields and review status.'

def snapshot():
 if (RUN/'candidates.json').exists():return
 audit=json.loads((r.AUDIT/'discovery.json').read_bytes());leads={x['work']['id']:x for x in audit['leads']}
 with base.connect() as db:
  rows=db.execute('''SELECT a.id::text artwork_id,a.slug,a.title,a.alternate_title,a.creation_year_start,a.creation_year_end,a.date_precision,a.date_display,a.work_type,a.accession_number,
   to_jsonb(a) before_record,i.id::text institution_id,i.slug institution_slug,i.name museum,
   ARRAY(SELECT aa.attribution_role FROM artwork_artists aa WHERE aa.artwork_id=a.id ORDER BY aa.artist_id) roles,
   (SELECT jsonb_agg(to_jsonb(aa) ORDER BY aa.artist_id) FROM artwork_artists aa WHERE aa.artwork_id=a.id) creator_links,
   (SELECT jsonb_agg(to_jsonb(e) ORDER BY e.id) FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id) identifiers,
   COALESCE((SELECT jsonb_agg(to_jsonb(la) ORDER BY la.id) FROM artwork_location_assertions la WHERE la.artwork_id=a.id),'[]') holding_assertions
   FROM artworks a JOIN institutions i ON i.id=a.current_institution_id WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review'
   AND artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision)='eligible' AND artline_has_selection_evidence(a.id) ORDER BY a.id''',(IDS,)).fetchall()
  if len(rows)!=len(IDS):raise ValueError('Selected current gaps changed')
  arts=sorted({x['creator_links'][0]['artist_id'] for x in rows})
  artists={x['record']['id']:x['record'] for x in db.execute('SELECT to_jsonb(a) record FROM artists a WHERE id=ANY(%s::uuid[])',(arts,))}
  aliases,identifiers=collections.defaultdict(list),collections.defaultdict(list)
  for x in db.execute('SELECT to_jsonb(a) record FROM artist_aliases a WHERE artist_id=ANY(%s::uuid[]) ORDER BY id',(arts,)):aliases[x['record']['artist_id']].append(x['record'])
  for x in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(arts,)):identifiers[x['record']['entity_id']].append(x['record'])
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 for c in rows:
  lead=leads[c['artwork_id']];aid=c['creator_links'][0]['artist_id']
  if c['roles']!=['primary'] or len(c['creator_links'])!=1 or aid!=lead['work']['artist_id'] or aid not in r.ARTISTS:raise ValueError('Unique creator changed')
  if any(c[k]!=lead['work'][k] for k in ('title','accession_number','creation_year_start','creation_year_end','date_precision','work_type')):raise ValueError('Audited object changed')
  matches=[x for x in lead['candidates'] if x['completitionYear'] and c['creation_year_start']<=x['completitionYear']<=c['creation_year_end']]
  if c['artwork_id']=='55f7c6ed-df4e-46fd-b1f3-383907ec4f27' or c['artwork_id'] in DATE_VARIANT_IDS:matches=lead['candidates']
  if not 1<=len(matches)<=MAX_SOURCE_OPTIONS:raise ValueError('Unexpected alternative count')
  options=[]
  for selected in matches:
   filename=urlparse(selected['image']).path.split('/')[-1].split('!',1)[0].removesuffix('.jpg')
   if filename=='portrait-of-alexander-bruloff(1)':filename='portrait-of-alexander-bruloff'
   page='https://www.wikiart.org/en/'+lead['source_artist_slug']+'/'+filename
   options.append(dict(page=page,prior_index_lead=selected))
  if SOURCE_OPTION_TRANSFORM is not None:options=SOURCE_OPTION_TRANSFORM(c,options)
  es=[e for e in c['identifiers'] if e['scheme']=='european-russian-session-museum-object']
  if len(es)!=1:raise ValueError('Unique native object absent')
  e=es[0]
  c.update(provider=wiki.PROVIDER,scheme=e['scheme'],external_id=e['external_id'],source_id=e['source_id'],museum_page=e['canonical_url'],page=options[0]['page'],artist=artists[aid]['display_name'],target_ids={'local':c['artwork_id']},creator_authorities=[dict(artist_record=artists[aid],artist_aliases=aliases[aid],artist_identifiers=identifiers[aid])],source_options=options)
 core.save_new(RUN/'prior-discovery.json',(r.AUDIT/'discovery.json').read_bytes())
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=rows,selection=SELECTION))
 docs=[]
 for source in ('AGENTS.md','docs/ARTLINE_IMAGE_USE.md'):
  data=(core.ROOT/source).read_bytes();capture='metadata/authorization/'+Path(source).name;core.save_new(RUN/capture,data);docs.append(dict(source_path=source,capture=capture,sha256=core.sha(data)))
 core.save_new(RUN/'source-authorization.json',dict(at=core.now(),source='WikiArt',target='local',record_actual_rights_separately=True,documents=docs,user_instruction='see new md file - wiki art is fully approved',scope='Selected existing Russian Museum image gaps, with explicit version selection and unchanged catalogue metadata.'))
 print('Snapshotted',len(rows),'existing review gaps',flush=True)

def sources():
 snapshot();fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  r.capture(c['museum_page'],RUN/'metadata/museum'/(c['artwork_id']+'.html'))
  for option in c['source_options']:
   key=core.sha(option['page'].encode())[:20]
   r.capture(option['page'],RUN/'metadata/options'/(key+'.html'))
  ar=r.ARTISTS[c['creator_links'][0]['artist_id']]
  r.capture('https://rusmuseumvrm.ru/reference/classifier/author/'+ar['native']+'/index.php',RUN/'metadata/authors'/(ar['native']+'.html'))
  fetch.metadata('https://www.wikidata.org/wiki/Special:EntityData/'+ar['qid']+'.json')
  print('Captured native and',len(c['source_options']),'source options:',c['title'],flush=True)

def selected(c):
 review=json.loads((RUN/'metadata-identity-review.json').read_bytes())['artworks'][c['artwork_id']]
 choices=[o for o in c['source_options'] if o['page']==review['selected_page']]
 if len(choices)!=1:raise ValueError('Reviewed choice absent from bounded alternatives')
 result=copy.deepcopy(c);result.update(choices[0]);return result

def research():
 snapshot()
 for c in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  choice=selected(c);key=core.sha(choice['page'].encode())[:20]
  data,rc=r.capture(choice['page'],RUN/'metadata/options'/(key+'.html'))
  p=RUN/'metadata/pages'/(c['artwork_id']+'.html')
  core.save_new(p,data);core.save_new(p.with_suffix('.receipt.json'),dict(rc,requested_url=choice['page'],redirects=[],path=str(p.relative_to(core.ROOT)),reused_capture=rc))
 approval=wiki.approval();fetch=core.Fetcher(RUN/'metadata');fetch.defer_long_cooldowns=True
 for original in json.loads((RUN/'candidates.json').read_bytes())['candidates']:
  c=selected(original);path=RUN/'selected'/wiki.PROVIDER/(c['artwork_id']+'.json')
  if path.exists():wiki.verify_image(json.loads(path.read_bytes()));continue
  try:
   data,rc=wiki.capture_page(c,fetch);facts=wiki.page_facts(c,data,rc)
   im=dict(c,before_page=c['page'],page=rc['url'],source_image_url=facts['source_image_url'],rights_status=facts['rights_status'],license_label=facts['license_label'],policy_url=wiki.POLICY,
    creator_credit=c['artist']+'; WikiArt',checked_at=rc['at'],raw=dict(page_capture=rc,wikiart_facts=facts,user_source_approval=approval),
    attribution_text=f"{c['artist']}. {c['title']}. Image source: WikiArt. Source rights label: {facts['source_rights_label'] or 'not specified'}. {rc['url']}. Collected under the user's explicit WikiArt source approval of 6 October 2026; this approval is separate from the source's rights assertion. Full-frame proportional resize and JPEG compression."+(' '+facts['date_note'] if facts['date_note'] else ''))
   wiki.verify_image(im);core.save_new(path,im);core.event(RUN,dict(provider=wiki.PROVIDER,artwork_id=c['artwork_id'],outcome='source_selected'))
   print('Selected:',c['title'],facts['rights_status'],flush=True)
  except Exception as error:
   core.event(RUN,dict(provider=wiki.PROVIDER,artwork_id=c['artwork_id'],outcome='manual_review',reason=str(error)));print('Held:',c['title'],str(error),flush=True)

original_page_facts=r.page_facts
def page_facts(c,data,rc):
 return original_page_facts(selected(c),data,rc)
wiki.page_facts=page_facts
r.snapshot=snapshot

def prepare():
 for p in sorted((RUN/'selected'/wiki.PROVIDER).glob('*.json')):
  im=json.loads(p.read_bytes());dest=RUN/'images'/p.name
  if dest.exists():wiki.verify_image(json.loads(dest.read_bytes()));continue
  wiki.verify_image(im);core.validate_source_image_identity(im)
  with base.connect() as db:
   if db.execute('SELECT primary_media_id FROM artworks WHERE id=%s',(im['artwork_id'],)).fetchone()['primary_media_id']:raise ValueError('Selected gap already filled')
  key=core.sha(im['page'].encode())[:20];receipt=json.loads((RUN/'metadata/option-images'/(key+'.json')).read_bytes());data=Path(receipt['path']).read_bytes()
  if core.sha(data)!=receipt['sha256'] or len(data)!=receipt['bytes'] or receipt['url']!=im['source_image_url']:raise ValueError('Reviewed source original differs')
  archive=base.ARCHIVE/'source-images'/RUN.name/(im['artwork_id']+'-'+receipt['sha256'][:16]+'.image');core.save_new(archive,data)
  result,width,height,quality=core.compress(data)
  if min(width,height)<50 or max(width,height)<200:raise ValueError('Source image too small')
  digest=core.sha(result);path='/assets/artworks/imported/'+RUN.name+'/'+im['artwork_id']+'-'+digest[:16]+'.jpg'
  core.save_new(core.ROOT/'apps/web/public'/path.lstrip('/'),result)
  im.update(path=path,sha256=digest,bytes=len(result),width=width,height=height,jpeg_quality=quality,source_sha256=receipt['sha256'],source_bytes=len(data),source_archive=str(archive),downloaded_at=receipt['at'],response_headers=receipt['headers'],transform='Full-frame proportional resize and JPEG compression; no crop or generated content',media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)))
  im['raw']['reused_source_download']=receipt
  core.save_new(dest,im);core.event(RUN,dict(provider=wiki.PROVIDER,artwork_id=im['artwork_id'],outcome='prepared'))
  print('Prepared selected version:',im['title'],flush=True)
 base.prepare('contact-sheets-only')

def verify():
 r.verify()
 for im in base.prepared():
  key=core.sha(im['page'].encode())[:20];rc=json.loads((RUN/'metadata/option-images'/(key+'.json')).read_bytes())
  if im['raw']['reused_source_download']!=rc or core.sha(Path(rc['path']).read_bytes())!=im['source_sha256']:raise ValueError('Reviewed original reuse evidence differs')
 for p in (RUN/'metadata/option-images').glob('*.json'):
  rc=json.loads(p.read_bytes());data=Path(rc['path']).read_bytes()
  if core.sha(data)!=rc['sha256'] or len(data)!=rc['bytes']:raise ValueError('Private alternative source evidence differs')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['snapshot','sources','research','references','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='references':r.references()
 elif a.phase=='apply':base.apply()
 else:globals()[a.phase]()
