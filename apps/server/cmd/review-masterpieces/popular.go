package main

// Exact locally popular-artist identities selected on 11 September 2026.
// Museum holdings and image rights are independently validated at stage/apply.
var popularImagePicks = []coveragePick{
	{"nga", "164942", "Claude Monet", "Still Life with Bottle, Carafe, Bread, and Wine: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "178254", "Claude Monet", "The Willows: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "45872", "Claude Monet", "Morning Haze: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46523", "Claude Monet", "The Houses of Parliament, Sunset: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46524", "Claude Monet", "Rouen Cathedral, West Façade: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46652", "Claude Monet", "Banks of the Seine, Vétheuil: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46653", "Claude Monet", "Woman Seated under the Willows: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46654", "Claude Monet", "Rouen Cathedral, West Façade, Sunlight: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46655", "Claude Monet", "The Seine at Giverny: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46656", "Claude Monet", "Jerusalem Artichoke Flowers: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46657", "Claude Monet", "Palazzo da Mula, Venice: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46658", "Claude Monet", "Waterloo Bridge, Gray Day: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "52185", "Claude Monet", "Bazille and Camille (Study for \"Déjeuner sur l'Herbe\"): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "52186", "Claude Monet", "Argenteuil: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "52187", "Claude Monet", "Ships Riding on the Seine at Rouen: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "52188", "Claude Monet", "Bridge at Argenteuil on a Gray Day: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "52189", "Claude Monet", "The Artist's Garden at Vétheuil: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61374", "Claude Monet", "The Bridge at Argenteuil: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61375", "Claude Monet", "The Cradle - Camille with the Artist's Son Jean: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61376", "Claude Monet", "Interior, after Dinner: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61377", "Claude Monet", "Waterloo Bridge, London, at Dusk: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61378", "Claude Monet", "Waterloo Bridge, London, at Sunset: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61379", "Claude Monet", "Woman with a Parasol - Madame Monet and Her Son: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "66425", "Claude Monet", "Cliffs at Pourville: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "71550", "Claude Monet", "Sainte-Adresse: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "72138", "Claude Monet", "The Artist's Garden in Argenteuil (A Corner of the Garden with Dahlias): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "74796", "Claude Monet", "The Japanese Footbridge: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "41600", "Albrecht Dürer", "Portrait of a Clergyman (Johann Dorsch?): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "52227", "Alfred Sisley", "Meadow: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46649", "Amedeo Modigliani", "Roma Woman with Baby: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "41682", "Andrea Mantegna", "The Infant Savior: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "1230", "Anthony van Dyck", "A Genoese Noblewoman and Her Son: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "1185", "Bartolomé Esteban Murillo", "Two Women at a Window: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46661", "Berthe Morisot", "The Mother and Sister of the Artist: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "1143", "Bronzino", "A Young Woman and Her Little Boy: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "164950", "Camille Pissarro", "Landscape, Ile-de-France: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "32589", "Canaletto", "Entrance to the Grand Canal from the Molo, Venice: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "130555", "Caspar David Friedrich", "Northern Landscape, Spring: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "51095", "Claude Lorrain", "The Judgment of Paris: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "121051", "Diego Rivera", "No. 9, Nature Morte Espagnole: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "88", "Diego Velázquez", "The Needlewoman: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "10", "Duccio", "The Nativity with the Prophets Isaiah and Ezekiel: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "1158", "Edgar Degas", "Before the Ballet: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "195132", "Eugène Delacroix", "Tiger and Snake: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "41613", "Fra Angelico", "The Healing of Palladia by Saint Cosmas and Saint Damian: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46469", "Francisco Goya", "Young Lady Wearing a Mantilla and Basquina: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "12209", "Francisco de Zurbarán", "Saint Lucy: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "74", "Frans Hals", "Portrait of a Woman Aged Sixty: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "12200", "François Boucher", "The Bath of Venus: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "74771", "Georges Braque", "Harbor: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61383", "Georges Seurat", "The Lighthouse at Honfleur: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "397", "Giotto di Bondone", "Madonna and Child: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46060", "Giovanni Battista Tiepolo", "Bacchus and Ariadne: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "358", "Giovanni Bellini", "Saint Jerome Reading: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "56662", "Gustav Klimt", "Baby (Cradle): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "30231", "Gustave Courbet", "The Stream (Le Ruisseau du Puits-Noir; vallée de la Loue): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46514", "Henri Matisse", "Lorette with Turban, Yellow Jacket: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46538", "Henri Rousseau", "Boy on the Rocks: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "89687", "Henri de Toulouse-Lautrec", "Hussars: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "41645", "Hieronymus Bosch", "Death and the Miser: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46488", "Honoré Daumier", "French Theater: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "41535", "J. M. W. Turner", "The Rape of Proserpine: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "55819", "Jackson Pollock", "Number 1, 1950 (Lavender Mist): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46113", "Jacques-Louis David", "Madame David: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "45880", "James Abbott McNeill Whistler", "George W. Vanderbilt: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46149", "Jean-Antoine Watteau", "Ceres (Summer): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "41606", "Jean-Auguste-Dominique Ingres", "Pope Pius VII in the Sistine Chapel: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "176397", "Jean-Baptiste-Camille Corot", "Dance under the Trees at the Edge of the Lake: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "35093", "Jean-François Millet", "The Bather: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "32683", "Jean-Honoré Fragonard", "A Game of Horse and Rider: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61373", "Joan Miró", "Flight of the Dragonfly in Front of the Sun: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46437", "Johannes Vermeer", "A Lady Writing: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "33750", "Lucas Cranach the Elder", "A Prince of Saxony: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "53588", "Marc Chagall", "Houses at Vitebsk: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61172", "Max Ernst", "A Moment of Calm: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "32692", "Nicolas Poussin", "The Baptism of Christ: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46664", "Pablo Picasso", "Classical Head: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "45", "Paolo Veronese", "The Finding of Moses: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "53122", "Paul Cézanne", "Montagne Sainte-Victoire, from near Gardanne: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46502", "Paul Gauguin", "Madame Alexandre Kohler: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61372", "Paul Klee", "New House in the Suburbs: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46473", "Peter Paul Rubens", "Agrippina and Germanicus: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "51136", "Pierre-Auguste Renoir", "Mlle Charlotte Berthier: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "52614", "Piet Mondrian", "Tableau No. IV; Lozenge Composition with Red, Gray, Blue, Yellow, and Black: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "29", "Pietro Perugino", "The Crucifixion with the Virgin, Saint John, Saint Jerome, and Saint Mary Magdalene [left panel]: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "12131", "Raphael", "Bindo Altoviti: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "85", "Rembrandt van Rijn", "A Polish Nobleman: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "66422", "René Magritte", "The Blank Signature: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "50662", "Rogier van der Weyden", "Saint George and the Dragon: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46486", "Salvador Dalí", "Chester Dale: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "21", "Sandro Botticelli", "Portrait of a Youth: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46504", "Théodore Géricault", "Nude Warrior with a Spear: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46143", "Tintoretto", "Doge Alvise Mocenigo and Family before the Madonna and Child: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "41593", "Titian", "Ranuccio Farnese: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "46506", "Vincent van Gogh", "Roulin's Baby: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "498", "Vittore Carpaccio", "The Virgin Reading: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "56670", "Wassily Kandinsky", "Improvisation 31 (Sea Battle): popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "61246", "Édouard Manet", "Masked Ball at the Opera: popular-artist museum painting selected for study; no masterpiece designation inferred."},
	{"nga", "172073", "Élisabeth Vigée Le Brun", "Madame du Barry: popular-artist museum painting selected for study; no masterpiece designation inferred."},
}

func isPopularImagePick(p coveragePick) bool {
	for _, selected := range karlsruheImagePicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range poldiImagePicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range nivaImagePicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range smkMatissePicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range durerImagePicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range pinakothekPicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range popularCyclePicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range popularSMKPicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range impressionistFollowupPicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range chicagoPicks {
		if p == selected {
			return true
		}
	}
	for _, selected := range popularImagePicks {
		if p == selected {
			return true
		}
	}
	return false
}
