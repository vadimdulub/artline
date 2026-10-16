"""Selected regional collections, with explicit caption and loan evidence."""
import runpy,re,collections,sys
from urllib.parse import urljoin
b=runpy.run_path('ops/germany-deep-facts-20261011.py');m=b['m'];soup=b['soup'];add=b['add'];museum=b['museum'];M=b['M'];F=b['F'];H=b['H']
def fields(s):return {dt.get_text(' ',strip=True):dt.find_next_sibling('dd').get_text(' ',strip=True)for dt in s.select('dt')if dt.find_next_sibling('dd')}
def lenbach():
    u='https://www.lenbachhaus.de/entdecken/der-blaue-reiter';mu=museum('de-lenbachhaus','Lenbachhaus','Munich','Bavaria',u);s,p=soup(u);selected=[];counts=collections.Counter()
    for fig in s.select('figure'):
        cr=fig.select_one('.image-title');a=fig.find_parent('a',href=True)
        if not cr or not a or'/sammlung-online/detail/'not in a['href']:continue
        cr=cr.get_text(' ',strip=True)
        if counts[cr]>=3:continue
        selected.append(urljoin(u,a['href']));counts[cr]+=1
    for url in list(dict.fromkeys(selected))[:30]:
        try:
            s,p=soup(url);fld=fields(s);h=s.select_one('h1.mms_title');cr=h.select_one('.mms_title-person_name');creator=cr.a.get_text(' ',strip=True);cr.extract();title=h.get_text(' ',strip=True)
            image=next((i['url']for i in p['images']if i['alt'].startswith(creator+',')and'/fileadmin/'in i['url']),None)
            licence=next((x for x in p['links']if'creativecommons.org'in x['url']),None)
            credit=p['text'].split('Creditline\n',1)[-1].split('Zitiervorschlag',1)[0].strip()if'Creditline\n'in p['text']else'Lenbachhaus'
            f=add(mu,title,creator,fld.get('Datierung',''),url,url.rsplit('-',1)[-1],image,fld.get('Material'),fld.get('Maße'),fld.get('Inventarnummer'),source_receipt=p['receipt'],source_fields=fld,holding_note=credit)
            if not f:continue
            f.update(creator_credit=credit,rights_label=licence['text']if licence else'Lenbachhaus; per-object copyright and credit retained',license_url=licence['url']if licence else None,rights_status='cc0'if licence and'zero/1.0'in licence['url']else'restricted')
            if 'Gemälde'not in fld.get('Objektart',''):f['work_type']='unknown'
            print('LENBACH',title,f['date_display'],flush=True)
        except Exception as e:H.append(dict(url=url,reason=type(e).__name__+': '+str(e)[:200]))
def barberini():
    u='https://sammlung.museum-barberini.de/en/';mu=museum('de-museum-barberini','Museum Barberini – Hasso Plattner Collection','Potsdam','Brandenburg',u);s,p=soup(u);chosen=[];count=collections.Counter()
    for a in s.select('a[href]'):
        cr=a.find('strong')
        if not cr or'/MB-'not in a['href']:continue
        cr=cr.get_text(' ',strip=True)
        cap=3 if cr=='Claude Monet'else 1
        if count[cr]>=cap:continue
        if 'n.d.'in a.get_text():continue
        chosen.append((a['href'],cr));count[cr]+=1
    for url,creator in chosen:
        try:
            s,p=soup(url);h=s.find(['h2','h3'],class_=lambda x:x and'title'in x);heads=[x.get_text(' ',strip=True)for x in s.find_all(['h1','h2','h3','h4'])]
            titleline=next(x for x in heads if re.search(r',\s*(?:ca\. )?\d{4}',x));ma=re.search(r',\s*((?:ca\. )?\d{4}.*)$',titleline);title=titleline[:ma.start()];dt=ma[1]
            inv=re.search(r'Inv\.-no\.\s+(MB-[\w-]+)',p['text'])[1]
            im=next(x for x in s.select('img')if'/collection-images/'in str(x))
            img=im.get('data-src')or im.get('src');img=urljoin(url,img)
            f=add(mu,title,creator,dt,url,inv,img,accession=inv,source_receipt=p['receipt'],holding_note='Hasso Plattner Collection, presented at Museum Barberini. The source collection credit does not imply ownership by the museum corporation.',original_caption=titleline)
            if f:
                meta=next((x.get_text(' ',strip=True)for x in s.select('p')if'Inv.-no.'in x.get_text()),'');f.update(source_fields=dict(object_description=meta),creator_credit='Hasso Plattner Collection, Museum Barberini, Potsdam',rights_label='Museum Barberini / Hasso Plattner Collection; no open image reuse licence stated');print('BARBERINI',title,dt,flush=True)
        except Exception as e:H.append(dict(url=url,reason=type(e).__name__+': '+str(e)[:180]))
def bremen():
    u='https://www.kunsthalle-bremen.de/de/sb-page/sammlung/die-sammlung/romantik-bis-impressionismus';mu=museum('de-kunsthalle-bremen','Kunsthalle Bremen','Bremen','Bremen',u);s,p=soup(u)
    for fig in s.select('figure'):
        h=fig.select_one('figcaption strong');im=fig.find('img');title_tag=h.find('em')if h else None
        if not title_tag or not im:continue
        head=h.get_text(' ',strip=True);title=title_tag.get_text(' ',strip=True);creator=head.split(title,1)[0].strip(' ,');dt=head.split(title,1)[1].strip(' ,');cap=fig.figcaption.get_text(' ',strip=True)
        f=add(mu,title,creator,dt,u,m.h.sha(im['src'].encode())[:16],im['src'],source_receipt=p['receipt'],original_caption=cap,holding_note=cap)
        if not f:continue
        if creator in ['Antonio Canova','Auguste Rodin']:f['work_type']='sculpture'
        f.update(creator_credit=cap.split('Kunsthalle Bremen')[-1].strip(' /')or'Kunsthalle Bremen',rights_label='Kunsthalle Bremen / Der Kunstverein in Bremen; website reproduction retained. Separate high-resolution press download is password-protected and was not accessed.')
        if creator=='Auguste Rodin':f.update(image_eligible=False,date_evidence_note='The caption supplies 1875/76 for the work but not the casting year of this bronze; image held for physical-version dating.')
def mdbk():
    u='https://mdbk.de/sammlungen/';mu=museum('de-mdbk-leipzig','Museum der bildenden Künste Leipzig','Leipzig','Saxony',u);s,p=soup(u)
    for fig in s.select('figure'):
        cap=fig.find('figcaption');im=fig.find('img')
        if not cap or not im:continue
        text=cap.get_text(' ',strip=True);ma=re.match(r'(.+?), (.+?), ((?:um )?\d{4}(?:/\d{1,4})?|o\. J\.)(?:,|$)',text)
        if not ma:continue
        creator,title,dt=ma.groups();srcset=im.get('data-srcset','');image=urljoin(u,srcset.split(',')[min(3,len(srcset.split(','))-1)].strip().split(' ')[0])if srcset else urljoin(u,im['src'])
        f=add(mu,title,creator,dt,u,m.h.sha(title.encode())[:16],image,source_receipt=p['receipt'],original_caption=text,holding_note=text)
        if not f:continue
        f['rights_label']='Museum der bildenden Künste Leipzig; source caption and any named lender rights retained'
        if creator=='Balthasar Permoser':f['work_type']='sculpture'
        elif creator in ['Johann Heinrich Füssli','Johan Heinrich Ferdinand Olivier','Giovanni Battista Piranesi','Max Beckmann']:f['work_type']='unknown'
def saarland():
    u='https://www.modernegalerie.org/de/';mu=museum('de-saarlandmuseum-moderne-galerie','Saarlandmuseum – Moderne Galerie','Saarbrücken','Saarland',u);s,p=soup(u)
    for cap in s.select('.image-caption'):
        t=cap.get_text(' ',strip=True);ma=re.match(r'(.+?), (.+?), ((?:um )?\d{4}(?:[-/]\d{1,4})?)(?:[, ]|$)',t)
        if not ma:continue
        cr,title,dt=ma.groups();im=cap.parent.find('img');f=add(mu,title,cr,dt,u,m.h.sha(t.encode())[:16],urljoin(u,im['src'])if im else None,source_receipt=p['receipt'],original_caption=t)
        if f:
            if 'Kohle'in t:f.update(work_type='drawing',medium='Kohle auf Büttenpapier')
            if 'Albuminpapier'in t:f.update(work_type='photograph',medium='Albuminpapier auf Karton')
def finish():b['finish']('regional')
if __name__=='__main__':
    for name in ['lenbach','barberini','bremen','mdbk','saarland']:
        try:globals()[name]()
        except Exception as e:H.append(dict(museum=name,reason=type(e).__name__+': '+str(e)[:200]));print('PARSER HOLD',name,str(e)[:180],flush=True)
    finish()
