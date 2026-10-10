import importlib.util,collections,requests,subprocess,hashlib,uuid,shutil
from pathlib import Path
from PIL import Image,ImageDraw
s=importlib.util.spec_from_file_location('key',Path.cwd()/'ops/painter-key-artworks-20261008.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
pkg=m.base.load(m.RUN/'local-supplement-source.json.gz');awby={r['id']:r for r in pkg['artworks']};media={r['id']:r for r in pkg['media']};ready=[];held=[]
with m.base.connect('local') as db:
 for r in pkg['selected']:
  artist=pkg['crosswalk'][r['artist_id']]
  if db.execute('SELECT 1 FROM artist_key_artworks WHERE artist_id=%s',(artist['id'],)).fetchone():continue
  w=awby[r['id']]
  found=db.execute("SELECT id,slug,title,status,primary_media_id,artline_creation_scope(creation_year_start,creation_year_end,date_precision) scope FROM artworks WHERE id=%s OR slug=%s",(w['id'],w['slug'])).fetchall()
  if found:
   if len(found)!=1 or found[0]['scope']!='eligible':held.append(dict(artist=artist['slug'],work=w['id'],reason='local_date_or_identity_needs_review'));continue
   ready.append(dict(candidate=r,artist=artist,source=w,target=found[0],new=False));continue
  # Do not create a second record under an already-known authority or title.
  identifiers=[e for e in pkg['identifiers'] if e['entity_id']==w['id']]
  matches=[]
  for e in identifiers:
   other=db.execute("SELECT entity_id FROM external_identifiers WHERE scheme=%s AND external_id=%s",(e['scheme'],e['external_id'])).fetchone()
   if other:matches.append(str(other['entity_id']))
  same_title=db.execute('SELECT 1 FROM artwork_artists aa JOIN artworks w ON w.id=aa.artwork_id WHERE aa.artist_id=%s AND w.normalized_title=lower(%s)',(artist['id'],w['title'])).fetchone()
  if matches or same_title:held.append(dict(artist=artist['slug'],work=w['id'],reason='existing_local_identity_needs_review'));continue
  ready.append(dict(candidate=r,artist=artist,source=w,target={'id':w['id'],'slug':w['slug']},new=True))
m.save('local-supplement-plan.json.gz',ready);m.save('local-supplement-held.json.gz',held);print('Local supplement selected',len(ready),'new records',sum(r['new'] for r in ready),'held',len(held),flush=True)
selected_media=[media[r['source']['primary_media_id']] for r in ready if r['new'] and r['source']['primary_media_id']];token=None;assets=Path('/tmp/artline-key-artwork-20261008/local-supplement-assets');assets.mkdir(exist_ok=True)
for ma in selected_media:
 path=Path.cwd()/'apps/web/public'/ma['storage_path'].lstrip('/');out=assets/(ma['id']+'.jpg')
 if path.exists():data=path.read_bytes()
 else:
  if token is None:token=subprocess.check_output(['gcloud','auth','print-access-token'],text=True).strip()
  response=requests.get('https://storage.googleapis.com/storage/v1/b/artline-508319-images/o/'+requests.utils.quote(ma['storage_path'].lstrip('/'),safe=''),params={'alt':'media'},headers={'Authorization':'Bearer '+token},timeout=30);response.raise_for_status();data=response.content
 assert len(data)<=100000,(ma['id'],len(data));assert hashlib.sha256(data).hexdigest()==ma['checksum_sha256'].strip();out.write_bytes(data)
sheet=Image.new('RGB',(1200,300*((len(selected_media)+5)//6)),'white');draw=ImageDraw.Draw(sheet)
for i,ma in enumerate(selected_media):
 row=next(r for r in ready if r['source']['primary_media_id']==ma['id']);im=Image.open(assets/(ma['id']+'.jpg'));im.thumbnail((190,220));x=i%6*200;y=i//6*300;sheet.paste(im,(x+(200-im.width)//2,y));draw.text((x+3,y+226),row['artist']['display_name'][:29],fill='black');draw.text((x+3,y+243),row['source']['title'][:29],fill='black')
if selected_media:sheet.save('/tmp/artline-key-artwork-20261008/local-supplement-review.jpg')
print('Local supplement images ready',len(selected_media),flush=True)
