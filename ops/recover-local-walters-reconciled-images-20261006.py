#!/usr/bin/env python3
"""Revisit held native images using pinned Walters person/object authorities."""
import argparse,csv,functools,importlib.util,io,json,re
from pathlib import Path
from PIL import Image,ImageOps

s=importlib.util.spec_from_file_location('walters',Path(__file__).with_name('recover-local-walters-native-images-20261006.py'))
w=importlib.util.module_from_spec(s);s.loader.exec_module(w);core=w.core
RUN=core.ROOT/'docs/research/local-walters-reconciled-images-20261006';w.RUN=RUN;w.base.RUN=RUN
SOURCES=core.ROOT/'docs/research/overnight-images-20260915/walters'
PRIOR=['local-walters-native-images-20261006','local-walters-followup-images-20261006','local-walters-later-images-20261006','local-walters-midcentury-images-20261006']
NEW_CANDIDATES=False
EXCLUDE_RUNS=[RUN.parent/name for name in PRIOR]
ALIASES={
 '88c1ca10-00b9-46b0-834b-142c3cc4741e':('Narcisse Virgilio Díaz','Narcisse Virgile Diaz de la Peña'),
 '5ec0be23-9aed-45ff-883c-83f7c6ffd15d':('Édouard Frère','Pierre-Édouard Frère'),
 '60767a31-45d6-4e4f-8301-857bbd071659':('Augustin Théodule Ribot','Théodule Ribot'),
 '53e4beb4-e032-44c7-aba6-31a479029f56':('Élisabeth Vigée Le Brun','Marie Louise Elisabeth Vigée-Lebrun'),
 '6db827ac-21c7-45cd-be14-b9e1ac71255d':('Félix Ziem','Félix François Georges Philibert Ziem'),
 '61a9aa63-0a4a-406e-b4d9-234cb51bff7f':('Marià Fortuny','Mariano Fortuny'),
 'bcb88437-6072-47bf-92ae-a68e1e962bf2':('Hermann-Paul','Paul Hermann'),
 'ee367e6d-c042-470f-9d95-c142df16400d':('Chartran Théobald','Theobald Chartran'),
}
SELECTED_FRONTS={
 '37.1758':'PS1_37.1758_Fnt_DD_AST-014781-tms.jpg',
 '37.226':'PS1_37.226_Fnt_DD_T13.jpg',
 '37.1654':'PS1_37.1654_FntCc_DD_T12-2.jpg',
 '37.191':'PL1_37.191_Fnt_TR_C80.jpg',
 '37.185':'PL7_37.185_Fnt_BW_H52.jpg',
}
INDIVIDUAL_VIEWS={
 '35.313':'PS1_TL.2013.11.2_FntA_DD_T13.jpg',
 '35.310':'PS1_TL.2013.11.3_FntA_DD_T13.jpg',
 '35.311':'PS1_TL.2013.11.4A_FntA_DD_T13.jpg',
 '38.274':'PL7_38.274_NF_A-37_-tms.jpg',
 '38.305':'PL7_38.305_NF_A-37-tms.jpg',
 '37.761':'PS1_37.761_ATFnt_DD_T16-022087-2-tms.jpg',
 '37.2778':'PS1_37.2778_FntAftTrt_DD_T09.jpg',
 '38.166':'PS3_38.166_Opn_DD_T13.jpg',
 '37.2602':'PS1_37.2602_ATFnt_DD_T12.jpg',
 '38.194':'PS3_38.194_Opn_DD_T13.jpg',
 '37.1657':'PS4_37.1657_CCFnt_DD_AT21_23648 1-tms.jpg',
 '37.1664':'PS4_37.1664_CCFnt_DD_AT21_23677 1-tms.jpg',
 '37.1644':'PS1_37.1644_FntAT_DD_T15.jpg',
 '37.1654':'PS1_37.1654_FntCc_DD_T12-2.jpg',
 '37.2780':'PS1_37.2780_ATFnt_DD_T15-tms.jpg',
 '37.73':'PS1_37.73_AT_DD_T14.jpg',
 '37.2536':'PS1_37.2536_AT_DD_T15.jpg',
 '37.2740':'PS1_37.2740_AT_DD_T14.jpg',
 '37.970':'PS1_37.970_BTFnt_DD_T16-tms.jpg',
 '37.965':'PS1_37.965_BTFnt_DD_T16-tms.jpg',
 '37.1007':'PL1_37.1007_FntA_TR_T86IA.jpg',
 '44.971':'PS1_44.971_OpnFnt_DD_T17-tms.jpg',
}
ASSET_CONCORDANCE={
 '35.313':('91850','PS1_TL.2013.11.2_FntA_DD_T13.jpg'),
 '35.310':('91851','PS1_TL.2013.11.3_FntA_DD_T13.jpg'),
 '35.311':('91852','PS1_TL.2013.11.4A_FntA_DD_T13.jpg'),
 '37.2939':('101353','PS1_TL.2019.2.1_Fnt_DD_AT19_1-tms.jpg'),
}
ART_FIELDS=('ObjectID','AccessionNumber','Title','Creators','DateText','DateBeginYear','DateEndYear','ObjectName','ResourceURL')
QUALIFIED_VIEWS={'35.105':dict(filename='PS1_35.105_Fnt_DD_T09.jpg',view_label='Album cover only; the eight paintings are not shown',kind='album_cover')}
ACTIVITY_NOTE='The museum lists the maker as active 1874–1908; those are activity dates, not established birth and death years.'

original_compress=core.compress
def compress(data):
 # This museum JPEG was downloaded and inspected individually. Keep the
 # general source-size guard; only its exact bytes may use decoder reduction.
 if core.sha(data)!='de6d0f02e0eecfc1551433810f7e9c1fd0dab2800a23b9c4b3b96c28b2ac969b':return original_compress(data)
 with Image.open(io.BytesIO(data)) as opened:
  if len(data)!=6210029 or opened.format!='JPEG' or opened.size!=(7959,8914):raise ValueError('Pinned large JPEG dimensions differ')
  opened.draft('RGB',(1200,1200))
  if opened.size!=(1990,2229):raise ValueError('Bounded JPEG decoder reduction unavailable')
  opened.load();frame=ImageOps.exif_transpose(opened).convert('RGB');buffer=io.BytesIO();frame.save(buffer,'PNG')
 return original_compress(buffer.getvalue())
core.compress=compress

@functools.lru_cache(maxsize=1)
def authorities():
 result={};captures={}
 for name,key in [('creators.csv','id'),('art.csv','ObjectID')]:
  path=SOURCES/name;receipt_path=path.with_suffix(path.suffix+'.receipt.json');receipt=json.loads(receipt_path.read_bytes())
  if core.sha(path.read_bytes())!=receipt['sha256'] or not re.fullmatch(r'[0-9a-f]{40}',receipt['commit']):raise ValueError('Pinned source dataset differs')
  if receipt['url']!=f"https://raw.githubusercontent.com/WaltersArtMuseum/api-thewalters-org/{receipt['commit']}/{name}":raise ValueError('Source dataset provenance differs')
  with path.open(newline='') as stream:parsed_rows=list(csv.DictReader(stream))
  # The published creator export contains orphaned continuation rows with blank
  # IDs. They cannot identify a person; selected numeric IDs must still be unique.
  rows=[r for r in parsed_rows if re.fullmatch(r'[0-9]+',r.get(key) or '')]
  indexed={r[key]:r for r in rows}
  if len(indexed)!=len(rows):raise ValueError('Source identifiers are not unique')
  result[name]=indexed;captures[name]=dict(path=str(path.relative_to(core.ROOT)),receipt_path=str(receipt_path.relative_to(core.ROOT)),ignored_rows_without_numeric_id=len(parsed_rows)-len(rows),**receipt)
 return result,captures

def identity(c,artist,identifiers):
 data,captures=authorities();person=[r for r in identifiers if r['scheme']=='walters-person']
 if len(c['creators'])!=1 or c['roles']!=['primary'] or len(person)!=1:raise ValueError('Exact single source creator authority absent')
 if c['creator_links'][0]['artist_id']!=artist['id']:raise ValueError('Existing creator link differs')
 obj=data['art.csv'].get(c['external_id']);creator=data['creators.csv'].get(person[0]['external_id'])
 if not obj or not creator or obj['Creators']!=creator['id']:raise ValueError('Source object and existing creator authority disagree')
 if (obj['AccessionNumber'],w.clean(obj['Title']),w.clean(obj['DateText']))!=(c['accession_number'],w.clean(c['title']),w.clean(c['date_display'])):raise ValueError('Pinned source object facts differ')
 if c['external_id'] not in creator['CreatorArt'].split('|'):raise ValueError('Source creator does not list this object')
 if not int(obj['DateBeginYear'])<=c['creation_year_start']<=c['creation_year_end']<=int(obj['DateEndYear'])<=1970:raise ValueError('Source date indexing conflicts with scope')
 return dict(artist_record=artist,artist_identifiers=identifiers,object_record={k:obj[k] for k in ART_FIELDS},creator_record=creator,source_captures=captures)

def select(limit):
 if (RUN/'candidates.json').exists():return
 if NEW_CANDIDATES:
  spec=importlib.util.spec_from_file_location('follow',Path(__file__).with_name('recover-local-walters-followup-images-20261006.py'));follow=importlib.util.module_from_spec(spec);spec.loader.exec_module(follow)
  document=follow.query_candidates(limit,EXCLUDE_RUNS)
  artist_ids=list({link['artist_id'] for c in document['candidates'] for link in c['creator_links']})
  with w.base.connect() as db:
   artists={r['record']['id']:r['record'] for r in db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=ANY(%s::uuid[])',(artist_ids,)).fetchall()}
   identifiers={aid:[] for aid in artist_ids}
   for row in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=ANY(%s::uuid[]) ORDER BY id",(artist_ids,)).fetchall():identifiers[row['record']['entity_id']].append(row['record'])
  for c in document['candidates']:
   try:
    if len(c['creator_links'])!=1:raise ValueError('Creator link requires individual review')
    aid=c['creator_links'][0]['artist_id'];c['creator_identity']=identity(c,artists[aid],identifiers[aid])
   except ValueError as error:c['identity_hold']=str(error)
  core.save_new(RUN/'candidates.json',document);print('Selected',len(document['candidates']),'new missing-image records with native authority evidence',flush=True);return
 prior={}
 for name in PRIOR:
  for c in json.loads((RUN.parent/name/'candidates.json').read_bytes())['candidates']:prior[c['artwork_id']]=dict(c,previous_operation=name)
 selected=[];omitted=[]
 with w.base.connect() as db:
  current={r['record']['id']:r['record'] for r in db.execute("SELECT to_jsonb(a) record FROM artworks a WHERE a.id=ANY(%s::uuid[]) AND a.primary_media_id IS NULL AND a.status='review'",(list(prior),)).fetchall()}
  for aid in sorted(current):
   c=prior[aid]
   if aid==w.ICON:continue # The photograph is already known to show only one panel.
   if current[aid]!=c['before_record']:raise ValueError('Previously held catalogue record changed')
   c.pop('creator_identity',None)
   try:
    if len(c['creator_links'])!=1:raise ValueError('Creator link requires individual review')
    artist_id=c['creator_links'][0]['artist_id']
    artist=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s',(artist_id,)).fetchone()['record']
    identifiers=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(artist_id,)).fetchall()]
    c['creator_identity']=identity(c,artist,identifiers)
   except ValueError as error:c['identity_hold']=str(error)
   selected.append(c)
  baseline=db.execute('SELECT count(*) total,count(*) FILTER(WHERE primary_media_id IS NULL) missing FROM artworks').fetchone()
 if len(selected)>limit:raise ValueError('Reconciliation selection exceeds the explicit bound')
 core.save_new(RUN/'candidates.json',dict(at=core.now(),baseline=baseline,candidates=selected,excluded_known_single_panel=w.ICON))
 for c in selected:
  old=RUN.parent/c['previous_operation']/'metadata'/(c['accession_number']+'.html')
  if old.exists():
   cap=json.loads(old.with_suffix('.receipt.json').read_bytes());data=old.read_bytes()
   if core.sha(data)!=cap['sha256']:raise ValueError('Earlier current-page capture differs')
   new=RUN/'metadata'/old.name;core.save_new(new,data)
   core.save_new(new.with_suffix('.receipt.json'),dict(cap,path=str(new.relative_to(core.ROOT)),reused_from=str(old.relative_to(core.ROOT))))
 print('Selected',len(selected),'previously held records for individual source reconciliation',flush=True)

def creator_matches(im,native_name):
 proof=im.get('creator_identity')
 if not proof:raise ValueError(im.get('identity_hold','Source creator authority absent'))
 if identity(im,proof['artist_record'],proof['artist_identifiers'])!=proof:raise ValueError('Pinned creator authority differs')
 creator=proof['creator_record'];local_name=im['creators'][0]['name'];artist_id=proof['artist_record']['id']
 if w.clean(native_name)!=w.clean(creator['name']):raise ValueError('Current native creator differs from its pinned authority')
 pair=(local_name,native_name)
 # The explicit pairs also require the museum's stable person ID and reciprocal
 # object membership above; no fuzzy name match or global creator edit is used.
 return w.base.m.norm(local_name)==w.base.m.norm(native_name) or ALIASES.get(artist_id)==pair or pair==('Edouard de Beaumont','Édouard de Beaumont')

original_facts=w.facts
original_parse_creation_date=w.parse_creation_date
def parse_creation_date(im,date):
 if (im['accession_number'],im['external_id'],date)==('37.2775','33174','1867/1880'):
  obj=im['creator_identity']['object_record']
  if (obj['DateText'],obj['DateBeginYear'],obj['DateEndYear'])!=('1867/1880','1867','1880'):raise ValueError('Individual slash-date source indexing differs')
  return 1867,1880,'range'
 return original_parse_creation_date(im,date)
w.parse_creation_date=parse_creation_date

def asset_concordance(im,filename):
 if ASSET_CONCORDANCE.get(im['accession_number'])!=(im['external_id'],filename):raise ValueError('Individual source asset concordance absent')
 data,captures=authorities();obj=data['art.csv'][im['external_id']]
 if obj['AccessionNumber']!=im['accession_number'] or filename not in obj['Images'].split('|'):raise ValueError('Pinned museum object does not list the selected asset')
 return dict(object_id=obj['ObjectID'],accession_number=obj['AccessionNumber'],selected_filename=filename,source_images_field=obj['Images'],source_capture=captures['art.csv'])

original_inventory_image_matches=w.inventory_image_matches
def inventory_image_matches(im,filename):
 if original_inventory_image_matches(im,filename):return True
 asset_concordance(im,filename)
 return True
w.inventory_image_matches=inventory_image_matches

def facts(im,path):
 result=original_facts(im,path);proof=im['creator_identity'];creator=proof['creator_record']
 if [u.rstrip('/') for u in result['creator_links']]!=[creator['CreatorURL'].rstrip('/')]:raise ValueError('Current native creator URL differs from its authority')
 if not result['author'].startswith(w.clean(creator['name']+' '+creator['date'])+' '):raise ValueError('Current creator biographical qualifier differs')
 if im['accession_number'] in ('38.274','38.305') and Path(result['image_url']).name==INDIVIDUAL_VIEWS[im['accession_number']]:result['monochrome']=True
 if im['accession_number']=='37.1980' and Path(result['image_url']).name=='ARG_37.1980_Fnt_UK.jpg':result['monochrome']=True
 if im['accession_number']=='35.105L':
  if result['image_url']!='https://art.thewalters.org/images/art/PS1_35.105L_Fnt_DD_T09.jpg':raise ValueError('Exact alternate-download source differs')
  result['display_image_url']=result['image_url'];result['image_url']=result['download_url']
 if im['accession_number'] in ASSET_CONCORDANCE:result['native_asset_concordance']=asset_concordance(im,Path(result['image_url']).name)
 result['creator_authority']=proof
 return result
w.creator_matches=creator_matches;w.facts=facts;w.select=select

original_role_matches=w.creator_role_matches
def creator_role_matches(im,name,author_text):
 if im['accession_number'] in ('38.2','38.16'):return author_text==name+' (Enameler)'
 return original_role_matches(im,name,author_text)

def select_photo(im,images):
 filename=SELECTED_FRONTS.get(im['accession_number'])
 if not filename:return images[0]
 matches=[a for a in images if a.find('img',src=True) and Path(a.find('img')['src']).name==filename]
 if len(matches)!=1:raise ValueError('Individually selected full front is absent or ambiguous')
 return matches[0]

original_front_image_matches=w.front_image_matches
def front_image_matches(im,filename):
 return original_front_image_matches(im,filename) or INDIVIDUAL_VIEWS.get(im['accession_number'])==filename
w.creator_role_matches=creator_role_matches;w.select_photo=select_photo;w.front_image_matches=front_image_matches

def decorate_image(im):
 view=QUALIFIED_VIEWS.get(im['accession_number'])
 if view:
  if Path(im['source_image_url']).name!=view['filename']:raise ValueError('Qualified album cover source differs')
  im['view_label']=view['view_label'];im['alt_text']=im['title']+' — '+view['view_label']
  im['raw']['view_scope_review']=view.copy()
  if view['view_label'] not in im['attribution_text']:im['attribution_text']+=' '+view['view_label']+'.'
 if im['accession_number']=='44.971':
  im['raw']['creator_date_review']=dict(native_dates_are_activity=True,native_death_year_not_established=True,note=ACTIVITY_NOTE)
  if ACTIVITY_NOTE not in im['attribution_text']:im['attribution_text']+=' '+ACTIVITY_NOTE
 return im
w.decorate_image=decorate_image

original_verify_image=w.verify_image
def verify_image(im):
 original_verify_image(im)
 view=QUALIFIED_VIEWS.get(im['accession_number'])
 if view:
  if im.get('view_label')!=view['view_label'] or im.get('alt_text')!=im['title']+' — '+view['view_label'] or im['raw'].get('view_scope_review')!=view or view['view_label'] not in im['attribution_text']:raise ValueError('Album cover scope omitted or changed')
 if im['accession_number']=='44.971':
  expected=dict(native_dates_are_activity=True,native_death_year_not_established=True,note=ACTIVITY_NOTE)
  if im['raw'].get('creator_date_review')!=expected or ACTIVITY_NOTE not in im['attribution_text']:raise ValueError('Maker activity dates must not be presented as a lifespan')
w.verify_image=verify_image

def attach(db,im,target):
 proof=im['creator_identity'];artist_id=proof['artist_record']['id']
 current=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s FOR SHARE',(artist_id,)).fetchone()['record']
 identifiers=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(artist_id,)).fetchall()]
 if current!=proof['artist_record'] or identifiers!=proof['artist_identifiers']:raise ValueError('Existing creator authority changed before attachment')
 verify_image(im);result=w.attach(db,im,target)
 if result=='attached' and im.get('view_label'):
  db.execute('UPDATE media_assets SET alt_text=%s WHERE id=%s',(im['alt_text'],im['media_id']))
  db.execute('INSERT INTO artwork_media(artwork_id,media_id,sort_order,view_label) VALUES(%s,%s,0,%s)',(im['artwork_id'],im['media_id'],im['view_label']))
 return result
w.base.m.attach=attach

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['research','prepare','apply','verify']);p.add_argument('--run-name',default=RUN.name);p.add_argument('--new-candidates',action='store_true');p.add_argument('--exclude-run',type=Path,action='append',default=[]);p.add_argument('--retry-held',action='store_true');p.add_argument('--limit',type=int,default=30);a=p.parse_args()
 if not re.fullmatch(r'local-walters-[a-z0-9-]+-20261006',a.run_name):raise ValueError('Invalid operation directory')
 RUN=core.ROOT/'docs/research'/a.run_name;w.RUN=RUN;w.base.RUN=RUN;NEW_CANDIDATES=a.new_candidates;EXCLUDE_RUNS.extend(path.resolve() for path in a.exclude_run)
 if a.phase=='research':w.research(a.limit,retry_held=a.retry_held)
 elif a.phase=='prepare':
  for path in (RUN/'selected'/w.PROVIDER).glob('*.json'):w.verify_image(json.loads(path.read_bytes()))
  w.base.prepare(w.PROVIDER)
 elif a.phase=='apply':w.base.apply()
 else:
  for im in w.base.prepared():w.verify_image(im)
  w.base.verify();w.verify_rights_and_holds()
  checked=set()
  with w.base.connect() as db:
   for im in w.base.prepared():
    proof=im['creator_identity'];artist_id=proof['artist_record']['id']
    if artist_id in checked:continue
    current=db.execute('SELECT to_jsonb(ar) record FROM artists ar WHERE id=%s',(artist_id,)).fetchone()['record']
    identifiers=[r['record'] for r in db.execute("SELECT to_jsonb(e) record FROM external_identifiers e WHERE entity_type='artist' AND entity_id=%s ORDER BY id",(artist_id,)).fetchall()]
    if current!=proof['artist_record'] or identifiers!=proof['artist_identifiers']:raise ValueError('Creator record changed')
    checked.add(artist_id)
  core.save_new(RUN/'creator-authority-verification.json',dict(at=core.now(),passed=True,unchanged_artist_records_and_identifiers=sorted(checked)))
