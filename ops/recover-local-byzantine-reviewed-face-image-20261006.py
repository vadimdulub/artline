#!/usr/bin/env python3
"""One reviewed icon-face attachment; preserve unknown dates and review status."""
import argparse,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from bs4 import BeautifulSoup
from psycopg.types.json import Jsonb

spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('recover-local-commons-images-20261005.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);core=base.core
RUN=core.ROOT/'docs/research/local-byzantine-reviewed-face-image-20261006';base.RUN=RUN
AID='b86763e3-1d07-5a31-a816-2088c1c3a0d3';IID='2b06cc02-0efe-458c-80e0-cc4c27ca5494'
PROVIDER='byzantine-reviewed-face';core.PROVIDERS[PROVIDER]='Wikimedia Commons — independent photograph'
POLICY='https://commons.wikimedia.org/wiki/Template:Attribution'
FILE="File:1988 - Byzantine Museum, Athens - Crucifixion - 9th-13th century - Photo by Giovanni Dall'Orto, Nov 12 2.jpg"
VIEW='Crucifixion face only; reverse Hodegetria face not shown'
LABEL='Attribution-only permission (photograph); public-domain artwork'
CREDIT="Photograph: Giovanni Dall'Orto (G.dallorto), 12 November 2009"
NATIVE='https://www.ebyzantinemuseum.gr/?i=bxm.en.exhibit&id=32'
SCOPE_REVIEW=dict(decision='Approve this independently licensed face photograph for the existing review record only',source_periods=['9th-century front layer','10th-century front additions','13th-century front repaint','16th-century reverse repaint'],source_material_precedes_1970=True,unknown_catalogue_dates_preserved=True,publication_status_preserved=True,view_label=VIEW)

def clean(value):return ' '.join(value.split())
def plain(value):return clean(BeautifulSoup(value,'html.parser').get_text(' ',strip=True))

def candidate_guard(c):
 expected=dict(artwork_id=AID,institution_id=IID,accession_number='ΒΧΜ 00995',external_id='32',scheme='european-icons-athens-object',date_display='Date not stated',date_precision='unknown',creation_year_start=None,creation_year_end=None,object_form='icon',unlinked_creator_label='Unidentified artist (not named in the source catalogue)')
 if any(c.get(k)!=v for k,v in expected.items()) or c['creators'] or c['creator_links'] or c['roles']:raise ValueError('Individually reviewed icon identity, anonymous label or unknown dates differ')
 if c['before_record']['status']!='review' or c['before_record']['primary_media_id'] is not None or not c['before_record']['research_candidate']:raise ValueError('Expected existing missing-image research record absent')

def source_facts(c,native,page,sdc,rendered,policy):
 candidate_guard(c);soup=BeautifulSoup(native,'html.parser');text=plain(native)
 if [clean(n.get_text(' ',strip=True)) for n in soup.find_all('h2')]!=[c['title']]:raise ValueError('Native object title differs')
 if 'Exhibit Number: '+c['accession_number'] not in text or 'Measurement: 87 x 63 cm' not in text:raise ValueError('Native inventory or dimensions differ')
 for phrase in ['9th c.','10th c.','13th-century phase','over-painted in the 16th century']:
  if phrase not in text:raise ValueError('Individual native dating evidence absent')
 if page.get('pageid')!=16605336 or page.get('title')!=FILE or page.get('ns')!=6:raise ValueError('Exact Commons file differs')
 if len(page.get('imageinfo',[]))!=1 or len(page.get('revisions',[]))!=1:raise ValueError('Commons file evidence ambiguous')
 info=page['imageinfo'][0];wiki=page['revisions'][0]['slots']['main']['*'];meta=info['extmetadata']
 if 'Exhibit Number: '+c['accession_number'] not in wiki or c['title'] not in wiki or '87 x 63 cm' not in wiki:raise ValueError('Commons object identity differs')
 if '{{Licensed-PD-Art|PD-old-100|rawphotolicense={{self|Attribution}}}}' not in wiki:raise ValueError('Separately scoped photograph permission absent')
 if plain(meta['Credit']['value'])!='Own work' or plain(meta['Artist']['value'])!='G.dallorto':raise ValueError('Independent photographer credit differs')
 for doc in [plain(rendered),plain(policy)]:
  if 'provided that the copyright holder is properly attributed' not in doc or 'Redistribution, derivative work, commercial use, and all other use is permitted.' not in doc:raise ValueError('Attribution permission terms absent')
 if sdc.get('id')!='M16605336' or sdc.get('lastrevid')!=page['revisions'][0]['revid']:raise ValueError('Structured file revision differs')
 statements=sdc.get('statements',{})
 def values(prop):return [x['mainsnak'].get('datavalue',{}).get('value') for x in statements.get(prop,[]) if x.get('rank')!='deprecated']
 if values('P275')!=[{'entity-type':'item','numeric-id':98923445,'id':'Q98923445'}]:raise ValueError('Structured photograph licence differs')
 if {v['id'] for v in values('P6216')}!={'Q50423863','Q19652'}:raise ValueError('Scoped artwork/photograph copyright statements differ')
 if values('P4092')!=[info['sha1']] or info['sha1']!='2705366c70deaa00e6edbb9b268b65fd77427f77':raise ValueError('Exact reviewed photograph checksum differs')
 if values('P1163')!=['image/jpeg'] or (info['width'],info['height'],info['size'])!=(1258,1800,1187634):raise ValueError('Photograph dimensions or type differ')
 parsed=urlsplit(info['url'])
 if parsed.fragment or not re.fullmatch(r'https://upload\.wikimedia\.org/wikipedia/commons/[0-9a-f]/[0-9a-f]{2}/[^/]+\.jpg',parsed._replace(query='').geturl()):raise ValueError('Original photograph URL unapproved')
 if parse_qs(parsed.query) not in ({},{'utm_source':['commons.wikimedia.org'],'utm_campaign':['imageinfo'],'utm_content':['original']}):raise ValueError('Unexpected source URL query')
 return dict(native_url=NATIVE,inventory=c['accession_number'],native_title=c['title'],commons_page_id=page['pageid'],commons_revision=page['revisions'][0]['revid'],image_url=info['url'],source_page_url=info['descriptionurl'],source_sha1=info['sha1'],photographer=CREDIT,photograph_permission=LABEL,view_scope=VIEW,editorial_review=SCOPE_REVIEW)

def sources():
 captures={};docs={}
 for name,suffix in [('commons-file','.json'),('commons-page','.html'),('native-object','.html'),('structured-data','.json'),('attribution-policy','.html')]:
  path=RUN/'metadata'/(name+suffix);cap=json.loads((RUN/'metadata'/(name+'.receipt.json')).read_bytes())
  if cap['path']!=str(path.relative_to(core.ROOT)) or core.sha(path.read_bytes())!=cap['sha256']:raise ValueError('Pinned source capture differs')
  captures[name]=cap;docs[name]=json.loads(path.read_bytes()) if suffix=='.json' else path.read_text()
 if captures['native-object']['url']!=NATIVE or captures['attribution-policy']['url']!=POLICY:raise ValueError('Native/policy source URL differs')
 pages=list(docs['commons-file']['query']['pages'].values())
 if len(pages)!=1:raise ValueError('Commons response not exact single file')
 return captures,docs,pages[0],docs['structured-data']['entities']['M16605336']

def verify_image(im):
 captures,docs,page,sdc=sources();facts=source_facts(im,docs['native-object'],page,sdc,docs['commons-page'],docs['attribution-policy'])
 if im['raw']!=dict(captures=captures,commons=page,structured_data=sdc,source_facts=facts):raise ValueError('Reviewed complete source evidence differs')
 expected=dict(rights_status='licensed',license_label=LABEL,policy_url=POLICY,creator_credit=CREDIT,page=facts['source_page_url'],source_image_url=facts['image_url'],commons_original_sha1=facts['source_sha1'],view_label=VIEW)
 if any(im.get(k)!=v for k,v in expected.items()):raise ValueError('Image permission, credit or face scope differs')
 for part in [CREDIT,VIEW,POLICY,'unknown']:
  if part not in im['attribution_text']:raise ValueError('Required photo attribution or review qualification omitted')
 if VIEW not in im['alt_text']:raise ValueError('Accessible image text must identify the pictured face')
 if base.policy_hold(im):raise ValueError('Conflicting source policy remains unresolved')

def research():
 c=json.loads((RUN/'candidates.json').read_bytes())['candidates'][0];captures,docs,page,sdc=sources()
 facts=source_facts(c,docs['native-object'],page,sdc,docs['commons-page'],docs['attribution-policy'])
 im=dict(c,provider=PROVIDER,page=facts['source_page_url'],source_image_url=facts['image_url'],rights_status='licensed',license_label=LABEL,policy_url=POLICY,creator_credit=CREDIT,checked_at=core.now(),commons_original_sha1=facts['source_sha1'],raw=dict(captures=captures,commons=page,structured_data=sdc,source_facts=facts),view_label=VIEW,alt_text=c['title']+' — '+VIEW+'. Anonymous maker.',attribution_text=c['title']+'. Inventory '+c['accession_number']+'. '+VIEW+'. '+CREDIT+'. Photograph used under attribution-only permission ('+POLICY+'). Underlying icon: public domain. Catalogue creation date remains unknown and under review. Full source frame retained; proportional resize and JPEG compression. '+facts['source_page_url'])
 verify_image(im);core.save_new(RUN/'selected'/PROVIDER/(AID+'.json'),im);core.event(RUN,dict(provider=PROVIDER,artwork_id=AID,outcome='rights_selected',reason='Individual pre-1970 source-material review, exact inventory and photographer permission; unknown catalogue date and publication hold preserved'))

def attach(db,im,target):
 if target!='local':raise ValueError('Only local image attachment authorized')
 verify_image(im)
 row=db.execute('''SELECT to_jsonb(a) record,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,artline_has_selection_evidence(a.id) selected FROM artworks a WHERE a.id=%s FOR UPDATE''',(AID,)).fetchone()
 if not row or row['record']!=im['before_record'] or row['scope']!='review' or not row['selected']:raise ValueError('Reviewed icon state or scope changed')
 # This explicit image-only case leaves the existing catalogue classification
 # in review. Normal eligible-date attachment and publication gates are intact.
 db.execute('''INSERT INTO media_assets(id,storage_kind,storage_path,source_page_url,provider_name,mime_type,width,height,byte_size,checksum_sha256,alt_text,rights_status,license_label,license_url,creator_credit,attribution_text,retrieved_at,verified_at,verified_by)
 VALUES(%s,'local',%s,%s,%s,'image/jpeg',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(im['media_id'],im['path'],im['page'],core.PROVIDERS[PROVIDER],im['width'],im['height'],im['bytes'],im['sha256'],im['alt_text'],im['rights_status'],im['license_label'],im['policy_url'],im['creator_credit'],im['attribution_text'],im['downloaded_at'],im['checked_at'],core.ACTOR))
 db.execute('''INSERT INTO media_rights_evidence(media_id,source_id,source_record_id,source_checksum,source_image_url,policy_url,rights_basis,adapter_version,checked_at,evidence_json) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',(im['media_id'],im['source_id'],im['external_id'],core.sha(core.encode(im['raw'])),im['source_image_url'],POLICY,'Exact existing museum inventory and independently authored Commons photograph; public-domain underlying icon and separate attribution-only photo permission. Reviewed historical layers all precede 1970. One pictured face explicitly labelled; unknown catalogue dates and review/publication hold preserved.','local-byzantine-reviewed-face-v1',im['checked_at'],Jsonb({k:v for k,v in im.items() if k not in ('artist','title')})))
 db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(AID,im['media_id'],VIEW))
 db.execute('UPDATE artworks SET primary_media_id=%s,revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND primary_media_id IS NULL',(im['media_id'],core.ACTOR,AID))
 return 'attached'
base.m.attach=attach

def verify():
 base.verify();im=base.prepared()[0];verify_image(im)
 with base.connect() as db:
  row=db.execute('''SELECT a.status,a.date_precision,a.creation_year_start,a.creation_year_end,artline_creation_scope(a.creation_year_start,a.creation_year_end,a.date_precision) scope,m.rights_status,m.alt_text,m.attribution_text,am.view_label,e.evidence_json,e.source_checksum FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id JOIN artwork_media am ON am.artwork_id=a.id AND am.media_id=m.id JOIN media_rights_evidence e ON e.media_id=m.id WHERE a.id=%s''',(AID,)).fetchone()
  if (row['status'],row['scope'],row['date_precision'],row['creation_year_start'],row['creation_year_end'])!=('review','review','unknown',None,None):raise ValueError('Catalogue review/date safeguards changed')
  for k in ['rights_status','alt_text','attribution_text','view_label']:
   if row[k]!=im[k]:raise ValueError('Stored photo scope or permission differs')
  if row['source_checksum']!=core.sha(core.encode(im['raw'])) or row['evidence_json']!={k:v for k,v in im.items() if k not in ('artist','title')}:raise ValueError('Stored complete evidence differs')
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 core.save_new(RUN/'source-rights-verification.json',dict(at=core.now(),passed=True,verified=1,review_status_and_unknown_dates_preserved=True,complete_stored_evidence_verified=True,face_scope_explicit_in_view_label_alt_text_and_attribution=True))
 core.save_new(RUN/'report.json',dict(at=core.now(),local_only=True,reviewed=1,attached=1,baseline_after=baseline,production_changed=False,all_catalogue_metadata_preserved=True,remaining_catalogue_work=True,http_verification='No new delivery receipt following earlier server timeouts'))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':
  for path in (RUN/'selected'/PROVIDER).glob('*.json'):verify_image(json.loads(path.read_bytes()))
  base.prepare(PROVIDER)
 elif a.phase=='apply':base.apply()
 else:verify()
