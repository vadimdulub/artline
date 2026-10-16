#!/usr/bin/env python3
"""Bounded Getty1953 eleven-drawing metadata and reciprocal exhibition audit."""
import json
import exhibitions_common as c
OUT=c.DATA/'getty-ra1953-discovery'
def main():
 event=c.load(c.DATA/'getty-ra-1953-activity.json');refs=event['data']['used_specific_object'][0]['member'];rows=[]
 for ref in refs:
  raw,receipt=c.capture(ref['id']);d=json.loads(raw);c.save(OUT/'objects'/(ref['id'].rsplit('/',1)[-1]+'.json'),dict(receipt=receipt,data=d))
  ids=d['identified_by'];acc=next(x['content']for x in ids if x.get('_label')=='Accession Number')
  prod=d.get('produced_by',{});date=prod.get('timespan',{});label=next((x['content']for x in date.get('identified_by',[])if x.get('content')),None)
  exhibitions=[a for s in d.get('member_of',[])for a in s.get('used_for',[])]
  reciprocal=any(x['id']==event['data']['id']for x in exhibitions)
  rows.append(dict(id=ref['id'],title=d['_label'],accession=acc,dateLabel=label,dateBounds=date,creatorLabels=[x.get('content')for x in prod.get('referred_to_by',[])if x.get('_label')=='Artist/Maker (Producer) Name'],reciprocal=reciprocal,otherExhibitions=exhibitions,source=receipt))
 assert len(rows)==11 and all(x['reciprocal']for x in rows)
 result=dict(at=c.now(),source=event['receipt'],objects=rows,counts=dict(objects=11,reciprocalReferences=11,activityReferences=sum(len(x['otherExhibitions'])for x in rows)),checklistComplete=False,sourceDatePrecision='year',sourceDateWarning='Jan1 and Dec31 are bounds on source1953 year, not exact opening/closing dates.')
 c.save(OUT/'discovery.json.gz',result);c.save(c.ROOT/'docs/research/historical-exhibitions-20261012/getty-ra1953-discovery.json',dict(at=result['at'],counts=result['counts'],objects=[{k:v for k,v in x.items()if k not in ['otherExhibitions','source','dateBounds']}for x in rows],source=event['receipt'],checklistComplete=False));print(json.dumps({k:v for k,v in result.items()if k!='objects'}))
if __name__=='__main__':main()
