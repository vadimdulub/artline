"""Existing catalogue connection settings without persisted database secrets.

The Cloud SQL proxy must already listen on127.0.0.1:55432. Production credentials
are read from this project's configured Terraform state into process memory;
the state and password must never be logged or written to research artifacts.
"""
import json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def environment(cloud):
    env=os.environ.copy()
    env['PGOPTIONS']='-c timezone=UTC -c extra_float_digits=3 -c default_transaction_read_only=on'
    env['PGDATABASE']='artline';env['PGHOST']='127.0.0.1';env['PGPORT']='55432' if cloud else '5432'
    if cloud:
        state=json.loads(subprocess.check_output(['sh','ops/terraform_gcloud.sh','state','pull'],cwd=ROOT,text=True))
        values=[r['instances'][0]['attributes']['result'] for r in state['resources'] if r['type']=='random_password' and r['name']=='database']
        assert len(values)==1,'Expected one configured Artline database credential'
        env['PGUSER']='artline_app';env['PGPASSWORD']=values[0]
    return env
