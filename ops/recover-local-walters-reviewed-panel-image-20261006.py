#!/usr/bin/env python3
"""Attach the explicitly labelled Virgin panel of one existing Deesis group."""
import argparse,importlib.util,json,uuid
from pathlib import Path

spec=importlib.util.spec_from_file_location('native',Path(__file__).with_name('recover-local-walters-native-images-20261006.py'))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);core=w.core
PRIOR=w.RUN;RUN=core.ROOT/'docs/research/local-walters-reviewed-panel-image-20261006';w.RUN=RUN;w.base.RUN=RUN
VIEW='Virgin panel only; Christ and John the Baptist panels not shown'
native_facts=w.facts
def facts(im,path):
 if im['artwork_id']!=w.ICON:raise ValueError('Only the individually reviewed Deesis group is in scope')
 result=native_facts(im,path);result['image_scope']=VIEW
 return result
w.facts=facts

def verify_image(im):
 w.verify_image(im)
 if im.get('view_label')!=VIEW or VIEW not in im.get('alt_text','') or VIEW not in im['attribution_text']:raise ValueError('Partial group view must be explicit in label, accessible text and credit')
 proof=json.loads((RUN/'prior-full-group-rejection.json').read_bytes());path=core.ROOT/proof['prior_prepared_image'];old=json.loads(path.read_bytes())
 if core.sha(path.read_bytes())!=proof['prior_metadata_sha256'] or core.sha(Path(old['source_archive']).read_bytes())!=proof['original_source_sha256']:raise ValueError('Prior private source evidence changed')
 if im['raw'].get('archive_reuse')!=dict(source_archive=old['source_archive'],source_sha256=old['source_sha256'],downloaded_at=old['downloaded_at'],previous_operation=PRIOR.name):raise ValueError('Existing source reuse provenance differs')
 if im['source_image_url']!=old['source_image_url']:raise ValueError('Reused source URL differs')

def research():
 c=json.loads((RUN/'candidates.json').read_bytes())['candidates'][0];path=RUN/'metadata/37.568.html';cap=json.loads(path.with_suffix('.receipt.json').read_bytes());obj=facts(c,path)
 old=json.loads((PRIOR/'images'/(w.ICON+'.json')).read_bytes())
 im=dict(c,page='https://art.thewalters.org/object/37.568/',source_image_url=obj['image_url'],rights_status='cc0',license_label='CC0 1.0',policy_url=w.CC0,creator_credit=obj['credit'],checked_at=core.now(),view_label=VIEW,alt_text=c['title']+' — '+VIEW+'. Archival monochrome photograph.',raw=dict(native_capture=cap,native_facts=obj,archive_reuse=dict(source_archive=old['source_archive'],source_sha256=old['source_sha256'],downloaded_at=old['downloaded_at'],previous_operation=PRIOR.name)),attribution_text=c['artist']+'. '+c['title']+', '+c['date_display']+'. '+VIEW+'. '+obj['credit']+'. Inventory 37.568. CC0 ('+w.CC0+'). Source-provided archival monochrome reproduction; original painting colours are not represented. Full source frame retained; proportional JPEG resize. https://art.thewalters.org/object/37.568/')
 verify_image(im);core.save_new(RUN/'selected'/w.PROVIDER/(w.ICON+'.json'),im);core.event(RUN,dict(provider=w.PROVIDER,artwork_id=w.ICON,outcome='rights_selected',reason='Qualified Virgin-panel representation only; historical full-group rejection preserved'))

def prepare():
 im=json.loads((RUN/'selected'/w.PROVIDER/(w.ICON+'.json')).read_bytes());verify_image(im)
 old=json.loads((PRIOR/'images'/(w.ICON+'.json')).read_bytes());data=Path(old['source_archive']).read_bytes();compressed,width,height,quality=core.compress(data);digest=core.sha(compressed)
 archive=w.base.ARCHIVE/'source-images'/RUN.name/(w.ICON+'-'+core.sha(data)[:16]+'.image');core.save_new(archive,data)
 path='/assets/artworks/imported/'+RUN.name+'/'+w.ICON+'-'+digest[:16]+'.jpg';core.save_new(core.ROOT/'apps/web/public'/path.lstrip('/'),compressed)
 im.update(path=path,sha256=digest,bytes=len(compressed),width=width,height=height,jpeg_quality=quality,source_sha256=core.sha(data),source_bytes=len(data),source_archive=str(archive),downloaded_at=old['downloaded_at'],prepared_at=core.now(),response_headers=old['response_headers'],transform='Reused archived source; full-frame proportional resize and JPEG compression; no crop or generated content',media_id=str(uuid.uuid5(uuid.NAMESPACE_URL,path)))
 verify_image(im);core.save_new(RUN/'images'/(w.ICON+'.json'),im);core.event(RUN,dict(provider=w.PROVIDER,artwork_id=w.ICON,outcome='prepared',path=path))
 print('Prepared labelled panel from verified private original; no image redownload',path,flush=True)

def attach(db,im,target):
 if target!='local':raise ValueError('Only local attachment authorized')
 verify_image(im)
 result=w.base.m.original_attach(db,im,target)
 if result=='attached':
  db.execute('UPDATE media_assets SET creator_credit=%s,attribution_text=%s,alt_text=%s WHERE id=%s',(im['creator_credit'],im['attribution_text'],im['alt_text'],im['media_id']))
  db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(im['artwork_id'],im['media_id'],VIEW))
  db.execute('UPDATE media_rights_evidence SET rights_basis=%s WHERE media_id=%s',('Exact native Walters inventory, anonymous Russian maker label and century bounds retained; selected photograph has its own CC0 grant. Image depicts the Virgin panel only, explicitly stated in the view label, accessible text and attribution. Full-group use remains rejected; no catalogue metadata or publication changes.',im['media_id']))
 return result
w.base.m.attach=attach

def verify():
 w.base.verify();im=w.base.prepared()[0];verify_image(im);w.verify_rights_and_holds()
 with w.base.connect() as db:
  row=db.execute('SELECT m.alt_text,m.attribution_text,am.view_label FROM media_assets m JOIN artwork_media am ON am.media_id=m.id WHERE m.id=%s AND am.artwork_id=%s',(im['media_id'],w.ICON)).fetchone()
  if row!=dict(alt_text=im['alt_text'],attribution_text=im['attribution_text'],view_label=VIEW):raise ValueError('Stored partial-view qualification differs')
 core.save_new(RUN/'qualified-view-verification.json',dict(at=core.now(),passed=True,view_label=VIEW,anonymous_maker_label_preserved=True,original_full_group_rejection_preserved=True))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);a=p.parse_args()
 if a.phase=='research':research()
 elif a.phase=='prepare':prepare()
 elif a.phase=='apply':w.base.apply()
 else:verify()
