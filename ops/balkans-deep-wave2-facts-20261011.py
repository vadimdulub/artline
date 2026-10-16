"""Selected ancient art and documented collection ownership from illustrated catalogues."""
import runpy,collections,re,pymupdf
b=runpy.run_path('ops/balkans-deep-facts-20261011.py');m=b['m'];fact=b['fact'];soup=b['soup'];MUSEUMS={}
def museum(slug,name,city,cc,url):MUSEUMS[slug]=dict(slug=slug,name=name,city=city,country_code=cc,website_url=url);return slug
def dated(f,a,z,display,precision='range'):
    f.update(start=a,end=z,date_display=display,precision=precision,image_eligible=bool(f.get('image_url')or f.get('pdf_xref'))and z is not None and z<=1955);return f
def plate(f,key,page,xref):
    rc=m.h.load(m.RUN/'publications'/(key+'.json'));doc=pymupdf.open(rc['original_path']);assert xref in[x['xref']for x in doc[page].get_image_info(xrefs=True)]
    f.update(pdf_path=rc['original_path'],pdf_page_index=page,pdf_xref=xref,publication_receipt=rc,image_eligible=f['end']is not None and f['end']<=1955,image_url=rc['url']+'#page='+str(page+1),view_label='Complete embedded catalogue reproduction; source framing and margins retained; no cropping')
    return f
def pella():
    url='https://www.palaceofpella.gr/archaeological-museum-of-pella/?lang=en';mu=museum('gr-archaeological-museum-pella','Archaeological Museum of Pella','Pella','GR',url);s,p=soup(url);out=[]
    selected={
      '6355':('Eros and Psyche',-100,-1,'1st century BCE','sculpture','Terracotta'),
      '6356':('Female figurine from the Eastern Cemetery (source object 68)',-300,-101,'3rd–2nd century BCE','sculpture','Terracotta'),
      '6358':('Female figurine from the Eastern Cemetery (source object 70)',-300,-101,'3rd–2nd century BCE','sculpture','Terracotta'),
      '6362':('Attic red-figure hydria',-500,-301,'Late 5th–early 4th century BCE','ceramic','Painted ceramic'),
      '6364':('Doric capital from the Palace of Pella',-350,-350,'About 350 BCE','sculpture',None),
      '6365':('Marble head of Alexander the Great',-400,-301,'Late 4th century BCE','sculpture','Marble'),
      '6366':('Lion-hunt mosaic from the House of Dionysos',-400,-301,'Late 4th century BCE','mosaic',None),
      '6367':('Painted wall from the House of the Plasters',-300,-201,'Early 3rd century BCE','fresco',None),
      '6368':('Sleeping Eros',-325,-300,'325–300 BCE','sculpture',None),
      '6369':('Mould for a relief skyphos with the Sack of Troy',-100,-1,'1st century BCE','ceramic',None),
    }
    for a in s.select('a.fg-thumb'):
        rid=a['data-attachment-id']
        if rid not in selected:continue
        t,y,z,dt,k,med=selected[rid];f=fact('pella/'+rid,mu,t,None,'',url,rid,a['href'],medium=med,source_receipt=p['receipt'],original_caption=a['data-caption-desc']);dated(f,y,z,dt,'circa'if y==z else'range');f['work_type']=k
        if rid=='6367':f['view_label']='Museum reconstruction incorporating painted wall decoration; complete source photograph'
        out.append(f)
    return out
def piraeus():
    rc=m.h.load(m.RUN/'publications/piraeus.json');url=rc['url'];mu=museum('gr-archaeological-museum-piraeus','Archaeological Museum of Piraeus','Piraeus','GR','https://www.thisisathens.org/museums/piraeus-archaeological-museum');pages=m.h.load(m.RUN/'publications/piraeus-pages.json');doc=pymupdf.open(rc['original_path']);out=[]
    selected=[
     (117,'Red-figure lekythos depicting Apollo with a lyre and phiale',-460,-460,'Circa 460 BCE','ceramic','Painted ceramic',None),
     (129,'Loutrophoros with Paris and Helen',-420,-410,'420–410 BCE','ceramic','Painted ceramic','In the style of the Meidias Painter'),
     (188,'Large bronze Artemis of Piraeus',-400,-301,'4th century BCE','sculpture','Bronze',None),
     (200,'Small bronze Artemis of Piraeus',-400,-201,'4th–early 3rd century BCE; catalogue discussion qualifies the plate caption','sculpture','Bronze',None),
     (210,'Piraeus Athena',-400,-301,'4th century BCE','sculpture','Bronze',None),
     (235,'Cult statue of Cybele, Mother of the Gods',-400,-301,'4th century BCE','sculpture',None,'After Agorakritus (classical copy)'),
     (319,'Funerary stele of Artemisia',-400,-301,'Early 4th century BCE','sculpture',None,None),
     (331,'Funerary stele of a young athlete with his tutor',-400,-351,'First half of the 4th century BCE','sculpture',None,None),
     (379,'Archaistic Artemis Phosphoros',-200,-101,'2nd century BCE','sculpture',None,None),
     (397,'Portrait of an unknown man',201,300,'Circa mid-3rd century CE','sculpture',None,None),
    ]
    for i,t,a,z,dt,k,med,cr in selected:
        xrefs=doc[i].get_image_info(xrefs=True);assert len(xrefs)==1
        f=fact('piraeus/catalogue-page-'+str(i+1),mu,t,cr,'',url,'plate-page-'+str(i+1),medium=med,original_caption=pages[i]['text'],rights_label='Hellenic Ministry of Culture copyright in photographs; Archaeological Receipts Fund royalties stated in the publication',creator_credit='Hellenic Ministry of Culture / Archaeological Museum of Piraeus')
        dated(f,a,z,dt,'circa'if a==z else'range');plate(f,'piraeus',i,xrefs[0]['xref']);f['work_type']=k;f['locator']='George Steinhauer, The Archaeological Museum of Piraeus (2001), PDF page '+str(i+1)
        if i in[188,200,210]:f['additional_date_evidence']={str(j+1):pages[j]['text']for j in[169,170,171,187,199,209]}
        out.append(f)
    return out
def profane():
    url=m.h.load(m.RUN/'publications/mk-profane.json')['url'];ng=museum('mk-national-gallery','National Gallery of North Macedonia','Skopje','MK','https://nationalgallery.mk/');pr=museum('mk-institute-museum-prilep','Institute and Museum, Prilep','Prilep','MK','https://muzejprilep.org.mk/');sk=museum('mk-city-museum-skopje','Museum of the City of Skopje','Skopje','MK','https://mgs.org.mk/');ve=museum('mk-national-museum-veles','National Museum, Veles','Veles','MK',url);ku=museum('mk-museum-kumanovo','Museum of Kumanovo','Kumanovo','MK',url);te=museum('mk-icon-gallery-tetovo','Icon Gallery, Church of Saints Cyril and Methodius, Tetovo','Tetovo','MK',url);st=museum('mk-icon-gallery-novo-selo-stip','Icon Gallery, Dormition Cathedral, Novo Selo, Štip','Štip','MK',url)
    out=[];held=[];plate_map={1:(9,49),2:(4,41),7:(14,66),66:(25,101),74:(18,79),78:(16,74),79:(27,108)}
    for r in m.h.load(m.RUN/'mk-profane-entries.json'):
        n=r['number'];owner=' '.join(r['owner_tail'].split());raw=r['text']
        if n==73:held.append(dict(number=n,reason='Conflicting owner: opening plate says Municipality Veles, catalogue says Novo Selo icon gallery.'));continue
        mu=ng if owner.startswith('Национална галерија')else pr if n==2 else sk if owner.startswith('Музеј на град Скопје')else ve if n==19 else ku if n>=80 else te if n==23 else st if n==1 else None
        if not mu:continue
        cr='Theodosy Zograph'if n==1 else'Dimitrija Krstevic (Dicho Zograph)'if n==2 else'Dimitar Andonov Papradishki'if n<=54 else'Gjorgji Zografski'if n<=72 else'Gjorgji Andonov'if n==74 else'Kosta Shkodreanu'if n in[77,78]else'Trajko Muftinski'
        head=re.split(r'\n(?=[A-Za-z])',raw,1)[0].replace('\n',' ').strip()
        if n==66:head='Portrait of His Wife Sava, 1938'
        ma=re.search(r',\s*((?:околу |пред )?\d{4}(?:[/-]\d{1,4})?(?: \(\d{4}\))?)$',head)
        assert ma,(n,head)
        title=head[:ma.start()];dt=ma[1].replace('пред ','before ');med=re.search(r'(масло|темпера|пастел)[\s\S]*?(?=\n[сС]опственост)',raw);med=' '.join(med[0].split())if med else None
        f=fact('mk-profane/'+str(n),mu,title,cr,dt,url,'catalogue-'+str(n),medium=med,original_caption=raw,ownership_evidence=owner,rights_label='National Gallery of Macedonia catalogue; photographs credited to Igor Vasilev and Gjorgji Trichovski; no open reuse licence stated',creator_credit='Igor Vasilev and Gjorgji Trichovski (catalogue photography credit)')
        f['locator']='Macedonian Profane Painting (2013), catalogue no. '+str(n)
        if n==1:dated(f,1813,1828,'1813 (1828), catalogue alternative dating');f['date_evidence_note']='Year bounds enclose the two supplied dates; they do not assert continuous execution.'
        if n in[13,35]:f.update(start=None,end=None,precision='unknown',date_display='Conflicting catalogue date; see source evidence',date_evidence_note='Macedonian and translated date captions disagree; no normalized creation year assigned.')
        if n in plate_map:plate(f,'mk-profane',*plate_map[n])
        out.append(f)
    return out,held
def africa():
    rc=m.h.load(m.RUN/'publications/mk-africa.json');url=rc['url'];oh=museum('mk-institute-museum-ohrid','Institute and Museum, Ohrid','Ohrid','MK','https://muzejohrid.mk/');sk=MUSEUMS['mk-city-museum-skopje']['slug'];st=museum('mk-national-institution-stobi','National Institution Stobi','Gradsko','MK','https://stobi.mk/');out=[]
    specs=[(oh,'Earrings with African head terminals from Gorna Porta',-300,-201,'3rd century BCE',43,132,'Gold and dark stone or glass components; exact inset material not specified for this pair','jewelry','Printed pages 116–117, fig. 2; colour plate identifies Institute and Museum Ohrid as owner'),(sk,'Lamp with Serapis from Scupi, grave 1053',151,300,'Second half of 2nd–early 3rd century CE',62,305,'Ceramic','ceramic','Printed pages 122–123, fig. 1; Museum of the City of Skopje'),(sk,'Lamp with Serapis and Isis from Scupi, grave 3584',151,300,'Second half of 2nd–early 3rd century CE',62,304,'Ceramic','ceramic','Printed pages 122–123, fig. 2; Museum of the City of Skopje'),(st,'Votive relief dedicated to Isis and Serapis as theoi epekooi',101,200,'2nd century CE',67,212,None,'sculpture','Printed page 132, fig. 2; explicit National Institution Stobi ownership')]
    pages=m.h.load(m.RUN/'publications/mk-africa-pages.json')
    for mu,t,a,z,dt,i,xref,med,k,loc in specs:
        f=fact('mk-africa/'+str(xref),mu,t,None,'',url,'xref-'+str(xref),medium=med,original_caption=pages[59 if xref==132 else i]['text']);dated(f,a,z,dt);plate(f,'mk-africa',i,xref);f.update(work_type=k,locator=loc);out.append(f)
    return out
if __name__=='__main__':
    facts=pella()+piraeus();pr,held=profane();facts+=pr+africa()
    m.h.save(m.RUN/'selection-wave2-draft.json',dict(at=m.h.now(),records=facts,held=held,museums=list(MUSEUMS.values())))
    print(len(facts),sum(f['image_eligible']for f in facts),collections.Counter(f['museum_slug']for f in facts))
