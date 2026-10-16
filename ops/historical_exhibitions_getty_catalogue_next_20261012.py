#!/usr/bin/env python3
"""Selected eighteen illustrated-book exhibition leads; native metadata only."""
import json,concurrent.futures
import exhibitions_common as c
from getty_selected_accession_search import resolve
OUT=c.DATA/'getty-catalogue-next';LEADS=[(35,'85.GG.26'),(37,'83.GG.279'),(41,'83.GG.18'),(43,'82.GB.137'),(63,'84.GG.23'),(67,'85.GG.289'),(71,'83.GG.262'),(77,'85.GG.960'),(85,'84.GA.61'),(87,'83.GA.265'),(91,'85.GG.39'),(102,'85.GG.379'),(108,'84.GA.920'),(113,'82.GG.139'),(119,'83.GB.261'),(123,'83.GB.17'),(133,'84.GG.10'),(137,'83.GA.266')]
def main():
 book=c.load(c.DATA/'getty-drawings-inventory/inventory.json.gz');rows=[];errors=[]
 def get(lead):
  page,accession=lead;resolved=resolve(accession);raw,rc=c.capture(resolved['objectURL']);d=json.loads(raw);key=d['id'].rsplit('/',1)[-1];c.save(OUT/'objects'/(key+'.json'),dict(receipt=rc,data=d));prod=d.get('produced_by',{});activities=[a for m in d.get('member_of',[])for a in m.get('used_for',[])];return dict(accession=accession,id=d['id'],title=d.get('_label'),page=page,bookEntry=next(r for r in book['records']if r['pdfPage']==page),date=prod.get('timespan'),creators=[x.get('content')for x in prod.get('referred_to_by',[])if x.get('_label')in ['Artist/Maker (Producer) Name','Artist/Maker (Producer) Description']],types=[x.get('_label')for x in d.get('classified_as',[])],activities=activities,resolution=resolved,source=rc)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  jobs={pool.submit(get,l):l for l in LEADS}
  for f in concurrent.futures.as_completed(jobs):
   try:r=f.result();rows.append(r);print(r['accession'],r['title'],'activities',len(r['activities']),flush=True)
   except Exception as e:errors.append(dict(lead=jobs[f],error=repr(e)))
 result=dict(at=c.now(),objects=rows,errors=errors,counts=dict(selectedLeads=len(LEADS),resolved=len(rows),errors=len(errors),activityReferences=sum(len(r['activities'])for r in rows)),review='Exact accession resolution; OCR-derived accession variants require source/title comparison. No production writes or image downloads. Modern activities remain unclassified until source timespans are checked.')
 c.save(OUT/'discovery.json.gz',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-catalogue-next-discovery.json',dict(at=result['at'],counts=result['counts'],errors=errors));print(result['counts'],errors)
if __name__=='__main__':main()
