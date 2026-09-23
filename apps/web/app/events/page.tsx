import { explorerMetadata } from "@/lib/seo";
import { EventsIndex } from "@/components/EventsIndex";

export function generateMetadata() { return explorerMetadata("Historical events & movements", "Explore the events, movements and historical periods that connect art, books and world history through 2000.", "/events"); }
export default function EventsPage() { return <main id="main-content"><EventsIndex /></main>; }
