#!/usr/bin/env python3
"""Read selected official SIRBeC catalogue sheets through verified system TLS."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('campaign', ROOT / 'ops/italy-image-campaign.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
OUT = c.RUN / 'primary-catalogue-followup'
TMP = Path('/tmp/artline-italy-catalogue-evidence')
HOST = 'www.lombardiabeniculturali.it'


def capture(url, suffix, max_bytes):
    if urlparse(url).hostname != HOST or not url.startswith('https://'):
        raise ValueError('Unapproved official source')
    key = hashlib.sha256(url.encode()).hexdigest()
    path = OUT / 'captures' / (key + suffix)
    receipt_path = OUT / 'captures' / (key + '.receipt.json')
    if path.exists() and receipt_path.exists():
        receipt = c.load(receipt_path)
        if receipt['sha256'] != c.core.sha(path.read_bytes()):
            raise ValueError('Saved primary source checksum mismatch')
        return path, receipt
    TMP.mkdir(parents=True, exist_ok=True)
    temporary = TMP / (key + '.part')
    c.core.provider_rate_slot(HOST)
    result = subprocess.run(['curl', '--silent', '--show-error', '--location',
        '--proto', '=https', '--proto-redir', '=https', '--max-time', '35',
        '--max-filesize', str(max_bytes), '--output', str(temporary),
        '--write-out', '%{http_code}\n%{content_type}\n%{url_effective}\n%{ssl_verify_result}',
        '--user-agent', 'ArtlineResearch/1.0 (selected museum catalogue metadata)', url],
        capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Verified system TLS capture failed: ' + result.stderr[:250])
    status, content_type, effective, ssl_result = result.stdout.splitlines()
    raw = temporary.read_bytes()
    if status != '200' or ssl_result != '0' or urlparse(effective).hostname != HOST:
        raise ValueError('Official source status, TLS validation or redirect needs review')
    if len(raw) > max_bytes or suffix == '.pdf' and (not raw.startswith(b'%PDF-') or 'pdf' not in content_type):
        raise ValueError('Unexpected official catalogue content')
    receipt = {'url':url, 'resolved_url':effective, 'retrieved_at':c.core.now(),
        'http_status':int(status), 'content_type':content_type, 'ssl_verify_result':0,
        'transport':'System curl; normal certificate verification; no insecure option',
        'bytes':len(raw), 'sha256':c.core.sha(raw), 'path':str(path.relative_to(ROOT)),
        'purpose':'Selected catalogue metadata evidence; embedded reproductions not licensed for upload'}
    c.save(path, raw)
    c.save(receipt_path, receipt)
    temporary.unlink()
    return path, receipt


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    robots_path, robots_receipt = capture('https://' + HOST + '/robots.txt', '.txt', 200000)
    policy = RobotFileParser(robots_receipt['url'])
    policy.parse(robots_path.read_text().splitlines())
    rows = c.load(OUT / 'selected-catalogue-sheets.json')['records']
    for number, row in enumerate(rows, 1):
        result_path = OUT / 'records' / (row['source_id'] + '.json')
        if result_path.exists():
            continue
        try:
            if not policy.can_fetch('ArtlineResearch', row['url']):
                raise ValueError('Official robots policy disallows selected sheet')
            path, receipt = capture(row['url'], '.pdf', 10000000)
            text_path = path.with_suffix('.txt')
            subprocess.run(['pdftotext', '-layout', str(path), str(text_path)], check=True)
            c.save(result_path, {'candidate':row, 'capture':receipt,
                'extracted_text':str(text_path.relative_to(ROOT)), 'text_sha256':c.core.sha(text_path.read_bytes()),
                'status':'Captured official sheet; inventory identity requires review',
                'robots_receipt':robots_receipt})
            print(number, '/', len(rows), row['source_id'], 'official PDF captured', flush=True)
        except Exception as error:
            c.save(result_path, {'candidate':row, 'status':'source_access_hold', 'reason':str(error)[:350]})
            print(number, '/', len(rows), row['source_id'], 'held', type(error).__name__, flush=True)


if __name__ == '__main__':
    main()
