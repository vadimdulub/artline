"""Source-note maker aliases and translated titles for selected physical review."""
import copy,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('museum-expansion-italy-second-identity-20261008.py'));i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
m=i.m;RUN=i.RUN;ref=i.ref;checked=i.checked
ESTENSE=[11,42,59,65,70,76,78,83,84,87,94,98,104,110,123,124,125,127,133,139,142,147,148,163,164,170,174,175,176,177]
ALBERTINA=[331]+[n for n in range(332,368) if n not in [345,352,362,365,366,367]]
CORSINI=[422,428,443,480,488,504]
FANO=[533,542,544,557,558,567,568,570,573,574,586,587,589,590,599,606,607,608,609,610,611,612,613,615,616,621]
SELECTED=ESTENSE+ALBERTINA+CORSINI+FANO
EXTRA={11:['piazzetta','longhi'],42:['albani'],59:['mignard','nanteuil','mazarin'],65:['sarto','filippi','bastianino'],76:['bronzino'],83:['brueghel','bruegel'],84:['saftleven','camphuyzen','teniers'],87:['schoevaerdts','schoevaerts'],94:['ravensteyn','ravensteyen','potter'],98:['pesari','romani'],123:[],124:['francken'],125:['teniers'],133:['abate','abbate'],139:['rubens','dyck','vorsterman'],142:['guercino','barbieri'],163:['wouwerman','wouverman','wouwermans'],164:['wouwerman','wouverman','wouwermans'],170:['carracci'],174:['crespi'],335:['vacca'],422:['neefs','neeffs','neyts','francken'],428:['domenichino','zampieri','lanfranco','alberti','barbalonga'],443:['facchetti','fachetti','commodi'],558:['giaquinto','gianquinto'],570:['bellucci'],616:['galli','bibiena'],621:['ceccarini']}
TITLE_ADDITIONS={11:['The Scribe','The Writer'],42:['Aurora Abducting Cephalus','Aurora and Cephalus'],59:['Portrait of Cardinal Mazarin'],65:['Saint James of Compostela'],70:['Landscape with Abraham leading Isaac to the Sacrifice'],76:['Portrait of Cosimo I de Medici'],78:['Landscape with Elijah fed by Angels'],83:['Tower of Babel'],84:['Cattle Fair'],87:['Fair with a Picture Seller'],94:['Stable Interior with Figures and Animals'],98:['Saints and a Storm'],104:['Portrait of Emanuele Filiberto of Savoy Prince of Carignano'],110:['View of a Bay'],123:['Witchcraft Scene'],124:['Seven Works of Mercy'],125:['Dance outside an Inn','Peasants Dancing outside an Inn'],127:['Market in the Forum Boarium in Rome'],133:['Prasildo and the Old Man'],139:['Job Tormented by his Wife and Demons'],142:['Saint Mark the Evangelist'],147:['Portrait of Marquis Giovanni Calori Cesis'],148:['Portrait of Marquis Giovanni Calori Cesis'],163:['Horsemen'],164:['Horsemen Refreshing with Peasants'],170:['Madonna Enthroned with Saints Francis, John the Baptist and Matthew'],174:['Saint Clare'],175:['Saint Bernardino of Siena and an Angel'],176:['Saint Anthony of Padua and a Capuchin Saint'],177:['Saint Vincent Ferrer and Saint Francis of Paola'],422:['Interior of Antwerp Cathedral by Day'],428:['Lucina, Norandino and the Ogre'],443:['Portrait of Prince Michele Peretti'],480:['Rinaldo and Armida at the Mirror'],488:['Allegory'],504:['Sculptor and Other Figures'],533:['Saul and the Witch of Endor summon the Spirit of Samuel'],544:['Saint Clare Repels the Saracens'],557:['Portrait of Nicola Ferretti Gabuccini'],558:['Saint Dominic and the Angel'],570:['Allegory of Love'],586:['Altar Boy'],599:['View of the City of Fano'],615:['Portrait of Francesca de Suez'],621:['Bishop Blessing']}
original_terms=i.terms
def rows():
 result=[]
 for row in m.load(RUN/'native-candidates-001.json.gz')['rows']:
  if row['number'] not in SELECTED:continue
  assert row['state']=='candidate';r=copy.deepcopy(row);r['facts']['comparison_extra_terms']=EXTRA.get(r['number'],[]);r['facts']['titles']=sorted(set(r['facts']['titles'])|set(TITLE_ADDITIONS.get(r['number'],[])));result.append(r)
 assert len(result)==len(SELECTED)==len(set(SELECTED));return result
def terms(f):return sorted(set(original_terms(f))|set(f.get('comparison_extra_terms',[])))
i.terms=terms
def main():
 dest=RUN/'selected-identity-002.json.gz';assert not dest.exists();rs=rows();params=i.params_for(rs)
 with m.connect() as db,db.transaction():
  db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ');state=i.queries(db,params)
  citations=[v['row'] for v in db.execute("SELECT to_jsonb(c) row FROM citations c WHERE entity_type='artwork' AND entity_id=ANY(%s::uuid[]) ORDER BY entity_id,id",(state['artwork_ids'],))]
 comps=i.comparisons(rs,state);m.save(dest,dict(at=m.now(),rows=rs,params=params,state=state,comparisons=comps,script_reference=ref(Path(__file__).resolve()),original_identity_reference=ref(RUN/'native-identity-001.json.gz'),policy='Search-only source-note former/related maker names and English title translations. These are not catalogue attributions or replacement titles. Every hit still requires physical identity review.',read_only=True))
 m.save(RUN/'selected-citations-002.json.gz',dict(at=m.now(),identity_reference=ref(dest),citations=citations,read_only=True))
 print(json.dumps(dict(selected=len(rs),scope=len(state['artwork_ids']),hits=sum(len(v['hits']) for v in comps),source_hits=sum(len(v['source_hits']) for v in comps))),flush=True)
if __name__=='__main__':main()
