#!/usr/bin/env python3
"""Revisit formatting holds using exact POP biographies and structured SMK dates.

Preserve the original twenty round plans. Uncertain Tate lives and unqualified
historical Flemish-to-modern-country mappings remain held.
"""
import argparse,importlib.util,json,re
from pathlib import Path
s=importlib.util.spec_from_file_location('c',Path(__file__).with_name('apply-closed-identity-countries.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
ORIGINAL=c.RUN;RUN=ORIGINAL/'primary-citation-recovery';SOURCES=ORIGINAL/'primary-citation-followup-sources';CORE=c.CORE
c.RUN=RUN;c.SOURCE='overnight-recovered-primary-country-citations-20260913';c.m.BACKUPS=c.m.BACKUPS/'primary-country-citation-recovery'

def proof(a,citations):
 good=[]
 for ct in citations:
  match=re.search(r'source biography:\s*([^;]+?)\. Source authority ID:',ct['evidence_note'] or '')
  if 'pop.culture.gouv.fr/' in (ct['source_url'] or '') and match:
   expected=rf"{re.escape(a['display_name'])}\s*\({a['birth_year']}\s*[-–—]\s*{a['death_year']}\)"
   if re.fullmatch(expected,match[1].strip()):good.append(ct)
 for path in SOURCES.glob('Q*.json'):
  if path.name.endswith(('.raw.json','.receipt.json')):continue
  d=json.loads(path.read_text())
  if d['artist']['slug']!=a['slug']:continue
  receipt=json.loads(path.with_suffix('.receipt.json').read_text());assert CORE.sha(path.with_suffix('.raw.json').read_bytes())==receipt['sha256']
  ids={re.search(r'Source authority ID: (\d+_person)',ct['evidence_note'])[1] for ct in citations if re.search(r'Source authority ID: (\d+_person)',ct['evidence_note'] or '')}
  for person in d['creators']:
   if person['creator_lref'] not in ids:continue
   name=' '.join((person.get('creator_forename',''),person.get('creator_surname','')))
   if c.m.f.names.namekey(name)!=c.m.f.names.namekey(a['display_name']):continue
   if tuple(int(person[k][:4]) for k in ('creator_date_of_birth','creator_date_of_death'))!=(a['birth_year'],a['death_year']):continue
   good.append(dict(source_url=receipt['url'],field_name='museum_creator_record',source_record_id=person['creator_lref'],structured_primary_creator=person,receipt=receipt,original_citations=citations,identity_policy='Exact museum person identifier, full source name and structured closed life years. January1 placeholders are not imported as exact day/month dates.'))
 return good
c.primary_proof=proof

def plan():
 folder=RUN/'round-01'
 if not (folder/'research.json').exists():
  proposals=json.loads((ORIGINAL/'primary-citation-followup-candidates.json').read_text());held=[];selected=[]
  for p in proposals:
   q=p['candidate']['qid']
   if q in {'Q6076334','Q4302276','Q21461028','Q5081991','Q2543048','Q4755278','Q5075815'}:held.append(dict(qid=q,reason='Primary Tate dates are approximate or alternative; separate qualified identity workflow required.'));continue
   if q=='Q424307':held.append(dict(qid=q,reason='Primary SMK historical Flemish affiliation requires contextual reconciliation with the Dutch biography; no mechanical modern-country conversion.'));continue
   if q=='Q3499576':p={**p,'country_codes':['DK'],'additional_context':'SMK expressly Danish/Flemish; Danish biography corroborated, historical Flemish affiliation retained in source evidence without mapping it to a modern state.'}
   selected.append(p)
  CORE.save_new(folder/'research.json',dict(at=CORE.now(),country_proposals=selected,holds=held,policy='Revisit original primary-citation formatting holds; dates and publication status remain untouched.'))
 c.plan(1)

def apply():c.apply(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply']);a=p.parse_args();globals()[a.command]()
