#!/usr/bin/env python3
"""NGA26319 and Tate297 identify Cornelius Johnson / Jonson van Ceulen."""
import argparse,importlib.util,json
from pathlib import Path
s=importlib.util.spec_from_file_location('a',Path(__file__).with_name('consolidate-overnight-person-aliases.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
a.c.RUN=a.BASE/'cornelius-johnson-consolidation';a.c.SOURCE='overnight-cornelius-johnson-primary-20260913';a.m.BACKUPS=a.m.BACKUPS/'cornelius-johnson'
a.PAIRS=[('Q636113','cornelius-johnson-research-d22aa8e5cc64','cornelis-jonson-van-ceulen-nga-26319','cornelius-johnson-nga',['Cornelis Jonson van Ceulen','Johnson, Cornelius','1593','1661'])]
def plan():
    # Reuse the same FK/identity preflight, adapting only the capture reader.
    import inspect
    source=inspect.getsource(a.plan)
    source=source.replace("(name+'.html')", "(name+'.web.json')")
    source=source.replace("text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)", "text=raw.decode('utf-8')")
    namespace=dict(a.__dict__);exec(source,namespace);namespace['plan']()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['plan','apply','verify']);args=p.parse_args();(plan if args.command=='plan' else getattr(a.c,args.command))()
