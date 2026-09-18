import type { Metadata } from "next";
import { AllAtlas } from "@/components/AllAtlas";
export const metadata: Metadata = { title: "All · Artline", description: "Explore artwork, literature and events together through thirty historical lenses." };
export default function AllPage() { return <main id="main-content" className="all-page"><AllAtlas /></main>; }
