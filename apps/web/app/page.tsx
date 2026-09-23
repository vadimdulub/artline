import { TimelineExplorer } from "@/components/TimelineExplorer";
import { researchPreviewEnabled } from "@/lib/server-api";
import { absoluteURL, explorerMetadata, siteDescription } from "@/lib/seo";
import { StructuredData } from "@/components/StructuredData";
export function generateMetadata() { return explorerMetadata("Art history timeline, painters & artworks", siteDescription, "/"); }
export default function HomePage() {
  return <main id="main-content"><StructuredData data={{ "@context": "https://schema.org", "@type": "WebSite", name: "Artline", url: absoluteURL("/"), description: siteDescription, inLanguage: "en" }} /><TimelineExplorer preview={researchPreviewEnabled()} /></main>;
}
