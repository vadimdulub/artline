import runpy,collections,re,unicodedata
m=runpy.run_path('ops/balkans-deep-20261011.py');h=m['h'];RUN=m['RUN']
s=h.load(RUN/'selection-wave1.json');names={f['creator'].strip()for f in s['records']if f['creator']}
# Source Cyrillic forms are retained in facts; these bilingual authority leads only scope duplicate research.
names.update(['Fernand Leger','Fernand Léger','Pablo Picasso','Emil Filla','Eugene Brands','Eugène Brands','Jan Stursa','Jan Štursa','Frantisek Muzika','František Muzika','Petar Lubarda','Lazar Licenoski','Lazar Ličenoski','Dimitar Avramovski Pandilov','Borko Lazeski','Dimitar Kondovski','Mile Korubin','Vojtech Preissig','Vojtěch Preissig','Oscar Dalvit','Marcello Mascherini','Lorenzo Guerrini','Ivan Kozaric','Ivan Kožarić','Elisaveta Konsulova-Vazova','Nikola Avramov','Georgi Baev','Nikola Tanev','Konstantin Shtarkelov','Nenko Balkanski','Dobri Dobrev','Vasil Barakov','Franz Stuck','Ivan Aivazovsky','Zlatyu Boyadzhiev','Zahari Zograf','Zahariy Zograph','Vladimir Dimitrov'])
def key(v):return re.sub(r'[^a-zа-яѓќљњџјѕ]+','', ''.join(c for c in unicodedata.normalize('NFKD',v.lower())if not unicodedata.combining(c)))
with m['d'].connect()as db:
 ars=db.execute("SELECT id::text,display_name FROM artists WHERE status<>'archived'").fetchall()
 aliases=db.execute('SELECT artist_id::text,alias FROM artist_aliases').fetchall()
 needles={key(n)for n in names};matched={a['id']:a for a in ars if key(a['display_name'])in needles}
 for a in aliases:
  if key(a['alias'])in needles:
   matched[a['artist_id']]=next(x for x in ars if x['id']==a['artist_id'])
 works=db.execute("SELECT to_jsonb(a)artwork,aa.artist_id::text FROM artwork_artists aa JOIN artworks a ON a.id=aa.artwork_id WHERE aa.artist_id=ANY(%s::uuid[])AND a.status<>'archived'",(list(matched),)).fetchall()
 ids=[x['artwork']['id']for x in works]
 citations=db.execute("SELECT to_jsonb(c)v FROM citations c WHERE entity_type='artwork'AND entity_id=ANY(%s::uuid[])",(ids,)).fetchall()
 held=h.load(m['BACKUP']/'wave1-plan.json.gz')['held'];hids=list({i for x in held for i in x['ids']})
 held_creators=db.execute('SELECT aa.artwork_id::text,a.id::text,a.display_name FROM artwork_artists aa JOIN artists a ON a.id=aa.artist_id WHERE aa.artwork_id=ANY(%s::uuid[])',(hids,)).fetchall()
h.save(RUN/'identity-authority-scope.json.gz',dict(at=h.now(),artists=list(matched.values()),artworks=works,citations=[x['v']for x in citations],held_creators=held_creators))
print('AUTHORITY',len(matched),'ARTWORKS',len(works))
for a in matched.values():
 ws=[x['artwork']for x in works if x['artist_id']==a['id']]
 print(a['display_name'],len(ws))
 for w in ws:
  if len(ws)<25 or any(h.norm(f['title'])in h.norm(w['title'])or h.norm(w['title'])in h.norm(f['title'])for f in s['records']if f['creator']and key(f['creator'])==key(a['display_name'])):
   print(' ',w['id'],w['title'],w['date_display'],w['current_location_text'])
