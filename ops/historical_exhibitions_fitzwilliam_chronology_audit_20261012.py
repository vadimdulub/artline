"""Read-only source chronology checks across selected delivered Fitzwilliam batches."""
import json,sys
import historical_exhibitions_fitzwilliam_london_early_discovery_20261012 as d
c=d.c
MODULES=['broughton','cambridge_remaining','london_early_release','horne_1916','tate_1923','ruskin_1878','early_london','rembrandt_release']
rows=[];unsupported=[];checked=0
for name in MODULES:
 mod=__import__('historical_exhibitions_fitzwilliam_'+name+'_20261012');p=c.load(mod.OUT/'plan.json.gz');events={e['id']:e for e in p['events']}
 for entry in p['entries']:
  eid=entry.get('eid')or entry.get('eventID');event=events.get(eid)
  if not event:unsupported.append(dict(batch=name,entryID=entry['id'],reason='unrecognized event key'));continue
  end=event.get('endYear')or event.get('year');assert isinstance(end,int)
  dates=[dt for cr in entry['source']['data'].get('lifecycle',{}).get('creation',[])for dt in cr.get('date',[])];checked+=1
  for dt in dates:
   earliest=dt.get('earliest')
   if isinstance(earliest,int)and earliest>end:
    rows.append(dict(batch=name,entryID=entry['id'],eventID=eid,eventTitle=event['title'],eventEndYear=end,nativeID=entry.get('nid')or entry.get('nativeID'),creation=dt,sourceURL=entry['source']['receipt']['url'],decision='Chronological conflict requires source review; no automatic date rewrite or record deletion.'))
result=dict(at=c.now(),checkedEntries=checked,conflicts=rows,unsupported=unsupported,newProductionChanges=0,realLocalWrites=False)
c.save(d.OUT/'delivered-chronology-audit.json',result);print(json.dumps(result))
