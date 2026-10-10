#!/usr/bin/env python3
"""Reviewable, evidence-verified, production-only museum assignment delivery."""
import argparse,collections,copy,gzip,importlib.util,json,re
from pathlib import Path
from urllib.parse import urlsplit,unquote
ROOT=Path(__file__).resolve().parents[1]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
t=mod('assessment','ops/assess-random-5000-round3-20261007.py');r=t.r;RUN=t.RUN;OLD=t.OLD;d=t.t.d
legacy=mod('receipts','ops/apply-random-5000-museums-20261006.py');native=mod('native','ops/refine-random-5000-native-identities-20261006.py')
r.RUN=RUN;r.BACKUP=t.t.BACKUP;r.PORT=55489;d.ACTOR='random-5000-museums-round3-20261007'
GENERIC={'portrait of a man','portrait of a woman','still life with fruit','the judgment of paris','l adoration des bergers','portrait of a lady','portrait of a gentleman','self portrait','landscape','composition','untitled'}
EXCLUDED={'cd28d96a-35fc-4bde-a551-061f8877829c':'Private Gere collection loan; no administrative museum collection/deposit correspondence established.','4f620afe-6ac5-4041-85f3-0189c3b1deb2':'Composite altarpiece with missing original elements; component identity unresolved.','9b312ad0-2da4-5200-9141-183dfa765757':'Multiple illustrated-book copies in different museums.','18cdda5a-6670-52bf-8fab-40e595419ed2':'Photographic print identity is unresolved.','f6272897-c2e3-599c-885c-6ff6cd28e091':'Source is a print after Fragonard, not an established match to the original painting.'}
INSTITUTION_RECONCILIATION={'65b372fb-53ba-5881-bc41-33ef06c08fbc':'b5d60a22-a3db-5597-b327-d8a31d17c8bb','7b891415-2d1b-5daa-8ba3-261d0d6b3c7a':'7a2e2ce4-de79-5c1c-a0f7-f9c3da7809a6'}

def indexed_reason(c):
 if c['artwork_id']in EXCLUDED:return EXCLUDED[c['artwork_id']]
 if c['artwork_id']=='972e197f-439b-4ad6-acaf-fb0c935d13ee':return 'Catalogue chapter reconstructs a dismembered altarpiece; National Gallery owns selected panels, not an identified whole-object museum holding.'
 if c['artwork_id']=='9d4f3f7a-feb7-5d96-a250-647295ad8483':return 'Princeton source describes a compositional study, not the catalogued original painting.'
 if c['artwork_id']=='086b9a08-93f2-5e11-ad95-9699b863400e'and not c['inventory_correspondence']:return 'Repeated Sisley riverside subject; dimensions or native identity required to resolve the version.'
 if not c.get('institution')or t.NON_MUSEUM.search(c['institution']['name']):return 'not_an_identified_museum'
 if not c['detail_page']or re.search(r'/archive/exhibition/|/exhibitions/',c['source_url']):return 'not_a_current_collection_object_record'
 if c['qualified_holding_text']:return 'source_qualifies_holding_or_ownership'
 strong=c['exact_source_url']or c['inventory_correspondence'];text=c['excerpt']
 if not strong and (c['print_impression_unresolved']or re.search(r'\b(?:etching|engraving|woodcut|woodblock|lithograph|lithographs|screenprint|linocut|aquatint|pochoir|albumen|gelatin silver|photograph|portfolio|artist after)\b',text,re.I)):return 'specific_edition_or_derivative_not_established'
 title=t.norm(c['title']);header=title in t.norm(c['source_title'])
 if 'study'in t.norm(c['source_title']).split()and 'study'not in title.split():return 'source_title_describes_different_preparatory_version'
 if strong:return None
 if title in GENERIC:return 'generic_title_requires_inventory_or_version_evidence'
 if not(header and len(title.split())>=4 and c['year_correspondence']):return 'identity_below_editorial_threshold'
 return None

def web_plan():
 rows=r.load(RUN/'baseline.json.gz');validation={v['url']:v for v in r.load(RUN/'indexed-page-validation.json.gz')};groups=collections.defaultdict(dict);holds=[];pins=[]
 for folder in [OLD,t.t.PREV,RUN]:
  pin=r.load(folder/'latest-web-review.json');pins.append({'folder':str(folder.relative_to(ROOT)),**pin});review=r.load(folder/pin['path'])
  for aid,cs in review['related_source_leads'].items():
   if aid not in rows:continue
   for c in cs:
    reason=indexed_reason(c)
    if reason:holds.append({'artwork_id':aid,'source_url':c['source_url'],'reason':reason});continue
    groups[aid][c['source_url']]=c
 claims=[]
 for aid,group in groups.items():
  # URL language/query aliases of the same native object are one candidate.
  dedup={}
  for c in group.values():
   url=unquote(c['source_url']).split(';jsessionid=')[0].split('?')[0].replace('/en/ark:', '/ark:');dedup[url]=c
  if len(dedup)!=1:holds.append({'artwork_id':aid,'reason':'multiple_primary_objects_or_museums','source_urls':list(group)});continue
  c=next(iter(dedup.values()));rc=legacy.indexed_receipt(c);direct=validation.get(c['source_url'],{});confidence=.9 if c['exact_source_url']or c['inventory_correspondence']else .84
  # Index text remains the matching evidence; a successful JavaScript shell
  # alone is never substituted as proof of content that it does not contain.
  if direct.get('receipt',{}).get('status')==200 and t.norm(c['title'])in t.norm(direct.get('text','')):rc=direct['receipt']
  basis=('Exact native object URL or inventory correspondence'if confidence==.9 else 'Distinctive exact object heading, named creator and creation-year correspondence on the museum catalogue detail record')+'; editorial confidence '+str(int(confidence*100))+'%, not a calibrated probability.'
  claim={'artwork_id':aid,'title':rows[aid]['artwork']['title'],'scheme':'museum-catalogue-url','external_id':c['source_url'],'institution':c['institution'],'source_url':c['source_url'],'checked_at':rc['retrieved_at'],'location_text':c['institution']['name'],'identity_basis':basis,'source_class':'reviewed_primary_museum_catalogue_index','source_receipt':rc,'object_evidence':{'reviewed_indexed_object':c,'direct_page_validation':direct,'editorial_confidence':confidence,'calibrated_probability':False},'editorial_confidence':confidence,'claim_type':'holding','review_state':'accepted','limitation':'Documented museum collection connection at the approved 80% editorial threshold. Direct/index transport and source qualifications retained. No current-display or ownership claim; original dates, creator labels and relationships, images and publication status preserved.'}
  if aid=='201e0fec-5c9d-4686-bf71-2921704fcc73':
   assert 'On long-term loan to'in c['excerpt']and 'Versailles'in c['excerpt']
   inst=next(i for i in r.load(RUN/'institutions.json.gz')if i['id']=='f4eea5e8-e7ba-4843-b2c2-bda64513cfd1')
   claim['institution']=inst;claim['location_text']=inst['name'];claim['object_evidence']['collection_role']='explicit_receiving_museum_deposit';claim['object_evidence']['administrative_collection_retained']='Louvre Department of Paintings; French State ownership, as stated in the official object record.';claim['identity_basis']+=' Official Louvre record explicitly identifies the long-term deposit at the national museum of Versailles; receiving-museum custody selected, administrative owner retained separately.';claim['limitation']+=' Versailles is the documented receiving museum; no transfer of State ownership or current-display claim.'
  claims.append(native.enrich(claim))
 r.save_gz(RUN/'primary-plans/indexed-80-reviewed.json.gz',{'at':r.now(),'claims':claims,'holds':holds,'review_pins':pins});print('Indexed museum matches',len(claims),'individual holds',len(holds),flush=True)

def manual():
 rows=r.load(RUN/'baseline.json.gz');ii=r.load(RUN/'institutions.json.gz');path=RUN/'multiple-museum-research.json';proof=r.load(path)
 aid='dc7b42ea-69c3-574a-bb91-830c5727c283';url='https://onlinecollection.nationalgallery.ie/objects/8710';inst=next(i for i in ii if i['id']=='8aa52843-c70a-4f48-8bdd-9965d04339ae');assert url in proof['result']and '55 x 118'in proof['result']and rows[aid]['artwork']['dimensions_text']=='118 x 55 cm'
 rc={'url':url,'body_path':str(path.relative_to(ROOT)),'sha256':r.sha(path.read_bytes()),'retrieved_at':proof['at'],'transport':'web_tool_primary_catalogue_index','http_status_not_observed':True}
 basis='Exact existing WikiArt object title, creator and 118 x 55 cm dimensions identify the National Gallery of Ireland version with the Supper at Emmaus, NGI.4538, official object 8710; Chicago has the other kitchen scene version. Editorial confidence 96%, not a calibrated probability.'
 claim={'artwork_id':aid,'title':rows[aid]['artwork']['title'],'scheme':'national-gallery-ireland-object','external_id':'8710','institution':inst,'source_url':url,'checked_at':proof['at'],'location_text':inst['name'],'identity_basis':basis,'source_class':'primary_museum_multiple_version_resolution','source_receipt':rc,'object_evidence':{'inventory':['NGI.4538'],'primary_source_dimensions':'55 x 118 cm','catalogue_dimensions_preserved':'118 x 55 cm','resolution':basis,'editorial_confidence':.96},'editorial_confidence':.96,'claim_type':'holding','review_state':'accepted','limitation':'Documented collection membership; exact version resolved by subject and dimensions. No current display or ownership transfer claim. Artwork dates, images, labels and publication status preserved.'}
 holds=[{'artwork_id':'a688c4af-7c9d-5c4e-a97f-e5e2166245a8','reason':'Two museum versions of the Venetian view; absent dimensions/inventory prevent an 80% version decision.','source_path':'wikiart-authority-review-3.json'},{'artwork_id':'ee38aafe-c82a-535d-a8ae-8ffa1aa44558','reason':'Official National Library of Wales object page resolves the collection as a library rather than National Museum Cardiff.','source_url':'https://www.library.wales/discover-learn/digital-exhibitions/pictures/europeana-280/james-ward-an-overshot-mill-in-wales','decision':'identified_non_museum_collection'}]
 r.save_gz(RUN/'primary-plans/multiple-museum-labels-resolved.json.gz',{'at':r.now(),'claims':[claim],'holds':holds})

def prepare():
 rows=r.load(RUN/'baseline.json.gz');ii=r.load(RUN/'institutions.json.gz');byid={i['id']:i for i in ii};pool=collections.defaultdict(list)
 inputs=[('wikidata-80',r.load(RUN/'wikidata-assessment-v4.json.gz')['claims']),('wikiart-80',r.load(RUN/'wikiart-holding-plan-v9.json.gz')['claims'])]
 for name in ['primary-reconciled','museum-deposits-reviewed','lombardia','fng-date-reviewed','moma-date-reviewed','indexed-80-reviewed','multiple-museum-labels-resolved']:inputs.append((name,r.load(RUN/'primary-plans'/(name+'.json.gz'))['claims']))
 source_order={name:n for n,(name,cs)in enumerate(inputs)};reconciled=[]
 for name,cs in inputs:
  for original in cs:
   c=copy.deepcopy(original);assert c['artwork_id']in rows
   if c['institution']['id']in INSTITUTION_RECONCILIATION:
    originalinst=c['institution'];c['institution']=byid[INSTITUTION_RECONCILIATION[originalinst['id']]];c['object_evidence']['delivery_institution_reconciliation']={'source_authority':originalinst,'existing_institution':c['institution'],'basis':'Reviewed exact distinctive museum name: Museum Ludwig Cologne or Towneley Hall Art Gallery and Museum Burnley; building/collection authorities refer to the same museum, without rewriting existing authority IDs.'}
   while c['institution'].get('canonical_institution_id'):c['institution']=byid[c['institution']['canonical_institution_id']]
   c['location_text']=c['institution']['name'];c['origin_provider']=name;c['review_state']='accepted';c.setdefault('editorial_confidence',.94 if name=='wikiart-80'else .9)
   if 'editorial confidence'not in c['identity_basis'].lower():c['identity_basis']+=' Editorial confidence '+str(int(100*c['editorial_confidence']))+'%, not a calibrated probability.'
   c['source_receipt']=legacy.verified_receipt(c)
   if c['artwork_id']=='0654e2ea-74bf-5589-bdbf-11a57cb5a47a':
    c['object_evidence']['primary_original_version_review']='edition-version-review.json';c['object_evidence']['inventory']=['1950-134-71'];c['duplicate_source_urls']=['https://www.philamuseum.org/objects/51541'];c['identity_basis']+=' Philadelphia official catalogue object 51541 and institutional account explicitly identify the 1916 original readymade, accession 1950-134-71.'
   if name=='indexed-80-reviewed':
    page=c['object_evidence']['reviewed_indexed_object'];url=c['source_url'];text=page['excerpt'];inventories=[]
    if match:=re.search(r'art\.thewalters\.org/object/([^/]+)/?',url):inventories=[unquote(match[1])]
    elif 'rijksmuseum.nl/'in url:inventories=re.findall(r'Object(?: number|nummer)[\s*:\|]+(SK-[A-Z]-\d+(?:-[A-Z])?)',text,re.I)
    elif 'americanart.si.edu/'in url:inventories=re.findall(r'Object Number\s+([A-Za-z0-9.\-/]+)',text)
    elif 'nationalgallery.org.uk/'in url:inventories=re.findall(r'Inventory number\s+(NG\d+)',text)
    if inventories:c['object_evidence']['inventory']=sorted(set(inventories))
   if name=='wikidata-80':
    refs=c['object_evidence']['native_catalogue_references'];urls=set(c.get('duplicate_source_urls',[]));urls.update('https://artuk.org/discover/artworks/'+v for v in refs.get('P1679',[]));urls.update(v for v in refs.get('P973',[])if v.startswith('https://'));c['duplicate_source_urls']=sorted(urls)
    if not rows[c['artwork_id']]['creators']:
     ca=r.load(RUN/'selected-creator-authorities.json.gz');c['object_evidence']['unlinked_creator_authority_receipts']={q:ca[q]['receipt']for q in c['object_evidence']['source_creator_qids']if q in ca};c['object_evidence']['unlinked_creator_label_preserved']=rows[c['artwork_id']]['artwork']['unlinked_creator_label']
   pool[c['artwork_id']].append(c)
 selected=[];conflicts=[]
 for aid,group in pool.items():
  museums={c['institution']['id']for c in group};preferred=sorted(group,key=lambda c:(source_order[c['origin_provider']],c['editorial_confidence']),reverse=True)
  if len(museums)>1:
   # Only an explicit current national deposit/primary custody resolution
   # resolves a different collection owner; all other differences stay visible.
   custody=[c for c in preferred if c['origin_provider']in ['museum-deposits-reviewed','multiple-museum-labels-resolved']]
   if len(custody)==1:
    chosen=custody[0];chosen['object_evidence']['conflicting_collection_roles']=[{'institution':c['institution'],'source_url':c['source_url'],'identity_basis':c['identity_basis']}for c in group if c is not chosen];reconciled.append({'artwork_id':aid,'resolution':'explicit_receiving_museum_deposit','chosen_institution':chosen['institution'],'other_claims':group})
   else:conflicts.append({'artwork_id':aid,'reason':'contradictory_museum_objects_not_reconciled','claims':group});continue
  else:chosen=preferred[0]
  chosen['object_evidence']['corroborating_claims']=[{'source_url':c['source_url'],'source_class':c['source_class'],'institution':c['institution']['name']}for c in group if c is not chosen];selected.append(chosen)
 r.save_gz(RUN/'primary-plans/combined-80-reviewed.json.gz',{'at':r.now(),'claims':selected,'holds':conflicts,'resolved_collection_conflicts':reconciled,'review_scope':'Museum connections only; user-approved editorial threshold is 80%, not a calibrated probability.'});print('Combined distinct source-supported',len(selected),'unresolved source conflicts',len(conflicts),'resolved collection-role conflicts',len(reconciled),flush=True)

def inventory_keys(c):
 values=c.get('object_evidence',{}).get('inventory',[])
 if isinstance(values,str):values=[values]
 return {v for v in values if isinstance(v,str)and len(v.strip())>=3 and t.norm(v)not in ['none','unknown','not known','not recorded','sans numero']}

def preflight():
 data=r.load(RUN/'primary-plans/combined-80-reviewed.json.gz');claims=data['claims'];iids=sorted({c['institution']['id']for c in claims});urls=sorted(set().union(*(d.claim_urls(c)for c in claims)));inventories=sorted(set().union(*(inventory_keys(c)for c in claims)))
 query="SELECT h.artwork_id::text,h.institution_id::text,h.source_url FROM artwork_location_assertions h JOIN artworks a ON a.id=h.artwork_id WHERE h.institution_id=ANY(%s::uuid[]) AND h.source_url=ANY(%s) AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL AND a.status<>'archived'"
 invquery="SELECT id::text,current_institution_id::text,accession_number,title FROM artworks WHERE current_institution_id=ANY(%s::uuid[]) AND accession_number=ANY(%s) AND status<>'archived'"
 with r.connect('production')as db:
  owners=db.execute(query,(iids,urls)).fetchall();existing=db.execute(invquery,(iids,inventories)).fetchall();plans={'holding_urls':db.execute('EXPLAIN (FORMAT JSON) '+query,(iids,urls)).fetchone(),'institution_inventory':db.execute('EXPLAIN (FORMAT JSON) '+invquery,(iids,inventories)).fetchone()}
 shared=collections.defaultdict(set)
 for c in claims:
  for v in inventory_keys(c):shared[(c['institution']['id'],v)].add(c['artwork_id'])
 held=[];ready=[]
 for c in claims:
  collisions=[o for o in owners if o['source_url']in d.claim_urls(c)and o['artwork_id']!=c['artwork_id']]
  inv=[o for o in existing if o['current_institution_id']==c['institution']['id']and o['accession_number']in inventory_keys(c)and o['id']!=c['artwork_id']]
  inbatch=set().union(*(shared[(c['institution']['id'],v)]for v in inventory_keys(c)))-{c['artwork_id']}if inventory_keys(c)else set()
  if collisions or inv or inbatch:held.append({'artwork_id':c['artwork_id'],'reason':'existing_or_in_batch_same_museum_object_requires_reconciliation','source_url':c['source_url'],'existing_holding_url_owners':collisions,'existing_museum_inventory_owners':inv,'other_candidate_ids':sorted(inbatch)})
  else:ready.append(c)
 r.save_gz(RUN/'primary-plans/delivery-80-verified.json.gz',{'at':r.now(),'claims':ready,'holds':held,'combined_source_plan':'combined-80-reviewed.json.gz'});r.save_gz(RUN/'native-identity-preflight.json.gz',{'at':r.now(),'claims_considered':len(claims),'claims_ready_for_delivery_preflight':len(ready),'held':held,'existing_accepted_source_owners':owners,'existing_inventory_owners':existing,'bounded_query_plans':plans});print('Source URL / institution inventory duplicate check:',len(ready),'ready',len(held),'holds',flush=True)

def plan(wave):d.plan(wave,['delivery-80-verified'],targets=['production'])
def apply(wave):d.apply(wave,'production')
def verify(wave):d.verify(wave,targets=['production'])

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['web_plan','manual','prepare','preflight','plan','apply','verify']);ap.add_argument('--wave',default='museum-holdings-01');a=ap.parse_args()
 if a.phase in ['plan','apply','verify']:globals()[a.phase](a.wave)
 else:globals()[a.phase]()
