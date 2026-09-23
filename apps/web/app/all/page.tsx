import { explorerMetadata } from "@/lib/seo";
import { AllAtlas } from "@/components/AllAtlas";
export function generateMetadata() { return explorerMetadata("Art, literature & world history atlas", "Explore artwork, literature and events together through thirty historical lenses.", "/all"); }
export default function AllPage() { return <main id="main-content" className="all-page"><AllAtlas /></main>; }
