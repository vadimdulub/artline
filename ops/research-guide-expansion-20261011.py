"""Read-only production evidence for 80 additional editorial museum guides."""
import datetime
import gzip
import json
import subprocess
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'docs/research/museum-guides-80-20261011'
RUN.mkdir(parents=True, exist_ok=True)

def connect():
    raw = subprocess.check_output(['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=artline-database-url', '--project=artline-508319'], text=True).strip()
    fields = psycopg.conninfo.conninfo_to_dict(raw)
    fields.update(host='127.0.0.1', port='55448', sslmode='disable')
    return psycopg.connect(**fields, options='-c default_transaction_read_only=on -c statement_timeout=60000', row_factory=dict_row)

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, indent=2, default=str).encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw + b'\n')

def inventory():
    with connect() as db:
        rows = db.execute("""SELECT to_jsonb(i) institution, count(*) works,
          count(a.primary_media_id) images,
          count(*) FILTER (WHERE a.primary_media_id IS NOT NULL AND a.creation_year_end<=1970) dated_images
          FROM institutions i JOIN artworks a ON a.current_institution_id=i.id
          WHERE a.status<>'archived' GROUP BY i.id
          HAVING count(a.primary_media_id)>=20 ORDER BY dated_images DESC,i.id""").fetchall()
    save(RUN/'inventory.json', {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'readOnly':True,'institutions':rows})
    for row in rows[:180]:
        i=row['institution']
        print(i['slug'], '|',i['name'],'|',row['dated_images'],'dated images', '|',i.get('city'), '|',i.get('country_code'))

PAGE = """SELECT a.id::text,a.slug,a.title,a.alternate_title,a.date_display,
  a.creation_year_start,a.creation_year_end,a.date_precision,a.work_type,
  a.description_md,a.medium_text,a.dimensions_text,a.accession_number,a.status,
  a.unlinked_creator_label,to_jsonb(m) media,
  coalesce((SELECT jsonb_agg(jsonb_build_object('name',ar.display_name,'slug',ar.slug,'role',aa.attribution_role))
    FROM artwork_artists aa JOIN artists ar ON ar.id=aa.artist_id WHERE aa.artwork_id=a.id),'[]') artists,
  coalesce((SELECT jsonb_agg(jsonb_build_object('url',h.source_url,'checkedAt',h.checked_at,'context',h.context))
    FROM artwork_location_assertions h WHERE h.artwork_id=a.id AND h.institution_id=a.current_institution_id
    AND h.claim_type='holding' AND h.review_state='accepted' AND h.superseded_by IS NULL),'[]') holdings,
  coalesce((SELECT jsonb_agg(jsonb_build_object('url',e.canonical_url,'scheme',e.scheme))
    FROM external_identifiers e WHERE e.entity_type='artwork' AND e.entity_id=a.id),'[]') identifiers
  FROM artworks a JOIN media_assets m ON m.id=a.primary_media_id
  WHERE a.current_institution_id=%s AND a.status<>'archived'
    AND (a.creation_year_end<=1970 OR a.creation_year_end IS NULL)
    AND (%s::uuid IS NULL OR a.id>%s::uuid) ORDER BY a.id LIMIT 500"""

def export():
    inventory=json.loads((RUN/'inventory.json').read_text())
    institutions={row['institution']['slug']:row['institution'] for row in inventory['institutions']}
    candidates=[dict(zip(['institutionSlug','slug','museum','city','country'],line.split('\t'))) for line in (RUN/'candidates.tsv').read_text().splitlines()]
    for candidate in candidates:
        dest=RUN/'catalogue'/(candidate['slug']+'.json.gz')
        if dest.exists():
            continue
        inst=institutions[candidate['institutionSlug']]
        works=[]; cursor=None
        with connect() as db:
            while True:
                batch=db.execute(PAGE,(inst['id'],cursor,cursor)).fetchall()
                if not batch:break
                works.extend(batch);cursor=batch[-1]['id']
        save(dest,{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'readOnly':True,'candidate':candidate,'institution':inst,'works':works})
        print(candidate['slug'],len(works),'illustrated works;',sum(bool(w['holdings']) for w in works),'holding sources',flush=True)
    save(RUN/'candidates.json', candidates)

if __name__ == '__main__':
    {'inventory':inventory,'export':export}[sys.argv[1]]()
