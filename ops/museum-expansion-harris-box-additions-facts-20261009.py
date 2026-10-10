"""Selected museum-authored physical-object facts; missing dates remain unknown.

This is a research candidate list, not approval to add every candidate. Public
WordPress publication timestamps are deliberately not requested or interpreted.
"""
import gzip,hashlib,html,importlib.util,json,re
from pathlib import Path
def module(name,file):
 z=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));v=importlib.util.module_from_spec(z);z.loader.exec_module(v);return v
s=module('s','museum-expansion-harris-box-additions-common-20261009.py');m=s.m;RUN=s.RUN;ref=s.ref;checked=s.checked
def clean(v):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',v))).strip()
# Exact labels available in current museum narratives. Surnames are retained
# without manufacturing an artist-authority match or inferred first name.
HARRIS={1788:'Gunn',1807:'John Frederick Lewis',1809:'Nash',1812:'Arthur Devis',1814:'JMW Turner',1816:'Angelica Kauffman',1898:'Richard Dadd',14859:'Sir Alfred Gilbert',14862:'William Trost Richards',15562:'Edwin Austen Abbey',15566:'John Atkinson Grimshaw',15569:'Julius Olsson',15575:'Artist influenced by Frans Snyders; possibly trained in his workshop',15579:'John',15591:'Ruysch (authorship unresolved in source narrative)',15595:'Anthony Devis',15598:'Etty',15602:'Alma-Tadema',15605:'Mercié',15608:'Spencelayh',15614:'Goodall',15620:'Webster',15623:'Sherwood',15629:'Leighton',15632:'Hughes',15667:'Laura Knight',15671:'Bateman',15675:'Worsley',15678:'Richards',15681:'Richards',15684:'Dring',15689:'Hennell',15696:'Cole',15699:'Bone',15702:'Bone',15705:'Armstrong',15723:'Blake',15727:'Fuseli',15730:'Galli Bibiena family (individual maker not identified)',15733:'Reni',15736:'Martin',15739:'Nollekens',15744:'Hogarth',15748:'Thornhill',15751:'Thornhill',15754:'Baldinucci',15757:'Edward Stott',15765:'Cruikshank',15768:'Nollekens',15771:'Kauffman',15774:'Nollekens',15777:'Wolf',15780:'Varley',15788:'Romney',16791:'Patti Mayor',16794:'Mayor'}
HARRIS_HOLDS={1774:'2018 artist project/exhibition; outside creation cutoff and individual held object not established.',1818:'Generic print-collection narrative gives no maker,creation date or impression identity.',1901:'Painting title is present but current narrative supplies no maker or object date; seek fuller metadata.',15572:'Current narrative describes Longfellow subject,not painter or creation date.',15611:'Current narrative describes mythological subject,not painter or creation date.',15617:'Current narrative describes French royal family,not painter or creation date.',15626:'Current narrative describes fisherman subject,not painter or creation date.',15784:'Manuscript accompanying drawing instructions: art-object scope and relationship to P1001.2 require review; do not count manuscript and drawings as extra paintings.'}
HARRIS_DATES={1807:(1865,1865,'exact','1865'),1898:(1841,1841,'exact','1841'),14859:(1890,1899,'decade','1890s'),14862:(1903,1903,'exact','1903'),15575:(1640,1649,'circa_range','possibly 1640s'),15605:(1880,1889,'decade','1880s (this cast)'),16791:(1920,1929,'circa_range','probably 1920s')}
INVENTORIES={16794:'P2361',16791:'P1179',15788:'P2365',15784:'P1001.3',15780:'P1001.2',15777:'P1126.6',15774:'P441',15771:'P348',15768:'P439'}
NOTES={
1788:'1944 is exhibition/reception context; creation year remains unknown.',1809:'Retain source surname Nash; do not choose Paul/John authority automatically.',1814:'Watercolour,not derivative print.1835 refers to returning to subject for publication series; exact object creation remains unknown.',1816:'Preparatory drawing,not commissioned painting.1775 commission date is not silently copied to study.',15575:'Current source explicitly rejects simple copy identification and does not attribute to Frans Snyders himself.1640s inferred by museum from costume remains qualified.',15579:'Source surname John retained; biography dates do not become painting dates.',15591:'Museum discusses frequent copying; attribution remains unresolved and needs object-level comparison.',15605:'This physical cast is from1880s;1874 is date of original model,not this cast.',15667:'Wartime subject and maker biography retained; no exact year inferred.',15678:'Smaller painting of church,rectory and camouflage truck; distinct from The Minute Halt.1941 billeting context is retained,not assigned as exact creation year.',15681:'Larger composition with soldiers resting; distinct from smaller church-and-rectory study.',15689:'1944 siege/liberation is subject context; exact creation unknown.',15696:'1943 artist arrival not exact creation.',15699:'1944 subject/artist activity not exact date of this physical painting.',15702:'1943 war-artist appointment not exact creation.',15705:'Other commissioned work September1941 is in Manchester; no date or identity transferred from it.',15723:'Single sheet with Pindar and Lais,not all Blake Visionary Heads;1819 is series context.',15730:'Family attribution remains qualified; no chosen individual maker.',15736:'Small drawing by Martin,not Harris Danby1825 oil of related subject.',15739:'Drawing of memorial,not sculpture;1803 installation and1789 death do not date drawing.',15744:'Reversed preparatory drawing,not print impression;1746 arrest not exact drawing date.',15748:'Four designs treated as one source-catalogued group pending physical accession verification;1715 commission is not exact drawing date.',15754:'Presumed sitter identity retained in title.',15757:'Several poses on a single sheet counted once; source explicitly distinguishes Edward from William Stott of Oldham.',15765:'Letter dated1828 provides substrate context,not exact sketch date;one sheet.',15768:'One sketch on letter,not architectural keystone;1772/1989 biographical/building dates not creation.',15771:'Drawing after ancient fresco,not fresco itself;Kauffman label retained.',15774:'Separate Nollekens drawing after same fresco;not Kauffman sheet;1762–1770 travel context not automatically assigned.',15780:'One source-catalogued series P1001.2;no individual sketch multiplication;1818 refers to similar published guide.',16791:'Probably1920s remains qualified.',16794:'12-year-old sitter and1908 march do not by themselves establish precise painting date.'}
# Each tuple is one physical work discussed by a current museum article.
# Titles qualified as descriptive are not claimed to be formal catalogue titles.
BOX=[
(2478,'napoleon','Napoleon on the Bellerophon in Plymouth Sound, August 1815','Jules Girardet',1890,1890,'circa','around 1890','painting','Oil on canvas','1815 is depicted event,not creation.'),
(2478,'twilit','In Memoriam — Twilit Waters','Jack Pickup',1951,1951,'exact','1951','painting','Oil on hardboard','Potential existing undated record; preserve its metadata if reconciled.'),
(2478,'may','A May Morning','Elsie Higgins',1903,1903,'exact','1903','painting','Oil on canvas','Likely sitter Edith Gorham remains qualified.'),
(2478,'march','March Sky, Cape Cornwall','Karl Weschke',1962,1962,'exact','1962','painting','Oil on canvas','Documented museum collection,not permanent on-view claim.'),
(2024,'rogers','Portrait of Charles Rogers','Sir Joshua Reynolds',1777,1777,'exact','1777','painting',None,'Portrait commissioned1777;distinct from Ryland1778 engraving.'),
(2007,'frances','Portrait of Frances Reynolds','Joshua Reynolds',None,None,'unknown',None,'painting',None,'Source dates companion father portrait1745–1746;do not transfer date from companion or calculate from sitter age.'),
(2007,'samuel','Portrait of Reverend Samuel Reynolds','Joshua Reynolds',1745,1746,'range','1745–1746','painting',None,'Companion work specifically dated;same museum article confirms both Cottonian holdings.'),
(1794,'catherine','Portrait of Catherine Savery','Unidentified artist (formerly attributed to Marcellus Laroon)',1700,1700,'circa','around 1700','painting','Oil on canvas','2006 research rejected Laroon attribution;do not attach Laroon as maker.'),
(1794,'william','Portrait of William Savery','Marcellus Laroon',None,None,'unknown',None,'painting',None,'Father portrait independently confirmed held;do not transfer daughter date or attribution.'),
(1730,'guard','Mrs E.B. Guard, The First Lady Doctor of Music','Edith Morris',None,None,'unknown','early 1900s (precise range unresolved)','painting','Oil','Museum explicitly says early1900s;do not choose decade versus broader early-century range without clarification.'),
(1956,'sarto','Head of a Woman','Andrea del Sarto',None,None,'unknown',None,'drawing',None,'Explicit Cottonian drawing,not similarly titled painting.'),
(1956,'boucher','Study of a Head of a Woman','Francois Boucher',None,None,'unknown',None,'drawing',None,'Specific Cottonian drawing;generic title requires physical-version comparison.'),
(1956,'mercier','Study of a Woman, after Watteau','Phillipe Mercier (after Watteau)',None,None,'unknown',None,'drawing',None,'Original source spelling Phillipe retained;after relationship explicit;not Watteau original.'),
(1956,'dyck','Portrait of a Lady after Rubens','Anthony van Dyck (after Rubens)',None,None,'unknown',None,'drawing',None,'Drawing after Rubens,not Rubens painting.'),
(1956,'sirani','Virgin and Child','Elisabetta Sirani',None,None,'unknown',None,'drawing',None,'Specific Cottonian drawing;not generic Virgin and Child painting.'),
(1388,'heron','Rectilinear Reds and Blues','Patrick Heron',1963,1963,'exact','1963','painting','Oil on canvas','Current museum-curated rainbow article;full work,not reproduced detail.'),
(1388,'wynter','Pas','Bryan Wynter',1970,1970,'exact','1970','painting',None,'Inclusive creation cutoff permits1970;article reproduces detail but candidate is whole work.'),
(1388,'bevan','Green Devon','Robert Pohill Bevan',1919,1919,'exact','1919','painting',None,'Source spelling Pohill retained;no silent authority correction.'),
(1388,'equator','Under the Equator','Herbert F. Williams-Lyouns',1932,1932,'exact','1932','painting',None,'Potential existing undated record;creation source retained as evidence,not overwrite.'),
(1388,'herman','Reclining Figure','Josef Herman',None,None,'unknown',None,'painting',None,'Specific reclining worker painting;creator biography not creation.'),
(1388,'violet','H.M.S. Violet Destroyer Submarine B.2. On Surface (Broadside On)','Douglas Everard Row',1907,1907,'exact','1907','watercolor','Watercolour and ink','One selected album image;museum title conflates ship/submarine labels,retain ambiguity;do not invent separate works or download album.'),
(1394,'eddystone','Eddystone Lighthouse, During a Storm','William Daniell',1825,1825,'exact','1825','painting',None,'Large painting specifically made1825;distinct from associated print;conservation does not create new version.'),
(1906,'hooe','Hooe Lake','Philip Hutchins Rogers',1814,1814,'circa','circa 1814','painting','Oil','Current dedicated article gives circa date;general panorama article1814 retained as supporting context.'),
(1565,'smart','Chemical works at Cattedown (descriptive title)','Borlase Smart',None,None,'unknown',None,'painting',None,'Specific chemical-works painting described in museum panorama article;postwar context not exact creation.'),
(1565,'condy','Fish market on the Barbican (descriptive title)','Nicholas Condy',None,None,'unknown',None,'painting',None,'Specific scene with Island House;compare existing Sutton Pool/Barbican works before any new record.'),
(1565,'cogle','Barbican with customs watch house (descriptive title)','Henry George Cogle',1931,1933,'range','1931–1933','painting',None,'Museum research dates this physical painting from absence/presence of demolished buildings;range retained.'),
(1521,'ward','View of Plymouth (descriptive title)','Dorothy Ward',1933,1933,'exact','1933','watercolor','Gouache on paper pasted to board','Monumental degree work;descriptive title pending native catalogue title;frame not separate artwork.'),
(1756,'hamar','Miss Limeburner (formerly titled Mrs Hamar)','Sir Joshua Reynolds',1748,1748,'circa','around 1748','painting',None,'Current museum labels prefer unmarried sitter name;1753 marriage is not painting date. Holding needs confirmation beyond temporary exhibition.'),
(2012,'innocence','The Age of Innocence','Studio of Sir Joshua Reynolds',None,None,'unknown',None,'painting',None,'Museum explicitly distinguishes its studio copy from Tate original;around1788 in article precedes version distinction,so not automatically assigned to this copy.'),
(2015,'selfportrait','Early Self-Portrait','Sir Joshua Reynolds',1746,1746,'circa','around 1746','painting',None,'Current narrative qualifies1746;underpainted unidentified portrait is same physical canvas,not second object.'),
(2018,'sketchbook','Italian Sketchbook','Sir Joshua Reynolds',1750,1752,'range','1750–1752','drawing','Pencil, pen and ink and black chalk; original vellum binding','One bound sketchbook with121 drawn sides;count once,not121artworks.')]
def sources():
 hs={};bs={}
 for fn in ['selected-indexes-001.json.gz','supplements-001.json.gz','historic-articles-001.json.gz']:
  doc=m.load(RUN/fn)
  for row in doc['rows']:
   if 'data' not in row:continue
   cap=row['capture'];raw=gzip.decompress((m.ROOT/cap['body_path']).read_bytes());assert hashlib.sha256(raw).hexdigest()==cap['receipt']['sha256'] and json.loads(raw)==row['data']
   for x in row['data']:
    dest=hs if row['provider']=='harris' else bs
    if x['id'] in dest:
     old=dest[x['id']]['data'];assert {k:v for k,v in x.items() if k!='content'}=={k:v for k,v in old.items() if k!='content'}
     # WordPress varies loading/fetchpriority by the position in each response.
     strip=lambda v:re.sub(r' (?:loading|fetchpriority)="[^"]*"','',v)
     assert strip(x['content']['rendered'])==strip(old['content']['rendered'])
    else:dest[x['id']]=dict(data=x,capture=cap,artifact_reference=ref(RUN/fn))
 return hs,bs
def row(number,provider,src,key,title,creator,date,work_type,medium,note,inventory=None):
 x=src['data'];first,last,precision,display=date;iid=s.IIDS[0 if provider=='harris' else 1];sid=provider+'/'+str(x['id'])+('/'+key if key else '');text=clean(x.get('excerpt',{}).get('rendered','')+' '+x['content']['rendered']);unidentified=creator.startswith('Unidentified');issues=[]
 if first is None:assert last is None and precision=='unknown';issues.append('unknown_creation_date_requires_review')
 else:assert 100<=first<=last<=1970
 if any(t in creator.lower() for t in ['after','formerly','studio','influenced','possibly','unresolved','not identified']):issues.append('qualified_creator')
 if len(creator.split())==1:issues.append('source_surname_only')
 f=dict(source_id=sid,native_id=str(x['id'])+('-'+key if key else ''),source_url=x['link'],source_retrieved_url=src['capture']['receipt']['url'],title=title,titles=[title],creator_label=creator,identity_creator_labels=[creator],source_artist_fields=[creator],unidentified_creator=unidentified,source_fields={'ATTRIBUZIONI':creator,'museum_narrative':text,'editorial_note':note},inventory=inventory,normalized_inventory=inventory,alternative_inventories=[],date_display=display,first=first,last=last,date_precision=precision,work_type=work_type,object_form=None,medium=medium,dimensions_text=None,description=text,physical_object_count='1',native_page_urls=[x['link']],native_metadata_urls=[src['capture']['receipt']['url']],artuk_url='',museum_qid=s.QIDS[iid],issues=issues)
 return dict(number=number,source_id=sid,institution_id=iid,facts=f,issues=issues,version_note=note,source_capture=src['capture'],source_record_reference=src['artifact_reference'],retrieved_at=src['capture']['receipt']['retrieved_at'])
def rows():
 hs,bs=sources();out=[];holds=[]
 # Current fine-art archive preserves the exact nine accession labels below.
 archive=m.load(RUN/'native-probes-001.json.gz');h=next(x for x in archive['rows'] if x['provider']=='harris');raw=gzip.decompress((m.ROOT/h['capture']['body_path']).read_bytes()).decode();assert all(v in raw for v in INVENTORIES.values())
 for id,creator in HARRIS.items():
  src=hs[id];x=src['data'];wt='sculpture' if 237 in x['collections'] else 'painting' if 238 in x['collections'] else 'drawing';medium=None
  if id==1814:wt='watercolor'
  if id in [1898,14862]:medium='Oil on canvas'
  if id==14859:medium='Bronze'
  if id==1898:
   artfund=next(x for x in m.load(RUN/'supplements-001.json.gz')['rows'] if x['provider']=='artfund');assert 'Puck, 1841' in artfund['parsed']['text'] and 'Richard Dadd' in artfund['parsed']['text']
  out.append(row(id,'harris',src,'',clean(x['title']['rendered']),creator,HARRIS_DATES.get(id,(None,None,'unknown',None)),wt,medium,NOTES.get(id,'Current museum featured collection entry;unknown creation date is retained without lifespan,depicted-year or acquisition-date inference.'),INVENTORIES.get(id)))
  if id in INVENTORIES:out[-1]['inventory_source_reference']=ref(RUN/'native-probes-001.json.gz')
  if id==1898:out[-1]['supplementary_source']=artfund;out[-1]['facts']['dimensions_text']='61.9 x 61.8 cm'
 for id,reason in HARRIS_HOLDS.items():holds.append(dict(number=id,source_id='harris/'+str(id),institution_id=s.IIDS[0],state='source_fact_hold',hold_reason=reason,source_record_reference=hs[id]['artifact_reference']))
 # One separately described Danby painting, not the Martin drawing.
 out.append(row(915736,'harris',hs[15736],'danby','The Delivery of Israel out of Egypt','Francis Danby',(1825,1825,'exact','1825'),'painting',None,'Museum explicitly identifies and dates this separate painting while discussing Martin drawing.'))
 for n,v in enumerate(BOX,1):
  id,key,title,creator,first,last,precision,display,wt,medium,note=v;out.append(row(100000+n,'box',bs[id],key,title,creator,(first,last,precision,display),wt,medium,note))
 return sorted(out,key=lambda x:x['number']),holds
def main():
 out,holds=rows();m.save(RUN/'candidate-facts-001.json.gz',dict(at=m.now(),rows=out,source_fact_holds=holds,parser_reference=ref(Path(__file__).resolve()),policy='Candidate facts only,pending duplicate/version/holding review. Unknown dates remain ineligible for dated scope;no artist-lifespan dates. Source surnames and qualified creators retained without authority links. All current source API bodies hash checked. One sketchbook counts once. Modern/artifact/non-object leads excluded.'))
 print(json.dumps(dict(candidates=len(out),dated=sum(x['facts']['first'] is not None for x in out),source_fact_holds=len(holds))),flush=True)
if __name__=='__main__':main()
