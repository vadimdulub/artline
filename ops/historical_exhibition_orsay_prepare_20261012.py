from pathlib import Path
import sys,json,re,datetime,collections
import exhibitions_common as c
OUT=Path.home()/'Library/Application Support/Artline/source-metadata/historical-exhibitions-1600-1989-20261012'
URL='https://www.musee-orsay.fr/sites/default/files/2022-06/SalonsExpositions_1673-1961_v1_20220707.pdf'
MONTHS={v:i+1 for i,v in enumerate(['janvier','fevrier','mars','avril','mai','juin','juillet','aout','septembre','octobre','novembre','decembre'])}
COUNTRIES={'France':'FR','Suisse':'CH','Belgique':'BE','Royaume-Uni':'GB','Allemagne':'DE','Italie':'IT','Pays-Bas':'NL','Espagne':'ES','Norvège':'NO','Autriche':'AT','Danemark':'DK','Suède':'SE','Russie':'RU','États-Unis':'US','Etats-Unis':'US','Hongrie':'HU','Portugal':'PT'}
def parse_date(raw):
 s=c.norm(raw).replace('1er','1');m=re.fullmatch(r'(\d{1,2}) (\w+) (\d{4})',s)
 if m and m[2]in MONTHS:
  try:return datetime.date(int(m[3]),MONTHS[m[2]],int(m[1])).isoformat(),'day',int(m[3])
  except ValueError:return None,'invalid',None
 m=re.fullmatch(r'(\w+) (\d{4})',s)
 if m and m[1]in MONTHS:return None,'month',int(m[2])
 if re.fullmatch(r'\d{4}',s):return None,'year',int(s)
 return None,'unknown',None
rows=c.load(OUT/'source-discovery/orsay-table-rows.json');selected=[];held=[];seen={};duplicates=[]
for n,row in enumerate(rows):
 values=[' '.join((v or'').split())for v in row['cells']]
 year,title,venue,start,end,city,country=values
 if n==0:continue
 def hold(why):held.append(dict(row=n+1,page=row['page'],cells=values,reason=why))
 if not re.fullmatch(r'\d{4}',year):hold('Missing explicit event-year column; verify adjacent rows');continue
 year=int(year)
 if not 1600<=year<=1989:hold('Outside selected event scope');continue
 norm=c.norm(title)
 if re.search(r'\bsupplements?\b|\badditions?\b|\bsupplementaire\b|\bcatalogue illustre\b|\bannexes?\b',norm):hold('Supplement or derivative catalogue; reconcile to parent event');continue
 positive=re.search(r'salon|peint|tableaux|aquarell|pastell|dessin|gravur|estamp|lithograph|etching|painting|watercolo|beaux arts|amis des arts|artistes vivants|societe artistique',norm)
 specific2d=re.search(r'peint|tableaux|aquarell|pastell|dessin|gravur|estamp|lithograph|etching|painting|watercolo',norm)
 negative=re.search(r'photograph|sculpt|cerami|potterie|medaill|bijou|orf[eè]vr|architecture|architectes|industrie|industrielle|d art decoratif|arts decoratifs',norm)
 if negative and not specific2d:hold('Excluded media or mixed industrial/decorative scope needs a checklist');continue
 if not positive:hold('Title alone does not establish selected visual-art scope');continue
 sd,sp,sy=parse_date(start);ed,ep,ey=parse_date(end)
 if sp=='invalid'or ep=='invalid':hold('Invalid calendar date in source');continue
 if sy is not None and sy!=year:hold('Source event-year/start-year discrepancy');continue
 if ey and (ey<year or ey>1989):hold('Source end-year discrepancy/outside scope');continue
 if sd and ed and sd>ed:hold('Source start date follows end date');continue
 # Do not silently correct an erroneous country or merge a touring appearance.
 if city=='Genève'and country=='France':hold('Source country conflict: Geneva labelled France');continue
 key=(year,norm,c.norm(city),c.norm(venue),start,end)
 if key in seen:duplicates.append(dict(row=n+1,parentRow=seen[key],page=row['page'],cells=values));continue
 seen[key]=n+1
 ident=c.sha(json.dumps(key,ensure_ascii=False).encode())[:24]
 selected.append(dict(id=c.uid('orsay-historical/'+ident),sourceID=ident,sourceRow=n+1,sourcePage=row['page'],title=title,year=year,startYear=sy or year,endYear=ey,startDate=sd,endDate=ed,dateDisplay=' – '.join([start,end])if end and end!=start else start or str(year),datePrecision=sp if sp==ep else 'mixed',venue=venue or None,city=city or None,country=country or None,countryCode=COUNTRIES.get(country),sourceURL=URL,rawCells=values))
# Same event title/year/city with different venue/date rows: hold for reconciliation.
groups=collections.defaultdict(list)
for r in selected:groups[(r['year'],c.norm(r['title']),c.norm(r['city']))].append(r)
conflictids={r['id']for rs in groups.values()if len(rs)>1 for r in rs}
kept=[]
for r in selected:
 if r['id']in conflictids:held.append(dict(row=r['sourceRow'],page=r['sourcePage'],cells=r['rawCells'],reason='Repeated title/year/city with differing date/venue; reconcile before import'))
 else:kept.append(r)
c.save(OUT/'orsay-prepared.json',dict(at=c.now(),sourceURL=URL,sourceSHA256=c.sha((OUT/'source-discovery/orsay-salons-1673-1961.pdf').read_bytes()),selected=kept,held=held,duplicateRows=duplicates,scannedDataRows=len(rows)-1))
print(json.dumps(dict(selected=len(kept),held=len(held),duplicates=len(duplicates),years=[min(r['year']for r in kept),max(r['year']for r in kept)],countries=dict(collections.Counter(r['country']for r in kept)),holds=dict(collections.Counter(r['reason']for r in held))),ensure_ascii=False,indent=2))
