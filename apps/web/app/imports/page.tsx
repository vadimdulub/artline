import type { Metadata } from "next";
import { EditorNav } from "@/components/EditorNav";

export const metadata: Metadata = { title: "Imports" };

export default function ImportsPage() {
  return (
    <main id="main-content" className="admin-page">
      <EditorNav />
      <header className="admin-heading"><div><h1>Imports</h1><p>Bring authority and museum records into a review queue.</p></div></header>
      <section className="import-empty">
        <div><h2>Import tools are not available yet</h2><p>For now, add painter records in the catalogue. Museum imports and CSV uploads will need a preview and review step before they can add or change your records.</p><a href="/catalogue">Open the catalogue</a></div>
      </section>
    </main>
  );
}
