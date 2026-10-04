#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,urllib.request,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/research/author-portraits-20260929'
assets=ROOT/'apps/web/public/images/authors/selected-20260929'; assets.mkdir(parents=True,exist_ok=True)
cache=pathlib.Path('/tmp/artline-portrait-images');cache.mkdir(exist_ok=True)
# Individual metadata review: retain warnings and unselected candidates in the audit.
excluded={'Q36322':'Source records a third-party copyright claim; seek another reproduction','Q3335':'Modern colorization; seek the original historical photograph','Q80137':'Source explicitly disputes whether the sitter is Emily or Anne','Q535':'Seek an alternative reproduction with clear source reuse terms'}
selected=[];audit=[]
for r in json.loads((OUT/'candidates.json').read_text()):
 qid=r['id'];m=r.get('metadata',{});reason=excluded.get(qid) or r.get('error')
 if not reason and (m.get('LicenseShortName')!='Public domain' or m.get('Restrictions')):reason='License/restriction needs further review'
 if reason:
  audit.append({'id':qid,'name':r['name'],'selected':False,'reason':reason});continue
 info=r['info'];url=info.get('thumburl') or info['url'];original=cache/(qid+'.source');target=assets/(qid+'.jpg')
 try:
  if not original.exists():
   time.sleep(4)
   req=urllib.request.Request(url,headers={'User-Agent':'ArtlineResearch/1.0 (selected public domain author portraits)'})
   with urllib.request.urlopen(req,timeout=40) as response: original.write_bytes(response.read())
  for quality in (82,70,55,40):
   subprocess.run(['sips','-s','format','jpeg','-s','formatOptions',str(quality),'-Z','640',str(original),'--out',str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
   if target.stat().st_size<=100000:break
  assert target.stat().st_size<=100000
  artist=m.get('Attribution') or m.get('Artist') or 'Photographer not identified in the source'
  if artist=='Unknown author Unknown author':artist='Photographer not identified in the source'
  label=('Later depiction of ' if qid in ['Q81731','Q1067'] else 'Portrait of ')+r['name']
  row=dict(creatorId=qid,creatorSourceUrl=r['source_url'],imageUrl='/images/authors/selected-20260929/'+qid+'.jpg',sourceUrl=info['descriptionurl'],label=label,credit=artist,license='Public domain',licenseUrl='https://creativecommons.org/publicdomain/mark/1.0/',checkedAt='2026-09-29')
  selected.append(row);audit.append(dict(id=qid,name=r['name'],selected=True,sourceImage=url,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),sourceSHA256=hashlib.sha256(original.read_bytes()).hexdigest(),sourceRevision=r['entityRevision'],imageDate=m.get('DateTimeOriginal'),basis=m.get('Categories'),transformation='Full supplied composition, proportional resize and JPEG compression; no additional cropping.'))
  print(qid,r['name'],target.stat().st_size,flush=True)
 except Exception as e:
  audit.append(dict(id=qid,name=r['name'],selected=False,reason=str(e)));print(qid,str(e),flush=True)
(OUT/'selection-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
(ROOT/'apps/server/internal/books/portrait-selection.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
print('Selected',len(selected),flush=True)
