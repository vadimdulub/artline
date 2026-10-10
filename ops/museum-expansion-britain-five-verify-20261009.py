"""Verify replay makes no changes, then take the next read-only coverage audit."""
import contextlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-britain-five-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
def main():
 root=Path('/Users/vadimdulub/Library/Logs');replay=root/'artline-britain-five-replay-20261009.log';audit=root/'artline-britain-five-audit-20261009.log';assert not replay.exists() and not audit.exists()
 with replay.open('w') as fp,contextlib.redirect_stdout(fp):a.apply('f3a7e61100a91b8bb426ea94537d4c8c9097c5b437b412e8ff616cee293451b6')
 assert replay.read_text().strip()=='Unchanged replay: zero writes';print('Replay verified',flush=True)
 with audit.open('w') as fp,contextlib.redirect_stdout(fp):a.m.audit('after-wave-82')
 print(json.dumps(a.m.load(a.m.RUN/'after-wave-82.json')['summary']),flush=True)
if __name__=='__main__':main()
