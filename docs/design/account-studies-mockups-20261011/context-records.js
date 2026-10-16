// Small source-backed context fixtures for the design preview only.
window.CONTEXT_RECORDS = [
  {
    id: 50001, kind: 'book', title: 'L’Assommoir', artist_title: 'Émile Zola',
    date_display: '1877 · first book edition', intervals: [[1877, 1877]],
    dateNote: 'First book edition: 1877. Serial publication began in 1876. The timeline marks the book edition, not its earlier serialization.',
    source: 'https://data.bnf.fr/ark:/12148/cb12001598m',
    sourceName: 'Bibliothèque nationale de France',
    additionalSource: 'https://catalogue.bnf.fr/ark:/12148/cb31690619g',
    sourceChecked: '2026-10-11', medium_display: 'Novel', dimensions: '',
    credit_line: 'Bibliographic reference: Bibliothèque nationale de France.', image: null,
    rowLabel: 'Émile Zola', rowType: 'Book',
  },
  {
    id: 50002, kind: 'event', title: 'First Impressionist exhibition opens',
    artist_title: 'Exhibition history', date_display: '15 April 1874',
    intervals: [[1874, 1874]],
    dateNote: 'The first exhibition opened on 15 April 1874 at 35 boulevard des Capucines, Paris. This is the historical opening date, not the date of a later exhibition about it.',
    source: 'https://salons.musee-orsay.fr/Detail/occurrences/83',
    sourceName: 'Musée d’Orsay · Base Salons',
    sourceChecked: '2026-10-11', medium_display: 'Exhibition opening', dimensions: '',
    credit_line: 'Historical event reference: Musée d’Orsay, Base Salons.', image: null,
    rowLabel: 'Exhibition history', rowType: 'Event',
  },
];
