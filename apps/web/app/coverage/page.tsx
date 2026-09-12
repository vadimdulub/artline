import type { Metadata } from "next";
import { CoverageClient } from "@/components/CoverageClient";
import { EditorNav } from "@/components/EditorNav";

export const metadata: Metadata = { title: "Coverage" };

export default function CoveragePage() {
  return <main id="main-content" className="admin-page"><EditorNav /><header className="admin-heading"><div><h1>Coverage</h1><p>How the collection is growing, and where it needs attention.</p></div></header><CoverageClient /></main>;
}
