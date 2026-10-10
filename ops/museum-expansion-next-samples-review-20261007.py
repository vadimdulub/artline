#!/usr/bin/env python3
"""Individual editorial decisions for two complete official source records."""
import importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('f',Path(__file__).with_name('museum-expansion-next-samples-20261007.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f);m=f.m;ref=f.ref;RUN=m.RUN/'native/next-samples'
NOTES={
 'ago':'The complete official AGO object20664 and published Canadian painting index agree on George Theodore Berthon, The Three Robinson Sisters,1846. Oil canvas111.8x83.8cm, inventory2007/33 and the1944J.BeverlyRobinson gift identify one group portrait, not three separate artworks. All21creator/title/inventory/museum-scope records were reviewed: the19Berthon surname leads concern Paul,Rene,Nicolas or Maurice Berthon, with different subjects and objects; the2pendingAGOrecords are MacDonald landscapes. No selected source URL,native ID,accession or title collision. Preserve George Theodore Berthon as the supplied object creator label without creating or choosing a different Berthon authority.',
 'detroit':'The official DIA highlight selection, complete HTML and linked JSON identify object109832, Reading the Fate of the Christ Child,1667, oil on copper23x29cm, accession2020.15, purchased2020using theRobertH.TannahillFoundationFund. Reviewed33creator/title/inventory/museum-scope works, including16Obidos/Ayala surname leads and17olderpendingDetroitworks; no native URL/ID,accession or exact-title collision. The Lisbon SaintJosephandtheChild is a tall71cm composition rather than this23x29cm fortune-telling scene. The retained dealer2019source describes the newly identified1667signed copper. Nativity,SalvatorMundi and other namedObidos compositions remain distinct. One physical painting, no detail/group duplication.'}
def checked(r):
 p=m.ROOT/r['path'];assert ref(p)==r;return p
def build():
 rows=[]
 for fn,mod in [(f.ago,f.a),(f.detroit,f.d)]:
  row=fn();identity=m.load(mod.RUN/'complete-sample-identity-001.json.gz');assert identity['row']==row;assert not identity['native_scheme_hits'];cm=identity['comparisons'][0]
  assert not any(cm[k] for k in ['native_url_hits','source_hits','exact_title_hits','inventory_hits','untitled_creator_hits'])
  candidates=m.load(mod.RUN/'complete-sample-candidate-001.json.gz');checked(candidates['parser_reference']);assert candidates['rows']==[row]
  refs=[ref(mod.RUN/name) for name in ['complete-sample-identity-001.json.gz','complete-sample-citations-001.json.gz','complete-sample-candidate-001.json.gz']]
  discrepancies=[]
  if row['provider']=='detroit':
   p=mod.RUN/'complete-sample-version-evidence-001.json';v=m.load(p);refs.append(ref(p));refs+=v['references'];discrepancies=v['source_discrepancies']
  rows.append(dict(row,state='approved_review_only_addition',confidence=.9,basis=NOTES[row['provider']],limitation='90%editorial confidence for documented museum collection connection,not a calibrated probability. No legal-title,current-custody or current-display determination. Literal creator/date/credit/rights and unresolved secondary discrepancies retained. Existing records and pending associations remain unchanged.',source_discrepancies=discrepancies,supplement_references=refs))
 return rows
def main():
 rows=build();m.save(RUN/'editorial-reviewed-001.json.gz',dict(at=m.now(),decisions=rows,reviewer_reference=ref(Path(__file__).resolve()),policy='Two individually reviewed complete source records only. The172AGO and118Detroit indexed queues are unapproved leads; theSaintLouis403,AGO403/timeouts andDetroit429remain open source holds. No permission to publish,invent missing facts,download images or change existing metadata.'))
 print(json.dumps([dict(provider=r['provider'],title=r['facts']['title'],decision=r['state']) for r in rows]),flush=True)
if __name__=='__main__':main()
