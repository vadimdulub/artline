"""Prepare a bounded image selection; originals outside Documents, no database writes."""
import collections,concurrent.futures,hashlib,io,json,runpy,sys,time,threading
from pathlib import Path
from urllib.parse import urlparse
import requests,pymupdf
from PIL import Image,ImageOps,ImageDraw,ImageFont
m=runpy.run_path('ops/germany-deep-facts-20261011.py')['m'];TEMP=Path('/tmp/artline-germany-delivery');TEMP.mkdir(exist_ok=True);(m.RUN/'images').mkdir(exist_ok=True);m.ORIGINALS.mkdir(parents=True,exist_ok=True)
def plan():
    x=m.h.load(m.RUN/'selection-reviewed.json');by=collections.defaultdict(list)
    for f in x['records']:
        if f['image_eligible']:by[f['museum_slug']].append(f)
    selected=[]
    for mu,rows in by.items():
        cap=16 if mu=='de-ikonenmuseum-frankfurt'else 12
        # Spread larger selections through the museum's source list, avoiding an
        # old-master-only selection from Städel's two curated highlight albums.
        indexes=list(range(len(rows)))if len(rows)<=cap else sorted({round(i*(len(rows)-1)/(cap-1))for i in range(cap)})
        selected.extend(rows[i]['key']for i in indexes)
    m.h.save(m.RUN/'image-selection.json',dict(keys=selected,metadata_sha256=m.h.sha((m.RUN/'selection-reviewed.json').read_bytes()),selection='At most 12 eligible reproductions per museum, with 16 for Frankfurt’s selected icon album. Metadata selected before downloads; no complete collection/image harvesting.'))
    print('PLANNED',len(selected),'images across',len(by),'museums')
locks=collections.defaultdict(threading.Lock);blocked=set()
if (m.RUN/'image-failures.json').exists():
    # Access denials persist across runs; a rerun is not an authorization change.
    old_facts={f['key']:f for f in m.h.load(m.RUN/'selection-reviewed.json')['records']}
    for failure in m.h.load(m.RUN/'image-failures.json'):
        if any(t in failure['reason']for t in ['403 Client Error','401 Client Error','429 Client Error','Host stopped after access denial']):blocked.add(urlparse(old_facts[failure['key']]['image_url']).netloc)
def prepare(retry=False):
    p=m.h.load(m.RUN/'image-selection.json');x=m.h.load(m.RUN/'selection-reviewed.json');facts={f['key']:f for f in x['records']};assert p['metadata_sha256']==m.h.sha((m.RUN/'selection-reviewed.json').read_bytes())
    def one(key):
        f=facts[key];tag=m.h.sha(key.encode())[:24];out=m.RUN/'images'/(tag+'.jpg');original=m.ORIGINALS/(tag+'.source');rp=m.ORIGINALS/(tag+'.receipt.json')
        if original.exists()and rp.exists():raw=original.read_bytes();rc=json.loads(rp.read_text());assert m.h.sha(raw)==rc['sha256']
        elif f.get('pdf_image'):
            v=f['pdf_image'];doc=pymupdf.open(v['path']);assert v['xref']in[q[0]for q in doc[v['page']-1].get_images()];raw=doc.extract_image(v['xref'])['image'];rc=dict(url=f['source_url'],pdf_page=v['page'],figure=v['figure'],xref=v['xref'],sha256=m.h.sha(raw),retrieved_at=m.h.now());original.write_bytes(raw);m.h.save(rp,rc)
        else:
            host=urlparse(f['image_url']).netloc
            with locks[host]:
                if host in blocked:raise RuntimeError('Host stopped after access denial or rate limit: '+host)
                r=requests.get(f['image_url'],timeout=(15,50),stream=True)
                if r.status_code in[401,403,429]:blocked.add(host)
                r.raise_for_status();buf=io.BytesIO()
                for chunk in r.iter_content(65536):
                    buf.write(chunk)
                    if buf.tell()>30000000:raise ValueError('Selected source exceeds 30 MB limit')
                raw=buf.getvalue();rc=dict(url=f['image_url'],final_url=r.url,status=r.status_code,content_type=r.headers.get('Content-Type'),sha256=m.h.sha(raw),bytes=len(raw),retrieved_at=m.h.now());time.sleep(.6)
            original.write_bytes(raw);m.h.save(rp,rc)
        # Some museum download buttons return a public JSON string pointing to
        # the JPEG. Preserve that resolver response and follow only its exact URL.
        if 'application/json'in rc.get('content_type',''):
            resolved=json.loads(raw);assert isinstance(resolved,str)and resolved.startswith('https://www.kunsthalle-karlsruhe.de/'),resolved
            resolved_path=m.ORIGINALS/(tag+'.resolved.source');resolved_receipt=m.ORIGINALS/(tag+'.resolved.receipt.json')
            if resolved_path.exists():raw=resolved_path.read_bytes();rc=json.loads(resolved_receipt.read_text());assert m.h.sha(raw)==rc['sha256']
            else:
                with locks[urlparse(resolved).netloc]:
                    r=requests.get(resolved,timeout=(15,50));r.raise_for_status();raw=r.content;assert len(raw)<30000000
                rc=dict(url=resolved,final_url=r.url,status=r.status_code,content_type=r.headers.get('Content-Type'),sha256=m.h.sha(raw),bytes=len(raw),retrieved_at=m.h.now(),resolver_receipt=rc);resolved_path.write_bytes(raw);m.h.save(resolved_receipt,rc)
            original=resolved_path
        im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw)));assert im.width>100 and im.height>100,('Placeholder dimensions',im.size)
        if im.mode in['RGBA','LA']:
            bg=Image.new('RGBA',im.size,'white');bg.alpha_composite(im.convert('RGBA'));im=bg.convert('RGB')
        else:im=im.convert('RGB')
        original_size=im.size;im.thumbnail((1500,1500));quality=88
        while True:
            buf=io.BytesIO();im.save(buf,'JPEG',quality=quality,optimize=True);data=buf.getvalue()
            if len(data)<=100000:break
            if quality>54:quality-=6
            else:im.thumbnail((int(im.width*.86),int(im.height*.86)));quality=82
        out.write_bytes(data)
        return dict(key=key,museum_slug=f['museum_slug'],title=f['title'],creator=f['creator'],file=str(out.relative_to(m.RUN)),original_path=str(original),receipt=rc,sha256=m.h.sha(data),bytes=len(data),width=im.width,height=im.height,original_size=original_size,source_url=f['source_url'],image_url=f.get('image_url'),view_label=f['view_label'],rights_status=f['rights_status'],rights_label=f['rights_label'],creator_credit=f['creator_credit'])
    ok=[];fail=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:
        futures={ex.submit(one,k):k for k in p['keys']}
        for fu in concurrent.futures.as_completed(futures):
            try:r=fu.result();ok.append(r);print('IMAGE',len(ok),r['museum_slug'],r['title'],flush=True)
            except Exception as e:fail.append(dict(key=futures[fu],reason=type(e).__name__+': '+str(e)[:250]));print('FAILED',futures[fu],str(e)[:150],flush=True)
    order={k:i for i,k in enumerate(p['keys'])};ok.sort(key=lambda x:order[x['key']]);suffix='-resolved'if retry else'';m.h.save(m.RUN/('images-prepared'+suffix+'.json'),ok);m.h.save(m.RUN/('image-failures'+suffix+'.json'),fail);print('PREPARED',len(ok),'FAILED',len(fail))
def retry():prepare(True)
def sheets():
    path=m.RUN/'images-prepared-resolved.json';rows=m.h.load(path if path.exists()else m.RUN/'images-prepared.json');font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',14)
    for offset in range(0,len(rows),20):
        sheet=Image.new('RGB',(1500,1400),'#e8e5df');d=ImageDraw.Draw(sheet)
        for j,r in enumerate(rows[offset:offset+20]):
            im=Image.open(m.RUN/r['file']);im.thumbnail((280,278));x=j%5*300;y=j//5*350;sheet.paste(im,(x+(300-im.width)//2,y+5+(278-im.height)//2));d.text((x+8,y+287),str(offset+j+1)+' '+r['museum_slug'].removeprefix('de-')[:32],font=font,fill='black');d.text((x+8,y+308),r['creator'][:34],font=font,fill='black');d.text((x+8,y+329),r['title'][:38],font=font,fill='black')
        sheet.save(TEMP/('contact-'+str(offset//20+1)+'.jpg'))
    print('CONTACT SHEETS',(len(rows)+19)//20)
if __name__=='__main__':globals()[sys.argv[1]]()
