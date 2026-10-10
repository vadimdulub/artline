#!/usr/bin/env python3
"""Reviewed object captions from smaller Nicosia collections; no database writes."""
import importlib.util,re
from pathlib import Path
s=importlib.util.spec_from_file_location('candidates',Path(__file__).with_name('nicosia-artwork-candidates-20261007.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
h,n,R=c.h,c.n,c.R
records=[]
def page(key):
    p=R/'pages'/(key+'.json')
    return h.load(p if p.exists()else R/'artwork-pages'/(key+'.json'))
def add(key,museum,title,when,kind,*,accession=None,creator=None,medium=None,dimensions=None,object_key=None,evidence=None,note=None,explicit_bounds=None):
    x=page(key);text=re.sub(r'\s+',' ',x['text']);assert evidence and evidence in text,(key,evidence)
    f=c.fact(x,'nicosia-editorial-primary-caption',museum+'/'+(object_key or accession),museum,dict(verified_caption=evidence,page_key=key))
    f.update(title=title,creator_label=creator,medium=medium,dimensions=dimensions,accession=accession,work_type=kind)
    f.update(c.dates(when))
    if explicit_bounds:f.update(date_display=when,first=explicit_bounds[0],last=explicit_bounds[1],precision=explicit_bounds[2])
    assert f['last']is not None and f['last']<=1970 and f['precision']!='unknown',(title,when)
    f['shared_source_url']=True
    f['identity_note']='Inventory identifies the object where supplied; otherwise the editorial source key is an internal caption selector, not an invented museum accession.'
    if note:f['holding_note']+=' '+note
    records.append(f)

def municipal():
    museum='leventis-municipal-museum-nicosia'
    rows=[
      ('municipal-maps','B/1989/204,4','Map of Nicosia','c. 1579','print','Engraving'),
      ('municipal-maps','B/1989/204,6','Map of Nicosia','c. 1570','print','Engraving'),
      ('municipal-maps','B/1989/204,8','Map of Nicosia','c. 1572-1573','print','Engraving'),
      ('municipal-cornaro','B/1996/1241','Caterina Cornaro hands over the Crown of Cyprus to Doge Agostino Barbarigo in 1489','19th century','print','Engraving'),
      ('municipal-cornaro','C/2003/0,224','The coat of arms of Caterina Cornaro','c. 1680','textile','Tapestry'),
      ('municipal-ceramics','Β/1996/1421','Bowl with an anthropomorphic sun','14th century','ceramic',None),
      ('municipal-ceramics','B/2003/0,21','Bowl with a hunter-falconer','15th century','ceramic',None),
      ('municipal-ceramics','Β/2003/0,225','Bowl with rosettes','14th century','ceramic',None),
      ('municipal-ceramics','Β/2003/0,70','Bowl with a fish','mid-13th century','ceramic',None),
      ('municipal-ancient-times','A/2001/2569','Pyxis','1450-1200 BC','ceramic','Mycenaean IIIA2 ware'),
      ('municipal-ancient-times','A/1989/302,10','Bowl','1450-1200 BC','ceramic','White Slip Ware II ceramic'),
      ('municipal-british-rule','D/1989/345','Statuette depicting Lieutenant Horatio Herbert Kitchener on horseback','1880','sculpture',None),
      ('municipal-british-rule','D/1988/126','Commemorative cup depicting King Edward VIII','1937','unknown',None),
      ('municipal-british-rule','D/1990/353, 13','Commemorative tray with a portrait of King George I of Greece','circa 1870','unknown',None),
      ('municipal-british-rule','D/1996/1345','Silver ring','1940','metalwork','Silver'),
      ('municipal-byzantine-period','Β/1995/1202','Coin of Isaac Comnenos with chain','12th century','metalwork',None),
      ('municipal-byzantine-period','Β/2000/2303','Copper cross–reliquary','14th century','metalwork','Copper'),
      ('municipal-byzantine-period','B/1995/1185','Golden coin of Nikiforos II Phocas','10th century','metalwork','Gold'),
      ('municipal-frankish-period','C/2001/2445','Silver seal with handle, decorated with floral motifs and a lion of Venice','16th century','metalwork','Silver'),
      ('municipal-frankish-period','B/1995/1200','Portable Cross and Chain','13th century','metalwork',None),
      ('municipal-jewellery-collection','C/2003/0,162','Buckle','18th century','metalwork','Silver'),
      ('municipal-jewellery-collection','C/2000/2154','Cross with Toutounia and Chain','Mid-19th century','metalwork','Silver gilt with coral beads'),
      ('municipal-ottoman-period','C/2009/0,793','Portrait of Archbishop Chrysanthos','18th century','painting','Oil on canvas'),
      ('municipal-ottoman-period','C/2022/5995','Scene from the siege of Nicosia by the Ottomans in 1570','1880','print','Engraving drawn over in pencil and charcoal'),
      ('municipal-ottoman-period','C/1994/947','Silver Chalice','1921','metalwork','Silver'),
      ('municipal-ottoman-period','C/2000/2329','Yataghan','19th century','metalwork','Steel and ivory'),
      ('municipal-venetian-period','Β/1990/452','Maiolica ceramic plate','16th century','ceramic','Maiolica ceramic'),
      ('municipal-venetian-period','Β/1986/55','Silver bowl decorated with a rosette','16th century','metalwork','Silver'),
      ('municipal-venetian-period','B/1986/61','Silver liturgical spoon','c. 1472','metalwork','Silver'),
      ('municipal-venetian-period','B/1995/1222','Gold ducat minted under Girolamo Priuli','1565','metalwork','Gold'),
      ('municipal-venetian-period','Β/1986/60','Gilted ring','16th century','metalwork',None),
    ]
    for key,accession,title,when,kind,medium in rows:
        x=page(key);s=c.soup(x);captions=[]
        for t in s.find_all(string=lambda t:t and 'Object:'in t):
            caption=re.sub(r'\s+',' ',t.parent.parent.get_text(' ',strip=True))
            if accession in caption:captions.append(caption)
        assert len(set(captions))==1,(key,accession,captions)
        add(key,museum,title,when,kind,accession=accession,medium=medium,evidence=captions[0],creator='Hermann Vogel'if accession=='C/2022/5995'else None)

def smaller():
    museum='archbishop-kyprianos-museum-strovolos'
    for title,when,creator,evidence in [
        ('Virgin Mary of Passion','16th century',None,'Virgin Mary of Passion (16th century)'),
        ('Virgin Mary-Odegetria with saints','beginning of 17th century',None,'Virgin Mary-Odegetria with saints (beginning of 17 th century) from the Ionian Islands'),
        ('Saint Photios','1957','Solomon Fragkoulidi','Saint Photios (1957)'),
        ('The Virgin of Eleusis of Strovolos','1949','Ioannis Kissonergis','“The Virgin of Eleusis of Strovolos”, a painting of Ioannis Kissonergis (1949)'),
        ('Saint Nicholas','1953','Panaretos Kousoulidis','works of Panaretos Kousoulidis, such as Saint Nicholas (1953)'),
        ('Saint Elias','1959','Andreas Paparistodimou','works of Andreas Paparistodimou, such as Saint Elias (1959)'),
    ]:add('kyprianos',museum,title,when,'painting',creator=creator,object_key=h.norm(title).replace(' ','-'),evidence=evidence)
    add('kyprianos',museum,'Written antimension','1692','textile',object_key='written-antimension-1692',evidence='written (1692) and stamped altar cloths',note='The 1692 written cloth is a distinct object; the later plural stamped cloths are not split into invented records.')
    add('folk-art','cyprus-folk-art-museum-nicosia','Ευαγγελισμός (Annunciation)','16ος αι.','fresco',object_key='annunciation-fresco',evidence='τοιχογραφία του Ευαγγελισμού (16ος αι.)',explicit_bounds=(1501,1600,'century'),note='Architectural fresco within the museum building; discovery in 1950 is not its creation date.')
    add('folk-month','cyprus-folk-art-museum-nicosia','Κολότζι με ήρωες της Ελληνικής Επανάστασης (Decorated gourd with heroes of the Greek Revolution)','1902','unknown',accession='Α.Μ. 41',creator='Δημήτριος Γεωργίου από τα Πυργά',medium='Engraved gourd with metal-lined mouth',evidence='Σύμφωνα με επιγραφή του ιδίου του τεχνίτη, αποτελεί έργο του 1902, του Δημητρίου Γεωργίου από τα Πυργά.',note='Museum gift around 1950 remains provenance only.')
    add('north-lapidary','lapidary-museum-nicosia','Tombstone of Adam de Gaures of Antioch','13th century','sculpture',object_key='adam-de-gaures-tombstone',evidence='the tombstone of Adam de Gaures of Antioch, Marshal of Cyprus dating to the 13th century')
    add('north-dervish','dervish-pasha-museum-nicosia','Decorated ceiling of the main room','1869','sculpture',medium='Wood carving',object_key='main-room-ceiling',evidence='The main room bears the date 1869 on its decorated ceiling boasting ornate wood carvings.',note='Fixed architectural decoration in the museum house, not a movable painting or separate entire-building artwork.')

def boccf():
    # Museum collection samples have distinct exhibition numbers, not accession numbers.
    x=page('boccf-pierides-samples')
    for number,title,dim in [('01/01','Jug','Height: 44.5cm.'),('01/02','Bowl','Height: 14.5cm.; diam.: 31.5cm.'),('01/03','Jug','Height: 29.3cm.')]:
        evidence=re.search(r'Exhibition Number: '+re.escape(number)+r'.*?(?=Exhibition Number:|✖|$)',re.sub(r'\s+',' ',x['text']))[0].strip()
        add('boccf-pierides-samples','giabra-pierides-collection-museum-nicosia',title,'2000-1900 BC','ceramic',medium='Clay, Red Polished III Ware',dimensions=dim,object_key='exhibition-'+number,evidence=evidence,note='Native exhibition number '+number+'; accession not supplied. No claim of current display.')
    x=page('boccf-coins-samples')
    for number,title,when,dim,bounds in [
      ('2/12','Siglos of Evelthon’s successors, Salamis','ca 478–460 BC','22 mm',(-478,-460,'circa_range')),
      ('2/19','1/12 siglos of Evanthes, Salamis','ca 450-430(?) BC','11 mm',(-450,-430,'circa_range')),
      ('2/3','Siglos of Evelthon or successors, Salamis','ca 530/520-500 BC','18 mm',(-530,-500,'circa_range')),
    ]:
        evidence=re.search(r'Exhibition Number: Case '+re.escape(number)+r'.*?(?=Exhibition Number:|✖|$)',re.sub(r'\s+',' ',x['text']))[0].strip()
        add('boccf-coins-samples','cypriot-coinage-museum-nicosia',title,when,'metalwork',medium='AR',dimensions=dim,object_key='case-'+number,evidence=evidence,explicit_bounds=bounds,note='Case number is preserved as source identity only. Issuing authority is not assigned as a named artist.')
    for key in ['boccf-maps-samples','boccf-engravings-samples']:
        x=page(key);s=c.soup(x)
        for node in s.select('.rte-block'):
            text=re.sub(r'\s+',' ',node.get_text(' ',strip=True));ident=re.match(r'(A&L-\d+|E-\d+),',text)
            if not ident:continue
            # Each card's labelled fields are source values, not image captions.
            labels=['Work title','Engraver','Dimensions','Work type','Authors','Book title','Publication year','Title','Cartographer','Publisher','Publication place']
            pattern=r'('+'|'.join(map(re.escape,labels))+r'):\s*'
            parts=re.split(pattern,text);fields=dict(zip(parts[1::2],parts[2::2]))
            year=fields.get('Publication year','').strip(' []')
            if ident[1]=='A&L-004':continue # Book edition explicitly 1513 OR 1520; resolve impression first.
            assert year in ['1540','1652','1799'],(ident[1],fields)
            add(key,'boccf',fields.get('Work title')or fields['Title'],year,'print',accession=ident[1],creator=fields.get('Engraver')or fields.get('Cartographer'),medium=fields.get('Work type')or'Printed map',dimensions=fields.get('Dimensions'),evidence=text,note='Printed edition date refers to this catalogued print; qualified engraver/cartographer credit retained verbatim.')

if __name__=='__main__':
    municipal();smaller();boccf();h.save(R/'editorial-artwork-candidates.json',dict(records=records));print('Prepared',len(records),'editorially checked primary object captions')
