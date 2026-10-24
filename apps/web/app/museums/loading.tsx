import { AtlasPageHeader } from "@/components/AtlasPageHeader";
import styles from "@/components/Museums.module.css";

export default function MuseumLoading() {
  return <main id="main-content" className={styles.page} aria-busy="true">
    <AtlasPageHeader title="Museums and collections" />
    <p role="status" className={styles.loading}>Opening the collections…</p>
    <div className={styles.museumGrid} aria-hidden="true">{Array.from({ length: 6 }, (_, index) => <div className={styles.museumSkeleton} key={index}><div className={styles.collectionImage} /><div><span /><span /><span /></div></div>)}</div>
  </main>;
}
