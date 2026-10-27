import Link from "next/link";
import MemberLink from "./MemberLink";
import { StructuredData } from "./StructuredData";
import { absoluteURL, breadcrumbs, pageMetadata } from "@/lib/seo";
import { getGuideIndex } from "@/lib/museum-guides";
import { getGuideMuseumLinks, museumCollectionLabels } from "@/lib/museum-guide-links";
import { guideLanguages, guideSubject, guideLocation, guidePath, guidePortalLinks, guideWorkPath as workPath, type MuseumGuide as Guide } from "@/lib/museum-guide-types";
import { guidePortalCopy, guidePortalImages } from "@/lib/museum-guide-portal";
import { museumGuideStructuredData } from "@/lib/museum-guide-seo";
import styles from "@/app/guides/museum-guide.module.css";

export function museumGuideMetadata(guide: Guide) {
  const route = guidePath(guide.slug, guide.locale);
  const meta = pageMetadata(guide.title, guide.subtitle, route, { image: guide.works[0]?.image });
  const locales = getGuideIndex().find(item => item.slug === guide.slug)!.locales;
  return { ...meta, alternates: { canonical: absoluteURL(route), languages: Object.fromEntries([...locales.map(locale => [locale, absoluteURL(guidePath(guide.slug, locale))]), ["x-default", absoluteURL(guidePath(guide.slug))]]) }, openGraph: { ...meta.openGraph, locale: guide.locale, type: "article" as const } };
}
export function MuseumGuide({ guide }: { guide: Guide }) {
  const l = guide.labels, links = guidePortalLinks(guide);
  const portal = guidePortalCopy[guide.locale], images = guidePortalImages(guide);
  const museums = getGuideMuseumLinks(guide);
  const locales = getGuideIndex().find(item => item.slug === guide.slug)!.locales;
  return <main id="main-content" className={styles.page} data-return-label={`${guideSubject(guide)} guide`} data-return-path={guidePath(guide.slug, guide.locale)} lang={guide.locale} dir={guide.locale === "ar" ? "rtl" : "ltr"}>
    <StructuredData data={museumGuideStructuredData(guide)} />
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Guides", path: "/guides" }, { name: guide.title, path: guidePath(guide.slug, guide.locale) }])} />
    <header className={styles.heading}>
      <div><p className={styles.place}>{guideLocation(guide)}</p><h1>{guide.title}</h1><p className={styles.subtitle}>{guide.subtitle}</p></div>
      <a className={styles.download} href={`/guides/${guide.slug}/pdf/${guide.locale}`} download={`${guide.slug}-${guide.locale}.pdf`}>{l.download}</a>
    </header>
    {museums.length > 0 && <nav className={styles.museumLinks} aria-label={museumCollectionLabels[guide.locale]}>{museums.map(museum => <MemberLink key={museum.slug} prefetch={false} href={museum.href}>{museumCollectionLabels[guide.locale]}: {museum.name}</MemberLink>)}</nav>}
    <nav className={styles.languages} aria-label={l.language}>{locales.map(locale => <Link key={locale} href={guidePath(guide.slug, locale)} hrefLang={locale} lang={locale} aria-current={guide.locale === locale ? "page" : undefined}>{guideLanguages[locale]}</Link>)}</nav>
    {guide.locale !== "en" && <p className={styles.translation}>{l.translation}</p>}
    <div className={styles.introduction}>{guide.introduction.split(/\n\s*\n/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}<p className={styles.note}>{guide.selectionNote}</p></div>
    <section className={styles.portal} aria-labelledby="guide-portal">
      <div><h2 id="guide-portal">{l.explore}</h2><p>{l.contextNote}</p><div className={styles.previews}>{guide.works.slice(0, 5).map(work => <a key={work.id} href={`#work-${work.id}`} title={`${work.artist}: ${work.title}`}><img src={work.image} alt={`${work.title} — ${work.artist}`} width="112" height="80" loading="lazy" /></a>)}</div></div>
      <nav className={styles.portalCards} aria-label={l.explore}>
        <Link prefetch={false} className={styles.portalCard} href={links.all} aria-labelledby="guide-context-title" aria-describedby="guide-context-hint">
          <div className={styles.contextImages} aria-hidden="true">
            {[{ src: images.artwork.image, label: portal.artwork }, { src: images.book, label: portal.book }, { src: images.event, label: portal.event }].map(image => <figure key={image.label}><img src={image.src} alt="" width="120" height="140" loading="lazy" /><figcaption>{image.label}</figcaption></figure>)}
          </div>
          <div className={styles.portalCardCopy}><h3 id="guide-context-title">{portal.all}</h3><p id="guide-context-hint">{portal.allHint}</p><span className={styles.portalAction}>{portal.allAction}<span aria-hidden="true">↗</span></span></div>
        </Link>
        <Link prefetch={false} className={styles.portalCard} href={links.painters} aria-labelledby="guide-artists-title" aria-describedby="guide-artists-hint">
          <div className={styles.artistImage} aria-hidden="true"><img src={images.artistWork.image} alt="" width="260" height="140" loading="lazy" /></div>
          <div className={styles.portalCardCopy}><h3 id="guide-artists-title">{portal.painters}</h3><p id="guide-artists-hint">{portal.paintersHint}</p><span className={styles.portalAction}>{portal.paintersAction}<span aria-hidden="true">↗</span></span></div>
        </Link>
      </nav>
    </section>
    <details className={styles.contents}><summary>{l.contents} ({guide.works.length})</summary><ol>{guide.works.map(work => <li key={work.id}><a href={`#work-${work.id}`}>{work.title}<span> — {work.artist}</span></a></li>)}</ol></details>
    <section aria-label={l.artworks} className={styles.works}>{guide.works.map((work, i) => <article id={`work-${work.id}`} key={work.id} className={styles.work}>
      <figure><a href={workPath(work)}><img src={work.image} alt={`${work.title} — ${work.artist}`} loading={i === 0 ? "eager" : "lazy"} width="800" height="650" /></a><figcaption><a href={work.imageSource} target="_blank" rel="noreferrer">{work.credit}</a>{work.license && <span> · <a href={work.licenseUrl || work.imageSource} target="_blank" rel="noreferrer">{work.license}</a></span>}</figcaption></figure>
      <div className={styles.copy}><span className={styles.number}>{String(i + 1).padStart(2, "0")}</span><h2>{work.title}</h2><p className={styles.artist}>{work.artists.length === 1 ? <Link prefetch={false} href={`/artists/${work.artists[0].slug}`}>{work.artist}</Link> : work.artist}</p><p className={styles.metadata}>{[work.date, work.medium, work.museum].filter(Boolean).join(" · ")}</p>{work.description.split(/\n\s*\n/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}{work.importance && <><h3>{l.importance}</h3>{work.importance.split(/\n\s*\n/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}</>}<div className={styles.workLinks}><Link prefetch={false} href={workPath(work)}>{l.artwork}</Link><a href={work.source} target="_blank" rel="noreferrer">{l.source}</a></div>{work.accession && <p className={styles.inventory}>{l.inventory}: {work.accession}</p>}</div>
    </article>)}</section>
    {guide.closingSections?.length ? <section className={styles.closing}>{guide.closingSections.map(section => <article key={section.title}><h2>{section.title}</h2>{section.paragraphs.map((paragraph, index) => <p key={index}>{paragraph}</p>)}</article>)}</section> : null}
    <section className={styles.reading} aria-labelledby="further-reading"><h2 id="further-reading">{l.reading}</h2><ul>{guide.books.map(book => <li key={book.url}><h3><a href={book.url} target="_blank" rel="noreferrer">{book.title}</a></h3><p className={styles.bookAuthor}>{book.author} <span>{book.access}</span></p><p>{book.note}</p></li>)}</ul></section>
    <aside className={styles.visit}>{!guide.closingSections?.length && <><h2>{l.visit}</h2><p>{guide.visitNote}</p></>}<p><a href={guide.website} target="_blank" rel="noreferrer">{l.website}</a>{guide.officialGuide && <> · <a href={guide.officialGuide} target="_blank" rel="noreferrer">{l.officialGuide}</a></>}</p><p className={styles.note}>{l.updated}: {guide.updated}</p></aside>
    <footer className={styles.end}><a className={styles.download} href={`/guides/${guide.slug}/pdf/${guide.locale}`} download>{l.download}</a></footer>
  </main>;
}
