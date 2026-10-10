"""Internal thumbnails for selected object/version review, with immutable receipts."""
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

spec = importlib.util.spec_from_file_location('t', Path(__file__).with_name('museum-expansion-zongolopoulos-paintings-source-20261010.py'))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
m, RUN, q = t.m, t.RUN, t.q
PROOF = Path.home() / 'Library/Application Support/Artline/research-proofs/zongolopoulos-paintings-20261010'
DEST = PROOF / 'identity-images'
DEST.mkdir(parents=True, exist_ok=True)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    selected = m.load(RUN / 'selected-source-records-001.json.gz')['rows']
    rows = []
    for i, source in enumerate(selected, 1):
        sid = source['source_id'].rsplit('-', 1)[1]
        path = DEST / (sid + '.jpg')
        rp = RUN / 'captures' / ('thumbnail-' + sid + '-001.json')
        if rp.exists():
            receipt = m.load(rp)
            assert path.is_file() and sha(path) == receipt['sha256'] and receipt['status'] == 200
        else:
            assert not path.exists()
            res = requests.get(source['thumbnail_url'], timeout=(15, 45))
            # A denial is preserved and terminates this provider pass without retries.
            receipt = dict(at=m.now(), number=source['number'], source_id=source['source_id'],
                           source_url=source['source_url'], url=source['thumbnail_url'], final_url=res.url,
                           status=res.status_code, content_type=res.headers.get('Content-Type'),
                           bytes=len(res.content), sha256=hashlib.sha256(res.content).hexdigest(),
                           path=str(path), rights_links=source['rights_links'], purpose='Internal selected-object identity review; no public asset attachment.')
            if res.status_code != 200 or not res.headers.get('Content-Type', '').startswith('image/'):
                m.save(rp, receipt)
                raise RuntimeError('Image source unavailable: ' + sid + ' status=' + str(res.status_code))
            path.write_bytes(res.content)
            with Image.open(path) as im:
                receipt.update(width=im.width, height=im.height)
            m.save(rp, receipt)
        rows.append(dict(receipt, role=source['role'], title=source['fields']['Τίτλος'][-1],
                         date=(source['fields'].get('Ημερομηνία') or ['n.d. (no dedicated source date)'])[-1]))
        if i % 30 == 0:
            print(json.dumps(dict(thumbnails=i, total=len(selected))), flush=True)
    sheets = []
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
    small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 13)
    for page, start in enumerate(range(0, len(rows), 20), 1):
        batch = rows[start:start + 20]
        canvas = Image.new('RGB', (1600, 1480), 'white')
        draw = ImageDraw.Draw(canvas)
        for k, row in enumerate(batch):
            left, top = (k % 5) * 320, (k // 5) * 370
            short = row['source_id'].rsplit('-', 1)[1]
            label = str(row['number']) + ' | ' + short + (' | EXISTING' if row['role'] == 'existing_comparator' else '')
            draw.text((left + 4, top + 4), label, fill='black', font=font)
            title = row['title']
            draw.text((left + 4, top + 25), title[:42], fill='black', font=small)
            draw.text((left + 4, top + 44), row['date'], fill='black', font=small)
            with Image.open(row['path']) as im:
                thumb = ImageOps.contain(im.convert('RGB'), (310, 300))
                canvas.paste(thumb, (left + (320 - thumb.width) // 2, top + 65 + (300 - thumb.height) // 2))
        path = DEST / ('contact-' + str(page) + '.jpg')
        assert not path.exists()
        canvas.save(path, quality=92)
        sheets.append(dict(path=str(path), sha256=sha(path), numbers=[v['number'] for v in batch]))
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row['sha256']].append(row['source_id'])
    m.save(RUN / 'visual-references-001.json', dict(at=m.now(), rows=rows, sheets=sheets,
        exact_duplicate_images=[v for v in groups.values() if len(v) > 1],
        source_reference=q.s.ref(RUN / 'selected-source-records-001.json.gz'), script_reference=q.s.ref(Path(__file__).resolve()),
        policy='151 selected undated-index object thumbnails only. Preserve unknown creation dates and description/inscription evidence; no production image eligibility inferred. Multiple views or sides must be reconciled before counting artworks. Raw source images unchanged; contact sheets are internal review aids. No publication, production asset upload or claimed visual review until separately recorded.'))
    print(json.dumps(dict(thumbnails=len(rows), sheets=len(sheets), exact_duplicate_groups=sum(len(v) > 1 for v in groups.values()))), flush=True)


if __name__ == '__main__':
    main()
