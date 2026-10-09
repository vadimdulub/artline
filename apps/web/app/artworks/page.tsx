import { ArtworksIndex } from "@/components/ArtworksIndex";
import { explorerMetadata } from "@/lib/seo";

export function generateMetadata() {
  return explorerMetadata("Artwork catalogue", "Browse Artline's recorded artworks, including research records, undated works and museum collections.", "/artworks");
}
export default function ArtworksPage() { return <ArtworksIndex />; }
