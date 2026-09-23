import { BooksIndex } from "@/components/BooksIndex";

import { explorerMetadata } from "@/lib/seo";
export function generateMetadata() { return explorerMetadata("Books & literature through history", "Explore books connecting art, philosophy, faith and the way people make meaning in Artline’s literature timeline.", "/books"); }

export default function BooksPage() { return <main id="main-content"><BooksIndex /></main>; }
