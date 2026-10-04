import sys,importlib.util,json,time
from pathlib import Path
import psycopg
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'ops'))
s=importlib.util.spec_from_file_location('research',R/'ops/research-early-books-20260923.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
r.OUT=R/'docs/research/pre1850-books-20261001'
assert not (r.OUT/'plan.json').exists(), 'Preserve completed campaign evidence; use a new campaign for new research.'
titles='''Refutation of the Sects|Life of Mashtots|History of the Armenians|History of the Caucasian Albanians|Ashkharatsuyts|Book of Questions (Gregory of Tatev)|The History of Vardan and the Armenian War|Datastanagirk|The Key of Truth|The City of the Sun|New Atlantis|Utopia (book)|The Blazing World|The Description of a New World, Called The Blazing-World|The Unfortunate Traveller|The English Rogue|The Princess of Cleves|The Adventures of Telemachus|Vathek|The Castle of Otranto|The Monk|The Mysteries of Udolpho|The Italian (novel)|The Old English Baron|The Recess|The Female Quixote|Oroonoko|Love-Letters Between a Nobleman and His Sister|The Pilgrim's Progress|The Holy War|Religio Medici|Hydriotaphia, Urn Burial|The Garden of Cyrus|Pseudodoxia Epidemica|Anatomy of Melancholy|Micrographia|Opticks|De Magnete|Discourses and Mathematical Demonstrations Relating to Two New Sciences|Harmonices Mundi|Astronomia nova|Sidereus Nuncius|Mundus Subterraneus|Musurgia Universalis|Arithmologia|The Sceptical Chymist|Exercitatio Anatomica de Motu Cordis et Sanguinis in Animalibus|The Advancement of Learning|Novum Organum|New Science|Scienza Nuova|The New Organon|Tableau économique|On Crimes and Punishments|The Law of Peoples|Perpetual Peace: A Philosophical Sketch|The Social Contract|The Spirit of Law|An Essay on Man|The Dunciad|The Rape of the Lock|The Seasons (poem)|The Task (poem)|Aureng-zebe|All for Love (play)|The Orphan|Venice Preserv'd|The Mourning Bride|The Way of the World|The Conscious Lovers|She Stoops to Conquer|The School for Scandal|The Rivals|The Beggar's Opera|The Busie Body|The Wonder: A Woman Keeps a Secret|A Bold Stroke for a Wife|The Gamester|The Tragedy of Tragedies|The London Merchant'''.split('|')
with psycopg.connect('postgres://localhost/artline',options='-c default_transaction_read_only=on') as db: existing={a:b for a,b in db.execute('select source_id,id from book_records')}
candidates=[]
for offset in range(0,len(titles),12):
 data,proof=r.capture('en.wikipedia.org',{'action':'query','titles':'|'.join(titles[offset:offset+12]),'redirects':1,'prop':'pageprops|extracts|revisions','ppprop':'wikibase_item','exintro':1,'explaintext':1,'exlimit':20,'rvprop':'ids|timestamp'})
 for p in data['query']['pages']:
  q=p.get('pageprops',{}).get('wikibase_item')
  if q and not p.get('missing'): candidates.append({'title':p['title'],'qid':q,'extract':p.get('extract',''),'revision':p.get('revisions',[{}])[0].get('revid'),'source':proof,'existing':existing.get(q)})
 time.sleep(5)
wanted=sorted({i['qid'] for i in candidates if not i['existing']});entities={}
for offset in range(0,len(wanted),40):
 data,proof=r.capture('www.wikidata.org',{'action':'wbgetentities','ids':'|'.join(wanted[offset:offset+40]),'props':'info|labels|descriptions|claims','languages':'en'})
 entities.update({q:{'entity':e,'source':proof} for q,e in data['entities'].items()});time.sleep(5)
for i in candidates: i['wikidata']=entities.get(i['qid'])
r.OUT.mkdir(parents=True,exist_ok=True);(r.OUT/'candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2))
print(json.dumps({'candidates':len(candidates),'missing':[(i['title'],i['qid']) for i in candidates if not i['existing']]},indent=2))
