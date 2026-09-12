"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { CoverageSummary } from "@/lib/types";
import { apiRequest, editorHeaders, errorMessage } from "@/lib/api";
import { EditorAccess, useEditorToken } from "./EditorAccess";

export function CoverageClient() {
  const [summary, setSummary] = useState<CoverageSummary | null>(null);
  const [error, setError] = useState("");
  const [token, setToken] = useEditorToken();
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest<CoverageSummary>("coverage/summary", { headers: editorHeaders(token), signal: controller.signal })
      .then(data => { setSummary(data); setError(""); })
      .catch(error => { if (!controller.signal.aborted) { setError(errorMessage(error)); setSummary(null); } });
    return () => controller.abort();
  }, [token, retry]);

  if (error) return <><EditorAccess token={token} onChange={setToken} /><div className="record-error"><h2>Coverage unavailable</h2><p>{error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div></>;
  if (!summary) return <p className="record-loading">Calculating catalogue coverage…</p>;

  const statuses = ["published", "review", "draft", "archived"];
  return (
    <>
      <div className="coverage-lead"><strong>{summary.total_artists}</strong><span>painters in the catalogue</span></div>
      <div className="coverage-grid">
        {statuses.map((status) => <Link key={status} href={`/catalogue?status=${status}`}><span>{status === "review" ? "In review" : status[0].toUpperCase() + status.slice(1)}</span><strong>{summary.by_status[status] ?? 0}</strong><small>View painters</small></Link>)}
      </div>
      <section className="quality-section">
        <h2>What needs attention</h2>
        <dl>
          <div><dt>Fewer than five published works</dt><dd>{summary.missing_representative_works}</dd></div>
          <div><dt>Missing short biography</dt><dd>{summary.missing_biography}</dd></div>
          <div><dt>Nordic records</dt><dd>{summary.nordic_artists}</dd></div>
          <div><dt>Asian records</dt><dd>{summary.asian_artists}</dd></div>
        </dl>
      </section>
      <p className="coverage-note">These counts describe this small research collection, not the history of painting as a whole. Regional distributions and detailed gap reports are still planned.</p>
    </>
  );
}
