"""Verify official HTTPS collection-to-HTTP-native source chain after atomic rollback."""
import importlib.util,json
from pathlib import Path
from urllib.parse import urljoin
z=importlib.util.spec_from_file_location('p',Path(__file__).with_name('museum-expansion-ferens-native-20261009.py'));p=importlib.util.module_from_spec(z);z.loader.exec_module(p);m=p.m;RUN=p.RUN
def main():
 dest=RUN/'holding-source-001.json';assert not dest.exists();url='https://www.hullmuseums.co.uk/collections-ferens-art-gallery';p.n.SITES['hull_modern']='https://www.hullmuseums.co.uk';raw,cap=p.n.capture('hull_modern',url);soup=p.n.BeautifulSoup(raw,'html.parser');links=[dict(text=a.get_text(' ',strip=True),url=urljoin(url,a['href'])) for a in soup.select('a[href]') if a['href'].startswith('http://museumcollections.hullcc.gov.uk/')];assert links
 plan=m.load(RUN/'ferens-native-additions-001-plan-001.json.gz');ids=[r['artwork_id'] for r in plan['records']]
 with m.connect() as db:
  assert not db.execute('SELECT 1 FROM artworks WHERE id=ANY(%s::uuid[])',(ids,)).fetchone();assert not db.execute('SELECT 1 FROM sources WHERE id=%s',(m.uid('source/ferens-native-additions-001'),)).fetchone();constraints=[v for v in db.execute("SELECT conname,pg_get_constraintdef(oid) definition FROM pg_constraint WHERE conrelid='artwork_location_assertions'::regclass AND conname='artwork_location_assertions_source_url_check'")]
 m.save(dest,dict(at=m.now(),url=url,capture=cap,catalogue_links=links,db_constraint=constraints,failed_plan_reference=p.ref(RUN/'ferens-native-additions-001-plan-001.json.gz'),failed_transaction_rolled_back=True,new_records_remaining=0,script_reference=p.ref(Path(__file__).resolve()),policy='HTTPS official collection landing page explicitly links the native HTTP catalogue. Use the genuinely fetched HTTPS landing URL in schema-constrained holding source_url. Preserve exact accession-level HTTP URL in external identifier,citation,holding evidence_note and raw source chain. Never manufacture an unfetched HTTPS object URL or weaken database constraints.'))
 print(json.dumps(dict(links=links,rollback_verified=True,constraints=constraints)),flush=True)
if __name__=='__main__':main()
