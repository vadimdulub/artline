#!/usr/bin/env python3
import importlib.util,json,re
from pathlib import Path
from PIL import Image
spec=importlib.util.spec_from_file_location('b',Path(__file__).with_name('research-armenian-georgian-artworks.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
s=b.s;r=b.r
items=[json.loads(f.read_bytes()) for f in sorted((s.RUN/'final-ready').glob('*.json'))];assert len(items)==271
images=[]
with s.connect('local') as db:
 db.execute('SET TRANSACTION READ ONLY')
 for item in items:
  rec=item['record'];d=rec['date'];assert rec['title'] and not re.fullmatch(r'Q\d+',rec['title']);scope=db.execute('SELECT artline_creation_scope(%s,%s,%s) scope',(d['first'],d['last'],d['precision'])).fetchone()['scope']
  im=item['image']
  if not im:continue
  assert scope=='eligible';data=(s.ROOT/'apps/web/public'/im['path'].lstrip('/')).read_bytes();assert len(data)<=100000 and s.core.sha(data)==im['sha256'];picture=Image.open(s.ROOT/'apps/web/public'/im['path'].lstrip('/'));assert picture.size==(im['width'],im['height']) and picture.format=='JPEG';picture.verify()
  text=im['commons_page']['revisions'][0]['slots']['main']['*'];assert not re.search(r'\{\{\s*(?:delete|copyvio|no permission|disputed|wrong license|superseded)\b',text,re.I)
  images.append({'qid':rec['qid'],'bytes':len(data),'sha256':im['sha256'],'rights_status':im['rights_status'],'source':im['source_page_url']})
s.save(s.RUN/'quality-review/contact-sheet.jpg',Path('/tmp/artline-caucasus-contact-final.jpg').read_bytes())
s.save(s.RUN/'quality-review.json',{'at':s.core.now(),'reviewed_records':len(items),'images':images,'visual_review':'All 38 prepared images inspected in the full contact sheet. Source framing preserved; no obstructing visitor, composite, screenshot interface or obviously unrelated subject found. Reproductions vary in age and resolution.','machine_checks':['exact authority and file identity recorded','JPEG decoding and dimensions','SHA-256 and byte budget <=100000','PostgreSQL creation scope eligible for every image','no Commons dispute/deletion templates'],'native_titles_retained':189,'unresolved_date_identity':'Q138349988: primary 1906 versus authority 1909; unknown date and no image attachment'})
print('Quality verified',len(items),'records',len(images),'images',flush=True)
