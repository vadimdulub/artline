"""Select exact existing catalogue identities and render their original pages."""
import importlib.util,re,json
from pathlib import Path
import pymupdf
from PIL import Image,ImageDraw
s=importlib.util.spec_from_file_location('cyprus','ops/cyprus-deep-20261010.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
b=m.h.load(m.RUN/'baseline.json.gz');d=pymupdf.open('/tmp/artline-cyprus-pdf/catalogue.pdf');chosen=[]
for museum in b['museums']:
    if not museum['artworks']or museum['images']:continue
    n=0
    for a in [a for a in b['artworks']if a['current_institution_id']==museum['id']]:
        cs=[c for c in b['citations']if c['entity_id']==a['id']and 'CULTURES' in c['source_url']]
        if not cs:continue
        c=cs[0];pn=int(re.search(r'page (\d+)',c['page_or_locator'])[1])
        pages=[i for i,p in enumerate(d)if a['accession_number'] in p.get_text() and str(pn)in p.get_text()[-25:]]
        if not pages:pages=[pn,pn-1]
        pi=pages[0];page=d[pi]
        ims=[{k:v for k,v in x.items()if k!='digest'}for x in page.get_image_info(xrefs=True)]
        chosen.append(dict(artwork_id=a['id'],title=a['title'],museum=museum['slug'],accession=a['accession_number'],printed_page=pn,pdf_page_index=pi,images=ims,locator=c['page_or_locator'],source_url=c['source_url']));n+=1
        if n==2:break
m.h.save(m.RUN/'pdf-image-leads.json',chosen)
for k in range(0,len(chosen),4):
    sheet=Image.new('RGB',(1400,2000),'white')
    for j,r in enumerate(chosen[k:k+4]):
        p=d[r['pdf_page_index']];pix=p.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);im.thumbnail((690,960));x=j%2*700;y=j//2*1000;sheet.paste(im,(x,y+35));ImageDraw.Draw(sheet).text((x+5,y+5),str(k+j)+' '+r['title']+' / PDF '+str(r['pdf_page_index']+1),fill='black')
    sheet.save('/tmp/artline-cyprus-pdf/sheet-'+str(k//4)+'.jpg')
print([(i,r['museum'],r['title'],r['pdf_page_index']+1,len(r['images']))for i,r in enumerate(chosen)])
