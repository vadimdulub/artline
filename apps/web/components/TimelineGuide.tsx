import Link from "@/components/MemberLink";
import ReactMarkdown from "react-markdown";
import { StructuredData } from "./StructuredData";
import { absoluteURL, breadcrumbs, pageMetadata } from "@/lib/seo";
import { guideLanguages } from "@/lib/museum-guide-types";
import { timelineGuidePath, type TimelineGuide as TimelineGuideData } from "@/lib/timeline-guide";
import styles from "@/app/art-history-timeline/timeline-guide.module.css";

function Markdown({ children }: { children: string }) {
  return <ReactMarkdown components={{ a: ({ href = "", children: label }) => {
    const local = href.startsWith("https://artlines.org/") ? href.slice("https://artlines.org".length) : href;
    return local.startsWith("/") ? <Link href={local}>{label}</Link> : <a href={href} target="_blank" rel="noreferrer">{label}</a>;
  } }}>{children}</ReactMarkdown>;
}

export function timelineGuideMetadata(guide: TimelineGuideData) {
  const route = timelineGuidePath(guide.locale);
  const meta = pageMetadata(guide.title, guide.subtitle, route);
  return { ...meta, alternates: { canonical: absoluteURL(route), languages: Object.fromEntries([...Object.keys(guideLanguages).map(locale => [locale, absoluteURL(timelineGuidePath(locale as keyof typeof guideLanguages))]), ["x-default", absoluteURL(timelineGuidePath())]]) }, openGraph: { ...meta.openGraph, locale: guide.locale, type: "article" as const } };
}

export function TimelineGuide({ guide }: { guide: TimelineGuideData }) {
  const route = timelineGuidePath(guide.locale);
  return <main id="main-content" className={`admin-page prose-page ${styles.page}`} lang={guide.locale} dir={guide.locale === "ar" ? "rtl" : "ltr"} data-return-label={guide.title} data-return-path={route}>
    <StructuredData data={breadcrumbs([{ name: "Artline", path: "/" }, { name: "Guides", path: "/guides" }, { name: guide.title, path: route }])} />
    <header><p className={styles.eyebrow}>Artline guide</p><h1>{guide.title}</h1><p className={styles.subtitle}>{guide.subtitle}</p></header>
    <nav className={styles.languages} aria-label="Language">{Object.entries(guideLanguages).map(([locale, label]) => <Link key={locale} href={timelineGuidePath(locale as keyof typeof guideLanguages)} hrefLang={locale} lang={locale} aria-current={guide.locale === locale ? "page" : undefined}>{label}</Link>)}</nav>
    <div className={styles.introduction}>{guide.introduction.map((paragraph, index) => <Markdown key={index}>{paragraph}</Markdown>)}</div>
    {guide.sections.map(section => <section key={section.title}><h2>{section.title}</h2>{section.paragraphs.map((paragraph, index) => <Markdown key={index}>{paragraph}</Markdown>)}</section>)}
    <p className={styles.updated}><time dateTime={guide.updated}>{guide.updated}</time></p>
  </main>;
}
