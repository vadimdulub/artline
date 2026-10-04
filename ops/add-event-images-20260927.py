#!/usr/bin/env python3
"""Pinned museum selections for All historical periods; review records, no publication."""
import argparse, importlib.util, json
from pathlib import Path
s=importlib.util.spec_from_file_location('core',Path(__file__).with_name('add-islamic-world-images-20260925.py'))
core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
core.CAMPAIGN='event-images-20260927'
core.RUN=core.ROOT/'docs/research'/core.CAMPAIGN
core.BACKUP=core.DATA/'backups'/core.CAMPAIGN
core.ORIGINALS=core.DATA/'source-images'/core.CAMPAIGN
core.SOURCE_LABEL='Additional historical period museum selections'
core.MIGRATION='0029_textile_photograph_types.sql'
core.COUNTRIES={'IQ':('Iraq','western-asia'),'EG':('Egypt','northern-africa'),'GR':('Greece','southern-europe'),'IT':('Italy','southern-europe'),'CN':('China','eastern-asia'),'IN':('India','southern-asia'),'PK':('Pakistan','southern-asia'),'TH':('Thailand','south-eastern-asia'),'KH':('Cambodia','south-eastern-asia'),'IR':('Iran','southern-asia'),'ES':('Spain','southern-europe'),'SY':('Syria','western-asia'),'ML':('Mali','western-africa'),'UZ':('Uzbekistan','central-asia')}
GROUPS=[
 ('writing','IQ',[140011,150515,160080],'Early Mesopotamian sculpture and seal carving in the societies of the first cities.'),
 ('writing','EG',[148794,94136,93984,136482],'Egyptian royal representation, painted funerary culture and scribal tools.'),
 ('classical','GR',[144965,111499,110059,149405],'Attic vase painting: myth, ritual and warrior imagery.'),
 ('classical','IT',[399499,111818],'Greek communities in southern Italy: architectural ornament and bronze sculpture.'),
 ('buddhism','CN',[133035,140151],'Buddhist figure sculpture under Northern Wei and Sui China.'),
 ('buddhism','IN',[123021],'Early Buddhist sculpture from Sarnath.'),
 ('buddhism','PK',[159840],'Gandharan visual narrative of Siddhartha at the Bodhi Tree.'),
 ('buddhism','TH',[135328],'Mon-Dvaravati Buddhist imagery in Thailand.'),
 ('buddhism','KH',[147047],'Maitreya sculpture documenting Buddhist imagery in Cambodia.'),
 ('mughal','IN',[170828,146201,146198,170830,101358,124017,170840,170883],'Mughal court painting: portraiture, imaginative flora, narrative, music and intimate life; historical cultural context, not depictions of every political event.'),
 ('tang-song','CN',[149415,149119,130361,152556,149416,134843,111515,160955],'Song landscape, sericulture, poetry, floral imagery and decorative arts.'),
 ('islamic-learning','ES',[423613],'Carved architectural ornament of Umayyad Cordoba.'),
 ('islamic-learning','IR',[135708],'Samanid figural ceramic from Nishapur, alongside the Arabic-world selection.'),
 ('islamic-learning','EG',[95120,114235,170528],'Fatimid ceramic decoration and Mamluk Arabic manuscript calligraphy from Egypt.'),
 ('islamic-learning','IQ',[123982,133460,135809,152365,136410],'Abbasid and medieval Iraqi ceramics, inscription and inlaid metalwork; source locality qualifications retained.'),
 ('islamic-learning','SY',[95116,117918,116672,95151,95134,119842,99654,120202],'Syrian ceramics, glass and metalwork from Raqqa and other recorded Syrian origins.'),
]
TYPE={'Painting':'painting','Drawing':'drawing','Print':'print','Sculpture':'sculpture','Ceramic':'ceramic','Textile':'textile','Silver':'metalwork','Metalwork':'metalwork','Ivory':'sculpture','Calligraphy':'calligraphy','Manuscript':'calligraphy','Glass':'unknown'}

def plan():
 objects={};captures=core.ROOT/'docs/research/production-followup-20260927/captures'
 for f in sorted(captures.glob('cma-*.json')):
  if f.name.endswith('.receipt.json'):continue
  rec=json.loads(f.with_suffix('.receipt.json').read_bytes());assert core.sha(f.read_bytes())==rec['sha256']
  for o in json.loads(f.read_bytes()).get('data',[]):objects.setdefault(o['id'],(o,rec))
 records=[];excluded=[]
 with core.connect() as db:
  institutions={k:db.execute('SELECT to_jsonb(i) record FROM institutions i WHERE slug=%s',(v['slug'],)).fetchone()['record'] for k,v in core.PROVIDERS.items()}
  def add(c):
   duplicate=core.duplicate(db,c)
   parts=db.execute('SELECT id FROM artworks WHERE current_institution_id=%s AND accession_number LIKE %s LIMIT 1',(c['institution_id'],c['accession']+'.%')).fetchone()
   if duplicate or parts:
    excluded.append({'key':c['key'],'reason':'Existing exact accession, source identity or accession part','existing':str((duplicate or parts)['id'])});return
   assert c['lo']<=c['hi']<=1970 and c['lo']!=0 and c['hi']!=0
   records.append(c)
  for preset,country,ids,reason in GROUPS:
   for oid in ids:
    o,rec=objects[oid]
    assert o['share_license_status']=='CC0' and not o.get('copyright') and not o.get('rights_and_reproductions')
    assert o['legal_status']=='accessioned' and not o['on_loan'] and not o.get('cover_accession_number')
    creators=[x for x in o.get('creators',[]) if x.get('use_in_caption') and x.get('role')!='publisher']
    maker='; '.join(' '.join(x for x in [cr.get('qualifier'),cr['description'].split(' (')[0],('('+cr['role']+')') if cr.get('role') not in (None,'artist') else None] if x) for cr in creators) or None
    key='cleveland-'+str(oid);lo,hi=o['creation_date_earliest'],o['creation_date_latest'];date=o['creation_date'];approx=any(x in date for x in ('c.','probably','possibly'))
    add({'key':key,'provider':'cleveland','object_id':str(oid),'accession':o['accession_number'],'preset':preset,
     'title':o['title'],'lo':lo,'hi':hi,'date_display':date,'precision':('circa' if lo==hi else 'circa_range') if approx else ('exact' if lo==hi else 'range'),
     'type':TYPE.get(o['type'],'unknown'),'country':country,'culture':'; '.join(o['culture']),'place_display':'; '.join(o['culture']),
     'maker':maker,'artist_id':None,'url':o['url'],'image_url':o['images']['web']['url'],'medium':o['technique'],'dimensions':o.get('measurements'),'credit':o['creditline'],
     'reason':reason,'object':o,'capture':rec,'institution_id':institutions['cleveland']['id'],'artwork_id':core.uid(key),'slug':'event-'+key,
     'geography_note':'Country association from the museum object origin. Qualified localities retained; no nationality inferred.',
     'scope_note':'One accession per object, not separate recto/verso entries. Source attribution qualifiers retained in object-level creator labels; no new artist identity or biography invented.'})
  for oid,preset,country,kind,reason in [(310001,'sahel','ML','sculpture','Dogon or Bozo staff with seated male leader, 16th–17th century, Mali; visual culture of the Sahel.'),(449711,'silk-roads','UZ','ceramic','Arabic-inscribed bowl made in present-day Uzbekistan, probably Samarqand, late 10th–11th century; material culture along the Silk Roads.')]:
   f=captures/('met-'+str(oid)+'.json');o=json.loads(f.read_bytes());rec=json.loads(f.with_suffix('.receipt.json').read_bytes());assert core.sha(f.read_bytes())==rec['sha256']
   assert o['isPublicDomain'] and o['primaryImage'];key='met-'+str(oid)
   add({'key':key,'provider':'met','object_id':str(oid),'accession':o['accessionNumber'],'preset':preset,'title':o['title'],
    'lo':o['objectBeginDate'],'hi':o['objectEndDate'],'date_display':o['objectDate'],'precision':'range','type':kind,'country':country,'culture':o['culture'],
    'place_display':', '.join(x for x in [o['country'],o['city']] if x),'maker':o['artistDisplayName'] or None,'artist_id':None,'url':o['objectURL'],'image_url':o['primaryImage'],
    'medium':o['medium'],'dimensions':o['dimensions'],'credit':o['creditLine'],'reason':reason,'object':o,'capture':rec,'institution_id':institutions['met']['id'],'artwork_id':core.uid(key),'slug':'event-'+key})
  countries=db.execute('SELECT to_jsonb(c) record FROM countries c WHERE code=ANY(%s) ORDER BY code',(list(core.COUNTRIES),)).fetchall()
  places={}
  for code,(name,_) in core.COUNTRIES.items():
   rows=db.execute('SELECT to_jsonb(p) record FROM places p WHERE country_code=%s AND name=%s',(code,name)).fetchall();assert len(rows)<=1
   if rows:places[code]=rows[0]['record']
 policies={}
 for k,p in core.PROVIDERS.items():
  if k=='met':
   evidence=core.ROOT/'docs/research/islamic-world-images-20260925/captures/met-policy-web.json'
   assert 'Creative Commons Zero' in evidence.read_text()
   policies[k]={'url':p['policy'],'capture':str(evidence.relative_to(core.ROOT)),'sha256':core.sha(evidence.read_bytes()),'rechecked_at':core.now(),'recheck':'Primary page opened through web tool 27 September 2026; policy unchanged. Direct HTTP returned 429.'}
  else:
   _,policies[k]=core.fetch(p['policy'],core.RUN/'captures'/(k+'-policy.html'))
 core.save(core.RUN/'plan.json',{'records':records,'institutions':institutions,'artist_preimages':[],'country_preimages':countries,'places':places,'policies':policies,'excluded_existing':excluded,'selection_bound':'Individually enumerated objects from bounded museum metadata queries; permission and dates validated before any image download. No current-display or publication claim.'})
 core.save(core.RUN/'plan-pin.json',{'sha256':core.sha((core.RUN/'plan.json').read_bytes())})
 print('Pinned',len(records),'new objects; excluded',len(excluded),'existing identities.')
 for c in records:print(c['preset'],c['key'],c['title'],c['date_display'],c['country'])

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['plan','prepare','backup','apply','verify']);args=p.parse_args()
 (plan if args.phase=='plan' else getattr(core,args.phase))()
