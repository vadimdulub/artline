"""Protect focused comparison objects and record why shared subject names are distinct."""
import importlib.util,json,re
from pathlib import Path
z=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-rhodes-identity-v2-20261009.py'));i=importlib.util.module_from_spec(z);z.loader.exec_module(i);m=i.m;RUN=i.RUN
x=m.load(RUN/'production-identity-002.json.gz');ids={a['id']for c in x['comparisons']for a in c['hits']};links={}
for v in x['state']['links']:links.setdefault(v['artwork_id'],[]).append(v['display_name'])
for a in x['state']['artworks']:
 c=a['unlinked_creator_label']or','.join(links.get(a['id'],[]))
 if re.search('semert|σεμερτ|eggon|εγγονο|asteriad|αστεριαδ|arliot|αρλιωτ|tarsoul|ταρσουλ|orpheus|colossus',c+' '+a['title'],re.I):ids.add(a['id'])
ids=sorted(ids)
with i.prod.connect()as db,db.transaction():
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snap=i.s.snapshot(db,ids)
m.save(RUN/'subject-comparators-001.json.gz',dict(at=m.now(),ids=ids,snapshot=snap,identity_reference=i.s.ref(RUN/'production-identity-002.json.gz'),script_reference=i.s.ref(Path(__file__).resolve()),assessment='The four exact TehnisRodou source IDs already exist and are skipped. Existing Porro1576 Rhodes leaf differs from source4052 probable1620 impression by source edition and dimensions. Harry John Johnson Rhodes1845 is a different creator/work from Mallet,Turner-derived and LeBrun prints. Existing Heemskerck Colossus1570/1572 differ from Mallet17th/18th-century print. Modern Nicosia/Famagusta views by named19th/20th-century artists differ from anonymous historical map sheets1713/circa1595. Existing Tarsouli Cyprus watercolours/prints depict different buildings/costumes from selected Greek costume plates. Existing Asteriadis landscapes/stilllife differ by dates,materials,dimensions and subjects from Attica1948. Semertzidis Parnitha and Gounari portrait differ from new dated prints/studies. Demonstrations by Katsikogiannis/Sikeliotis differ from Semertzidis prints. Three modern works titled I are false positives from abbreviated I[sle]s, not matches. Unknown-date leads and held source versions remain excluded. No authority merge or object migration.',read_only=True));print(json.dumps(dict(protected_comparators=len(ids))),flush=True)
