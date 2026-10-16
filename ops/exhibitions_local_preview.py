#!/usr/bin/env python3
"""Start the local exhibition review with ephemeral membership and read-only SQL.

Requires the existing Cloud SQL loopback proxy and gcloud read access. Never
prints credentials, applies migrations, creates a database or changes records.
"""
import argparse
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

import psycopg
import exhibitions_common as c
from exhibitions_deep_local import DATA


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web-port',type=int,default=3107)
    parser.add_argument('--api-port',type=int,default=8099)
    parser.add_argument('--review-port',type=int,default=8098)
    parser.add_argument('--corpus',type=Path,default=DATA/'review-corpus.json')
    args=parser.parse_args()
    if os.environ.get('K_SERVICE') or os.environ.get('ARTLINE_ENV')=='production':
        parser.error('This command is for native local review only.')
    if not args.corpus.is_file():parser.error('Build the source-backed review corpus first.')
    ports=[args.web_port,args.api_port,args.review_port]
    if len(set(ports))!=3 or any(p<1024 or p>65535 for p in ports):parser.error('Choose three distinct local ports between 1024 and 65535.')
    for port in ports:
        with socket.socket() as sock:
            try:sock.bind(('127.0.0.1',port))
            except OSError:parser.error(f'Port {port} is occupied. Keep the existing preview or choose another port.')
    with c.connect() as db:
        assert db.execute('SHOW default_transaction_read_only').fetchone()['default_transaction_read_only']=='on'
    connection=psycopg.conninfo.conninfo_to_dict(c._db_base._dsn)
    # Use the same known loopback proxy as the read-only research connection.
    dsn='postgresql://'+urllib.parse.quote(connection['user'],safe='')+':'+urllib.parse.quote(connection['password'],safe='')+'@127.0.0.1:55519/'+urllib.parse.quote(connection['dbname'],safe='')+'?'+urllib.parse.urlencode({'sslmode':'disable','options':'-c default_transaction_read_only=on -c statement_timeout=60000 -c timezone=UTC'})
    runtime=Path(tempfile.mkdtemp(prefix='artline-exhibition-preview-'))
    env=os.environ.copy()
    go_root=Path(env.get('GOROOT','/nonexistent'))/'bin/go'
    go=str(go_root) if go_root.is_file() else shutil.which('go')
    if not go:parser.error('Go is required.')
    for name,package in [('catalogue-api','./cmd/api'),('review-api','./cmd/exhibition-preview')]:
        subprocess.run([go,'build','-o',str(runtime/name),package],cwd=c.ROOT/'apps/server',check=True,env=env)
    web=runtime/'web';web.mkdir()
    subprocess.run(['rsync','-a','--exclude=node_modules','--exclude=public','--exclude=.next','--exclude=.env*','--exclude=test-results','--exclude=playwright-report',str(c.ROOT/'apps/web')+'/',str(web)+'/'],check=True)
    (web/'node_modules').symlink_to(c.ROOT/'apps/web/node_modules');(web/'public').symlink_to(c.ROOT/'apps/web/public')
    origin=f'http://127.0.0.1:{args.web_port}'
    api=f'http://127.0.0.1:{args.api_port}';review=f'http://127.0.0.1:{args.review_port}'
    api_env=env.copy();api_env.update(DATABASE_URL=dsn,PORT=str(args.api_port),FRONTEND_ORIGIN=origin,ARTLINE_LOCAL_DEBUG='true')
    for key in ['ARTLINE_GOOGLE_CLIENT_ID','ARTLINE_GOOGLE_CLIENT_SECRET','ARTLINE_AUTH_COOKIE_KEY','ARTLINE_AUTH_ORIGIN']:api_env.pop(key,None)
    web_env=env.copy();web_env.update(API_INTERNAL_URL=api,EXHIBITIONS_REVIEW_API_URL=review)
    children=[]
    def wait_ready(url,child):
        for _ in range(150):
            if child.poll() is not None:raise RuntimeError('A local preview process exited; inspect its output.')
            try:
                with urllib.request.urlopen(url,timeout=1) as response:
                    if response.status==200:return
            except (OSError,TimeoutError):pass
            time.sleep(.2)
        raise RuntimeError('Local preview startup timed out.')
    try:
        children.append(subprocess.Popen([str(runtime/'catalogue-api'),'-skip-migrations'],env=api_env))
        wait_ready(api+'/health',children[-1])
        children.append(subprocess.Popen([str(runtime/'review-api'),'-corpus',str(args.corpus),'-listen',f'127.0.0.1:{args.review_port}','-upstream',api],env=env))
        wait_ready(review+'/healthz',children[-1])
        children.append(subprocess.Popen(['node','./node_modules/.bin/next','dev','--webpack','--hostname','127.0.0.1','--port',str(args.web_port)],cwd=web,env=web_env))
        print(f'Local review: {origin}/exhibitions\nResearch files: {args.corpus}\nCtrl-C stops these preview processes. Both catalogues remain read-only.',flush=True)
        children[-1].wait()
    except KeyboardInterrupt:pass
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill()


if __name__=='__main__':main()
