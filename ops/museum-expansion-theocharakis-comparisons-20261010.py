"""Selected original-resolution references for possible recto/verso identities."""
import hashlib
import importlib.util
import json
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

spec = importlib.util.spec_from_file_location('t', Path(__file__).with_name('museum-expansion-theocharakis-source-20261010.py'))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
m, RUN, q = t.m, t.RUN, t.q
PROOF = Path.home() / 'Library/Application Support/Artline/research-proofs/theocharakis-20261010'
DEST = PROOF / 'comparisons'
DEST.mkdir(parents=True, exist_ok=True)
GROUPS = [[3,45], [6,16], [11,47], [13,24], [31,39], [10,28], [111,140], [120,127], [153,163], [158,172], [157,159,173], [145,147], [61,75], [60,87]]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    rows = {r['number']:r for r in m.load(RUN / 'native-object-records-001.json.gz')['rows']}
    selected = sorted({n for ns in GROUPS for n in ns})
    receipts = {}
    for number in selected:
        row = rows[number]
        sid = row['source_id'].rsplit('-', 1)[1]
        path = DEST / (sid + '.jpg')
        receipt_path = RUN / 'captures' / ('comparison-' + sid + '-001.json')
        if receipt_path.exists():
            receipt = m.load(receipt_path)
            assert path.exists() and sha(path) == receipt['sha256'] and receipt['status'] == 200
        else:
            assert not path.exists()
            res = requests.get(row['full_image_url'], timeout=(15,45))
            receipt = dict(at=m.now(), number=number, source_id=row['source_id'], native_url=row['native_url'],
                           url=row['full_image_url'], status=res.status_code, bytes=len(res.content),
                           sha256=hashlib.sha256(res.content).hexdigest(), path=str(path),
                           purpose='Selected same-sheet identity comparison only; CC BY-SA source label, not a production attachment. Unknown dates remain under review.')
            if res.status_code != 200 or not res.headers.get('Content-Type','').startswith('image/'):
                m.save(receipt_path, receipt)
                raise RuntimeError('Comparison image unavailable: '+sid)
            path.write_bytes(res.content)
            with Image.open(path) as im:
                receipt.update(width=im.width, height=im.height)
            m.save(receipt_path, receipt)
        receipts[number] = receipt
    sheets = []
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22)
    for ns in GROUPS:
        canvas = Image.new('RGB', (600*len(ns),680), 'white')
        draw = ImageDraw.Draw(canvas)
        for i, number in enumerate(ns):
            row = rows[number]
            draw.text((i*600+8,8), str(number)+' | '+row['source_id'].rsplit('-',1)[1], fill='black', font=font)
            draw.text((i*600+8,37), row['fields']['διαστάσεις'], fill='black', font=font)
            with Image.open(receipts[number]['path']) as im:
                thumb = ImageOps.contain(im.convert('RGB'), (585,590))
                canvas.paste(thumb, (i*600+(600-thumb.width)//2, 82+(590-thumb.height)//2))
        p = DEST / ('compare-'+'-'.join(map(str,ns))+'.jpg')
        assert not p.exists()
        canvas.save(p,quality=94)
        sheets.append(dict(numbers=ns,path=str(p),sha256=sha(p)))
    m.save(RUN/'comparison-references-001.json',dict(at=m.now(),rows=list(receipts.values()),sheets=sheets,
        native_reference=q.s.ref(RUN/'native-object-records-001.json.gz'),script_reference=q.s.ref(Path(__file__).resolve()),
        policy='29 selected native image references for 14 physical-identity comparisons. No assumptions from adjacent page IDs or equal dimensions alone. Raw files unchanged.'))
    print(json.dumps(dict(originals=len(receipts),comparison_sheets=len(sheets))),flush=True)


if __name__=='__main__':
    main()
