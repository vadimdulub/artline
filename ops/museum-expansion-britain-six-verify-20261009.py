"""Verify replay makes no changes, then take the next read-only coverage audit."""
import contextlib,importlib.util,json
from pathlib import Path
z=importlib.util.spec_from_file_location('a',Path(__file__).with_name('museum-expansion-britain-six-apply-20261009.py'));a=importlib.util.module_from_spec(z);z.loader.exec_module(a)
def main():
 root=Path('/Users/vadimdulub/Library/Logs');replay=root/'artline-britain-six-replay-20261009.log';audit=root/'artline-britain-six-audit-20261009.log';assert not replay.exists() and not audit.exists()
 with replay.open('w') as fp,contextlib.redirect_stdout(fp):a.apply('1ff96ff11ddda8e4e09538fb105095267a3e1e3026207b5deb8ae128e1cfeb28')
 assert replay.read_text().strip()=='Unchanged replay: zero writes';print('Replay verified',flush=True)
 with audit.open('w') as fp,contextlib.redirect_stdout(fp):a.m.audit('after-wave-83')
 print(json.dumps(a.m.load(a.m.RUN/'after-wave-83.json')['summary']),flush=True)
if __name__=='__main__':main()
