import { guideLanguages, type GuideLocale } from "./museum-guide-types";

export type TimelineIntroductionKind = "artworks" | "lifespans";
type Copy = { artworksTitle: string; artworks: string; contextNote: string; lifespansTitle: string; lifespans: string; overlapNote: string; guideArtists: string; help: string; dismiss: string };

// Editorial interface copy, authored locally; no translation service.
export const timelineIntroductionCopy: Record<GuideLocale, Copy> = {
  en: {
    artworksTitle: "Your guide in context",
    artworks: "See this guide’s artworks by their recorded creation dates, alongside selected books and historical events from the same period.",
    contextNote: "Shared dates give context, not proof of influence. Change the years or select an entry to explore.",
    lifespansTitle: "Who lived at the same time?",
    lifespans: "Each bar follows an artist’s recorded lifespan or active years. Overlapping bars show who lived or worked at the same time. Select an artist to explore their artworks.",
    overlapNote: "An overlap does not mean the artists met or influenced each other.",
    guideArtists: "This view starts with the artists linked from your guide.",
    help: "How this view works", dismiss: "Got it",
  },
  ru: {
    artworksTitle: "Ваш путеводитель в контексте эпохи",
    artworks: "Рассмотрите произведения из путеводителя по указанным датам создания — рядом с избранными книгами и историческими событиями того же времени.",
    contextNote: "Совпадение дат даёт контекст, но не доказывает влияние. Измените период или выберите запись, чтобы узнать больше.",
    lifespansTitle: "Кто жил в одно время?",
    lifespans: "Каждая полоса показывает известные годы жизни или творчества художника. Пересечения помогают увидеть современников. Выберите художника, чтобы рассмотреть его работы.",
    overlapNote: "Совпадение периодов не означает, что художники встречались или влияли друг на друга.",
    guideArtists: "Сначала здесь выбраны художники, связанные с вашим путеводителем.",
    help: "Как устроен этот вид", dismiss: "Понятно",
  },
  it: {
    artworksTitle: "La tua guida nel contesto dell’epoca",
    artworks: "Esplora le opere della guida secondo le date di creazione registrate, accanto a una selezione di libri ed eventi storici dello stesso periodo.",
    contextNote: "Le date comuni offrono un contesto, non dimostrano un’influenza. Cambia gli anni o seleziona una voce per approfondire.",
    lifespansTitle: "Chi visse nello stesso periodo?",
    lifespans: "Ogni barra rappresenta gli anni di vita o di attività documentati di un artista. Le sovrapposizioni mostrano chi visse o lavorò nello stesso periodo. Seleziona un artista per esplorarne le opere.",
    overlapNote: "Una sovrapposizione non implica incontri o influenze reciproche.",
    guideArtists: "La vista parte dagli artisti collegati alla tua guida.",
    help: "Come funziona questa vista", dismiss: "Ho capito",
  },
  de: {
    artworksTitle: "Dein Kunstführer im Zeitkontext",
    artworks: "Sieh die Werke aus dem Kunstführer nach ihren erfassten Entstehungsdaten, zusammen mit ausgewählten Büchern und historischen Ereignissen derselben Zeit.",
    contextNote: "Zeitliche Nähe gibt Kontext, belegt aber keinen Einfluss. Ändere den Zeitraum oder wähle einen Eintrag, um mehr zu erfahren.",
    lifespansTitle: "Wer lebte zur gleichen Zeit?",
    lifespans: "Jeder Balken zeigt die überlieferten Lebens- oder Schaffensjahre eines Künstlers. Überschneidungen zeigen, wer zur gleichen Zeit lebte oder arbeitete. Wähle einen Künstler, um seine Werke zu erkunden.",
    overlapNote: "Eine Überschneidung belegt weder eine Begegnung noch gegenseitigen Einfluss.",
    guideArtists: "Diese Ansicht beginnt mit den Künstlern, die mit deinem Kunstführer verknüpft sind.",
    help: "So funktioniert diese Ansicht", dismiss: "Verstanden",
  },
  zh: {
    artworksTitle: "把导览放回时代之中",
    artworks: "按记录的创作年代浏览本导览中的作品，并对照同一时期精选的书籍与历史事件。",
    contextNote: "年代相近提供时代背景，并不证明影响关系。调整年份或选择条目，了解更多。",
    lifespansTitle: "谁生活在同一个时代？",
    lifespans: "每条横线表示艺术家有记录的生卒年或活动年代。重叠部分显示谁曾在同一时期生活或创作。选择艺术家，即可探索其作品。",
    overlapNote: "年代重叠不代表艺术家曾经见面或相互影响。",
    guideArtists: "此视图最初选中与本导览相关的艺术家。",
    help: "如何阅读此视图", dismiss: "明白了",
  },
  fr: {
    artworksTitle: "Votre guide dans son époque",
    artworks: "Découvrez les œuvres du guide selon leurs dates de création répertoriées, aux côtés d’une sélection de livres et d’événements historiques de la même période.",
    contextNote: "Des dates communes donnent un contexte, sans prouver une influence. Modifiez les années ou sélectionnez une entrée pour en savoir plus.",
    lifespansTitle: "Qui vivait à la même époque ?",
    lifespans: "Chaque barre suit les années de vie ou d’activité documentées d’un artiste. Les chevauchements montrent qui vivait ou travaillait à la même époque. Sélectionnez un artiste pour explorer ses œuvres.",
    overlapNote: "Un chevauchement ne signifie pas que les artistes se sont rencontrés ou influencés.",
    guideArtists: "Cette vue commence par les artistes liés à votre guide.",
    help: "Comprendre cette vue", dismiss: "Compris",
  },
  es: {
    artworksTitle: "Tu guía en su contexto",
    artworks: "Explora las obras de la guía según sus fechas de creación registradas, junto con una selección de libros y acontecimientos históricos del mismo período.",
    contextNote: "Las fechas compartidas aportan contexto, no prueban influencias. Cambia los años o selecciona una entrada para saber más.",
    lifespansTitle: "¿Quiénes vivieron en la misma época?",
    lifespans: "Cada barra muestra los años de vida o actividad documentados de un artista. Las coincidencias muestran quiénes vivieron o trabajaron en la misma época. Selecciona un artista para explorar sus obras.",
    overlapNote: "Coincidir en el tiempo no significa que los artistas se conocieran o influyeran entre sí.",
    guideArtists: "Esta vista comienza con los artistas vinculados a tu guía.",
    help: "Cómo funciona esta vista", dismiss: "Entendido",
  },
  pt: {
    artworksTitle: "O seu guia no contexto da época",
    artworks: "Explore as obras do guia pelas datas de criação registadas, ao lado de uma seleção de livros e acontecimentos históricos do mesmo período.",
    contextNote: "Datas em comum oferecem contexto, não provam influências. Altere os anos ou selecione uma entrada para saber mais.",
    lifespansTitle: "Quem viveu na mesma época?",
    lifespans: "Cada barra mostra os anos de vida ou de atividade documentados de um artista. As sobreposições mostram quem viveu ou trabalhou na mesma época. Selecione um artista para explorar as suas obras.",
    overlapNote: "Uma sobreposição não significa que os artistas se conheceram ou influenciaram mutuamente.",
    guideArtists: "Esta vista começa com os artistas associados ao seu guia.",
    help: "Como funciona esta vista", dismiss: "Entendido",
  },
  ja: {
    artworksTitle: "ガイドの作品を時代の中で見る",
    artworks: "ガイドの作品を記録された制作年代に沿って、同時代の選ばれた書籍や歴史上の出来事とともに見てみましょう。",
    contextNote: "年代の一致は時代背景を示しますが、影響関係の証拠ではありません。年代を変えたり、項目を選んだりして探索できます。",
    lifespansTitle: "誰が同じ時代を生きたのでしょう？",
    lifespans: "各バーは、記録された芸術家の生没年または活動年代を示します。重なりから、誰が同時代に生き、制作したかが分かります。芸術家を選ぶと作品を探索できます。",
    overlapNote: "年代が重なっていても、互いに会ったり影響を与え合ったりしたとは限りません。",
    guideArtists: "最初は、このガイドに関連する芸術家が選択されています。",
    help: "この画面の見方", dismiss: "分かりました",
  },
  ar: {
    artworksTitle: "دليلك في سياق عصره",
    artworks: "استكشف أعمال هذا الدليل بحسب تواريخ إنجازها المسجّلة، إلى جانب كتب مختارة وأحداث تاريخية من الفترة نفسها.",
    contextNote: "تقارب التواريخ يوضح السياق، ولا يثبت التأثير. غيّر السنوات أو اختر عنصراً لمعرفة المزيد.",
    lifespansTitle: "من عاش في الفترة نفسها؟",
    lifespans: "يمثّل كل شريط سنوات حياة الفنان أو نشاطه المسجّلة. وتوضح الأشرطة المتداخلة من عاش أو عمل في الفترة نفسها. اختر فناناً لاستكشاف أعماله.",
    overlapNote: "تداخل الفترات لا يعني أن الفنانين التقوا أو أثّر بعضهم في بعض.",
    guideArtists: "يبدأ هذا العرض بالفنانين المرتبطين بدليلك.",
    help: "كيف تقرأ هذا العرض", dismiss: "فهمت",
  },
};

export function timelineGuideContext(params: URLSearchParams) {
  const slug = params.get("guide") ?? "";
  const fromGuide = /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug);
  const language = params.get("guide_lang") ?? "en";
  const locale: GuideLocale = fromGuide && Object.hasOwn(guideLanguages, language) ? language as GuideLocale : "en";
  return { fromGuide, locale };
}
