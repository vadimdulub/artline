#!/usr/bin/env python3
"""Selected regional catalogue objects, with literal source fields and conservative dates."""
import collections,importlib.util,re
from pathlib import Path
import pdfplumber
s=importlib.util.spec_from_file_location('island',Path(__file__).with_name('cyprus-island-20261007.py'));x=importlib.util.module_from_spec(s);s.loader.exec_module(x)
n,h,R=x.n,x.h,x.R
c=n.module('regional_candidate_helpers','nicosia-artwork-candidates-20261007.py')
cat=n.module('regional_catalogue_dates','nicosia-cyprus-museum-catalogue-20261007.py')
h.RUN=R
UNKNOWN=dict(date_display=None,first=None,last=None,precision='unknown')
def make(page,scheme,sid,slug,title,date=None,creator=None,medium=None,kind='unknown',dimensions=None,accession=None,raw=None):
    f=c.fact(page,scheme,str(sid),slug,raw or {})
    parsed=c.dates(date)if date else dict(UNKNOWN)
    f.update(title=title,creator_label=creator,medium=medium,work_type=kind,dimensions=dimensions,accession=accession,**parsed)
    f['shared_source_url']=True
    return f
def museum_map():
    reg=h.load(R/'institution-registry.json')['records']
    def slug(i):return next(r['slug']for r in reg if any(s.get('identifier')==str(i)for s in r['sources']))
    return {'Larnaca District Museum':slug(468520),'Limassol District Museum':slug(468714),'Paphos District Museum':slug(468798),'Marion-Arsinoe Local Museum':slug(468792),'Kourion-Episkopi Local Museum':slug(468738),'Kouklia Local Museum':'palaipafos-archaeological-museum-kouklia','Pierides – Laiki Bank Museum':slug(468548)}
def archaeological_date(value):
    parsed=cat.date(value)
    if parsed:return parsed
    # Keep qualifiers literally; use only the explicitly stated century envelope.
    nums=re.findall(r'\(([^()]*)\)',value);numeric=nums[-1]if nums else value
    m=re.fullmatch(r'(?:end of |early |late |earlier half of the |second half of the )?(\d{1,2})(?:st|nd|rd|th)(?:/(?:early )?(\d{1,2})(?:st|nd|rd|th))? c\. (AD|BC)',numeric)
    if m:
        one,two=int(m[1]),int(m[2]or m[1]);a,b=((one-1)*100+1,two*100)if m[3]=='AD'else(-one*100,-((two-1)*100+1))
        return dict(date_display=value,first=a,last=b,precision='century'if one==two else'range')
    m=re.fullmatch(r'(?:ca\. )?(\d{4})-(\d{4})/(\d{4}) BC',numeric)
    if m:return dict(date_display=value,first=-int(m[1]),last=-min(int(m[2]),int(m[3])),precision='circa_range'if numeric.startswith('ca.')else'range')
    return dict(UNKNOWN,date_display=value)
def regional_pdf():
    mapping=museum_map();cols=[];rows=[];held=[]
    rc=h.load(n.REPO/'docs/research/nicosia-museums-20261007/catalogue-pdf.json')
    with pdfplumber.open('/tmp/artline-nicosia-cultures-dialogue.pdf')as pdf:
        for num in range(106,270):
            p=pdf.pages[num-1]
            for side,(a,b)in [('left',(.14,.53)),('right',(.54,.94))]:
                text=p.crop((p.width*a,0,p.width*b,p.height*.92)).extract_text(x_tolerance=2,y_tolerance=3)or''
                if any(label+','in text for label in mapping):cols.append(dict(pdf_page=num,column=side,text=text))
    h.save(R/'regional-catalogue-clean-columns.json',cols)
    excluded={19,20,21,22,28,32,51,56,66,67,68,72,80,101,112,181}
    for col in cols:
        for match in re.finditer(r'(?:^|\n)(\d{1,3})\n((?:(?!\n\d{1,3}\n).)*?)(?=\n\d{1,3}\n|\Z)',col['text'],re.S):
            number=int(match[1]);lines=match[2].splitlines()
            found=next(((i,label)for i,l in enumerate(lines[:13])for label in mapping if l.startswith(label+',')),None)
            if not found:continue
            end,label=found;header=lines[:end+1];raw=dict(catalogue_number=number,pdf_page=col['pdf_page'],column=col['column'],header=header,description_and_references=lines[end+1:])
            if number in excluded:held.append(dict(raw_fields=raw,reason='natural_specimen_tool_industrial_or_unresolved_group'));continue
            dim=next((i for i,l in enumerate(header)if re.match(r'^(?:L\.|H\.|Diam\.|D\.|W\.)',l)),None)
            dp=next((i for i in range((dim or 0)+1,end)if re.search(r'\b(?:BC|AD|period)\b',header[i])),None)
            if dim is None or dim<2 or dp is None:held.append(dict(raw_fields=raw,reason='header_layout_review'));continue
            title=' '.join(header[:dim-1]).replace('fi gur','figur').replace('fl ask','flask');medium=header[dim-1]
            f=make(dict(url=rc['url'],receipt=rc),'cyprus-museum-cultures-in-dialogue-2012',number,mapping[label],title,medium=medium,dimensions=' '.join(header[dim:dp]),accession=header[-1][len(label)+1:].strip(),raw=raw)
            f.update(archaeological_date(header[dp]))
            f['work_type']='sculpture'if re.search('statue|statuette|figurine|head|relief|model|capital',title,re.I)else'ceramic'if'Clay'in medium or'Faience'in medium else'metalwork'if re.search('Gold|Silver|Bronze|Copper',medium)else'unknown'
            f['holding_note']=label+' lender credit and inventory in the Department of Antiquities 2012 catalogue, page '+str(col['pdf_page'])+', catalogue '+str(number)+'.'
            f['remaining_uncertainty']='Documented 2012 holding; later transfer and present display unverified. Numeric unknown dates remain in review. Temporary Brussels exhibition is not a current location.'
            rows.append(f)
    assert len({f['source_id']for f in rows})==len(rows)
    return rows,held
def christian():
    p=h.load(R/'indexes/christian-art-tour-captions.json');captions={re.search(r'spotpoint(\d+)',r['id'])[1]:r for r in p['captions']}
    # Component suffixes correspond to the source's explicitly numbered paintings,
    # not generated extra objects or separate details of one painting.
    selected=[
      ('13603','Last Supper',None,'Jan Tengnagel','Oil on copper','painting'),
      ('13605-1','Paintings of Magdalene — 1','17th century','Italian School','Oil on canvas','painting'),
      ('13605-2','Paintings of Magdalene — 2','18th century','Giangattista Tiepolo (attributed)','Oil on canvas','painting'),
      ('13604','Angels of Passion (The Deposition)','18th century',None,'Oil on canvas','painting'),
      ('13606-1','Mater Dolorosa — 1','18th century','Spanish School','Oil on canvas','painting'),
      ('13606-2','Mater Dolorosa — 2','18th century','Isidoro Tapia','Oil on canvas','painting'),
      ('13602','Ecce Homo','17th century',None,'Oil on canvas','painting'),
      ('13607','Christ driving the money changers from the temple',None,'Rembrandt','Etching','print'),
      ('13610',"Give to Caesar what is Caesar's",None,'Pietro Fontana (printmaker), after Peter Paul Rubens; designer Domenicos Del Frate','Etching and burin','print'),
      ('13609','Madonna Nera',None,'Salvador Dali','Coloured lithograph','print'),
      ('13612','The Storm',None,'Frantisek Kupka','Coloured engraved wood','print'),
      ('13622','Angel',None,'Aristides Patsoglou','Bronze','sculpture'),
      ('13623','Luke the Evangelist','late 18th century',None,'Tempera on wood','painting'),
      ('13732','Praying Nun',None,'Nikolaos Kounelakis','Oil on wood','painting'),
      ('13733','St Apostolos the Young',None,'Theofilos (Hadjimichael)','Oil on wood','painting'),
      ('13616-1','Madonna of Vladimir','early 18th century',None,'Tempera on wood','painting'),
      ('13616-2','Madonna of Smolensk','late 18th century',None,'Tempera on wood','painting'),
      ('13615','Madonna the Unexpected Mercy','18th century',None,'Tempera on wood','painting'),
      ('13614','The Songs of Mikis Theodorakis',None,'Evgeni Klemenov','Oil on canvas','painting'),
      ('13621','Holy Family','18th century',None,'Oil on tin','painting')]
    rows=[]
    for sid,title,date,creator,medium,kind in selected:
        original=captions[sid.split('-')[0]];f=make(dict(url=p['receipt']['url'],receipt=p['receipt']),'aradippou-christian-art-virtual-tour',sid,'cyprus-museum-christian-art-christoforou-collection',title,date,creator,medium,kind,raw=dict(caption=original,component=sid.split('-')[1]if'-'in sid else None))
        f['holding_note']='Official Larnaka regional museum directory links this Aradippou museum tour; its object hotspot and caption document the Christoforou collection work.'
        f['remaining_uncertainty']='Creation date remains unknown where only artist life dates, acquisition dates or print-design dates are supplied. Unknown-date records remain in review and are not eligible by date. No fresh display or image-rights claim.'
        if sid=='13607':f['date_display']='1635';f['raw_fields']['date_review']='Source gives 1635; physical print impression date not established. Numeric creation years remain unknown.'
        rows.append(f)
    held=[dict(source_id='13608',reason='1635 wood engraving conflicts with Durer death in 1528; edition and physical impression unresolved'),dict(source_id='13611',reason='Explicit creation 1974 is after cutoff'),dict(source_id='13605-3',reason='Third Magdalene painting has no maker or creation date'),dict(source_id='13613/13620/13624',reason='Video or title-only hotspot lacks sufficient object metadata')]
    return rows,held
def kykkos():
    pages={p['url'].split('.net/')[-1]:p for path in (R/'pages').glob('kykkos*.json')if '/room'in(p:=h.load(path))['url']}
    # Whole catalogued objects only. Detail figures and caption/text date conflicts held.
    groups={
      'room1/eg-page1.html':[(13,'Attic amphora with black figures','circa 520 BC','Painter of Antimenos',None,'ceramic'),(14,'Tray from Graecia Magna (Apuleia)','4th century BC','Workshop of the painter of Baltimore',None,'ceramic'),(15,'Krater from Graecia Magna (Southern Italy)','4th century BC','Painter De Santis',None,'ceramic')],
      'room2/eg-page1.html':[(16,'Bronze palm holding a globe and cross','6th-7th century',None,'Bronze','metalwork'),(17,'Bronze standard or fan','6th-7th century',None,'Bronze','metalwork'),(18,'Six-sided silver pan of a censer','4th-7th century',None,'Silver','metalwork')],
      'room2/eg-page2.html':[(20,'Silver gilt gospel cover with representation of the Ascension of Christ','1813','John and George (goldsmiths)','Silver gilt','metalwork'),(22,'Silver gilt gospel cover with stetharia of enamel and niello','1802','Russian workshop','Silver gilt, enamel and niello','metalwork')],
      'room2/eg-page3.html':[(23,'Silver gilt suspended lamp','19th century',None,'Silver gilt','metalwork'),(24,'Wooden, book-shaped reliquary with silver gilt plates','1801','Hadjilambrinos of Smyrna','Wood and silver gilt plates','unknown'),(25,'Wooden, book-shaped reliquary with silver gilt plates',None,'Philippos Chrysochos','Wood and silver gilt plates','unknown'),(26,'Silver gilt reliquary of the skull of Saint John Potamites','1782',None,'Silver gilt','metalwork')],
      'room2/eg-page4.html':[(29,'Silver gilt cross','18th century',None,'Silver gilt','metalwork'),(30,'Silver gilt processional cross','1636','Christophes Argyrou','Silver gilt','metalwork'),(31,'Silver gilt artoporion','1807',None,'Silver gilt','metalwork')],
      'room2/eg-page5.html':[(32,'Silver gilt cover of the Holy Icon of the Virgin of Kykkos','1576','Toumazos','Silver gilt','metalwork'),(33,'Wood-carved cross with base','1545','Probably George Lascaris','Wood','sculpture')],
      'room2/eg-page6.html':[(36,'Wooden antimensium','1653',None,'Wood with affixed ivory plaque and cameo','unknown')],
      'room2/eg-page6-2.html':[(39,'Cross for consecrating holy water','1710',None,'Wood-carved centre with silver frame and ornaments','unknown'),(40,'Epitaphios (Funeral Representation)','1703','Despoineta','Red silk with golden and silver threads','unknown'),(41,'Epitaphios of the Virgin','1847','Gregoria Costa Papa',None,'unknown')],
      'room2/eg-page7.html':[(42,'Stole','1735',None,None,'unknown'),(43,'Stole','1741',None,None,'unknown')],
      'room2/eg-page8.html':[(45,'Cover of the Holy Icon of the Virgin of Kykkos','1780',None,None,'unknown'),(46,"Knee-pad with representation of Christ's Baptism",'18th century',None,None,'unknown')],
      'room2/eg-page9.html':[(47,'Golden coin of Alexios I Komnenos','1092-1116',None,'Gold','metalwork'),(48,'Golden neck-lace with pearls and amethyst','6th-7th century',None,'Gold, pearls and amethyst','metalwork'),(49,'Pair of golden earrings','7th century',None,'Gold','metalwork'),(50,'Golden earring','5th-6th century',None,'Gold','metalwork'),(51,'Golden brooch','11th-13th century',None,'Gold','metalwork')],
      'room2/eg-page10.html':[(52,'Early Christian marble relief','5th-6th century',None,'Marble','sculpture')],
      'room3/eg-page1.html':[(53,'Processional Cross','14th-15th century',None,None,'unknown'),(54,'The Crucifixion','1520',None,None,'painting'),(55,'Mother of God the Kykkotissa','15th-16th century',None,None,'painting')],
      'room3/eg-page2.html':[(56,'Utter Humility','16th-17th century',None,None,'painting'),(57,'Saint John the Baptist','16th-17th century',None,None,'painting'),(58,'Enthroned baby-holding Mother of God','1650','Paul the Hierograph',None,'painting')],
      'room3/eg-page3.html':[(60,'Archangel Michael','1782','Michael of Cyprus',None,'painting'),(61,'Mother of God Hodegetria','13th century',None,None,'painting'),(63,'The Calling of the Apostles Andrew and Peter','1792','John Kornaros',None,'painting'),(64,'The Holy Mandelium','1776','Michael Apostoles',None,'painting'),(65,'Mother of God the Kykkiotissa','1757','Charalambos Kykkotis',None,'painting'),(66,'Jesus Christ as Saviour of the World','1641','Solomos Hierothytes (text: Solon Hierothytes)',None,'painting'),(67,'Saint Demetrios (removed fresco)','13th century',None,'Fresco','fresco')],
      'room3/eg-page4.html':[(68,'Wooden bone-ornamented throne of the Holy Icon of the Virgin of Kykkos','1785',None,'Wood and bone','unknown')],
      'room4/eg-index.html':[(71,'History of the Monastery of Kykkos','1778','Michael Apostoles','Colour-coated copper-engraving','print')],
      'room4/eg-page1.html':[(74,'Parchment manuscript scroll','circa 12th century',None,'Parchment','manuscript')]}
    rows=[]
    for path,objects in groups.items():
        p=pages[path]
        for sid,title,date,creator,medium,kind in objects:
            # Pict 13/67 are discussed in body text on this page; all others captioned.
            assert re.search(r'(?:Pict\.?|Pitc\.?|picture)\s*'+str(sid)+r'\b',p['text'],re.I),(path,sid)
            f=make(p,'kykkos-museum-native-guide',str(sid),'kykkos-monastery-museum',title,date,creator,medium,kind,raw=dict(figure=sid,guide_text=p['text'],source_publication_year=1998))
            if sid==13:f.update(date_display='c. 520 B.C.',first=-520,last=-520,precision='circa')
            if sid==74:f.update(date_display='circa the 12th century',first=1101,last=1200,precision='century')
            if sid==25:f['accession']='5949'
            if sid==26:f['dimensions']='36,5 × 23,3 × 13,4 cm'
            if sid==36:f['dimensions']='42,3 × 61,2 cm'
            if sid==71:f['dimensions']='96 × 67 cm'
            f['holding_note']='Whole object identified by figure number in the monastery-hosted museum guide (1998); contemporary primary directory verifies the museum identity.'
            f['remaining_uncertainty']='Historical catalogue holding; later transfers and current display unverified. No image use. Figure details remain part of their whole object; qualified creators retained.'
            rows.append(f)
    held=[dict(source_id='21',reason='Caption dates gospel cover 1693; body text distinguishes printed gospel 1693 and cover 1737; date conflict held'),dict(source_id='27',reason='Composite basin: base 1639 and basin 19th century; component/date review'),dict(source_id='69',reason='Body says 6th century, caption 16th; source date conflict'),dict(source_id='72/73',reason='Two manuscript illustrations may belong to one volume; physical object identity unresolved'),dict(source_id='4',reason='1996 floor mosaic after cutoff'),dict(source_id='19/28/34/35/37/38/59/62/70',reason='Detail images or constituent elements, not separate whole artworks')]
    return rows,held
def build():
    rows=[];held=[]
    for name,func in [('regional_pdf',regional_pdf),('christian',christian),('kykkos',kykkos)]:
        selected,excluded=func();rows+=selected;held.extend(dict(source=name,**r)for r in excluded);print(name,len(selected),'selected;',len(excluded),'held',flush=True)
    for f in rows:
        assert f['title'] and (f['last']is None or f['last']<=1970)
        assert f['precision']=='unknown'or f['last']is not None
    h.save(R/'regional-artwork-candidates.json.gz',dict(at=h.now(),selected_count=len(rows),records=rows,held=held,policy='Selected source-backed metadata; all new records in review, unknown dates preserved, no images or publication.'))
    print('TOTAL',len(rows),collections.Counter(r['museum_slug']for r in rows),flush=True)
if __name__=='__main__':build()
