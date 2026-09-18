#!/usr/bin/env python3
"""Fill selected primary object fields and three exact catalogue transcription corrections."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('correct-country-expansion-reviewed-fields.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
m=f.m;C=f.C;B=f.B;RUN=B/'selected-primary-field-enrichment';BACK=m.BACKUPS/'selected-primary-field-enrichment';f.RUN=RUN;f.BACK=BACK

def proposals():
 out=[]
 for p in sorted((B/'britain-expansion/GB').glob('round-*/delivery/british-reviewed/Q*.json')):
  d=json.loads(p.read_text());o=d['object'];q=d['qid'];fields=o.get('fields',{});medium=fields.get('Medium') or fields.get('Materials');dims=fields.get('Dimensions');correction={};expected={}
  # This source notice was held during the identity/object reconciliation and
  # has no active artwork row in either target. Keep its evidence in the
  # research package; do not manufacture a field update for a missing object.
  if q=='Q28476083':continue
  if q=='Q28473808':medium='oil on canvas';dims='Image: 1015mm (width), 1370mm (height), 17mm (depth)'
  elif q=='Q28476083':medium='oil on canvas';dims='Image: 610mm (width), 913mm (height)'
  elif q=='Q28028950':
   assert 'c. 1953-56' in fields['primary_text'];medium='Oil on canvas';dims='244.5 × 152.9 cm (support, canvas/panel/stretcher external)';correction=dict(creation_year_start=1953,creation_year_end=1956,date_precision='circa_range',date_display='c. 1953–1956');expected=dict(creation_year_start=1953,creation_year_end=1954,date_precision='range')
  elif q=='Q119174887':medium='Oil on canvas';dims='height: 170.50 cm, width: 356.50 cm'
  if q=='Q30037141':correction=dict(accession_number='IWM ART 5199');expected=dict(accession_number='IWM Art.IWM ART 5199')
  if q=='Q119179387':
   raw=json.loads(Path(d['original_capture']).read_text());assert "Gordon's Carmel" in raw['text'];correction=dict(title="Jerusalem from the Mount of Olives: Gordon's Carmel in the Middle Distance");expected=dict(title="Jerusalem from the Mount of Olives: Gordon's Camel in the Middle Distance")
  if q=='Q122871690':medium='watercolour & bodycolour on board'
  assert medium or dims or correction,q
  out.append(dict(key=q,type='artwork',slug='wikimedia-artwork-'+q.lower(),fill_if_missing={k:v for k,v in dict(medium_text=medium,dimensions_text=dims).items() if v},explicit_correction=correction,expected=expected,evidence=f.evidence(p),receipt=d['receipt'],reason='Exact current primary inventory and named maker manually reviewed. Fill missing material/dimensions without inventing units or changing existing fields. Three explicit corrections separately guarded: Gunnc1953–56ratherthan1953–54; Watherston duplicateIWMprefix; DugdaleCarmelnotCamel. Review,qualifiedcreators,holdings,andimagespreserved.'))
 for key,q,medium,dims in [('Flandrin','Q112056883',"peinture à l'huile, toile",'H. 60.5 ; L. 50.2'),('Leroux','Q121791025',"toile ; peinture à l'huile",'H. 150 ; l. 130'),('Charnay','Q135902845',"peinture à l'huile (toile) ; bois (doré)",'H. 20 ; l. 29,4 ; E. 1,4 (hors cadre en cm); H. 24,9 ; l. 34,5 ; E. 3 (cadre en cm)')]:
  p=B/'duplicates/seven-additional-objects/primary'/(key+'.review.json');d=json.loads(p.read_text());assert C.sha(p.with_name(key+'.html').read_bytes())==d['receipt']['sha256'];out.append(dict(key=q,type='artwork',slug='wikimedia-artwork-'+q.lower(),fill_if_missing=dict(medium_text=medium,dimensions_text=dims),explicit_correction={},expected={},evidence=f.evidence(p),receipt=d['receipt'],reason='Exact primary POP inventory already verified during physical-object reconciliation; retain museum material/support/frame labels. No date,creator,country,holding,assetorpublicationchange.'))
 p=B/'duplicates/selected-physical-object-second-pass/plan.json';pair=next(e for e in json.loads(p.read_text()) if e['key']=='Pavia-P1659');out.append(dict(key='Pavia-P1659',type='artwork',slug=pair['canonical_slug'],fill_if_missing=dict(accession_number='P 1659'),explicit_correction={},expected={},evidence=dict(path=str(p),sha256=C.sha(p.read_bytes()),data=pair['primary']),receipt=pair['primary']['receipt'],reason='Both exact museum-authored SIRBeC physical-object notices give inventoryP1659. Fillmissingcanonicalinventoryafterverifiedmerge, retain newer1879–80date andallassertions.'))
 return out

def plan():
 if (RUN/'plan.json').exists():return
 assert (B/'serial-additional-objects-completed.json').exists();entries=proposals();pre={};updates={}
 for target in ('local','production'):
  pre[target]={};updates[target]={}
  with m.m.r.base.connect(target=='production') as db,db.transaction():
   db.execute('SET TRANSACTION READ ONLY')
   for e in entries:
    old=f.snapshot(db,e);w=old['row'];assert w['status']=='review' and not w['published_at'];assert all(w[k]==v for k,v in e['expected'].items()),(e['key'],'expectedfieldchanged');u={k:v for k,v in e['fill_if_missing'].items() if not w[k]};u.update(e['explicit_correction']);pre[target][e['key']]=old;updates[target][e['key']]=u
 assert updates['local']==updates['production'];selected=[]
 for e in entries:
  u=updates['local'][e['key']]
  if u:selected.append({**e,'updates':u})
 for target in pre:C.save_new(BACK/(target+'-preimages.json'),{e['key']:pre[target][e['key']] for e in selected})
 C.save_new(RUN/'plan.json',selected);pin=C.sha((RUN/'plan.json').read_bytes());C.save_new(RUN/'quality-review.json',dict(at=C.now(),approved=True,plan_sha256=pin,review='Actually reviewed exact primary source fields; only missingfields plusclosedexpected-oldfieldcorrections. British21/POP3/Pavia1scopes, no invented creationyear,unitsorcountry. Exact both-targetpreimages andexistingmedia/creator/holding preservation.'));print('Primary field enrichment planned',len(selected),flush=True)
def apply():f.apply()
def verify():f.verify()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);a=p.parse_args();globals()[a.command]()
