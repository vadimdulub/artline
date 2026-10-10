"""Offline editorial selection safeguards; no databases or database fixtures."""
import copy,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-fifteenth-native-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class Selection(unittest.TestCase):
 def test_explicit_du_periods(self):
  self.assertEqual(n.period_bounds('3e quart du 18e siècle'),(1751,1775))
  self.assertEqual(n.period_bounds('1ère moitié du 19e siècle'),(1801,1850))
 def test_full_union_and_cutoff(self):
  self.assertEqual(n.period_bounds('16e siècle;17e siècle'),(1501,1700))
  self.assertIsNone(n.period_bounds('3e quart du 20e siècle'))
 def test_vague_period_not_invented(self):
  for raw in ['Milieu du 18e siècle','18e siècle (?)','vers le 18e siècle']:self.assertIsNone(n.period_bounds(raw))
 def test_date_period_conflict_remains_held(self):
  self.assertIsNone(n.date_facts(dict(Millesime_de_creation='En 1750',Periode_de_creation='3e quart du 18e siècle',Auteur=''))[0])
 def form(self,**kwargs):
  d=dict(Denomination='',Domaine='',Materiaux_techniques='',Description='',Mesures='',Titre='');d.update(kwargs);before=copy.deepcopy(d);r=n.physical_type(d);self.assertEqual(d,before);return r
 def test_missing_denomination_with_explicit_drawing_evidence(self):
  r,e=self.form(Domaine='beaux-arts;dessin',Materiaux_techniques='aquarelle',Mesures='H. 24 cm');self.assertIsNone(e);self.assertEqual(r[0],'drawing')
 def test_domain_alone_not_enough(self):self.assertIsNone(self.form(Domaine='dessin')[0])
 def test_blank_denomination_print_sheet(self):
  r,e=self.form(Domaine='estampe',Materiaux_techniques='papier (burin)',Mesures='14 H ; 12 L');self.assertIsNone(e);self.assertEqual(r[0],'print')
 def test_bound_leaf_remains_held(self):self.assertIsNone(self.form(Domaine='estampe',Materiaux_techniques='papier (burin)',Mesures='14 H ; 12 L',Description='collé sur une page')[0])
 def test_explicit_painting_miniature(self):
  r,e=self.form(Denomination='miniature',Domaine='peinture;emaillerie',Materiaux_techniques='Cuivre;Email',Mesures='diamètre 4 cm');self.assertIsNone(e);self.assertEqual(r[0],'painting')
 def test_box_and_jewelry_not_turned_into_free_paintings(self):
  for form in ['boîte;miniature',"boucle d'oreille;miniature"]:self.assertIsNone(self.form(Denomination=form,Domaine='peinture',Materiaux_techniques='gouache',Mesures='4 cm')[0])
 def test_ivory_figurine_supported(self):
  r,e=self.form(Denomination='figurine',Domaine='sculpture',Materiaux_techniques='ivoire (taillé)',Mesures='22.5 H');self.assertIsNone(e);self.assertEqual(r[0],'sculpture')
 def test_fragment_not_independent_unit(self):self.assertIsNone(self.form(Denomination='panneau;relief',Domaine='sculpture',Materiaux_techniques='noyer;bas-relief',Mesures='42 H',Titre='FRAGMENT')[0])
 def holding(self,code,**kwargs):
  c=n.m.load(n.RUN/'museum-name-reconciliation-001.json')['museums'][code];d=dict(Code_Museofile=code,Ville=c['city'],Nom_officiel_musee=c['names'][0],Localisation=c['locations'][0],Lieu_de_depot='',MANQUANT='',MANQUANT_COM='',Statut_juridique='');d.update(kwargs);before=copy.deepcopy(d);r=n.holding_context(d);self.assertEqual(d,before);return r
 def test_esteve_blank_location_stays_supported_by_owner(self):self.assertIsNotNone(self.holding('M0231',Statut_juridique='propriété de la commune;don manuel;Bourges;musée Estève'))
 def test_esteve_blank_location_without_owner_is_not_inferred(self):self.assertIsNone(self.holding('M0231'))
 def test_state_cluny_owner_renaissance_assignment_distinct(self):self.assertIsNotNone(self.holding('M5012',Statut_juridique="propriété de l'Etat;achat;Musée de Cluny",Lieu_de_depot='affectation;Musée de Cluny;affectation;Ecouen;musée national de la Renaissance'))
 def test_cluny_only_destination_not_reassigned(self):self.assertIsNone(self.holding('M5012',Statut_juridique="propriété de l'Etat;achat;Musée de Cluny",Lieu_de_depot='affectation;Musée de Cluny'))
 def test_missing_object_rejected(self):self.assertIsNone(self.holding('M1107',Statut_juridique='legs',MANQUANT='manquant'))
 def test_questioned_department_owner_rejected(self):self.assertIsNone(self.holding('M0745',Statut_juridique='propriété du département (?);legs;Nantes;musée Dobrée'))
 def test_other_city_rejected(self):self.assertIsNone(self.holding('M1107',Statut_juridique='legs',Ville='Lyon'))
if __name__=='__main__':unittest.main()
