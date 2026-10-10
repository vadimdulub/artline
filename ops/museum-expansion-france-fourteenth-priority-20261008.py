"""Read-only ranking of remaining French museum source leads; not an import plan."""
import collections,csv,hashlib,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('m',Path(__file__).with_name('museum-expansion-20261006.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
RUN=m.RUN/'native/france-fourteenth-minimum-20261008'
def ref(p):return dict(path=str(p.relative_to(m.ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def date_lead(row):
    raw=(row.get('Millesime_de_creation') or '').strip()
    if re.fullmatch(r'\d{3,4}',raw):return 100<=int(raw)<=1970
    match=re.fullmatch(r'(\d{3,4})\s*[-–]\s*(\d{3,4})',raw)
    if match:return 100<=int(match[1])<=int(match[2])<=1970
    if re.fullmatch(r'(?:avant\s+\d{3,4}|\d{3,4}\s+avant)',raw,re.I):return int(re.search(r'\d+',raw)[0])<=1971
    lo,hi,_=m.french_period(row.get('Periode_de_creation'))
    if lo is None or hi>1970:return False
    return not raw or bool(re.fullmatch(r'(?:vers\s+\d{3,4}|\d{3,4}\s+vers)',raw,re.I))
def main():
    dest=RUN/'priority-leads-001.json';assert not dest.exists();coverage=m.RUN/'museum-coverage-after-wave-68.csv'
    with coverage.open(newline='') as fp:targets={v['slug'].removeprefix('joconde-').upper():v for v in csv.DictReader(fp) if v['slug'].startswith('joconde-') and v['kind']=='museum' and not v['canonical_institution_id'] and v['status']!='archived' and int(v['eligible_works'])<100}
    assert ref(m.SNAPSHOT)['sha256']==m.SNAPSHOT_SHA;csv.field_size_limit(8_000_000);rows=[]
    with m.SNAPSHOT.open(encoding='utf-8-sig',newline='') as fp:
        for v in csv.DictReader(fp,delimiter='|'):
            if v['Code_Museofile'] not in targets or not date_lead(v):continue
            if not v['Titre'].strip() or not v['Numero_inventaire'].strip():continue
            kind,reason=m.joconde_object_kind(v,False)
            if reason:kind,reason=m.joconde_object_kind(v,True)
            if reason:continue
            rows.append(v)
    ids=sorted({v['Reference'] for v in rows})
    with m.connect() as db,db.transaction():
        assert db.execute('SHOW transaction_read_only').fetchone()['transaction_read_only']=='on'
        ext=db.execute("SELECT entity_id::text,external_id FROM external_identifiers WHERE entity_type='artwork' AND external_id=ANY(%s) AND scheme ILIKE '%%joconde%%' ORDER BY external_id,entity_id",(ids,)).fetchall()
        citations=db.execute("SELECT entity_id::text,source_record_id,source_url FROM citations WHERE entity_type='artwork' AND source_record_id=ANY(%s) AND source_url LIKE '%%/joconde/%%' ORDER BY source_record_id,entity_id",(ids,)).fetchall()
    known={v['external_id'] for v in ext}|{v['source_record_id'] for v in citations};by=collections.defaultdict(list)
    for v in rows:
        if v['Reference'] not in known:by[v['Code_Museofile']].append(v)
    ranked=[]
    for code,values in by.items():
        museum=targets[code];ranked.append(dict(code=code,institution_id=museum['id'],name=museum['name'],eligible_now=int(museum['eligible_works']),linked_now=int(museum['works']),remaining_minimum=100-int(museum['eligible_works']),unreviewed_date_form_leads=len(values),sample=[{k:v[k] for k in ['Reference','Titre','Auteur','Millesime_de_creation','Periode_de_creation','Domaine','Materiaux_techniques','Statut_juridique','Localisation']} for v in values[:3]]))
    ranked.sort(key=lambda v:(-min(v['unreviewed_date_form_leads']/v['remaining_minimum'],10),-v['unreviewed_date_form_leads'],v['code']))
    m.save(dest,dict(at=m.now(),read_only=True,database_writes=0,museums=ranked,source_rows_considered=len(rows),known_source_ids=len(known),dependencies=[ref(p) for p in [coverage,m.SNAPSHOT,Path(__file__).resolve(),Path(m.__file__).resolve()]],policy='Research prioritization only. Date and broad object-form leads are not approved objects, fresh holdings, physical duplicates or custody determinations. No quota-based additions. All candidates require selected current source capture, museum-name reconciliation and individual identity/date review. Existing access holds remain in force.'))
    print(json.dumps(dict(museums=len(ranked),top=[{k:v[k] for k in ['code','name','eligible_now','unreviewed_date_form_leads']} for v in ranked[:15]]),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
