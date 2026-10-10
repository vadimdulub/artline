"""Select specific translated-title/version comparators for source and visual review."""
import importlib.util
import json
from pathlib import Path
spec=importlib.util.spec_from_file_location('c',Path(__file__).with_name('museum-expansion-larissa-common-v2-20261010.py'))
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,RUN=c.m,c.RUN
# Exact IDs observed in the bounded production search; no metadata match inferred.
GROUPS={
    'volanakis-night-ships':dict(numbers=[7,8],ids=['0edb1790-59f5-5b06-af13-e3e5f4e48e10','230e743e-a22e-5b0b-8d6c-befcf445a061','56487c25-5702-519a-afb1-2def1cfdbdb7','13a756a2-b558-5576-8aca-08fba7adc68a','46a234ba-1a37-51c8-8432-2e79b7dc1405','963ecb46-3dd1-535e-a5e1-7d871a9b3d56','aee118e6-dae5-5447-bbc6-359437fe5746','e4067e54-4c1b-5214-b708-5c63a0ee934a','705a3848-5f30-5944-a614-8365fc408b3d','99b6897d-13ed-565c-a3ba-389e1cd00ae5']),
    'giallinas-corfu':dict(numbers=[9],ids=['42a38a25-5d96-53ee-95ea-60ce01fa9ae3','c43b5f5a-1823-52e8-8c0c-cb485272f20a','ffdcb349-2150-5ee7-bb7c-1889a602ed87','e78f98cd-2310-5f83-8df5-b5ee49f01be5']),
    'mathiopoulos-child':dict(numbers=[12],ids=['8e1f1b8d-c243-5ebe-a8e4-04e058339934']),
    'maleas-landscapes':dict(numbers=[13,14,22,23,25,29,32,43,44,45,48,49,52,55,58],ids=['57d9c26e-b1c4-5f72-8360-f6d51e8e70bf','89635d20-0000-5865-852c-ab7ac81baaf0','3f1bb857-c5c5-5568-860a-9c059a9d71c1','654408dd-8115-53f1-b44e-15f5ed981e4f','a138c0fa-2571-55fc-90c8-b9133e28075e','240c3422-621b-5697-9a8a-67b10d32f50d','9e10d417-33cb-5eda-bcc5-81ffed4d8ab2','2763ca1a-e7b7-5445-889c-ba238a6f8239','3f6795d9-87e0-5ff5-b746-32e936b711ad','5ddefc48-d30f-5921-8bb8-75bd20d57f98','bd12da28-7476-4254-be8a-c24a48845862','cdb2383b-0f2a-5a84-9cc1-1ae314cbb676']),
    'nikolaos-lytras-landscapes':dict(numbers=[30,39,41],ids=['5a65c84b-767d-5d87-9956-2c21fdc25548','d2f9a5b9-8fa7-51df-8cf1-5ce3ec307676','422d5dcb-184e-5eda-b89e-362e792b6b12','45358ba0-f6cd-5ecb-aaa0-590ca85739e7','e3acaa33-25e1-5792-bd67-05caead7ba61','f5242a41-8036-557b-882d-9e34a7e3604a']),
    'triantafyllidis-genre':dict(numbers=[28,33,34,56,71,73,82],ids=['ef92c311-78d9-5427-a033-12afc771c63b','eb53f917-4f4b-561d-a86f-09fe01f5c2f3','314c82c5-1883-5907-bd7c-94fe90f40b51','a80f8949-848f-5a0b-bb3f-37f168065633','2c3977e3-74c3-5d38-a6cf-999cb62bd6d3','0a0b311b-b858-58b6-b350-bef5dac60e6c','44ee8a6d-00b3-5d99-8b00-cebab1c91b53']),
    'vitsoris-portrait':dict(numbers=[77],ids=['4c73a6e2-9ae6-58c9-a4f7-b101f30002cc','d2d91f54-390a-5a7f-9d1f-abb828b571bf']),
    'moralis-landscape-and-nude':dict(numbers=[97,108,191],ids=['b318aa2a-7ae4-5d05-a195-a702783633d2','62d30e43-6b72-5906-b6ed-a26cf3854498','4802adb0-4c1e-5872-984b-e3d0fe094bda','75cf084b-e18c-542c-990f-e070ac4806c9','a0b14f9e-50ae-520e-860b-8f6c59e2aeba']),
    'nikolaou-hydra':dict(numbers=[78],ids=['c66efee7-9983-52cf-9219-cae35111cab5','2a021f40-c6ec-5c39-bcc5-09e2195dd384']),
    'documented-versions':dict(numbers=[42,72,122,142],ids=['031c7102-1ae7-5d6f-b87e-69b0d5e674ef','d554be0b-7dc2-5976-8eca-9d888a22bafb','752ef8cd-c530-5691-8498-c0e5dcb99c45','a072ef99-bac1-5dd1-b44f-cd220f49021b']),
}

def main():
    state=m.load(RUN/'production-identity-001.json.gz')['state'];ids=sorted({v for g in GROUPS.values() for v in g['ids']});assert set(ids)<=set(state['artwork_ids'])
    with c.prod.connect() as db,db.transaction():
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ,READ ONLY');snapshot=c.snapshot(db,ids)
    m.save(RUN/'focused-comparators-001.json.gz',dict(at=m.now(),groups=GROUPS,ids=ids,snapshot=snapshot,read_only=True,script_reference=c.ref(Path(__file__).resolve()),
        policy='Specific translated-title, subject, print/impression and support comparisons from6086bounded records. Names are search context only; no creator authority or artwork identity is assigned by this selection.'))
    print(json.dumps(dict(comparators=len(ids),images=len(snapshot['media_assets']),citations=len(snapshot['citations']))),flush=True)

if __name__=='__main__':main()
