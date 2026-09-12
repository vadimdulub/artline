import { test } from 'node:test';
import assert from 'node:assert/strict';
import { extract } from './research-normandy.mjs';

test('MuMa extracts factual caption, ignores essays and image URLs', () => {
  const html = '<h1 id="page-title">MONET, Les Nymphéas</h1><div class="visuel_oeuvre_unique"><img src="private.jpg"></div><div class="legend_visuel">Claude MONET (1840-1926)<br><b>Les Nymphéas</b><br>1904<br>huile sur toile<br>89&nbsp;x&nbsp;93 cm</div><article>Copyrighted essay</article>';
  const r = extract(html, 'https://www.muma-lehavre.fr/fr/collections/oeuvres-commentees/impressionnisme/monet-les-nympheas', 'muma');
  assert.deepEqual(r.lines, ['Claude MONET (1840-1926)','Les Nymphéas','1904','huile sur toile','89 x 93 cm']);
  assert.ok(!JSON.stringify(r).includes('private.jpg')); assert.ok(!JSON.stringify(r).includes('Copyrighted essay'));
});
test('grouped artwork captions are deferred', () => {
  const r = extract('<div class="visuel_oeuvre_unique"></div><div class="legend_visuel">one</div><div class="legend_visuel">two</div>', 'https://www.muma-lehavre.fr/', 'muma');
  assert.equal(r.state, 'group_or_layout_review');
});
test('Rouen extracts only object article labels', () => {
  const r = extract('<h1 id="page-title">A work</h1><article class="node node-oeuvre"><div class="artiste"><h2>Claude Monet</h2><p>(1840 - 1926) | 909.1.33</p></div><div class="details"><p>Date : 1894 | Technique : Huile sur toile</p></div></article><div class="details">2026 exhibition</div>', 'https://mbarouen.fr/fr/oeuvres/work', 'rouen');
  assert.equal(r.artist,'Claude Monet'); assert.equal(r.details,'Date : 1894 | Technique : Huile sur toile');
});
