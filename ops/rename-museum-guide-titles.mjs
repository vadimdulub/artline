#!/usr/bin/env node
// Offline, title-only publication transform. Content/PDF assets are managed
// separately from Git; the complete naming policy lives in the versioned manifest.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const json = value => JSON.stringify(value, null, 2) + '\n';

export function titleFor(policy, slug, locale) {
  const offset = policy.locales.indexOf(locale);
  assert.ok(offset >= 0, `Unknown locale: ${locale}`);
  const names = policy.museums[slug];
  assert.ok(names && names.length === policy.locales.length, `Missing localized names: ${slug}`);
  assert.ok(names.every(name => typeof name === 'string' && name.trim() && !/[<>\n\r]/.test(name)), `Invalid name: ${slug}`);
  const template = policy.templates[locale];
  assert.equal(template.split('{museum}').length, 2, `Invalid template: ${locale}`);
  return template.replace('{museum}', names[offset]);
}

function searchText(summary, editions) {
  const text = [summary.title, summary.subtitle, summary.museum, summary.city, summary.country, summary.artist?.name || ''];
  for (const edition of editions) {
    text.push(...['title', 'subtitle', 'museum', 'city', 'country'].map(key => edition[key] || ''));
    text.push(edition.artist?.name || '');
  }
  return [...new Set(text)].join(' ');
}

export function prepareRename({ policy, contentRoot, searchIndex, outputRoot }) {
  assert.notEqual(path.resolve(contentRoot), path.resolve(outputRoot), 'Use a separate output directory');
  const indexPath = path.join(contentRoot, 'museum-guides/index.json');
  const summaries = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
  assert.deepEqual(summaries.map(g => g.slug).sort(), Object.keys(policy.museums).sort(), 'Museum manifest coverage differs');
  assert.equal(new Set(policy.locales).size, policy.locales.length);
  assert.ok(policy.locales.every(locale => /^[a-z]{2}$/.test(locale)), 'Invalid locale path');
  assert.ok(summaries.every(guide => /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(guide.slug)), 'Invalid guide path');
  const index = JSON.parse(fs.readFileSync(searchIndex, 'utf8'));
  // Fail before writing if the immutable production search projection is stale.
  for (const [name, expected] of Object.entries(index.sources)) {
    assert.equal(sha256(fs.readFileSync(path.join(contentRoot, name))), expected, `Stale search source: ${name}`);
  }
  const files = new Map(), changes = [], revised = [];
  for (const summary of summaries) {
    assert.ok(!summary.kind || summary.kind === 'museum', `Not a museum: ${summary.slug}`);
    assert.deepEqual([...summary.locales].sort(), [...policy.locales].sort(), `Locale coverage: ${summary.slug}`);
    const beforeEditions = [], afterEditions = [];
    for (const locale of summary.locales) {
      const name = `museum-guides/${summary.slug}/${locale}.json`;
      const raw = fs.readFileSync(path.join(contentRoot, name), 'utf8');
      const before = JSON.parse(raw);
      assert.equal(before.slug, summary.slug); assert.equal(before.locale, locale);
      assert.ok(!before.kind || before.kind === 'museum');
      const title = titleFor(policy, summary.slug, locale);
      const needle = `  "title": ${JSON.stringify(before.title)},`;
      assert.equal(raw.split(needle).length, 2, `Expected one top-level title: ${name}`);
      const updated = raw.replace(needle, `  "title": ${JSON.stringify(title)},`);
      const after = JSON.parse(updated);
      assert.deepEqual({ ...after, title: before.title }, before, `Non-title content changed: ${name}`);
      files.set(name, updated); index.sources[name] = sha256(updated);
      beforeEditions.push(before); afterEditions.push(after);
      changes.push({ slug: summary.slug, locale, before: before.title, after: title, beforeSHA256: sha256(raw), afterSHA256: sha256(updated) });
    }
    const matches = index.entries.filter(entry => entry.slug === summary.slug && entry.kind === 'museum');
    assert.equal(matches.length, 1, `Expected one search entry: ${summary.slug}`);
    const entry = matches[0];
    assert.equal(entry.title, summary.title, `Stale index title: ${summary.slug}`);
    assert.equal(entry.search, searchText(summary, beforeEditions), `Stale search text: ${summary.slug}`);
    const next = { ...summary, title: titleFor(policy, summary.slug, 'en') };
    revised.push(next); entry.title = next.title; entry.search = searchText(next, afterEditions);
  }
  const indexRaw = json(revised);
  files.set('museum-guides/index.json', indexRaw); index.sources['museum-guides/index.json'] = sha256(indexRaw);
  // All validation completes before any staged artifact is written.
  fs.mkdirSync(outputRoot, { recursive: true });
  for (const [name, data] of files) {
    const target = path.join(outputRoot, name);
    fs.mkdirSync(path.dirname(target), { recursive: true }); fs.writeFileSync(target, data);
  }
  fs.writeFileSync(path.join(outputRoot, 'guide-search-index.json'), json(index));
  const report = { museums: summaries.length, editions: changes.length, changedEditions: changes.filter(row => row.before !== row.after).length, translationAPI: false, databaseWrites: false, changes };
  fs.writeFileSync(path.join(outputRoot, 'title-changes.json'), json(report));
  return report;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), options = {};
  for (let i = 0; i < args.length; i += 2) {
    assert.ok(['--output', '--content', '--index', '--policy'].includes(args[i]) && args[i + 1], `Invalid argument: ${args[i]}`);
    options[args[i]] = path.resolve(args[i + 1]);
  }
  assert.ok(options['--output'], 'Specify --output outside the source content directory');
  const result = prepareRename({
    policy: JSON.parse(fs.readFileSync(options['--policy'] || path.join(repo, 'content/curation/museum-guide-titles.json'))),
    contentRoot: options['--content'] || path.join(repo, 'apps/web/content/articles'),
    searchIndex: options['--index'] || path.join(repo, 'apps/server/internal/guides/index.json'),
    outputRoot: options['--output'],
  });
  console.log(JSON.stringify({ museums: result.museums, editions: result.editions, changedEditions: result.changedEditions, output: options['--output'], translationAPI: false, databaseWrites: false }));
}
