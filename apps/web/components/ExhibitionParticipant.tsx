import Link from "./MemberLink";
import { ExhibitionImage } from "./ExhibitionImage";
import type { ExhibitionPerson } from "@/lib/exhibitions";
import styles from "@/app/exhibitions/exhibitions.module.css";

export function ExhibitionParticipant({ person, showHistory = false }: { person: ExhibitionPerson; showHistory?: boolean }) {
  const image = person.image || person.portrait;
  const artwork = Boolean(person.image && person.imageKind === "artwork");
  const alt = artwork ? `${person.imageTitle || "Key artwork"} — ${person.name}` : `Portrait of ${person.name}`;
  return <li>
    <ExhibitionImage src={image} width={person.imageWidth || 72} height={person.imageHeight || 88} alt={alt} portrait />
    <div>
      <h3>{person.artist_slug ? <Link href={`/artists/${person.artist_slug}`} prefetch={false}>{person.name}</Link> : person.name}</h3>
      <p className={styles.meta}>{[person.role.replaceAll("_", " "), person.nationality, person.birthday ? `${person.birthday}${person.deathday ? `–${person.deathday}` : ""}` : null].filter(Boolean).join(" · ")}</p>
      {showHistory && <div className={styles.personActions}><Link href={`/exhibitions?${person.artist_id ? `artist=${person.artist_id}` : `person=${person.id}`}`} prefetch={false}>Exhibition history</Link></div>}
      {image && <details className={styles.caption}>
        <summary>{artwork ? "Artwork & image credit" : "Portrait credit"}</summary>
        {artwork && <p>Key artwork: {person.imageTitle || "Title not recorded"}</p>}
        <p>{person.imageCredit}{person.imageLicense ? ` · ${person.imageLicense}` : ""}</p>
      </details>}
    </div>
  </li>;
}
