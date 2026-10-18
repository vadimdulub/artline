import { IslamicPatternGuide } from "@/components/patterns/IslamicPatternGuide";
import { getPatternGuide, patternGuideMetadata } from "@/lib/pattern-guide";

export function generateMetadata() { return patternGuideMetadata(getPatternGuide()!); }
export default function Page() { return <IslamicPatternGuide copy={getPatternGuide()!} />; }
