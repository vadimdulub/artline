#!/usr/bin/env python3
"""Selected full-frame Getty CC0 source renditions for pending historical objects."""
import concurrent.futures
import exhibitions_common as c
import historical_exhibitions_getty_ra1953_images_20261012 as images
from historical_exhibitions_getty_checklist_expansion_20261012 import DEST

def main():
 scope=c.load(DEST/'scope-review.json.gz');done={r['accession_number']for r in scope['existingExactAccessionMatches']};objects=[o for o in scope['eligibleObjects']if o['accession']not in done]
 images.OUT=DEST;images.DEST=DEST/'images';images.DEST.mkdir(parents=True,exist_ok=True);rows=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:
  jobs={pool.submit(images.prepare,o,True):o for o in objects}
  for f in concurrent.futures.as_completed(jobs):
   try:rows.append(f.result())
   except Exception as e:errors.append(dict(objectID=jobs[f]['id'],error=repr(e)))
   if (len(rows)+len(errors))%5==0:print('Prepared',len(rows),'errors',len(errors),flush=True)
 result=dict(at=c.now(),images=rows,errors=errors,sourceKind='Advertised IIIF bounded source rendition, not maximum-resolution original.',visualReview='pending')
 c.save(images.DEST/'prepared-batch.json',result);print('Prepared',len(rows),'errors',errors)
if __name__=='__main__':main()
