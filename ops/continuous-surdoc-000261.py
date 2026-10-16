#!/usr/bin/env python3
"""Bounded SURDOC page-30 capture and production reconciliation for batch 261."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research/continuous-production-20261011/batches/000261"
INDEX = "https://www.surdoc.cl/colecciones"
PARAMS = {"first_level_classification":"549", "f[0]":"classification:555", "f[1]":"institution:3", "page":"30"}

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n")

def fields(page):
    result = {}
    for node in page.select("article .field"):
        label = node.find("div", class_="field-label", recursive=False)
        value = node.find("div", class_="field-item", recursive=False) or node.find("div", class_="field-items", recursive=False)
        if label and value: result[label.get_text(" ", strip=True)] = value.get_text(" ", strip=True)
    obj = page.select_one("article .field--name-object")
    if obj:
        for node in obj.select(".js-form-item"):
            label, value = node.select_one("label"), node.select_one(".field-item")
            if label and value: result[label.get_text(" ", strip=True)] = value.get_text(" ", strip=True)
    return result

def connect():
    secret = subprocess.check_output(["gcloud","secrets","versions","access","latest","--secret=artline-database-url","--project=artline-508319","--account=vadim@alingva.com"], text=True).strip()
    kw = psycopg.conninfo.conninfo_to_dict(secret)
    kw.update(host="127.0.0.1", port=os.environ.get("ARTLINE_SWISS_INDIA_PROXY_PORT","55519"), sslmode="disable", connect_timeout=20)
    return psycopg.connect(**kw, autocommit=True, row_factory=dict_row, options="-c default_transaction_read_only=on -c statement_timeout=60000")

def main():
    session = requests.Session(); session.headers["User-Agent"] = "ArtlineResearch/1.0"
    response = session.get(INDEX, params=PARAMS, timeout=30); response.raise_for_status()
    page = BeautifulSoup(response.content, "html.parser")
    ids = []
    for anchor in page.select('a.record-title[href^="/registro/"]'):
        native = anchor["href"].rsplit("/",1)[-1]
        if native not in ids: ids.append(native)
    objects=[]
    for native in ids[:10]:
        url="https://www.surdoc.cl/registro/"+native
        item=session.get(url, timeout=30); item.raise_for_status()
        objects.append({"id":native,"url":item.url,"status":item.status_code,"sha256":digest(item.content),"bytes":len(item.content),"fields":fields(BeautifulSoup(item.content,"html.parser"))})
    with connect() as db:
        target=db.execute("select current_database() database,current_setting('transaction_read_only') read_only").fetchone()
        existing=list(db.execute("select external_id,entity_id::text artwork_id from external_identifiers where entity_type='artwork' and scheme=%s and external_id=any(%s) order by external_id",("museum-native-chile-surdoc",ids)))
        batch107=json.loads((ROOT/"docs/research/continuous-production-20261011/batches/000260/batch107-live-reconciliation.json").read_text())["production_rows"]
    eligible=[]; held=[]
    for row in objects:
        f=row["fields"]; date=f.get("Fecha de creación","")
        if row["id"] in {x["external_id"] for x in existing}: held.append({"id":row["id"],"reason":"already_in_production"})
        elif not date: held.append({"id":row["id"],"reason":"missing_explicit_creation_date"})
        elif date.strip()=="1981": held.append({"id":row["id"],"reason":"creation_after_1970"})
        else: eligible.append(row["id"])
    save("surdoc-mnba-page30-source-verification.json", {"at":now(),"route":response.url,"status":response.status_code,"index_sha256":digest(response.content),"index_bytes":len(response.content),"index_ids":ids,"researched_objects":objects,"eligible_after_source_review":eligible,"held":held,"resume_cursor":{"institution":3,"page":31},"image_policy":"Metadata and holding only; registry says never_unless_record_explicitly_open and no record-level open grant was established."})
    save("production-target-reconciliation.json", {"at":now(),"connection_name":"artline-508319:europe-west1:artline-postgres","proxy_port":55519,"proxy_command_inspected":True,"database":target,"shared_ingestion_lock":"artline-curated-ingestion","write":False,"existing_native_matches":existing,"local_catalogue_connections":0})
    save("batch107-live-reconciliation.json", {"at":now(),"production_rows":batch107,"increment":0,"write":False})
    print(json.dumps({"ids":len(ids),"researched":len(objects),"eligible":eligible,"existing":existing,"batch107":batch107}))

if __name__ == "__main__": main()
