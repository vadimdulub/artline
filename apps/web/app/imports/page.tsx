import type { Metadata } from "next";
import Link from "next/link";
import { EditorNav } from "@/components/EditorNav";

export const metadata: Metadata = { title: "Imports" };

export default function ImportsPage() {
  return (
    <main id="main-content" className="admin-page">
      <EditorNav />
      <header className="admin-heading"><div><h1>Imports</h1><p>Bring authority and museum records into a review queue.</p></div></header>
      <section className="import-empty">
        <div><h2>Manage catalogue records</h2><p>Open the catalogue to add or edit painter records.</p><Link href="/catalogue">Open the catalogue</Link></div>
      </section>
    </main>
  );
}
