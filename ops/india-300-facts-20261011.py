#!/usr/bin/env python3
"""Interpret only source object fields; retain uncertainty and source wording."""
import argparse,collections,importlib.util,json,re
from pathlib import Path

s=importlib.util.spec_from_file_location('research',Path(__file__).with_name('india-300-research-20261011.py'))
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
m,RUN=r.m,r.RUN
REGISTRY={
 'alh_ald':('Allahabad Museum, Prayagraj','allahabad-museum-prayagraj','https://www.theallahabadmuseum.com','Prayagraj'),
 'gom_goa':('Archaeological Museum, Old Goa','archaeological-museum-old-goa','https://asigoacircle.gov.in','Velha Goa'),
 'im_kol':('Indian Museum, Kolkata','indian-museum-kolkata','https://indianmuseumkolkata.org','Kolkata'),
 'nkm_hyd':('Archaeological Museum, Nagarjunakonda','archaeological-museum-nagarjunakonda','https://asi.nic.in/asi_museums_nagarjunakonda.asp','Vijayapuri South'),
 'nat_del':('National Museum, New Delhi','national-museum-new-delhi','https://www.nationalmuseumindia.gov.in','New Delhi'),
 'ngma_blr':('National Gallery of Modern Art, Bengaluru','national-gallery-modern-art-bengaluru','https://www.ngmaindia.gov.in/ngma_bangaluru.asp','Bengaluru'),
 'ngma_del':('National Gallery of Modern Art','museum-authority-q1338832','http://ngmaindia.gov.in','New Delhi'),
 'ngma_mum':('National Gallery of Modern Art, Mumbai','national-gallery-modern-art-mumbai','https://www.ngmaindia.gov.in/ngma_mumbai.asp','Mumbai'),
 'sjm_hyd':('Salar Jung Museum, Hyderabad','salar-jung-museum-hyderabad','https://www.salarjungmuseum.in','Hyderabad'),
 'vmh_kol':('Victoria Memorial','museum-authority-q1356352','http://www.victoriamemorial-cal.org/','Kolkata'),
 'avm_pun':('Dr. Babasaheb Ambedkar Museum and Memorial, Pune','ambedkar-museum-memorial-pune','https://www.symbiosis-ambedkarmemorial.org/','Pune'),
}
UNKNOWN={'','na','n a','n a nil','not known','unknown','nil','none','not available','not applicable','unidentified','un known','anonymous'}
CENTRAL_ASIAN_SELECTION={
 '2003/7/1958':'sculpture', '2003/19/1129':'sculpture',
 '2003/7/1922':'sculpture', '2003/17/261':'painting',
 '2002/17/146':'painting', '2003/17/273':'painting',
 '2003/17/254':'painting', '99/1/46':'painting',
 '2002/17/206':'painting', '2003/17/349':'painting',
 '99/7/26':'sculpture',
}

def known(v):return r.clean(v) if m.norm(v) not in UNKNOWN else None

def dates(display):
 """Conservative enclosing ranges. Qualifiers stay in the display field."""
 if not known(display):return None,None,'date_review','Source creation date absent or explicitly unknown'
 t=r.clean(display).lower().replace('–','-').replace('—','-').replace('−','-')
 approx=bool(re.search(r'\bc\.|circa|about|early|late|mid|ca\.',t))
 t=re.sub(r'^(?:c\.?\s*|ca\.?\s*|circa\s+|about\s+)(?=\d|early|late|mid)','',t)
 t=re.sub(r'^(?:early|late|mid)\s*','',t)
 t=re.sub(r'b\.?\s*c\.?\s*e\.?','bce',t)
 t=re.sub(r'a\.?\s*d\.?\b','ad',t)
 t=re.sub(r'b\.?\s*c\.?\b','bc',t)
 t=re.sub(r'c\.?\s*e\.?\b','ce',t)
 # A labelled century inside the creation field can coexist with a dynasty
 # or regnal-year description. Only the explicit century supplies bounds.
 century=r'(\d{1,2})(?:st|nd|rd|th)?\s*(?:[-/]\s*(\d{1,2})(?:st|nd|rd|th)?\s*)?(?:century|centuries|cent\.?|cen\.?)\s*(ad|ce|bc|bce)?'
 found=list(re.finditer(century,t));match=found[0] if len(found)==1 else None
 if match:
  first,last=int(match[1]),int(match[2] or match[1]);era=match[3]
  if not 1<=first<=30 or not 1<=last<=30:return None,None,'date_review','Unrecognized century bounds'
  if era in ['bc','bce']:lo,hi=-max(first,last)*100,-(min(first,last)-1)*100-1
  else:lo,hi=(min(first,last)-1)*100+1,max(first,last)*100
  basis='Enclosing explicitly stated source century/centuries; dynasty and early/mid/late wording retained without invented narrower years'
  precise=re.search(r'\((\d{3,4})\)',t)
  if precise:
   year=int(precise[1])*(-1 if era in ['bc','bce'] else 1)
   if not lo<=year<=hi:return None,None,'date_review','Source parenthetical year conflicts with stated century'
   lo=hi=year;basis='Explicit parenthetical creation year, checked against the source century'
 else:
  match=re.fullmatch(r'(\d{3,4})(?:\s*[-/]\s*(\d{2,4}))?\s*(ad|ce|bc|bce)?\.?',t)
  if not match:return None,None,'date_review','Source date wording requires editorial review; no numeric year invented'
  lo=int(match[1]);end=match[2];hi=int(end) if end and len(end)>2 else (lo//100*100+int(end) if end else lo)
  if match[3] in ['bc','bce']:lo,hi=-max(lo,hi),-min(lo,hi)
  if lo>hi:return None,None,'date_review','Reversed or ambiguous creation interval'
  basis='Explicit source creation year or interval'
 if lo>1970:return lo,hi,'after_cutoff',basis
 if hi>1970:return None,None,'date_review','Source range crosses 1970; '+basis
 return lo,hi,'eligible',basis

def record(obj):
 fields=obj['fields'];code=obj['museum'];title=known(fields.get('Title'));acc=known(fields.get('Accession Number'))
 creator=known(fields.get('Main Artist'))
 date=known(fields.get('Period / Year of Work')) or 'Date unknown';lo,hi,decision,basis=dates(date)
 typ=(known(fields.get('Object Type')) or obj['category']).lower()
 technique=known(fields.get('Manufacturing Technique'));material=known(fields.get('Main Material'))
 if 'painting' in typ:kind='painting'
 elif 'sculpture' in typ:kind='sculpture'
 elif 'photograph' in typ:kind='photograph'
 elif 'drawing' in typ or 'sketch' in typ:kind='drawing'
 elif 'textile' in typ:kind='textile'
 else:kind='unknown'
 if code=='nat_del' and obj['category']=='central asian antiquity':kind=CENTRAL_ASIAN_SELECTION.get(acc,'unknown')
 culture='; '.join(k+': '+str(v) for k in ['School','Style','Culture','Origin Place','Country'] if (v:=known(fields.get(k)))) or None
 row=dict(provider='jatan-'+code,source_provider_name=fields['Museum Name']+' — Museums of India national repository',museum=REGISTRY[code][0],source_id=obj['native']['recordIdentifier'],source_url=obj['url'],title=title,creator_label=creator,date_display=date,year_start=lo,year_end=hi,date_decision=decision,date_basis=basis,source_type=kind,medium='; '.join(dict.fromkeys(v for v in [technique,material] if v)) or None,dimensions=known(fields.get('Dimensions')),accession_number=acc,culture=culture,evidence=obj['evidence'],raw=dict(native_fields=fields,index_entry=obj['native'],index_evidence=obj['index_evidence'],portal_museum_code=code),selection_basis='Bounded selection of documented holdings in Indian museums; breadth across collections and visual traditions. No current-display claim.',creator_link_hold=not creator or bool(re.search(r'unknown|unidentified|anonymous|attributed|workshop|school|style|copy|after |\?| not known',creator,re.I)))
 if not title or not acc:row['editorial_hold']='Missing native title or physical-object accession; no placeholder identity supplied'
 if kind=='unknown':row['editorial_hold']='Object category is not yet verified as a visual artwork'
 if code=='nat_del' and obj['category']=='central asian antiquity' and acc not in CENTRAL_ASIAN_SELECTION:
  row['editorial_hold']='Central Asian component/fragment selection deferred; manuscript leaves share near-identical descriptions and require whole-object/version reconciliation'
 # Photographs in a memorial may be later reproduction prints of historic
 # events. Unknown print identity/date is not resolved by the depicted event.
 if kind=='photograph' and decision!='eligible':row['editorial_hold']='Photographic object date/version unresolved; event or subject dates are not creation dates'
 if re.search(r'replica|reproduction|facsimile|photocopy',title or '',re.I):row['editorial_hold']='Possible later reproduction; physical creation/version requires review'
 return row

def facts():
 paths=sorted((RUN/'objects').glob('*.json.gz'));objects=[m.load(p) for p in paths]
 assert len(objects)==len(m.load(RUN/'object-candidates.json.gz')),'Object capture pass unfinished'
 rows=[record(x) for x in objects if x['result']=='native object captured']
 m.save(RUN/'IN-wave1/source-records.json.gz',rows)
 registry={name:dict(slug=slug,website=web,city=city,country_code='IN',portal_museum_code=code) for code,(name,slug,web,city) in REGISTRY.items()}
 m.save(RUN/'institution-registry.json',registry)
 branch={REGISTRY[c][0]:dict(same_host_institution_ids=['7bc6b022-51c3-5575-808e-fea5bc4015c4'],evidence=m.load(RUN/'museum-profiles'/(c+'.json.gz'))['evidence'],basis='Separate city branch explicitly identified by the official national museum portal') for c in ['ngma_blr','ngma_mum']}
 m.save(RUN/'institution-branch-review.json',branch)
 print('Facts',len(rows),'dates',dict(collections.Counter(r['date_decision'] for r in rows)),'initial holds',dict(collections.Counter(r.get('editorial_hold') for r in rows)),flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['facts']);args=parser.parse_args();globals()[args.action]()
