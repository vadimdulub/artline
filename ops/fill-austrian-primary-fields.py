#!/usr/bin/env python3
"""Fill only missing medium/dimensions from already reconciled Wien evidence."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('import-austrian-catalogue.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--target',choices=['local','cloud'],required=True);args=p.parse_args();sid=a.uid('source/'+a.SOURCE);out=[]
 with a.connect(args.target) as db:
  rows=db.execute("SELECT a.id::text,a.medium_text,a.dimensions_text,c.source_record_id,c.source_url,c.evidence_note,c.retrieved_at FROM citations c JOIN artworks a ON a.id=c.entity_id JOIN institutions i ON i.id=a.current_institution_id WHERE c.entity_type='artwork' AND c.field_name='official_object_identity' AND c.source_id=%s AND i.wikidata_id='Q505873' AND a.status='review'",(sid,)).fetchall()
  backup=Path.home()/'Library/Application Support/Artline/backups'/args.run.name/(args.target+'-wien-primary-field-preimages.json')
  if not backup.exists():a.core.save_new(backup,rows)
  for x in rows:
   evidence=json.loads(x['evidence_note']);facts=evidence['facts'];medium=facts.get('Technik');dimensions=facts.get('Maße');assert x['source_url'].startswith('https://sammlung.wienmuseum.at/objekt/') and facts['Inventarnummer']
   with db.transaction():
    current=db.execute("UPDATE artworks SET medium_text=coalesce(nullif(medium_text,''),%s),dimensions_text=coalesce(nullif(dimensions_text,''),%s),revision=revision+1,updated_at=now(),updated_by=%s WHERE id=%s AND status='review' AND ((nullif(medium_text,'') IS NULL AND %s::text IS NOT NULL) OR (nullif(dimensions_text,'') IS NULL AND %s::text IS NOT NULL)) RETURNING id",(medium,dimensions,a.core.ACTOR,x['id'],medium,dimensions)).fetchone()
    if current:out.append(x['id'])
  a.core.save_new(args.run/(args.target+'-wien-primary-fields.json'),{'at':a.core.now(),'updated_artworks':out,'verified_official_records':len(rows),'policy':'Only previously empty medium/dimensions; independently verified source citation retained; titles, attribution, dates and review status preserved.'});print(args.target,'Primary field enrichments',len(out),'verified',len(rows))
if __name__=='__main__':main()
