"""Selected regional museum objects; never writes a catalogue database."""
import runpy,re,sys,json,collections
from urllib.parse import urljoin
b=runpy.run_path('ops/germany-deep-facts-20261011.py');m=b['m'];soup=b['soup'];add=b['add'];museum=b['museum'];M=b['M'];F=b['F'];H=b['H']
def guard(fn,*args):
    try:return fn(*args)
    except Exception as e:H.append(dict(parser=fn.__name__,args=args,reason=type(e).__name__+': '+str(e)[:250]));print('HOLD',fn.__name__,str(e)[:180],flush=True)
def fieldtext(s):
    d={}
    for lab in s.select('.field__label'):
        par=lab.parent;items=par.select('.field__item');d[lab.get_text(' ',strip=True)]=' | '.join(x.get_text(' ',strip=True)for x in items)
    return d
def moritzburg():
    u='https://www.kunstmuseum-moritzburg.de/forschung-sammlungen/die-sammlungen/gemaelde/';mu=museum('de-moritzburg-halle','Kunstmuseum Moritzburg Halle (Saale)','Halle (Saale)','Saxony-Anhalt',u);s,p=soup(u)
    for fig in s.select('figure'):
        if not fig.figcaption or not fig.img:continue
        cap=fig.figcaption.get_text(' ',strip=True).replace('\xa0',' ');ma=re.match(r'([^:]+): (.+?), ((?:um )?\d{4}(?:/\d{4})?), (.+?), ([^|]+)\|(.+)',cap)
        if not ma:continue
        cr,title,dt,med,dim,credit=ma.groups();f=add(mu,title,cr,dt,u,m.h.sha(title.encode())[:16],urljoin(u,fig.img['src']),med,dim.strip(),source_receipt=p['receipt'],original_caption=cap)
        if f:
            f.update(creator_credit=credit.strip(),rights_label=credit.strip())
            if cr=='Carl Blechen':f['date_evidence_note']='Visible caption says circa 1828; image filename says circa 1829. Caption preserved; discrepancy requires editorial review.'
def hannover():
    u='https://www.landesmuseum-hannover.de/sammlung/kunst/';mu=museum('de-landesmuseum-hannover','Landesmuseum Hannover – Landesgalerie','Hannover','Lower Saxony',u);s,p=soup(u)
    for fig in s.select('figure'):
        c=fig.select_one('.akkordion-header');im=fig.img
        if not c or not im:continue
        cap=c.get_text(' ',strip=True);ma=re.match(r'(.+?), (.+?), ((?:um )?\d{4}(?:[-/]\d{1,4})?), (.+)',cap)
        if not ma:H.append(dict(url=u,caption=cap,reason='Caption needs manual date parsing'));continue
        cr,title,dt,rest=ma.groups();inv=re.search(r'Inv\.-Nr\. ([^,]+(?:, \d+)?)(?:,|$)',rest);f=add(mu,title,cr,dt,u,inv[1]if inv else m.h.sha(title.encode())[:16],im['src'],accession=inv[1]if inv else None,source_receipt=p['receipt'],original_caption=cap,holding_note=cap)
        if f:
            f['medium']=rest.split(',')[0]
            if any(x in rest for x in ['Feder','Lithografie','lithografie']):f['work_type']='drawing_or_print'
            if cr=='Tilman Riemenschneider':f['work_type']='sculpture'
            if 'Holbein'in cr:f['view_label']='Museum reproduction showing portrait with its cover; complete source frame retained'
def kiel(url):
    mu=museum('de-kunsthalle-kiel','Kunsthalle zu Kiel','Kiel','Schleswig-Holstein','https://www.kunsthalle-kiel.de/de/sammlung-online');s,p=soup(url);h=s.h1
    for x in h.select('.lebensdaten'):x.extract()
    cr=h.get_text(' / ',strip=True);line=s.select_one('.bildtitel2').get_text(' ',strip=True);title,dt=line.rsplit(', ',1)
    pic=s.find('picture',attrs={'data-alt':True});image=urljoin(url,pic.source['srcset'].split(', ')[0].split(' ')[0]);text=p['text'];fld={}
    for k in ['Inv.','Material','Maße','Signatur','Zugang','Creditline']:
        if '\n'+k+'\n'in text:fld[k]=text.split('\n'+k+'\n',1)[1].split('\n',1)[0]
    f=add(mu,title,cr,dt,url,url.rsplit('-',1)[-1],image,fld.get('Material'),fld.get('Maße'),fld.get('Inv.'),source_receipt=p['receipt'],source_fields=fld)
    if f:
        rights='; '.join(x for x in text.splitlines()if x.startswith('©')or'Urheberrecht verjährt'in x);f.update(rights_label=rights,creator_credit='Kunsthalle zu Kiel, Foto: Sönke Ehlert',license_url='https://creativecommons.org/licenses/by-nc-nd/4.0/')
        if 'Gujer'in cr:f.update(work_type='textile',date_evidence_note='Both Kirchner and the weaver Lise Gujer are credited. The museum creation date 1924/1925 is distinct from its 1964 acquisition date.')
def weimar(url):
    s,p=soup(url);fld={dt.get_text(' ',strip=True):dt.find_next_sibling('dd').get_text(' ',strip=True)for dt in s.select('dt')if dt.find_next_sibling('dd')}
    if not fld:
        # The treasury exposes its own labelled metadata as adjacent grid cells.
        txt=p['text'].splitlines()
        for k in ['Künstler','Titel','Standort','Entstehungszeit','Objekttyp','Material / Technik','Inventar-Nr.','Copyright']:
            if k in txt:fld[k]=txt[txt.index(k)+1]
    loc=fld.get('Standort','');assert 'Bauhaus'in loc,loc
    mu=museum('de-bauhaus-museum-weimar','Bauhaus-Museum Weimar','Weimar','Thuringia','https://100schaetze.klassik-stiftung.de/');cr=re.sub(r'\s*\(\d{4}[–-]\d{4}\).*','',fld['Künstler']);title=fld['Titel'];im=next(i['url']for i in p['images']if title in i['alt']and'Rückseite'not in i['alt'])
    f=add(mu,title,cr,fld['Entstehungszeit'],url,fld['Inventar-Nr.'],im,fld.get('Material / Technik'),accession=fld['Inventar-Nr.'],source_receipt=p['receipt'],source_fields=fld)
    if f:f.update(rights_label=fld.get('Copyright',f['rights_label']),creator_credit=fld.get('Copyright','Klassik Stiftung Weimar'))
def gnm(url):
    mu=museum('de-germanisches-nationalmuseum','Germanisches Nationalmuseum','Nuremberg','Bavaria','https://objektkatalog.gnm.de/');s,p=soup(url);fld=fieldtext(s)
    assert fld.get('Titel'),fld
    im=next((x['url']for x in p['links']if x['text']=='[JPG]'),None)
    f=add(mu,fld['Titel'],fld.get('Hersteller')or'Unknown maker',fld.get('Herstellungsdatum',''),url,fld['Inventarnummer'],im,fld.get('Material und Technik'),fld.get('Maße'),fld['Inventarnummer'],source_receipt=p['receipt'],source_fields=fld,holding_note=fld.get('Proviso','Germanisches Nationalmuseum catalogue record'))
    if f:
        f['creator']=re.sub(r'\s*GND.*','',f['creator']);f['rights_label']='Germanisches Nationalmuseum; exact image rights retained, no open licence established from this record'
def berlin(url):
    s,p=soup(url);fld={dt.get_text(' ',strip=True):dt.find_next_sibling('dd').get_text(' ',strip=True)for dt in s.select('dt')if dt.find_next_sibling('dd')};text=p['text'];title=s.h1.get_text(' ',strip=True);native=re.search(r'obj-(\d+)',url)[1]
    collection='Skulpturensammlung und Museum für Byzantinische Kunst'if'Museum für Byzantinische Kunst'in text else'Gemäldegalerie'if'Gemäldegalerie'in text else'Alte Nationalgalerie'if'Alte Nationalgalerie'in text else None
    assert collection, 'Specific Berlin collection not established'
    names={'Skulpturensammlung und Museum für Byzantinische Kunst':('de-bode-museum','Bode-Museum – Skulpturensammlung und Museum für Byzantinische Kunst'),'Gemäldegalerie':('de-gemaeldegalerie-berlin','Gemäldegalerie Berlin'),'Alte Nationalgalerie':('de-alte-nationalgalerie','Alte Nationalgalerie')};slug,name=names[collection];mu=museum(slug,name,'Berlin','Berlin',url)
    dt=fld.get('Datierung')or fld.get('Date(s)','');dt=dt.removeprefix('Datierung: ');cr=fld.get('Beteiligte')or fld.get('Involved parties')or'Unknown maker (Byzantine)';cr=re.sub(r'\s*\(\d{3,4} - \d{3,4}\)\s*,?\s*(?:Maler\*in|painter)?','',cr).strip()
    inv=re.search(r'Ident\.\s*Nr\.:\s*([^\n]+)',text);im=next((i['url']for i in p['images']if i['alt']==title),None);credits=[x for x in text.splitlines()if x.startswith(('Fotonachweis:','Credit:'))]
    f=add(mu,title,cr,dt,url,native,im,fld.get('Material / Technik')or fld.get('Material / Technique'),fld.get('Abmessungen')or fld.get('Dimensions'),inv[1]if inv else None,source_receipt=p['receipt'],source_fields=fld,holding_note=collection)
    if f:
        f.update(creator_credit=credits[0]if credits else'Staatliche Museen zu Berlin',rights_label=credits[0]if credits else'Staatliche Museen zu Berlin; rights not established')
        if 'Public Domain Mark 1.0'in text:f.update(rights_status='public_domain',rights_label='Public Domain Mark 1.0 (first object reproduction)',license_url='https://creativecommons.org/publicdomain/mark/1.0/')
        if 'Mosaik'in title:f['work_type']='mosaic_icon'
        if dt=='1. Viertel 12. Jahrhundert':f.update(start=1101,end=1125,precision='quarter_century',image_eligible=bool(im))
def schwerin():
    u='https://carlmalchin.museum-schwerin.de/';mu=museum('de-staatliches-museum-schwerin','Staatliches Museum Schwerin','Schwerin','Mecklenburg-Vorpommern',u);s,p=soup(u)
    for im in p['images']:
        if 'Carl Malchin, Dorfstraße, 1881'not in im['alt']:continue
        f=add(mu,'Dorfstraße','Carl Malchin','1881',u,'malchin-dorfstrasse-1881',im['url'],source_receipt=p['receipt'],original_caption=im['alt']);f.update(creator_credit=im['alt'].split('©')[-1].strip(),rights_label=im['alt'].split('©')[-1].strip());break
if __name__=='__main__':
    label=sys.argv[1]
    if label=='expanded':
        for fn in [moritzburg,hannover,schwerin]:guard(fn)
        for tail in ['bergleben-ernst-ludwig-kirchnerlise-gujer-361','landschaft-mit-weiden-paul-wassily-689']:guard(kiel,'https://www.kunsthalle-kiel.de/de/sammlung-online/'+tail)
        for tail in ['lyonel-feininger-gelmeroda-xi-1928/','johannes-itten-abstrakte-komposition-um-1917/']:guard(weimar,'https://100schaetze.klassik-stiftung.de/objekt/'+tail)
        for rid in ['Gm167','Gm168','Gm169']:guard(gnm,'https://objektkatalog.gnm.de/objekt/'+rid)
        for rid in ['965511','1408418','868435','870129','863178','870774']:guard(berlin,'https://search.smb.museum/object/obj-'+rid)
    b['finish'](label)
