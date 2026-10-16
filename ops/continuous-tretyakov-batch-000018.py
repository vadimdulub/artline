#!/usr/bin/env python3
"""Bounded official Tretyakov metadata delivery; uses established production transaction helper."""
import importlib.util,inspect,json,re,csv,gzip,sys,fcntl
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('prior',ROOT/'ops/continuous-greek-batch-000015.py');prior=importlib.util.module_from_spec(s);s.loader.exec_module(prior)
h=prior.h;E=ROOT/'docs/research/continuous-production-20261011/batches/000018';R=Path.home()/'Library/Application Support/Artline/continuous-research/batches/000018';h.OP='continuous-tretyakov-20261011-b000018';h.RUN=E;h.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/h.OP
FIELD='continuous_museum_batch_000018';PHASE='selected';MUSEUM='Tretyakov Gallery';IID='0f715d93-a36c-55b7-a690-1d573d64406f';h.SCHEMES['tretyakov']=['museum-native-tretyakov-object','tretyakov-object','continuous-tretyakov-object']
h.museums=lambda:{MUSEUM:('wikimedia-museum-q183334','https://www.tretyakovgallery.ru')}
freshspec=importlib.util.spec_from_file_location('original_helper',ROOT/'ops/india-300-delivery-20261011.py');fresh=importlib.util.module_from_spec(freshspec);freshspec.loader.exec_module(fresh)
src=inspect.getsource(fresh.apply).replace('india_minimum_300_museum_coverage_20261011',FIELD).replace("assert sum(not r['before'] for r in rows)>=300","assert 1<=len(rows)<=50")
src=src.replace("  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'","  inventory=db.execute('SELECT id::text FROM artworks WHERE current_institution_id=%s AND accession_number=ANY(%s)',(rows[0]['institution_id'],[r['accession_number'] for r in rows])).fetchall();assert {x['id'] for x in inventory}<={r['artwork_id'] for r in rows if r['before']},'Concurrent object insert; replan'\n  db.execute('SELECT id FROM artworks WHERE id=ANY(%s::uuid[]) ORDER BY id FOR UPDATE'")
exec(compile(src,str(ROOT/'ops/india-300-delivery-20261011.py'),'exec'),h.__dict__)
src=inspect.getsource(h.plan).replace('bounded Greek batch 000015','bounded Tretyakov batch 000018');exec(compile(src,__file__,'exec'),h.__dict__)
def stage():
 if (E/PHASE/'plan-pin.json').exists():return
 h.save(E/'production-target-before-plan.json',prior.target())
 registry=Path('/Users/vadimdulub/Downloads/GLOBAL_MUSEUM_SOURCE_REGISTRY.csv');rs=list(csv.DictReader(registry.open()));assert len(rs)==111
 holds=[ROOT/'docs/research/continuous-production-20261011/batches/000003/source-access-holds.json',ROOT/'docs/research/continuous-production-20261011/batches/000017/source-register.json']
 h.save(E/'source-register.json',dict(at=h.now(),registry_path=str(registry),registry_sha256=h.sha(registry.read_bytes()),registry_records=len(rs),source=next(x for x in rs if x['source_id']=='tretyakov_gallery'),policy='docs/ARTLINE_IMAGE_USE.md#explicit-russian-museum-extension--21-september-2026',prior_holds={str(p.relative_to(ROOT)):h.load(p) for p in holds},image_selection='No images selected until exact physical-version reconciliation; no thumbnails attached'))
 leads=h.load(E/'discovered-objects.json');records=[];held=[]
 with h.connect() as db:
  aliases=[dict(x) for x in db.execute("SELECT a.id::text,a.display_name,al.alias FROM artists a LEFT JOIN artist_aliases al ON al.artist_id=a.id WHERE a.display_name ILIKE '%%rublev%%' OR a.display_name ILIKE '%%vasnetsov%%' OR a.display_name ILIKE '%%ushakov%%' OR a.display_name ILIKE '%%dionys%%' OR a.display_name ILIKE '%%simakov%%' OR a.display_name ILIKE '%%ivash%%'")];h.save(E/'creator-global-review.json',dict(at=h.now(),candidates=aliases,policy='Anonymous or qualified historical makers remain object-level labels; no invented painter'))
  for row in leads:
   k=row['source_id'];soup=BeautifulSoup((ROOT/row['evidence_file']).read_bytes(),'html.parser');desc=' '.join(t.get_text(' ',strip=True) for t in soup.select('.text-block-item'));label=row['creator'];date=row['date'];fields=row['fields'];acc=fields.get('Инвентарный номер')
   # Remove the source's explicit inventory prefix for global accession reconciliation only.
   plain=re.sub(r'^Инв\.?\s*','',acc or '');globalacc=[dict(x) for x in db.execute("SELECT id::text,title,current_institution_id::text,accession_number FROM artworks WHERE accession_number=ANY(%s)",([acc,plain],))]
   if 'Рублев' in (label or ''):
    held.append(dict(record=row,reason='Global Rublev catalogue contains translated subject/version candidates; exact physical composition crosswalk required. Preserve museum narrative attribution uncertainty.',global_accession_matches=globalacc));continue
   if date=='XX век' or not acc:
    held.append(dict(record=row,reason='Cross-cutoff century or missing inventory requires editorial identity/date review',global_accession_matches=globalacc));continue
   year=int(date) if re.fullmatch(r'\d{4}',date) else None
   centuries={'XVII век':(1601,1700),'XVI век':(1501,1600),'XV век':(1401,1500),'XIV век':(1301,1400),'XIX век':(1801,1900),'XVIII век':(1701,1800)}
   lo,hi=(year,year) if year else centuries.get(date,(None,None))
   if lo is None:
    held.append(dict(record=row,reason='Source date wording retained for date-range review; no invented interval',global_accession_matches=globalacc));continue
   if hi>1970:continue
   if globalacc and (len(globalacc)>1 or globalacc[0]['current_institution_id']!=IID):
    held.append(dict(record=row,reason='Global accession collision requires exact object/version crosswalk',global_accession_matches=globalacc));continue
   # Named makers with untranslated titles must first reconcile globally by artist.
   artist=None
   if label and 'Васнецов' in label:
    held.append(dict(record=row,reason='Named Vasnetsov work: global artist/title/composition reconciliation queued',global_accession_matches=globalacc));continue
   if label and not any(t in label.lower() for t in ['неизвест','мастер','школ','дионис']):
    held.append(dict(record=row,reason='Creator global authority and translated-work identity need further reconciliation',global_accession_matches=globalacc));continue
   if label and 'дионис' in label.lower():
    held.append(dict(record=row,reason='Dionysius global translated-work/version reconciliation pending',global_accession_matches=globalacc));continue
   rc=row['evidence'];rc['retrieved_at']=rc['at'];medium='; '.join(fields[x] for x in ['Материал','Техника'] if x in fields)
   records.append(dict(provider='tretyakov',source_id=k,museum=MUSEUM,title=row['title'],date_display=date,year_start=lo,year_end=hi,date_decision='eligible',source_type='painting',creator_label=label,creator_link_hold=True,verified_existing_id=globalacc[0]['id'] if globalacc else None,accession_number=acc,medium=medium,dimensions=fields.get('Размер'),source_url=row['source_url'],evidence=rc,evidence_file=row['evidence_file'],raw=dict(original_title=None,source_fields=fields,narrative=desc),identity_review='Official physical inventory, complete original title, dimensions, date and narrative preserved. No current display claim. Anonymous makers remain unlinked.'))
 h.save(E/'research-holds.json',dict(at=h.now(),rows=held));h.save(E/PHASE/'source-records.json.gz',records);h.plan(PHASE)
 p,pin=h.pinned(PHASE);print('SELECTED',[(x['source_id'],x['title'],bool(x['before'])) for x in p['records']])
def deliver():
 p,pin=h.pinned(PHASE);assert p['records']
 with h.connect() as db:
  notes=db.execute("SELECT entity_id::text,evidence_note::jsonb->>'plan_sha256' pin FROM citations WHERE field_name=%s AND entity_id=ANY(%s::uuid[])",(FIELD,[r['artwork_id'] for r in p['records']])).fetchall()
 if notes:
  assert len(notes)==len(p['records']) and all(x['pin']==pin for x in notes);assert (h.BACKUP/PHASE/'locked-before.json.gz').exists();return
 import subprocess
 rc=json.loads(subprocess.check_output(['gcloud','sql','backups','describe','1791735810546','--instance=artline-postgres','--project=artline-508319','--account=vadim@alingva.com','--format=json'],text=True));assert rc['status']=='SUCCESSFUL';h.save(E/'cloud-sql-backup.json',rc);h.save(h.BACKUP/'cloud-sql-backup.json',rc)
 h.save(E/'production-target-before-write.json',prior.target());h.apply(PHASE)
if __name__=='__main__':
 R.mkdir(parents=True,exist_ok=True)
 with (R/'metadata-worker.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);dict(stage=stage,deliver=deliver)[sys.argv[1]]()
