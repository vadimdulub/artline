import { MuseumsIndex } from "@/components/MuseumsIndex";
import { explorerMetadata } from "@/lib/seo";
export function generateMetadata() { return explorerMetadata("Museums & art collections", "Explore museums, documented art collections and selected artworks. Discover collection records, sources and official visiting information.", "/museums"); }
export default function MuseumsPage() { return <MuseumsIndex />; }
