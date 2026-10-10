#!/usr/bin/env python3
import argparse,importlib.util,os
from pathlib import Path
s=importlib.util.spec_from_file_location('aliases',Path(__file__).with_name('museums-exactly-one-aliases-20261008.py'));a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
os.environ['ARTLINE_MUSEUM_PROXY_PORT']='55495'
a.m.RUN=a.m.ROOT/'docs/research/museums-exactly-one-deep-20261008';a.RUN=a.m.RUN/'aliases';a.OP=a.m.RUN.name+'-aliases';a.BACKUP=Path.home()/'Library/Application Support/Artline/backups'/a.m.RUN.name/'aliases'
a.PAIRS=[
 ('5037b865-3794-5d5e-9372-ed5e92fb2fb7','7f58dd97-d514-56d5-9521-29bfd2993029','https://www.lagallerianazionale.com/',['Galleria','Roma','Belle Arti'],'Galleria Naionale is a spelling error for Galleria Nazionale d’Arte Moderna in Rome; both national catalogue museum names identify the collection at Viale delle Belle Arti 131. Not the separate national ancient-art gallery.'),
 ('e585befd-ee7e-5db6-b486-c6971b63702d','9f5e7d2f-a80d-57ee-9c08-43a0923931ed','https://barberinicorsini.org/',['Arte Antica','Barberini','Corsini'],'National Gallery of Ancient Art (GNAA), Rome, is the English name of Galleria Nazionale d’Arte Antica Q2266081, now Gallerie Nazionali Barberini Corsini. Reconcile these two collection-level identities; retain separate Palazzo Barberini venue identity.'),
 ('c4488510-6857-5b46-981a-ac5b2062ebe4','e3f9a6ee-467f-5e2d-a1b7-b8d589abf632','https://gallerianazionaledellumbria.it/en/palace/',['National Gallery of Umbria','Palazzo dei Priori','Perugia'],'National Gallery of Umbria (Palazzo dei Priori), Perugia, and Galleria nazionale dell’Umbria — Perugia identify the same national collection in Palazzo dei Priori. The official English museum page explicitly establishes this identity. Retain separate deposit/storage institution records.'),
]
def final_plan():
 v=a.d.load(a.RUN/'plan.json.gz');assert len(v['records'])==3;a.d.save(a.RUN/'final-plan.json.gz',v);a.d.save(a.BACKUP/'final-plan-and-preimages.json.gz',v)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase');x=p.parse_args();(final_plan if x.phase=='final_plan' else getattr(a,x.phase))()
