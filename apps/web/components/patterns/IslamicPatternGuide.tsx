import Link from "next/link";
import { StructuredData } from "@/components/StructuredData";
import { guideLanguages } from "@/lib/museum-guide-types";
import { absoluteURL, breadcrumbs } from "@/lib/seo";
import { patternAssets, patternGuidePath, type PatternGuideCopy } from "@/lib/pattern-guide";
import { PatternInteractions } from "./PatternInteractions";
import styles from "./IslamicPatternGuide.module.css";

const cls = (name: string) => `IslamicPatternsArticle_${name}`;
type Asset = typeof patternAssets[number];
function RefText({ text, copy }: { text: string; copy: PatternGuideCopy }) {
  return <>{text.split(/(\[\d+\])/g).map((part, i) => /^\[\d+\]$/.test(part) ? <a key={i} className={cls("source")} href={copy.sources.references[part.slice(1, -1) as keyof typeof copy.sources.references]} target="_blank" rel="noreferrer">{part}</a> : part)}</>;
}
function Paragraphs({ values, copy }: { values: string[]; copy: PatternGuideCopy }) { return values.map((text, i) => <p key={i}><RefText text={text} copy={copy} /></p>); }
function Figure({ asset, text, copy, eager = false }: { asset: Asset; text: { title: string; caption: string; credit: string }; copy: PatternGuideCopy; eager?: boolean }) {
  const [small, medium, full] = asset.variants;
  return <figure className={cls("figure")}>
    <a href={full.url} data-enlarge-image data-full={full.url} aria-label={`${copy.ui.enlarge}: ${text.title}`}>
      <img src={small.url} srcSet={`${small.url} ${small.width}w, ${medium.url} ${medium.width}w`} sizes="(max-width:760px) calc(100vw - 32px), (max-width:1100px) 45vw, 540px" alt={text.title} width={small.width} height={small.height} loading={eager ? "eager" : "lazy"} decoding="async" fetchPriority={eager ? "high" : undefined} />
    </a>
    <figcaption><strong>{text.title}</strong><span>{text.caption}</span><span><RefText text={text.credit} copy={copy} /></span></figcaption>
  </figure>;
}
const crops = [
  { whole: "0 0 2636 3722", boxes: ["774.98 1566.96 767.08 591.8", "645.82 2225.76 1035.95 323.81"], width: 2636, height: 3722 },
  { whole: "0 0 2695 4000", boxes: ["1220.84 1952.0 676.45 524.0", "851.62 2704.0 1379.84 392.0"], width: 2695, height: 4000 },
];
function Painting({ index, copy }: { index: number; copy: PatternGuideCopy }) {
  const work = copy.paintings.works[index], asset = patternAssets[index + 4], crop = crops[index];
  const label = (text: string) => text.split(/[:：]/, 1)[0];
  const descriptions = [work.description, ...work.details];
  const labels = [copy.ui.whole, ...work.details.map(label)];
  return <figure className="ig-art">
    <a className="ig-art-image" href={asset.variants[2].url} data-enlarge-image data-full={asset.variants[2].url} data-title={work.title} aria-label={`${copy.ui.enlarge}: ${work.title}`}>
      <svg className="ig-art-canvas" viewBox={crop.whole} xmlns="http://www.w3.org/2000/svg" role="img" aria-label={work.title}><title>{work.title}</title><image data-lazy-image={asset.variants[1].url} data-detail-image={asset.variants[2].url} width={crop.width} height={crop.height} /></svg>
      <span className="ig-detail-tag">{copy.ui.whole} · {copy.ui.enlarge}</span>
    </a>
    <noscript><img src={asset.variants[1].url} alt={work.title} width={asset.variants[1].width} height={asset.variants[1].height} loading="lazy" /></noscript>
    <div className="ig-art-controls" role="group" aria-label={work.title}>{labels.map((text, i) => <button key={i} type="button" data-art-view={i ? "detail" : "whole"} data-box={i ? crop.boxes[i - 1] : crop.whole} data-description={descriptions[i]} aria-pressed={i === 0}>{text}</button>)}</div>
    <figcaption><strong>{work.title}</strong><p>{work.caption}</p><p>{work.credit}{asset.artistHref && <> · <Link href={asset.artistHref} prefetch={false}>Shaikh Zada</Link></>}</p><p><RefText text={work.record} copy={copy} />{asset.catalogueHref && <> · <Link href={asset.catalogueHref} prefetch={false}>{copy.ui.catalogue}</Link></>}</p></figcaption>
    <p className="ig-art-description" aria-live="polite">{work.description}</p>
  </figure>;
}

export function IslamicPatternGuide({ copy }: { copy: PatternGuideCopy }) {
  const families = copy.construction.families;
  const first = families[0];
  const navigation = [["seeing-patterns", copy.opening.title], ["pattern-geometry", copy.construction.title], ["patterns-in-life", copy.materials.title], ["pattern-paintings", copy.paintings.title], ["pattern-colour", copy.colour.title], ["pattern-studio", copy.studio.title], ["pattern-reading", copy.reading.title]];
  const interactive = { ui: copy.ui, construction: copy.construction, symmetry: copy.symmetry, colour: copy.colour, studio: copy.studio };
  return <main id="main-content">
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: copy.ui.guides, path: "/guides" }, { name: copy.guideTitle, path: patternGuidePath(copy.locale) }])} />
    <StructuredData data={{ "@context": "https://schema.org", "@type": "Article", headline: copy.title, name: copy.guideTitle, description: copy.intro, inLanguage: copy.locale, url: absoluteURL(patternGuidePath(copy.locale)), image: absoluteURL(patternAssets[0].variants[1].url), dateModified: "2026-10-18", publisher: { "@type": "Organization", name: "Artline" } }} />
    <PatternInteractions copy={interactive} locale={copy.locale} className={`${styles.scope} ${cls("article")}`}>
      <div className={styles.guideBar}><Link href="/guides">← {copy.ui.guides}</Link><nav aria-label={copy.ui.language}>{Object.entries(guideLanguages).map(([locale, name]) => <Link key={locale} href={patternGuidePath(locale)} lang={locale} hrefLang={locale} aria-current={locale === copy.locale ? "page" : undefined} prefetch={false}>{name}</Link>)}</nav></div>
      <header className={cls("hero")}>
        <div><p className={cls("breadcrumb")}>{copy.eyebrow}</p><h1>{copy.title}</h1><p className={cls("lead")}>{copy.intro}</p><a className={cls("action")} href="#pattern-studio">{copy.studio.title}</a><p className={cls("free")}>{copy.deck}</p></div>
        <Figure asset={patternAssets[0]} text={copy.hero} copy={copy} eager />
      </header>
      <nav className={cls("contents")} aria-label={copy.guideTitle}>{navigation.map(([id, title]) => <a key={id} href={`#${id}`}>{title}</a>)}</nav>
      <section id="seeing-patterns" className={cls("section")}><div className={cls("prose")}><h2>{copy.opening.title}</h2><Paragraphs values={copy.opening.paragraphs} copy={copy} /></div></section>
      <section id="pattern-geometry" className={cls("section")}>
        <div className={cls("prose")}><h2>{copy.construction.title}</h2><p>{copy.construction.intro}</p></div>
        <div className="ig-construction">
          <div className="ig-family-tabs" role="group" aria-label={copy.construction.title}>{families.map(f => <button key={f.id} type="button" data-family={f.id} aria-pressed={f.id === first.id}><svg viewBox="-18 -18 36 36" aria-hidden="true" /><span>{f.title}</span><small>{f.n} · {f.angle}°</small></button>)}</div>
          <div className="ig-construction-body"><div id="construction-view" className="ig-construction-view" aria-live="off"><svg viewBox="-280 -190 560 380" role="img" aria-label={first.title}><circle r="139" cx="0" cy="0" fill="none" stroke="#efdfb7" /></svg></div><div className="ig-construction-copy">
            <div className="ig-stage-tabs" role="group" aria-label={copy.construction.title}>{[copy.ui.construction, copy.ui.motif, copy.ui.arrangement].map((stage, i) => <button key={i} type="button" data-stage={i} aria-pressed={i === 0}>{i + 1}. {stage}</button>)}</div>
            <h3 id="construction-title">{first.titles[0]}</h3><p id="construction-text">{first.text[0]}</p><p id="construction-fact" className="ig-fact">{first.facts[0]}</p><p id="construction-foot" className="ig-foot">{first.foot}</p>
          </div></div>
        </div>
        <details className={styles.constructionText}><summary>{copy.construction.title} · {copy.ui.construction}</summary>{families.map(f => <section key={f.id}><h3>{f.title}</h3>{f.text.map((text, i) => <div key={i}><h4>{f.titles[i]}</h4><p>{text}</p><p>{f.facts[i]}</p></div>)}<p>{f.foot}</p></section>)}</details>
        <div className={cls("prose")}><h3>{copy.symmetry.title}</h3><p>{copy.symmetry.intro}</p></div>
        <div className="ig-symmetry"><div className="ig-symmetry-pair"><figure><div id="symmetry-star" /><figcaption>{copy.ui.star}</figcaption></figure><figure><div id="symmetry-grid" /><figcaption>{copy.ui.grid} <span id="grid-status" data-match="true">{copy.ui.matches}</span></figcaption></figure></div><div className="ig-symmetry-copy"><h3>{copy.symmetry.question}</h3><p id="symmetry-note" aria-live="polite">{copy.symmetry.initial}</p><div className="ig-controls"><button id="turn-button" type="button">{copy.ui.turn}</button><button id="turn-reset" type="button">{copy.ui.reset}</button><output id="turn-value">0°</output></div></div></div>
        <div className={cls("prose")}><Paragraphs values={copy.symmetry.paragraphs} copy={copy} /></div>
      </section>
      <section id="patterns-in-life" className={cls("section")}>
        <div className={cls("prose")}><h2>{copy.materials.title}</h2><p>{copy.materials.intro}</p></div>
        <div className={cls("objects")}>{copy.materials.objects.map((object, i) => <div key={i}><h3>{object.heading}</h3><Figure asset={patternAssets[i + 1]} text={object.figure} copy={copy} /><Paragraphs values={object.paragraphs} copy={copy} /></div>)}</div>
      </section>
      <section id="pattern-paintings" className={cls("section")}><div className={cls("prose")}><h2>{copy.paintings.title}</h2><p>{copy.paintings.intro}</p></div><div className="ig-art-grid"><Painting index={0} copy={copy} /><Painting index={1} copy={copy} /></div><div className={cls("prose")}><p>{copy.paintings.closing}</p></div></section>
      <section id="pattern-colour" className={cls("section")}><div className={cls("prose")}><h2>{copy.colour.title}</h2><Paragraphs values={copy.colour.paragraphs} copy={copy} /></div><div className="ig-colour-comparison"><div className="ig-colour-pair"><figure><div id="colour-reference" /><figcaption>{copy.ui.original}</figcaption></figure><figure><div id="colour-changed" /><figcaption id="colour-label">{copy.ui.swap}</figcaption></figure></div><div className="ig-colour-controls"><h3>{copy.colour.question}</h3><div className="ig-controls">{[["reverse", copy.ui.swap], ["lines", copy.ui.outlines], ["same", copy.ui.original]].map(([key, label]) => <button key={key} type="button" data-colour-mode={key} aria-pressed={key === "reverse"}>{label}</button>)}</div><p id="colour-note" aria-live="polite">{copy.colour.states[0]}</p></div></div><div className={cls("prose")}><p>{copy.colour.closing}</p></div></section>
      <section id="pattern-studio" className={cls("section")} aria-labelledby="studio-heading"><div className={cls("prose")}><h2 id="studio-heading">{copy.studio.title}</h2><p>{copy.studio.intro}</p></div>
        <div className="sp-workshop"><div className="sp-gallery-heading">{copy.studio.choose}</div><div className="sp-pattern-gallery" role="group" aria-label={copy.studio.choose}>{copy.studio.patterns.map((p, i) => <button key={p.id} type="button" data-studio-pattern={p.id} aria-pressed={i === 0}><span className="sp-thumbnail" /><strong>{p.name}</strong><small>{p.tag}</small></button>)}</div>
          <div className="sp-workspace"><div className="sp-settings"><div className="sp-current"><h3 id="studio-current-name">{copy.studio.patterns[0].name}</h3><p id="studio-pattern-note">{copy.studio.patterns[0].note}</p></div>
            <fieldset className="sp-palette-field"><legend>{copy.ui.palette}: <span id="studio-palette-name">{copy.ui.palettes[0]}</span></legend><div className="sp-palette-options">{copy.ui.palettes.map((palette, i) => <button key={palette} type="button" data-studio-palette={i} aria-label={palette} title={palette} aria-pressed={i === 0}><span className={`sp-palette-swatch sp-palette-${i}`} aria-hidden="true" />{palette}</button>)}</div></fieldset>
            <label>{copy.ui.style}<select id="maker-style" defaultValue="mosaic"><option value="mosaic">{copy.ui.styles[0]}</option><option value="outline">{copy.ui.styles[1]}</option><option value="double">{copy.ui.styles[2]}</option></select></label>
            <label>{copy.ui.scale}<span><input id="maker-scale" type="range" min="70" max="130" step="5" defaultValue="100" /><output id="maker-scale-value" htmlFor="maker-scale">100%</output></span></label>
            <label>{copy.ui.weight}<span><input id="maker-weight" type="range" min="0.6" max="3" step="0.2" defaultValue="1.2" /><output id="maker-weight-value" htmlFor="maker-weight">1.2</output></span></label>
            <label>{copy.ui.rotation}<span><input id="maker-angle" type="range" min="0" max="60" step="5" defaultValue="0" /><output id="maker-angle-value" htmlFor="maker-angle">0°</output></span></label>
          </div><div className="sp-canvas-wrap"><div id="maker-view" /><p className="sp-paint-hint">{copy.studio.hint}</p><p className="sp-keyboard-hint">{copy.studio.keyboard}</p></div></div>
          <div className="sp-actions"><div><button id="maker-undo" type="button" disabled>↶ {copy.ui.undo}</button><button id="maker-reset" type="button" disabled>{copy.ui.resetColours}</button></div><div><button id="maker-download-png" type="button">{copy.ui.downloadPNG}</button><button id="maker-download" type="button">{copy.ui.downloadSVG}</button></div></div><p className="sp-export-note">{copy.studio.exportNote}</p><p className="sp-note">{copy.studio.note}</p><p id="maker-live" className="sr-only" role="status" aria-live="polite" />
        </div>
      </section>
      <section id="pattern-reading" className={cls("section")}><div className={cls("prose")}><h2>{copy.reading.title}</h2><p>{copy.reading.intro}</p></div><div className={cls("books")}>{copy.reading.books.map(book => <div key={book.url}><p className={cls("bookMeta")}>{book.author}</p><h3><a href={book.url} target="_blank" rel="noreferrer">{book.title}</a></h3><p>{book.note}</p></div>)}</div></section>
      <section className={`${cls("section")} ${styles.sources}`}><h2>{copy.sources.title}</h2><Paragraphs values={copy.sources.paragraphs} copy={copy} /><ol>{Object.entries(copy.sources.references).map(([n, url]) => <li key={n} value={Number(n)}><a href={url} target="_blank" rel="noreferrer">{new URL(url).hostname} — {url.split("/").filter(Boolean).at(-1)}</a></li>)}</ol></section>
      <dialog id="image-dialog" aria-label={copy.ui.enlarge}><div className="dialog-header"><button type="button" aria-label={copy.ui.close}>{copy.ui.close} ×</button></div><img alt="" /><p /></dialog>
    </PatternInteractions>
  </main>;
}
