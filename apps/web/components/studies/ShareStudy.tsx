"use client";
import { useEffect, useState } from "react";
import { studyRequest, type StudyView } from "@/lib/studies";
import { StudyDialog } from "./StudyDialog";
import styles from "./Studies.module.css";

export function ShareStudy({ id, close, changed }: { id: string; close: () => void; changed: () => void }) {
  const [data, setData] = useState<StudyView | null>(null), [error, setError] = useState(""), [busy, setBusy] = useState(false), [message, setMessage] = useState(""), [retry, setRetry] = useState(0);
  const [origin, setOrigin] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    studyRequest<StudyView>(`/${id}`, { signal: controller.signal }).then(result => { setData(result); setOrigin(window.location.origin); }).catch(error => { if (!controller.signal.aborted) setError(error.message); });
    return () => controller.abort();
  }, [id, retry]);
  async function changeSharing(isPublic: boolean) {
    setBusy(true); setError(""); setMessage("");
    try {
      await studyRequest(`/${id}`, { method: "PATCH", body: JSON.stringify({ public: isPublic }) });
      changed();
      // Re-read the server's token; never invent a share URL in the browser.
      setData(await studyRequest<StudyView>(`/${id}`));
      setMessage(isPublic ? "Public link enabled. Visitors can read this study without signing in." : "Study is private. The previous link no longer works.");
    } catch (error) { setData(null); setError(error instanceof Error ? error.message : "Sharing could not be updated. Please reload its status."); }
    finally { setBusy(false); }
  }
  const url = data?.share_token ? `${origin}/shared/studies/${data.share_token}` : "";
  return <StudyDialog title="Share study" subtitle="Choose who can read this research." close={() => { if (!busy) close(); }} footer={<button disabled={busy} onClick={close}>Done</button>}>
    <div className={styles.sharePanel}>
      {error && <div role="alert" className={styles.error}><p>{error}</p><button onClick={() => { setError(""); setRetry(value => value + 1); }}>Reload sharing status</button></div>}
      {!data && !error && <p role="status">Loading sharing settings…</p>}
      {data && <>
        <div><h3>{data.public ? "Anyone with the link" : "Private"}</h3><p>{data.public ? "Visitors can read all records, sources and research notes, and compare artworks. Only you can make changes." : "Only you can access this study. A public link will let anyone read its records, sources and research notes without signing in."}</p></div>
        {data.public && url ? <>
          <label>Public link<input type="url" readOnly value={url} onFocus={event => event.target.select()} /></label>
          <div className={styles.shareLinkActions}><button disabled={busy} className={styles.primary} onClick={async () => { try { await navigator.clipboard.writeText(url); setMessage("Link copied."); } catch { setMessage("Select the public link above and copy it."); } }}>Copy link</button><a href={url} target="_blank" rel="noopener noreferrer">Open read-only view ↗</a></div>
          <p className={styles.help}>Changes you make appear in the public view. Making the study private disables this link.</p>
          <button disabled={busy} onClick={() => void changeSharing(false)}>{busy ? "Updating…" : "Make private"}</button>
        </> : <button disabled={busy} className={styles.primary} onClick={() => void changeSharing(true)}>{busy ? "Enabling…" : "Enable public link"}</button>}
      </>}
      <p role="status" className={styles.notice}>{message}</p>
    </div>
  </StudyDialog>;
}
