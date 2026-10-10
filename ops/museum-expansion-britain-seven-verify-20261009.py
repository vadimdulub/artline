"""Verify replay makes no changes, then take the next read-only coverage audit."""
import contextlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-britain-seven-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
def main():
 root=Path('/Users/vadimdulub/Library/Logs');replay=root/'artline-britain-seven-replay-20261009.log';audit=root/'artline-britain-seven-audit-20261009.log';assert not replay.exists() and not audit.exists()
 with replay.open('w') as fp,contextlib.redirect_stdout(fp):a.apply('ded236c4d926982c8877771a5cfa090d1aa16c22229cd19a1e86de58bcf5e8f2')
 assert replay.read_text().strip()=='Unchanged replay: zero writes';print('Replay verified',flush=True)
 with audit.open('w') as fp,contextlib.redirect_stdout(fp):a.m.audit('after-wave-85')
 print(json.dumps(a.m.load(a.m.RUN/'after-wave-85.json')['summary']),flush=True)
if __name__=='__main__':main()
