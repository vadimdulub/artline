#!/usr/bin/env python3
"""Select exact, reusable images from bounded Russian research results."""
import argparse,collections,csv,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlencode,urlparse
from bs4 import BeautifulSoup
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('research-russian-deep-images.py'));r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
core=r.core;RUN=r.RUN;IMAGES=RUN/'images'
def plain(s):return BeautifulSoup(s,'html.parser').get_text(' ',strip=True)
def pin(i):core.save_new(IMAGES/'selected'/i['provider']/(i['artwork_id']+'.json'),i)

def commons(deeper=False,photos=False):
 output=RUN/'photographs-verified-aliases' if photos else RUN/'accession-deeper' if deeper else RUN
 matches=json.loads((output/'new-commons-identity-matches.json').read_bytes());out=[];deferred=[]
 licenses={'Public domain':'public_domain','CC0':'cc0','CC BY 2.0':'cc_by','CC BY 3.0':'cc_by','CC BY 4.0':'cc_by','CC BY-SA 2.0':'cc_by_sa','CC BY-SA 2.5':'cc_by_sa','CC BY-SA 3.0':'cc_by_sa','CC BY-SA 4.0':'cc_by_sa'}
 for m in matches:
  w=m['target'];options=[]
  for p in m['files']:
   try:
    info=p['imageinfo'][0];meta=info['extmetadata'];field=lambda k:meta.get(k,{}).get('value','');label=m.get('photo_license') or field('LicenseShortName')
    assert label in licenses and not field('Restrictions'),'Unresolved per-file rights'
    if label=='Public domain':assert field('Copyrighted')=='False','Conflicting copyright status'
    assert not re.search(r'\b(?:rusmuseumvrm\.ru|(?:en\.)?rusmuseum\.ru)\b',field('Credit'),re.I),'Russian Museum reproduction source permission conflict'
    assert not re.search(r'\b(detail|detailled|collage|montage)\b|фрагмент',p['title'],re.I),'Detail or composite needs review'
    policy=m.get('photo_license_url') or ('https://creativecommons.org/publicdomain/mark/1.0/' if label=='Public domain' else field('LicenseUrl').replace('http://','https://'))
    assert policy.startswith('https://creativecommons.org/'),'Missing explicit license URL'
    credit=m.get('image_credit') or plain(field('Artist'));assert credit,'Missing reproduction creator credit'
    url=info.get('thumburl') or info['url'];assert urlparse(url).hostname in {'upload.wikimedia.org','thumb.wikimedia.org'}
    assert info.get('mime','').startswith('image/') and info['width']>200 and info['height']>200,'Unsuitable image format or dimensions'
    text=p['revisions'][0]['slots']['main']['*'];assert not re.search(r'\{\{\s*(?:delete|copyvio|no permission|disputed|wrong license|superseded)\b',text,re.I),'File dispute or superseded image needs review'
    options.append((p,info,label,policy,credit))
   except (AssertionError,KeyError,ValueError) as error:deferred.append({'artwork_id':w['id'],'file':p['title'],'reason':str(error)})
  if not options:continue
  options.sort(key=lambda x:(x[2] not in ('Public domain','CC0'),x[0]['title'].lower().endswith(('.tif','.tiff')),-min(x[1]['width'],x[1]['height']),x[0]['title']))
  p,info,label,policy,credit=options[0];e=next(e for e in w['identifiers'] if e['scheme']=='european-russian-session-museum-object');artist=m['artist']['display_name']
  i={'artwork_id':w['id'],'slug':w['slug'],'title':w['title'],'artist':artist,'countries':['RU'],'provider':'russian-deep-commons','scheme':e['scheme'],'external_id':e['id'],'page':info['descriptionurl'],'source_image_url':info.get('thumburl') or info['url'],'policy_url':policy,'rights_status':licenses[label],'license_label':label,'checked_at':core.now(),'creator_credit':credit,'attribution_text':f"{artist}. {w['title']}. Image credit: {credit}. {plain(info['extmetadata'].get('Attribution',{}).get('value',''))} {info['descriptionurl']}. {label} ({policy}). Full-frame proportional resize and JPEG compression.",'raw':{'identity_chain':{k:v for k,v in m.items() if k!='files'},'commons_page':p},'identity_basis':m['identity_basis'],'source_variant':'commons_thumbnail' if info.get('thumburl') else 'commons_original'}
  if not info.get('thumburl'):i['commons_original_sha1']=info['sha1']
  pin(i);out.append({k:i[k] for k in ('artwork_id','artist','title','page','license_label')})
 core.save_new(output/'new-commons-selection.json',out);core.save_new(output/'new-commons-rights-deferred.json',deferred);print('New Commons selections',len(out),'deferred files',len(deferred),flush=True)

class Metadata:
 def metadata(self,url):return r.fetch(url)

def photographs():
 d,g=r.gaps();artists={a['id']:a for a in d['artists']};authors=json.loads((r.ROOT/'docs/research/russian-painters-20260913/selected-authors.json').read_bytes());selected={p.stem for p in (IMAGES/'selected').glob('*/*.json')};pages={};good=[];deferred=[]
 for path in [RUN/'accession-search-files.json',RUN/'accession-deeper/accession-search-files.json']:pages.update(json.loads(path.read_bytes()))
 byinventory=collections.defaultdict(list)
 for p in pages.values():
  text=p.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
  for url in set(re.findall(r'https://rusmuseumvrm\.ru/data/[^\s\]<>"|]+',text)):
   match=re.search(r'(zhb|zh|r)[_-](\d+)/index\.php$',url,re.I)
   if match:byinventory[{'zhb':'жб','zh':'ж','r':'р'}[match[1].lower()]+match[2]].append((p,url))
 for w in g:
  if w['id'] in selected or w['institution']!='state-russian-museum' or len(w['creators'] or [])!=1 or w['creators'][0]['role']!='primary':continue
  e=next((e for e in w['identifiers'] if e['scheme']=='european-russian-session-museum-object'),None)
  if not e:continue
  candidates=[]
  for p,url in byinventory.get(r.inventory_key(r.accession_hint(w) or ''),[]):
   text=p.get('revisions',[{}])[0].get('slots',{}).get('main',{}).get('*','')
   if not re.search(r'\{\{\s*own(?: photo)?\s*\}\}',text,re.I) or '{{User:Shakko/Credit}}' not in text:continue
   meta=p.get('imageinfo',[{}])[0].get('extmetadata',{})
   if not re.search(r'\{\{\s*cc-by-sa-4\.0\s*\}\}',text,re.I):continue
   candidates.append((p,url))
  if not candidates:continue
  a=artists[w['creators'][0]['id']];q=next((e['id'] for e in a['identifiers'] if e['scheme']=='wikidata'),None);source=authors.get(q)
  if not source:continue
  if not a.get('death_year') or a['death_year']>1951:
   candidates=[(p,url) for p,url in candidates if re.search(r'\{\{\s*PD-(?:old|RusEmpire|Russia)',p['revisions'][0]['slots']['main']['*'],re.I)]
   if not candidates:
    deferred.append({'artwork_id':w['id'],'reason':'Photograph license found, but underlying artwork public-domain evidence needs review'});continue
  try:
   soup,capture=r.museum_detail(e['url']);txt=lambda sel:soup.select_one(sel).get_text(' ',strip=True) if soup.select_one(sel) else '';inv=txt('[title="Инвентарный номер"]');title=txt('.work__title');links=[a.get('href') for a in soup.select('.work__author a')]
   assert inv and r.inventory_key(inv)==r.inventory_key(r.accession_hint(w)),'Museum accession conflict'
   assert r.norm(title)==r.norm(w['title']),'Museum title conflict'
   assert len(links)==1 and source['url'].removeprefix('https://rusmuseumvrm.ru') in links,'Museum creator conflict'
   verified=[];aliases=[]
   for p,url in candidates:
    other,othercapture=r.museum_detail(url);otherinv=other.select_one('[title="Инвентарный номер"]');othertitle=other.select_one('.work__title');otherlinks=[a.get('href') for a in other.select('.work__author a')]
    assert otherinv and r.inventory_key(otherinv.get_text(' ',strip=True))==r.inventory_key(inv),'Cited museum URL inventory mismatch'
    assert othertitle and r.norm(othertitle.get_text(' ',strip=True))==r.norm(title) and otherlinks==links,'Cited museum URL title or creator mismatch'
    verified.append(p);aliases.append({'url':url,'museum_capture':othercapture})
   good.append({'target':w,'artist':a,'source_artist':source,'museum_inventory':inv,'museum_title':title,'museum_date':txt('.period'),'museum_capture':capture,'museum_author_links':links,'verified_museum_aliases':aliases,'files':verified,'image_credit':'Photo: Wikipedia / Shakko (Sofia Bagdasarova)','photo_license':'CC BY-SA 4.0','photo_license_url':'https://creativecommons.org/licenses/by-sa/4.0/','identity_basis':'Official museum object URL cited by an independent own-work Commons photograph and existing catalogue URL both confirm the same accession, title and creator authority. Explicit CC BY-SA 4.0 photograph template and Shakko credit preserved separately from underlying artwork rights.'})
  except (AssertionError,ValueError) as error:deferred.append({'artwork_id':w['id'],'reason':str(error)})
  print('Independent photograph identities',len(good),'deferred',len(deferred),flush=True)
 core.save_new(RUN/'photographs-verified-aliases/new-commons-identity-matches.json',good);core.save_new(RUN/'photographs-verified-aliases/new-commons-identity-deferred.json',deferred);commons(photos=True)

def museums():
 d,works=r.gaps();artists={a['id']:a for a in d['artists']};schemes={v:k for k,v in core.SCHEMES.items() if k!='rijks'};schemes.update({'met-object':'met','aic-object':'chicago'});targets=[]
 for w in works:
  if len(w['creators'] or [])!=1 or w['creators'][0]['role']!='primary':continue
  e=next((e for e in w['identifiers'] or [] if e['scheme'] in schemes),None)
  if e:targets.append((w,e,schemes[e['scheme']]))
 core.save_new(RUN/'direct-museum-targets.json',[{'target':w,'identifier':e,'provider':p} for w,e,p in targets])
 nga={};chicago={};out=[];deferred=[]
 wanted={e['id'] for w,e,p in targets if p=='nga'}
 source=r.ROOT/'docs/research/image-research-seven-rounds-20260913-pass2/round-07-nga-prints/metadata/nga/nga-published-images.csv'
 receipt=json.loads(source.with_suffix('.receipt.json').read_bytes());assert core.sha(source.read_bytes())==receipt['sha256']
 with source.open() as f:
  for row in csv.DictReader(f):
   oid=row.get('depictstmsobjectid');
   if oid in wanted and row.get('openaccess')=='1' and row.get('viewtype')=='primary':
    assert oid not in nga,'Ambiguous NGA primary image';nga[oid]=row
 core.save_new(RUN/'nga-scoped-open-images.json',{'source':str(source.relative_to(r.ROOT)),'receipt':receipt,'objects':nga})
 ids=[e['id'] for w,e,p in targets if p=='chicago']
 if ids:
  data=r.fetch('https://api.artic.edu/api/v1/artworks?'+urlencode({'ids':','.join(ids),'limit':100,'fields':'id,title,main_reference_number,artist_display,date_display,date_start,date_end,image_id,is_public_domain,copyright_notice'}))
  chicago={str(x['id']):x for x in data['data']}
 for w,e,p in targets:
  c={'artwork_id':w['id'],'slug':w['slug'],'title':w['title'],'artist':artists[w['creators'][0]['id']]['display_name'],'provider':p,'scheme':e['scheme'],'external_id':e['id'],'countries':['RU'],'page':e['url']}
  try:
   i=core.image_record(c,Metadata(),nga,chicago)
   if not i:deferred.append({'artwork_id':w['id'],'provider':p,'reason':'No explicitly reusable primary image in exact museum object record'});continue
   raw=i['raw'];inventory=raw.get('accessionNumber') if p=='met' else raw.get('accession_number') if p=='cleveland' else raw.get('main_reference_number') if p=='chicago' else None
   if inventory and w.get('accession_number'):assert r.inventory_key(inventory)==r.inventory_key(w['accession_number']),'Museum inventory mismatch'
   i.update(provider='russian-deep-'+p,identity_basis='Exact existing museum object identifier and explicit primary-image open-access flag in pinned official museum data; existing creator, date and holding metadata preserved.')
   if p=='nga':i['raw']={'object':raw,'source_receipt':receipt}
   pin(i);out.append({k:i[k] for k in ('artwork_id','provider','artist','title','page','license_label')})
  except (AssertionError,ValueError) as error:deferred.append({'artwork_id':w['id'],'provider':p,'reason':str(error)})
  print('Direct museum research',len(out),'selected',len(deferred),'deferred',flush=True)
 core.save_new(RUN/'direct-museum-selection.json',out);core.save_new(RUN/'direct-museum-deferred.json',deferred)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['commons','museums','photographs']);p.add_argument('--deeper',action='store_true');a=p.parse_args()
 if a.phase=='commons':commons(a.deeper)
 elif a.phase=='photographs':photographs()
 else:museums()
