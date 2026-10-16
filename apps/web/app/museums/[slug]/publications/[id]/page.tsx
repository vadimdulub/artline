import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { PickerImage } from "@/components/MuseumArtworkPicker";
import { notFound, redirect } from "next/navigation";
import { getMuseumPublication, getPublishedMuseum } from "@/lib/museum-publications";
import { getMuseum } from "@/lib/server-api";
import { pageMetadata } from "@/lib/seo";
import { museumImageURL, publicationPath } from "@/lib/museum-studio";
import { PublicationImage } from "@/components/MuseumPublicationView";
import styles from "@/components/MuseumPublic.module.css";
async function record(slug: string, id: string) {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100 || !/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(id)) notFound();
  const item = await getMuseumPublication(slug, id); if (!item) notFound(); return item;
}
export async function generateMetadata({ params }: { params: Promise<{ slug: string; id: string }> }) {
  const { slug, id } = await params, item = await record(slug, id);
  return pageMetadata(item.document.title, item.document.summary || "Published by the museum on Artline.", publicationPath(slug, id));
}
export default async function Page({ params }: { params: Promise<{ slug: string; id: string }> }) {
  const { slug, id } = await params, item = await record(slug, id);
  if (item.kind === "profile") redirect(`/museums/${slug}`);
  const museum = await getMuseum(slug) ?? await getPublishedMuseum(slug); if (!museum) notFound();
  const d = item.document;
  const facts = [["Artist / attribution", d.creator], ["Recorded date", d.date_label], ["Medium", d.medium], ["Dimensions", d.dimensions], ["Inventory", d.inventory], ["Opening date", d.start_date], ["Closing date", d.end_date], ["Venue", d.venue], ["Language", d.language]].filter(([, value]) => !!value);
  return <main id="main-content" className={styles.page}><Link className={styles.back} href={`/museums/${slug}`}>{museum.name}</Link><article><div className={styles.record}>{museumImageURL(slug, d) && <figure><PublicationImage item={item} slug={slug} /><figcaption>{d.image_credit}</figcaption></figure>}<header><p className={styles.note}>Published by {museum.name}</p><h1>{d.title}</h1>{d.summary && <p>{d.summary}</p>}<dl>{facts.map(([label, value]) => <div key={label} style={{ display: "contents" }}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>{d.source_url && <a href={d.source_url} target="_blank" rel="noreferrer">Source & further information</a>}</header></div>{d.body && <div className={d.body_format === "markdown" ? styles.formattedBody : styles.body}>{d.body_format === "markdown" ? <ReactMarkdown skipHtml disallowedElements={["img"]} components={{ h1: ({ children }) => <h2>{children}</h2> }}>{d.body}</ReactMarkdown> : d.body}</div>}
    {!!item.resolved_artworks?.length && <section className={styles.artworkSequence} aria-label="Artworks in this publication">{item.resolved_artworks.map((work, index) => <article className={styles.artworkEntry} key={work.kind + work.id}>
      {work.available && work.image_url && <figure><PickerImage item={work} />{work.credit && <figcaption>{work.credit}</figcaption>}</figure>}
      <div><p className={styles.note}>Artwork {index + 1}</p><h2>{work.available && work.href ? <Link href={work.href}>{work.title}</Link> : "Artwork unavailable"}</h2>{work.available ? <><p>{[work.creator, work.date].filter(Boolean).join(" · ")}</p>{work.note && <p className={styles.artworkNote}>{work.note}</p>}<Link href={work.href}>Artwork details and source</Link></> : <p>This artwork is no longer publicly available.</p>}</div>
    </article>)}</section>}<p className={styles.note}>Museum publication. {item.kind === "artwork" && "Collection information does not confirm current display."}</p></article></main>;
}
