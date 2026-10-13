import type { GuideLocale, MuseumGuide } from "./museum-guide-types";

type PortalCopy = {
  all: string; allHint: string; allAction: string;
  painters: string; paintersHint: string; paintersAction: string;
  artwork: string; book: string; event: string;
};

export const guidePortalCopy: Record<GuideLocale, PortalCopy> = {
  en: { all: "Artworks in context", allHint: "Explore the selected works with books and history from their time.", allAction: "Explore the collection", painters: "Who lived when?", paintersHint: "See when the artists lived and whose lives overlapped.", paintersAction: "Open artist timeline", artwork: "Artwork", book: "Book", event: "Event" },
  ru: { all: "Искусство в контексте", allHint: "Изучите выбранные работы вместе с книгами и историей их эпохи.", allAction: "Открыть подборку", painters: "Кто когда жил?", paintersHint: "Узнайте, когда жили художники и кто был их современником.", paintersAction: "Открыть шкалу жизни художников", artwork: "Картина", book: "Книга", event: "Событие" },
  it: { all: "L’arte nel suo contesto", allHint: "Esplora le opere selezionate insieme ai libri e alla storia della loro epoca.", allAction: "Esplora la selezione", painters: "Chi visse quando?", paintersHint: "Scopri quando vissero gli artisti e chi furono i loro contemporanei.", paintersAction: "Apri la cronologia degli artisti", artwork: "Opera", book: "Libro", event: "Evento" },
  de: { all: "Kunst im Kontext", allHint: "Entdecke die ausgewählten Werke mit Büchern und Geschichte ihrer Zeit.", allAction: "Auswahl entdecken", painters: "Wer lebte wann?", paintersHint: "Sieh, wann die Künstler lebten und wer ihre Zeitgenossen waren.", paintersAction: "Zeitleiste der Künstler öffnen", artwork: "Kunstwerk", book: "Buch", event: "Ereignis" },
  zh: { all: "时代中的艺术", allHint: "结合同时代的书籍与历史，探索精选作品。", allAction: "探索精选作品", painters: "艺术家生活在何时？", paintersHint: "查看艺术家的生卒年代，发现谁与谁生活在同一时代。", paintersAction: "打开艺术家时间轴", artwork: "作品", book: "书籍", event: "事件" },
  fr: { all: "L’art dans son contexte", allHint: "Explorez les œuvres sélectionnées avec les livres et l’histoire de leur époque.", allAction: "Explorer la sélection", painters: "Qui vivait à quelle époque ?", paintersHint: "Découvrez quand les artistes ont vécu et qui étaient leurs contemporains.", paintersAction: "Ouvrir la chronologie des artistes", artwork: "Œuvre", book: "Livre", event: "Événement" },
  es: { all: "El arte en su contexto", allHint: "Explora las obras seleccionadas junto con los libros y la historia de su época.", allAction: "Explorar la selección", painters: "¿Quién vivió en cada época?", paintersHint: "Descubre cuándo vivieron los artistas y quiénes fueron sus contemporáneos.", paintersAction: "Abrir la cronología de artistas", artwork: "Obra", book: "Libro", event: "Acontecimiento" },
  pt: { all: "A arte no seu contexto", allHint: "Explore as obras selecionadas com os livros e a história da sua época.", allAction: "Explorar a seleção", painters: "Quem viveu em cada época?", paintersHint: "Descubra quando viveram os artistas e quem foram os seus contemporâneos.", paintersAction: "Abrir a cronologia dos artistas", artwork: "Obra", book: "Livro", event: "Evento" },
  ja: { all: "時代とともに見る芸術", allHint: "同時代の書籍や歴史とともに、選ばれた作品を見てみましょう。", allAction: "作品を見る", painters: "画家はいつ生きた？", paintersHint: "画家たちの生没年を比べ、同じ時代を生きた人々を見つけましょう。", paintersAction: "画家の年表を開く", artwork: "作品", book: "書籍", event: "出来事" },
  ar: { all: "الفن في سياقه", allHint: "استكشف الأعمال المختارة مع كتب عصرها وأحداثه التاريخية.", allAction: "استكشف الأعمال المختارة", painters: "من عاش ومتى؟", paintersHint: "اكتشف متى عاش الفنانون ومن عاصرهم.", paintersAction: "افتح الخط الزمني للفنانين", artwork: "عمل فني", book: "كتاب", event: "حدث" },
};

// Static editorial illustrations, never live timeline requests. Source evidence:
// content/articles/museum-guide-portal-images.json. Work indices refer to each
// guide's fixed selection, whose object identity is shared across translations.
const selections: Record<string, { artwork: number; artistWork: number }> = {
  louvre: { artwork: 2, artistWork: 16 },
  prado: { artwork: 1, artistWork: 8 },
  "munich-museums": { artwork: 10, artistWork: 0 },
  "leventis-gallery": { artwork: 1, artistWork: 0 },
  "muma-le-havre": { artwork: 0, artistWork: 10 },
  "national-gallery-armenia": { artwork: 12, artistWork: 13 },
};

export function guidePortalImages(guide: MuseumGuide) {
  const selection = selections[guide.slug] ?? { artwork: 0, artistWork: 0 };
  const laterPeriod = guide.context.start >= 1849;
  return {
    artwork: guide.works[selection.artwork] ?? guide.works[0],
    artistWork: guide.works[selection.artistWork] ?? guide.works[0],
    book: laterPeriod ? "/images/books/selected-20261010-books-work-2/wd-q185118.jpg" : "/images/books/selected-20261001/wd-q150827.jpg",
    event: laterPeriod ? "/images/events/selected-20261010-events-1/event-q957317.jpg" : "/images/events/selected-20261010-events-3/event-q6534.jpg",
  };
}
