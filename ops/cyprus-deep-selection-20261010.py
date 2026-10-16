"""Reviewed selection of Cyprus museum objects and exact source reproductions."""
import importlib.util,json,re,gzip,collections
from urllib.parse import urljoin
from bs4 import BeautifulSoup
s=importlib.util.spec_from_file_location('cyprus','ops/cyprus-deep-20261010.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
b=m.h.load(m.RUN/'baseline.json.gz');works={a['id']:a for a in b['artworks']};museums={r['id']:r for r in b['museums']};out=[];held=[]
def existing(a,image,url,locator='',view='Complete supplied object photograph',**extra):
    if a['primary_media_id']:return
    cs=[c for c in b['citations']if c['entity_id']==a['id']]
    out.append(dict(key='existing:'+a['id'],existing_id=a['id'],museum_slug=museums[a['current_institution_id']]['slug'],title=a['title'],start=a['creation_year_start'],end=a['creation_year_end'],precision=a['date_precision'],date_display=a['date_display'],accession=a['accession_number'],creator=a['unlinked_creator_label'],work_type=a['work_type'],medium=a['medium_text'],dimensions=a['dimensions_text'],source_url=url,source_record_id=cs[0]['source_record_id']if cs else a['id'],locator=locator,image_url=image,view_label=view,image_eligible=True,**extra))
def tour(name,index,slug,start,end=None,precision=None,display=None,title=None,creator=None,typ='decorative_art',image=True):
    r=m.h.load(m.RUN/'tours'/(name+'.json'))['records'][index];end=start if end is None else end
    imgs=[x for x in r['image_urls']if re.search(r'\.(?:jpg|jpeg|png|webp)(?:\?|$)',x,re.I)]
    f=dict(key='tour:'+name+':'+r['action'],museum_slug=slug,title=title or r['title'],start=start,end=end,precision=precision or('unknown'if start is None else'exact'if start==end else'range'),date_display=display or('Creation date unknown'if start is None else str(start)if start==end else f'{start}–{end}'),accession=None,creator=creator,work_type=typ,medium=None,dimensions=None,source_url=r['source_url'],source_record_id=r['action'],locator='Officially linked virtual tour, '+r['action'],source_receipt=r['receipt'],description=r['description'],image_url=imgs[0]if image and imgs else None,image_eligible=image and end is not None and end<=1955,view_label='Complete supplied object photograph',identity_basis='Unique captioned tour hotspot and linked object photograph; repeated hotspots deduplicated. Museum collection context, not current display.',date_evidence='Literal object caption; historical events, acquisition dates and creator lifetimes not substituted for creation. '+('Conventional early/late-century interval retains qualifier; not an exact-year claim.'if precision=='circa_range'else''))
    assert f['title'];out.append(f);return f

# Pierides: individually identified craft/art objects; duplicate tour hotspots excluded.
P='cyprus-pierides-museum-bank-of-cyprus-cultural-foundation';seen=set()
for i,r in enumerate(m.h.load(m.RUN/'tours/PieridesMuseum.json')['records']):
    key=(r['title'],tuple(r['image_urls']))
    if key in seen:held.append(dict(source='PieridesMuseum',index=i,reason='Duplicate tour view of same object'));continue
    seen.add(key)
    if i==12:held.append(dict(source='PieridesMuseum',index=i,reason='Likely existing AR 30 Hathoric amphoriskos; title/period discrepancy needs cross-source comparison.'));continue
    text=r['description'];date=re.search(r'(\d+)\s*B\.?C\.?\s*-\s*(\d+)\s*A\.?D',text,re.I)
    if date:start,end=-int(date[1]),int(date[2]);display=f'{date[1]} BC–{date[2]} AD'
    else:
        date=re.search(r'(\d{2,4})\s*-\s*(\d{2,4})\s*(B\.?C\.?|A\.?D\.?)',text,re.I)
        if not date:held.append(dict(source='PieridesMuseum',index=i,reason='No unambiguous object creation interval'));continue
        start,end=int(date[1]),int(date[2]);display=date[0]
        if date[3].upper().startswith('B'):start,end=-start,-end
    title={37:'Sgraffito bowl with a falconer',38:'Sgraffito bowl with an embracing couple',39:'Bowl with a lion and coat of arms',21:'Black-figure vessel with Theseus and the Minotaur'}.get(i)
    tour('PieridesMuseum',i,P,start,end,display=display,title=title,typ='sculpture'if any(z in r['title'].lower()for z in ['figure','idol','mask'])else'decorative_art')

L='cyprus-agios-lazaros-byzantine-museum'
for i,a,z,disp,typ in [(0,1730,1730,'1730','decorative_art'),(2,1780,1780,'1780','decorative_art'),(3,1801,1900,'19th century','decorative_art'),(8,1501,1600,'16th century','painting'),(9,1501,1700,'16th–17th century','painting'),(13,1760,1760,'1760','decorative_art'),(15,1701,1800,'18th century','painting'),(16,1501,1600,'16th century','sculpture'),(17,1879,1879,'1879','print'),(18,1501,1600,'16th century','painting'),(19,1694,1694,'1694','painting'),(20,1501,1600,'16th century','painting')]:
    tour('Byzantine_Museum',i,L,a,z,display=disp,typ=typ,creator='Tzafouriaris'if i==9 else None)
K='cyprus-kallinikeio-municipal-museum-of-athienou'
tour('KallinikeioMuseum',3,K,-750,-480,display='Cypro-Archaic period (750–480 BC)',title='Bird-shaped clay bell (child’s toy)',typ='decorative_art')
tour('KallinikeioMuseum',9,K,1915,display='1915',title='Saint Nicholas',creator='Ioannikios Mavropoulos',typ='painting',image=False)
tour('Bee_Embroidery_Museum',10,'cyprus-kato-drys-bee-embroidery-museum',1870,precision='circa',display='c. 1870',title='Pittoti Venis lace handbag',creator='Chrystallou, daughter of Makroelia Tsamilli')
F='cyprus-local-museum-traditional-embroidery-and-silversmith-work-lefkara'
for i,a,z,disp,title,creator in [(2,1878,1878,'1878','Pithari (large clay storage vessel)',None),(8,1867,1900,'Late 19th century','Moskilios (embroidered bed valance)',None),(9,1867,1933,'Late 19th–early 20th century','Carved wooden four-poster bed',None),(11,1867,1933,'Late 19th–early 20th century','Filigree cross pendant with blue and coral stones',None),(12,1867,1933,'Late 19th–early 20th century','Skaletta (filigree necklace)',None),(16,1901,1933,'Early 20th century','Silkworm cocoon embroidery with flowers and bows',None),(17,1907,1907,'1907','Dawn and the Chariot of the Sun','Kallou Themistokli Patsalou'),(19,1913,1913,'1913','Embroidered flowers on silk','Chrystalla Petri'),(20,1901,1933,'Early 20th century','Linen curtain with Lefkara lace',None),(21,1901,1933,'Early 20th century','Tornarettos (silk bed valance)',None),(22,1867,1933,'Late 19th–early 20th century','Poukamisa with red and black embroidery',None),(23,1901,1933,'Early 20th century','Foustani (urban dress)',None),(25,None,1898,'By 1898; worn at Markarou Veouka-Karkidi’s wedding','Silk bridal outfit',None),(26,1901,1933,'Early 20th century','Silver censer with cherubs',None),(27,1901,1933,'Early 20th century','Kapnistomerrecho (silver ritual set)',None),(28,1901,1933,'Early 20th century','Wedding wreaths in a wooden case',None)]:
    tour('Lefkara_Museum',i,F,a,z,precision='before'if a is None else'exact'if a==z else'circa_range',display=disp,title=title,creator=creator)
R='cyprus-local-agricultural-museum-kato-drys'
for i,a,z,disp,title in [(0,1901,1933,'Early 20th century','Silkworm cocoon tapestry with a couple’s photograph'),(1,1867,1900,'Late 19th century','Sentouki (chest with incised decoration)'),(17,1901,1933,'Early 20th century','Stefana (wax orange-blossom wedding wreaths)'),(18,1901,1933,'Early 20th century','Canopied wrought-iron marital bed')]:tour('Local-Rural-Museum-Kato-Drys',i,R,a,z,precision='circa_range',display=disp,title=title)

# Direct native images for existing records, preserving all catalogue metadata.
for a in works.values():
    cs=[c for c in b['citations']if c['entity_id']==a['id']]
    for c in cs:
        u=c['source_url']
        if 'boccf.org'not in u:continue
        p=m.page(u);soup=BeautifulSoup(gzip.decompress((m.ROOT/p['receipt']['body_path']).read_bytes()),'html.parser')
        for block in soup.select('.zig-zag-item'):
            text=block.get_text(' ',strip=True);fig=block.select_one('figure[data-desktop-img]')
            if not fig:continue
            num=re.search(r'Exhibition Number: (?:Case )?([0-9/]+)',text)
            match=bool(a['accession_number']and text.startswith(a['accession_number']))or bool(num and (c['source_record_id']or'').endswith(num[1]))
            if match:existing(a,urljoin(u,fig['data-desktop-img']),u,locator=text,source_receipt=p['receipt'])
for suffix in ['065','449']:
    u=f'http://www.makariosfoundation.org.cy/bmen{suffix}.html';p=m.page(u);a=next(works[c['entity_id']]for c in b['citations']if c['source_url']==u);img=next(x['url']for x in p['images']if '/images/img/'in x['url']);existing(a,img,u,source_receipt=p['receipt'],view='Virgin Eleousa side of the bilateral icon'if suffix=='449'else'Complete supplied object photograph')
for aid,num,url in [('001ad345-d985-536b-aa2b-dcdec1bc9834',18,'https://kykkos.org.cy/kykkos-museum.cy.net/room2/eg-page1.html'),('014f3fc5-c897-5412-bb91-74ebd2775c7f',53,'https://kykkos.org.cy/kykkos-museum.cy.net/room3/eg-page1.html')]:
    p=m.page(url);img=next(x['url']for x in p['images']if f'eik-{num}.'in x['url']);existing(works[aid],img,url,locator=f'Picture {num}',source_receipt=p['receipt'])
p=m.page('https://leventismuseum.org.cy/medieval-ceramics/')
for acc,num in [('Β/1996/1421',1),('B/2003/0,21',2),('Β/2003/0,225',3),('Β/2003/0,70',4)]:
    candidates=[a for a in works.values()if (a['accession_number']or'').replace('Β','B')==acc.replace('Β','B')and museums[a['current_institution_id']]['slug']=='leventis-municipal-museum-nicosia'];assert len(candidates)==1
    existing(candidates[0],next(x['url']for x in p['images']if f'0{num}-Medieval'in x['url']),p['url'],locator='Object '+acc,source_receipt=p['receipt'])
p=m.page('https://www.cypriotstudies.org/ekthema%20mina.html');existing(works['c452900a-f56f-5c49-9c2e-12cb6451b3eb'],next(x['url']for x in p['images']if '/41%20'in x['url']),p['url'],locator='March 2015 exhibit; inventory Α.Μ. 41, dated 1902',source_receipt=p['receipt'])
for i in [2,4,12,18,20]:
    r=m.h.load(m.RUN/'tours/Christian_Art_Museum.json')['records'][i];title='Angels of Passion (The Deposition)'if i==2 else r['title'];matches=[a for a in works.values()if m.h.norm(a['title'])==m.h.norm(title)and museums[a['current_institution_id']]['slug']=='cyprus-museum-christian-art-christoforou-collection'];assert len(matches)==1,(r['title'],matches)
    existing(matches[0],r['image_urls'][0],r['source_url'],locator=r['action'],source_receipt=r['receipt'])

# Whole catalogue plates: preserve the complete source frame and identify the exact object.
pdf=m.h.load(m.ROOT/'docs/research/nicosia-museums-20261007/catalogue-pdf.json')
locations={0:'no. 132, lower left (front and back)',3:'no. 184, upper right',5:'no. 210, lower left',6:'no. 78, middle left',8:'no. 229, lower portion (relief and inscription)',9:'no. 64, lower left',12:'no. 288, lower right'}
for i,label in locations.items():
    r=m.h.load(m.RUN/'pdf-image-leads.json')[i];a=works[r['artwork_id']]
    existing(a,None,r['source_url'],locator=r['locator'],view='Complete catalogue plate; this object is '+label+'. Other numbered objects are also illustrated.',pdf_page_index=r['pdf_page_index'],pdf_xref=r['images'][0]['xref'],source_receipt=pdf)

for f in out:
    if f['work_type']=='decorative_art':
        # Use supported forms; furniture stays unknown rather than inventing a form.
        title=f['title'].lower()
        f['work_type']='textile'if any(t in title for t in ['embroider','lace','silk','curtain','valance','poukamisa','foustani','tapestry','handbag','antimension','epitrachelion'])else'metalwork'if any(t in title for t in ['silver','filigree','chalice'])else'ceramic'if any(t in title for t in ['vessel','bowl','jug','pyxis','askos','amphora','clay','pithari'])else'unknown'
assert len({x['key']for x in out})==len(out)
m.h.save(m.RUN/'selection-wave1.json',dict(at=m.h.now(),records=out,held=held,policy='Cyprus museum/artist source extension; selected authentic images through 1955, metadata through 1970; direct user instruction 10 October 2026. New objects in review. No current display claim.'))
print('SELECTED',len(out),'new',sum('existing_id'not in x for x in out),'existing images',sum('existing_id'in x for x in out),'museums',len({x['museum_slug']for x in out}))
