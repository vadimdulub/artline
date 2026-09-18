import type { Metadata } from "next";
import { EventsIndex } from "@/components/EventsIndex";

export const metadata: Metadata = {
  title: "Events · Artline",
  description: "Explore the events, movements and historical periods that connect art, books and world history through 2000.",
};
export default function EventsPage() { return <main id="main-content"><EventsIndex /></main>; }
