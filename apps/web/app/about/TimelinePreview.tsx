import Image from "next/image";
import Link from "@/components/MemberLink";
import { guidePortalLinks } from "@/lib/museum-guide-types";
import { previewYears, type PreviewWork } from "./about-content";
import { PreviewScroller } from "./PreviewScroller";
import styles from "./about.module.css";

export function TimelinePreview({ items }: { items: PreviewWork[] }) {
  const position = (year: number) => `${(year - previewYears.start) / (previewYears.end - previewYears.start) * 100}%`;
  const links = guidePortalLinks({ works: items.map(item => item.work), context: previewYears });

  return <PreviewScroller id="timeline-preview" label="Artwork timeline preview" previousLabel="Earlier artworks" nextLabel="Later artworks" dark
    heading={<div><h2 id="timelines-title">Travel through time.</h2><p>See the centuries in a single view.</p></div>}
    action={<Link href={links.all} className={styles.textLink} prefetch={false}>Open interactive timeline</Link>}>
    <div className={styles.timelineCanvas}>
      <div className={styles.timelineAxis} aria-hidden="true" />
      {[1500, 1600, 1700, 1800, 1900].map(year => <div className={styles.timelineTick} key={year} style={{ left: position(year) }} aria-hidden="true"><span>{year}</span></div>)}
      <ol className={styles.timelineWorks} aria-label="Selected artworks in chronological order">
        {items.map(({ guide, work }, index) => <li key={work.id} className={styles.timelineItem} data-lane={index % 2 ? "below" : "above"}
          style={{ left: position((work.start! + work.end!) / 2) }}>
          <Link href={`/guides/${guide}#work-${work.id}`} prefetch={false} aria-label={`${work.title}, ${work.artist}, ${work.date}. Read about this artwork`}>
            <Image src={work.image} alt="" width={320} height={220} unoptimized loading="lazy" />
            <span className={styles.timelineArtist}>{work.artist}</span><span className={styles.timelineDate}>{work.date}</span>
          </Link>
        </li>)}
      </ol>
    </div>
  </PreviewScroller>;
}
