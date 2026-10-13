import { AtlasPageHeader } from "@/components/AtlasPageHeader";
import styles from "@/components/Museums.module.css";

export default function MuseumLoading() {
  return <main id="main-content" className={styles.page} aria-busy="true">
    <AtlasPageHeader title="Museums and collections" />
    <p role="status" className={styles.loading}>Opening the collections…</p>
  </main>;
}
