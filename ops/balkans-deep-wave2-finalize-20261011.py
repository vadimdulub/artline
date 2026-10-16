import runpy,pymupdf,re,collections
b=runpy.run_path('ops/balkans-deep-wave2-facts-20261011.py');m=b['m'];h=m.h;RUN=m.RUN;fact=b['fact'];dated=b['dated'];plate=b['plate'];d=h.load(RUN/'selection-wave2-draft.json');fs=d['records'];mus={x['slug']:x for x in d['museums']};held=d['held']
def museum(k,n,c,cc,u):mus[k]=dict(slug=k,name=n,city=c,country_code=cc,website_url=u);return k
# Correct plate identity after rendered page comparison; preserve draft for the audit trail.
for f in fs:
 if f['key']=='mk-africa/212':
  f.update(key='mk-africa/309',source_record_id='xref-309');plate(f,'mk-africa',67,309)
 if f['key']=='piraeus/catalogue-page-201':
  doc=pymupdf.open(f['pdf_path']);plate(f,'piraeus',202,doc[202].get_image_info(xrefs=True)[0]['xref']);f['locator']+='; complete statue photograph on PDF page 203'
 if f['key']=='piraeus/catalogue-page-211':
  doc=pymupdf.open(f['pdf_path']);plate(f,'piraeus',212,doc[212].get_image_info(xrefs=True)[0]['xref']);f['locator']+='; complete statue photograph on PDF page 213'
# Unverified homepage guesses are replaced with the documented holding catalogue.
for key in ['mk-institute-museum-prilep','mk-city-museum-skopje','mk-national-institution-stobi']:
 mus[key]['website_url']=next(f['source_url']for f in fs if f['museum_slug']==key)
rc=h.load(RUN/'publications/eleusis.json');url=rc['url'];pages=h.load(RUN/'publications/eleusis-pages.json');mu=museum('gr-archaeological-museum-eleusis','Archaeological Museum of Eleusis','Eleusis','GR',url)
for i,xref,t,a,z,dt,cr,ev in [(120,761,'Caryatid from the Lesser Propylaea',-100,-1,'1st century BCE',None,[118,120]),(209,1344,'The Fleeing Maiden',-480,-480,'Circa 480 BCE',None,[205,212]),(213,1369,'Winged Nike torso',-480,-480,'Circa 480 BCE','Possibly Eleusinian workshop',[213]),(216,1389,'Eleusis Demeter',-420,-410,'Circa 420–410 BCE','Attributed to the workshop of Agorakritos',[213,214,216]),(217,1396,'Female torso wearing a peplos (Demeter?)',-420,-410,'Circa 420–410 BCE',None,[214,217]),(222,1430,'Votive relief with Demeter and Kore',-500,-401,'5th century BCE; precise dating disputed',None,[221,222])]:
 f=fact('eleusis/catalogue-'+str(i+1),mu,t,cr,'',url,'pdf-page-'+str(i+1),medium='Marble',original_caption={str(j+1):pages[j]['text']for j in ev},creator_credit='Hellenic Ministry of Culture / Archaeological Museum of Eleusis',rights_label='Hellenic Ministry of Culture copyright in photographs; Archaeological Receipts Fund royalties stated in the publication');dated(f,a,z,dt,'circa'if a==z else'circa_range'if'Circa'in dt else'range');plate(f,'eleusis',i,xref);f.update(work_type='sculpture',locator='Eleusis catalogue, PDF page '+str(i+1),view_label='Complete catalogue plate, including original caption/text where present; no cropping');fs.append(f)
mu=museum('bg-national-archaeological-museum','National Archaeological Museum – NAIM-BAS','Sofia','BG','https://naim.bg/')
for i,t,a,z,dt,med,acc in [(66,'Altar dedicated to Apollo Kendrisos',101,150,'First half of the 2nd century CE','Marble','2617'),(65,'Bronze statuette of Zeus from Priboy',-100,-1,'1st century BCE','Bronze with silver and copper inlays','7844'),(64,'Stone slab with a lion from Stara Zagora',801,1200,'9th–12th century; dating debated','Reddish slate',None)]:
 u='https://naim.bg/en/content/exhibits/'+str(i)+'/';p=m.page(u);im=next(x['url']for x in p['images']if'imagesExhibits'in x['url']);f=fact('naim/exhibit-'+str(i),mu,t,None,'',u,str(i),im,medium=med,accession=acc,source_receipt=p['receipt'],original_caption=p['text']);dated(f,a,z,dt);f['work_type']='sculpture'
 if i==65:f['creator_credit']='Chavdar Chomakov (photograph)';f['rights_label']='NAIM-BAS; photograph by Chavdar Chomakov; no open reuse licence stated'
 fs.append(f)
held.append(dict(source='NAIM-BAS monthly exhibits 60–63',reason='Temporary exhibition alone does not establish the collection owner; holdings not assigned.'))
mu=museum('bg-stara-zagora-art-gallery','Stara Zagora Art Gallery','Stara Zagora','BG','https://artgallerystz.com/');u='https://artgallerystz.com/events/в-царството-на-змея-от-никола-кожух/';p=m.page(u);im='https://artgallerystz.com/wp-content/uploads/2026/08/769309273_1677937820370637_1760675072905315972_n1.jpg';f=fact('stz/dragon-1921',mu,'In the Realm of the Dragon','Nikola Kozhuharov','1921',u,'dragon-1921',im,source_receipt=p['receipt'],original_caption=p['text']);f['view_label']='Source detail of a figure from the painting; the museum supplied this detail, not a complete composition';fs.append(f)
# Resolve false-positive common-title matches against recorded linked creators.
p=h.load(m.BACKUP/'wave1-plan.json.gz');ids=h.load(RUN/'identity-authority-scope.json.gz');exclude={'Portrait of Amalia Gavrilova','Vase with Flowers','Girl in Oriental Costume','Young Woman','Ahinora'}
for row in p['held']:
 f=dict(row['fact'])
 if f['title']in exclude:continue
 f['identity_exclusions']=row['ids'];f['identity_review']='All recorded same-title/year candidates have explicitly different creators; original source creator retained.';fs.append(f)
 for mu1 in h.load(RUN/'selection-wave1.json')['museums']:
  if mu1['slug']==f['museum_slug']:mus[mu1['slug']]=mu1
h.save(RUN/'selection-wave2.json',dict(at=h.now(),records=fs,held=held,museums=list(mus.values()),user_authorization='Continuation of user-requested deep research and selected artwork-image delivery for Greece, Bulgaria and North Macedonia.'))
print(len(fs),sum(x['image_eligible']for x in fs),collections.Counter(x['museum_slug']for x in fs))
