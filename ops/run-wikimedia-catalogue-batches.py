#!/usr/bin/env python3
"""Sequential bounded, pinned applications of already-researched candidates."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
RUN=ROOT/'docs/research/wikimedia-catalogue-scan-20260913'
for number in range(3,30):
    plans=[p for p in (RUN/'batches').glob('batch-*.json') if re.fullmatch(r'batch-\d{3}\.json',p.name)]
    planned={x['record']['qid'] for p in plans for x in json.loads(p.read_text())['entries']}
    path=RUN/'batches'/f'batch-{number:03d}.json'
    if not path.exists() and not any(p.stem not in planned for p in (RUN/'ready').glob('Q*.json')):
        print('All currently prepared records have reviewed batch plans',flush=True);break
    logfile=Path('/tmp')/f'artline-wikimedia-batch-{number:03d}.log'
    with logfile.open('a') as log:
        if not path.exists():
            print('Planning batch',number,flush=True)
            subprocess.run([sys.executable,str(ROOT/'ops/apply-wikimedia-catalogues.py'),'plan','--batch',str(number),'--limit','100'],stdout=log,stderr=subprocess.STDOUT,check=True)
        pin=hashlib.sha256(path.read_bytes()).hexdigest()
        for target in ('local','production'):
            receipt=RUN/'batch-results'/f'{number:03d}-{target}.json'
            if receipt.exists():continue
            print('Applying batch',number,target,flush=True)
            subprocess.run([sys.executable,str(ROOT/'ops/apply-wikimedia-catalogues.py'),'apply','--batch',str(number),'--target',target,'--sha256',pin],stdout=log,stderr=subprocess.STDOUT,check=True)
            print('Completed',number,target,json.loads(receipt.read_text())['counts'],flush=True)
