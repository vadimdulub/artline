"""Selected Box collection facts; creation dates, acquisitions and loans separated."""
import gzip,hashlib,html,importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('s',Path(__file__).with_name('museum-expansion-box-continuation-common-20261009.py'));s=importlib.util.module_from_spec(z);z.loader.exec_module(s);m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
def clean(t):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',t))).strip()
U=(None,None,'unknown',None)
def exact(y):return (y,y,'exact',str(y))
# One candidate per physical work. Missing dates are not replaced with acquisition years.
NATIVE=[
(1810,'gore','Someone Who Waits','Spencer Gore',exact(1907),'Oil',None,'Acquired from artist widow1958;excerpt explicitly dates painting1907.'),
(1863,'hartley','Devon Lane, Westlake','Ben Hartley',exact(1968),None,None,'Caption explicitly dates1968;Turner Rain,Steam and Speed1844 is National Gallery partner work,not Box holding.'),
(1881,'forbes','A Fish Sale on a Cornish Beach','Stanhope Forbes',U,None,None,'Finished painting distinct from abandoned larger canvas and preparatory sketches;1885 exhibition is not silently converted to exact creation year.'),
(1888,'lang','The Bridges by Night','Douglas Walter Lang',exact(1965),'Oil',None,'Gifted1969;created1965,not bridge opening1961.'),
(1891,'danckerts','View of Plymouth','Attributed to Hendrick Danckerts',exact(1675),'Oil on canvas',None,'Qualified attribution explicit;native distinguishes another Plymouth view in Yale. Acquired1954.'),
(1894,'brill','A Byway in Plymouth','Reginald Brill',(1950,1959,'circa_range','believed to be 1950s'),'Oil',None,'Museum qualifies decade;acquired2007. View inland from West Hoe,not generic harbour.'),
(1897,'gibbons','Admiral’s Hard, Stonehouse','William Gibbons',U,None,None,'Narrative dates buildings,ferry and urban history;no exact painting creation year.'),
(1900,'pocock','East Indiaman Dutton Wrecked in Plymouth Sound','Nicholas Pocock',U,None,None,'1796 is depicted shipwreck;Pocock and Luny made several versions. Compare actual work identity.'),
(1903,'spencer','Hoe Garden Nursery','Stanley Spencer',(None,None,'unknown','commissioned 1955; creation date unconfirmed'),None,None,'Native title and body reverse Garden/Nursery;1955 is commission year,not independently stated completion.'),
(1909,'ginner','Plymouth Pier from the Hoe','Isaac Charles Ginner',exact(1923),'Oil on canvas','76.3 x 61.4 cm','Native acquisition1987 conflicts with ArtFund support1988;both retained as evidence,not creation conflict.'),
(1912,'olsson','Plymouth Sound by Moonlight and Searchlight','Julius Olsson',U,None,None,'Gift1909 not creation;moonlit pier scene needs version comparison.'),
(1915,'velde','Plymouth in 1666','Attributed to Willem van de Velde the Younger',(1670,1670,'circa','around 1670'),'Oil',None,'1666 is title/depicted year;source explicitly says around1670 and attributed. Acquired1898.'),
(1918,'williams','Royal William Victualling Yard','William Williams',(1836,1836,'circa','around 1836'),'Oil on canvas','71 x 92 cm','Native and funder identify same1994acquisition;not two artworks. Building1824–1835 is contextual.'),
(1921,'pickup','Teats Hill','Jack Pickup',U,None,None,'Specific collection painting looking toward Barbican;artist wartime service does not date work.'),
(1947,'nicholson','Fern Colour','Kate Nicholson',U,'Oil on canvas',None,'Purchased1958 and made after studio move;exact creation remains unresolved,not inferred from biography.'),
(1966,'maeckelberghe','Fishing Boat, St Ives','Margo Maeckelberghe',U,None,None,'Acquired1967;creation unknown. No creator-lifespan eligibility inference.'),
(2030,'bonfoy','Portrait of Lady Ann Bonfoy','Sir Joshua Reynolds',(1750,1759,'decade','1750s'),None,None,'Part of Box Port Eliot Collection acquired2007 via Acceptance in Lieu;remains in situ at Port Eliot. Do not claim physical presence or current display at The Box.'),
(2038,'barnsgraham','Card Table','Wilhelmina Barns-Graham',(1967,1969,'range','1967–1969'),'Oil on hardboard',None,'Gift1976 does not place work after cutoff;native explicitly dates1967–1969.'),
(2085,'hart','Lady Jane Grey at Her Place of Execution','Solomon Hart',exact(1839),None,None,'Large original gifted1879,moved museum1911,rolled storage;distinct from Delaroche execution painting. Conservation is not new version.'),
(2105,'imogen','Imogen','Elizabeth Adela Stanhope Forbes',exact(1898),'Oil on canvas',None,'Specific Shakespearean scene of sleeping Imogen,acquired1904.'),
(2142,'glanville','Portrait of Jacqueline Glanville','Winifred de Vany',U,None,None,'Bequeathed2022;date of painting unresolved,not artist lifespan1900–1990.'),
(2142,'cumming','Portrait of A A Cumming','Winifred de Vany',U,None,None,'Native explicitly identifies a second held portrait;curator service1937–1978 is not creation date.')]
FUNDER=[
('plymouth-harbour','Plymouth Harbour','Thomas Rowlandson',U,'watercolor','Watercolour',None,'Source date1756–1827 is artist lifespan;retain literal field as evidence only. Gift2006 from Lady Frances Ann Stevens.'),
('plymouth-from-mount-edgcumbe','Plymouth, from Mount Edgcumbe','Joseph Mallord William Turner',exact(1814),'watercolor','Watercolour over pencil heightened with scratching out and touches of gum arabic, on wove paper','15.6 x 24.1 cm','Watercolour for Southern Coast series,not derivative print;acquired2006.'),
('kilchurn-castle-and-loch-awe','Kilchurn Castle and Loch Awe','Joseph Mallord William Turner',U,'watercolor','Watercolour','51 x 78 cm','Source1775–1851 is artist lifespan,not creation range. One work from1955Cookbequest,not150bequestitems.'),
('large-anthropomorphic-crab','Large Anthropomorphic Crab','Robert Wallace Martin',exact(1880),'sculpture','Salt-glazed stoneware','21 x 48.5 cm','One-off sculpted human-faced crab acquired2020;other106Martinwarepieces are not individually identified or counted.'),
('the-drake-cup','The Drake Cup','Abraham Gessner',(1571,1571,'circa','c1571'),'unknown','Silver gilt','52 cm','Decorative globe cup. Funderdate requires corroboration;gift legends explicitly traditions,not confirmed provenance.')]
def sources():
 bs={};afs={}
 for fn in ['native-discovery-001.json.gz','supplements-001.json.gz']:
  for row in m.load(RUN/fn)['rows']:
   if 'capture' not in row:continue
   cap=row['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert cap['receipt']['status']==200 and hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256']
   if row['provider']=='box' and '/posts?' in row['url']:
    assert json.loads(raw)==row['data']
    for v in row['data']:assert v['id'] not in bs;bs[v['id']]=dict(data=v,capture=cap,reference=ref(RUN/fn))
   elif row['provider']=='artfund':afs[row['url'].rstrip('/').split('/')[-1]]=dict(data=row['parsed'],capture=cap,reference=ref(RUN/fn))
 return bs,afs
def row(number,sid,nativeid,url,creator,title,date,wt,medium,dimensions,note,src,text):
 first,last,precision,display=date;issues=[]
 if first is None:assert last is None and precision=='unknown';issues.append('unknown_creation_date_requires_review')
 else:assert 100<=first<=last<=1970
 if creator.startswith('Attributed'):issues.append('qualified_creator')
 f=dict(source_id=sid,native_id=nativeid,source_url=url,source_retrieved_url=src['capture']['receipt']['url'],title=title,titles=[title],creator_label=creator,identity_creator_labels=[creator],source_artist_fields=[creator],unidentified_creator=False,source_fields={'ATTRIBUZIONI':creator,'museum_narrative':text,'editorial_note':note},inventory=None,normalized_inventory=None,alternative_inventories=[],date_display=display,first=first,last=last,date_precision=precision,work_type=wt,object_form=None,medium=medium,dimensions_text=dimensions,description=text,physical_object_count='1',native_page_urls=[url],native_metadata_urls=[src['capture']['receipt']['url']],artuk_url='',museum_qid=s.QID,issues=issues)
 return dict(number=number,source_id=sid,institution_id=s.IID,facts=f,issues=issues,version_note=note,source_capture=src['capture'],source_record_reference=src['reference'],retrieved_at=src['capture']['receipt']['retrieved_at'])
def rows():
 bs,afs=sources();out=[]
 for id,key,title,creator,date,medium,dims,note in NATIVE:
  src=bs[id];a=src['data'];n=id if key!='cumming' else 92142;v=row(n,'box/'+str(id)+'/'+key,str(id)+'-'+key,a['link'],creator,title,date,'painting',medium,dims,note,src,clean(a['excerpt']['rendered']+' '+a['content']['rendered']))
  if id==1903:v['facts']['titles'].append('Hoe Nursery Garden')
  if id in [1909,1918]:
   extra=afs['plymouth-pier-from-the-hoe' if id==1909 else 'the-royal-william-victualling-yard-at-plymouth'];v['supplementary_source']=extra;v['facts']['source_fields']['acquisition_funder_text']=extra['data']['text']
  out.append(v)
 for n,(slug,title,creator,date,wt,medium,dims,note) in enumerate(FUNDER,200001):
  src=afs[slug];out.append(row(n,'artfund/'+slug,'artfund-'+slug,src['capture']['receipt']['url'],creator,title,date,wt,medium,dims,note,src,src['data']['text']))
 return sorted(out,key=lambda v:v['number']),[]
def main():
 out,holds=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,source_fact_holds=holds,parser_reference=ref(Path(__file__).resolve()),policy='Candidate facts pending object/version and collection review. Native articles plus primary acquisition-funder evidence. Dates of creation distinct from lifespans,commissions,acquisitions and subject events. Qualified attributions preserved;no creator authority links.'))
 print(json.dumps(dict(candidates=len(out),dated=sum(v['facts']['first'] is not None for v in out))),flush=True)
if __name__=='__main__':main()
