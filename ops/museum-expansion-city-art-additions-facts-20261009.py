"""Selected City Art Centre collection objects, with explicit source and date boundaries."""
import gzip,hashlib,html,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-city-art-additions-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
U=(None,None,'unknown',None)
def exact(y):return(y,y,'exact',str(y))
def circa(y):return(y,y,'circa','c.'+str(y))
# Keys identify actual objects in collection articles, not complete exhibitions or bequests.
SELECTED=[
(1,'ramsay-hall','unmasked','Katherine Hall of Dunglass','Allan Ramsay',circa(1736),'painting',None,None,'Council collection portrait highlight; circa date retained.'),
(2,'cadenhead-screen','unmasked','Lady with Japanese Screen and Goldfish','James Cadenhead',exact(1886),'painting','Oil on canvas',None,'Council creation date; curator newsletter page15 supplies oil on canvas and title alias Portrait of the Artist’s Mother.'),
(3,'cadell-black-hat','unmasked','The Black Hat','Francis Campbell Boileau Cadell',exact(1914),'painting',None,None,'Council FCB Cadell and curator newsletter full maker name agree; page14 portrait beside fireplace.'),
(4,'king-fraunchyse','gifted','Fraunchyse','Jessie M. King',circa(1907),'drawing',None,None,'Art Nouveau drawing newly acquired; acquisition/exhibition2026 is not creation.'),
(5,'bough-windsor','longwalk','The Long Walk, Windsor','Sam Bough',U,'watercolor','Watercolour on paper','24 x 34 cm','ArtFund1989 Robinson bequest identifies one watercolour, not all75 distributed works. Creation date absent.'),
(6,'mctaggart-shelter','summer2014','Running for Shelter','William McTaggart',exact(1887),'painting',None,None,'Curator Helen Scott page14 gives explicit title, date and City Art Centre credit; children crouching on rocky shoreline.'),
(7,'macgregor-melrose','summer2022','Melrose','William York MacGregor',circa(1919),'painting',None,None,'Curator Helen Scott page12 caption identifies landscape and City collection; not acquisition1964.'),
(8,'miller-canal','summer2022','The House on the Canal','Josephine Haswell Miller',circa(1935),'painting',None,None,'Curator page13 caption: house, bare trees and canal reflections. Artist copyright retained in source evidence.'),
(9,'peploe-still-life','summer2022','Still Life','S.J. Peploe',(1905,1906,'circa_range','c.1905–1906'),'painting',None,None,'Curator page13: pink and white flowers in blue/white vase at right, fruit on plate at left, dark background. Generic title requires physical-version review; current museum filename1905 not preferred over caption range.'),
(10,'duncan-aoife','talbot','Aoife','John Duncan',U,'painting','Oil on canvas',None,'University gallery2014 lender list item1 explicitly City Art Centre. No date given; no lifespan inference.'),
(11,'duncan-excalibur','talbot','The Taking of Excalibur','John Duncan',U,'painting','Oil on canvas',None,'University gallery2014 lender list item3 explicitly City Art Centre; distinct from other Duncan/Arthurian works.'),
(12,'duncan-tristan','talbot','Tristan and Iseult','John Duncan',exact(1912),'painting','Tempera on canvas',None,'University gallery2014 lender list item4 City Art Centre. Lovers about to drink potion; title variant Tristan and Isolde considered.'),
(13,'robertson-fox','winter2014','Portrait of George Romney Fox','Eric Robertson',exact(1917),'drawing',None,None,'Newsletter page8 exhibition explicitly drawn from City collection; fellow ambulance volunteer portrait. Article byline unspecified, not claimed as curator-authored.'),
(14,'robertson-shellburst','winter2014','Shellburst','Eric Robertson',circa(1919),'painting',None,None,'Newsletter page8 caption explicitly City Art Centre credit; angular wartime abstraction. Article byline unspecified.'),
(15,'cameron-garment','winter2014','A Garment of War','D.Y. Cameron',U,'painting',None,None,'Newsletter page8 collection exhibition; no creation date. External discovery leads disagree c1926/c1936; neither adopted. Autumn1917 is battlefield visit, not creation.'),
(16,'lewis-mitchison','mitchison','Portrait of Naomi Mitchison','Wyndham Lewis',(1930,1932,'range','1930–1932'),'drawing','Pencil & wash on paper','46 x 36 cm','ArtFund acquisition2000; alternative title The Tragic Muse. Seated woman with scalloped sleeves, gold waist brooch, tight coiled hair.'),
(17,'fergusson-blue-hat','watson','The Blue Hat, Closerie des Lilas','JD Fergusson',U,'painting',None,None,'Current native collection highlight. Exact1909 creation requires retained supplementary exhibition credit, not inferred from 1962 purchase.'),
(18,'paolozzi-horse','chaos','Horse’s Head','Eduardo Paolozzi',U,'sculpture','Bronze',None,'Exact City bronze cast creation/version unresolved;1946 original concrete model is not proof of this cast date.'),
(19,'pow-angels','chaos','Fallen Angels','Tom Pow',U,'painting',None,None,'Native identifies rare surviving painting but1945–2000 exhibition crosses cutoff; require specific creation evidence.'),
(20,'robb-house','chaos','Cool House','Alan Robb',U,'painting','Oil',None,'Native collection recent acquisition, exact creation unknown. Exhibition1945–2000 cannot establish pre1971.'),
(21,'blackadder-irises','watson','Irises','Elizabeth Blackadder',U,'watercolor','Watercolour',None,'Native identifies specific watercolour, but independent exhibition lead1982 suggests postcutoff. Retain research hold, no eligible year invented.')]
def sources():
 out={};mapping={'/14283/':'unmasked','/14491/':'gifted','/14201/':'chaos','the-long-walk-windsor':'longwalk','portrait-of-naomi-mitchison':'mitchison','new-exhibition-explores-story':'watson','pallantbookshop.com/artist/':'pallant'}
 for fn in ['native-discovery-001.json.gz','selected-documents-001.json.gz','supplements-001.json.gz','supplements-002.json.gz']:
  for v in m.load(RUN/fn)['rows']:
   if 'capture' not in v:continue
   cap=v['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'];key=v.get('key') or next((key for part,key in mapping.items() if part in v['url']),None)
   if key:assert key not in out;out[key]=dict(capture=cap,reference=ref(RUN/fn),data=v.get('parsed',{'text':v.get('text','')}))
 return out
def rows():
 srcs=sources();out=[]
 for number,key,srcid,title,creator,date,wt,medium,dims,note in SELECTED:
  src=srcs[srcid];first,last,precision,display=date;issues=[];supp=[]
  if number==17 and 'pallant' in srcs:
   v=srcs['pallant'];assert all(t in v['data']['text'] for t in ['The Blue Hat, Closerie des Lilas, 1909','Oil on canvas','City Art Centre']);first=last=1909;precision='exact';display='1909';medium='Oil on canvas';creator='John Duncan Fergusson';supp.append(v)
  if number in [2,3]:supp.append(srcs['summer2014'])
  if first is None:assert last is None and precision=='unknown';issues.append('unknown_creation_date_requires_review')
  else:assert 100<=first<=last<=1970
  text=src['data']['text']
  if srcid in ['summer2014','summer2022','winter2014']:
   pages={'summer2014':[14,15],'summer2022':[12,13],'winter2014':[7,8]}[srcid];text='\n'.join(text.split('\f')[pg-1] for pg in pages)
  url=src['capture']['receipt']['url'];sid='city-art/'+key;titles=[title]
  if number==2:titles+=['Lady with Japanese Screen and Goldfish (Portrait of the Artist’s Mother)','Portrait of the Artist’s Mother']
  if number==12:titles+=['Tristan and Isolde']
  if number==16:titles+=['The Tragic Muse']
  f=dict(source_id=sid,native_id=key,source_url=url,source_retrieved_url=url,title=title,titles=titles,creator_label=creator,identity_creator_labels=[creator],source_artist_fields=[creator],unidentified_creator=False,source_fields={'ATTRIBUZIONI':creator,'museum_narrative':text,'editorial_note':note,'supplementary_sources':supp},inventory=None,normalized_inventory=None,alternative_inventories=[],date_display=display,first=first,last=last,date_precision=precision,work_type=wt,object_form=None,medium=medium,dimensions_text=dims,description=text,physical_object_count='1',native_page_urls=[url],native_metadata_urls=[url],artuk_url='',museum_qid=s.QID,issues=issues)
  out.append(dict(number=number,source_id=sid,institution_id=s.IID,facts=f,issues=issues,version_note=note,source_capture=src['capture'],source_record_reference=src['reference'],retrieved_at=src['capture']['receipt']['retrieved_at'],supplementary_source=supp))
 return out,[]
def main():
 rs,holds=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=rs,source_fact_holds=holds,parser_reference=ref(Path(__file__).resolve()),visual_review_reference=ref(RUN/'newsletter-visual-review-001.json'),policy='Exact individually identified collection objects only. Pending full identity review. Unnamed artists,exhibition totals,modern works and other lenders do not become quota additions.'))
 print(json.dumps(dict(candidates=len(rs),dated=sum(v['facts']['first'] is not None for v in rs))),flush=True)
if __name__=='__main__':main()
