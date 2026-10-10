"""Offline safeguards for Paris collection evidence, date scope and physical units."""
import copy,gzip,importlib.util,json,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('n',Path(__file__).with_name('museum-expansion-france-fourteenth-native-20261008.py'));n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
class Context(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  rows=n.m.load(n.DISCOVERY)['rows'];cls.samples={code:copy.deepcopy(next(v['raw_source_record'] for v in rows if v['raw_source_record']['Code_Museofile']==code)) for code in ['M1108','M1114','M1113','M1102','M0184']}
 def test_exact_museum_destinations(self):
  for code,d in self.samples.items():self.assertIsNotNone(n.holding_context(d),code)
 def test_blank_paris_ownership_preserved(self):
  d=copy.deepcopy(self.samples['M1108']);d['Statut_juridique']='';old=copy.deepcopy(d);self.assertIsNotNone(n.holding_context(d));self.assertEqual(d,old)
 def test_acquisition_not_invented_ownership(self):
  d=copy.deepcopy(self.samples['M1113']);d['Statut_juridique']='legs';old=copy.deepcopy(d);self.assertIsNotNone(n.holding_context(d));self.assertEqual(d,old)
 def test_private_or_deposit_label_not_whitelisted(self):
  for text in ['dépôt','propriété privée','restitution',"mode d'acquisition particulier"]:
   d=copy.deepcopy(self.samples['M1108']);d['Statut_juridique']=text;self.assertIsNone(n.holding_context(d))
 def test_wrong_museum_same_city_rejected(self):
  d=copy.deepcopy(self.samples['M1108']);d['Localisation']='Musée de la Vie romantique';self.assertIsNone(n.holding_context(d))
 def test_wrong_code_rejected(self):
  d=copy.deepcopy(self.samples['M1108']);d['Code_Museofile']='M1113';self.assertIsNone(n.holding_context(d))
 def test_wrong_city_rejected(self):
  d=copy.deepcopy(self.samples['M1114']);d['Ville']='Saint-Pierre-Port';self.assertIsNone(n.holding_context(d))
 def test_joint_hugo_label_not_site_claim(self):
  d=self.samples['M1114'];self.assertIn('Hauteville',d['Localisation']);self.assertIsNotNone(n.holding_context(d));c=n.m.load(n.RUN/'museum-name-reconciliation-001.json')['museums']['M1114'];self.assertFalse(c['current_display_claim']);self.assertIn('physical location',c['basis'])
 def test_missing_stolen_deposit_flags_block(self):
  for key in ['MANQUANT','MANQUANT_COM','Lieu_de_depot']:
   d=copy.deepcopy(self.samples['M1102']);d[key]='yes';self.assertIsNone(n.holding_context(d))
 def test_auxerre_owner_not_inferred_from_city(self):
  d=copy.deepcopy(self.samples['M0184']);d['Statut_juridique']='';self.assertIsNone(n.holding_context(d))
 def test_exact_cutoff_inclusive(self):self.assertEqual(n.date_facts(dict(Millesime_de_creation='1970',Periode_de_creation='20e siècle'))[0]['first'],1970)
 def test_post_cutoff_held(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='1971',Periode_de_creation='20e siècle'))[0])
 def test_creation_not_acquisition(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='',Periode_de_creation='',Date_d_acquisition='1880'))[0])
 def test_crossing_period_held(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='',Periode_de_creation='3e quart 20e siècle'))[0])
 def test_century_is_range(self):
  f=n.date_facts(dict(Millesime_de_creation='',Periode_de_creation='19e siècle'))[0];self.assertEqual((f['first'],f['last'],f['date_precision']),(1801,1900,'century'))
 def test_circa_no_invented_tolerance(self):
  f=n.date_facts(dict(Millesime_de_creation='Vers 1850',Periode_de_creation='19e siècle'))[0];self.assertEqual((f['first'],f['last'],f['date_precision']),(1801,1900,'circa_range'));self.assertEqual(f['date_display'],'Vers 1850')
 def test_circa_without_independent_period_held(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='Vers 1850',Periode_de_creation=''))[0])
 def test_before_1971_exclusive_unknown_lower(self):
  f=n.date_facts(dict(Millesime_de_creation='1971 avant',Periode_de_creation='20e siècle'))[0];self.assertEqual((f['first'],f['last'],f['date_precision']),(None,1971,'before'))
 def test_before_1972_not_eligible(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='avant 1972',Periode_de_creation='20e siècle'))[0])
 def test_period_contradiction_held(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='1698-1704',Periode_de_creation='1er quart 18e siècle'))[0])
 def test_wrong_source_life_dates_held(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='1868',Auteur='Gilbert Charles (1928-)'))[0])
 def test_reversed_dates_held(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='1860-1850'))[0])
 def test_qualified_unknown_period_held(self):self.assertIsNone(n.date_facts(dict(Millesime_de_creation='',Periode_de_creation='19e siècle ?'))[0])
 def test_explicit_drawing_domain_and_form(self):
  d=dict(Denomination='dessin',Domaine='arts graphiques',Materiaux_techniques='Plume;Encre;Papier',Mesures='H. 21; L. 30');self.assertEqual(n.physical_type(d)[0][0],'drawing')
 def test_double_face_is_one_drawing(self):
  d=dict(Denomination='dessin double face',Domaine='dessin;arts graphiques',Materiaux_techniques='Crayon;Papier',Mesures='H. 21; L. 30');self.assertEqual(n.physical_type(d)[0][0],'drawing')
 def test_garment_not_drawing(self):self.assertIsNone(n.physical_type(dict(Denomination='robe',Domaine='vêtements et accessoires de vêtement',Materiaux_techniques='soie'))[0])
 def test_printing_matrix_excluded(self):self.assertIsNone(n.physical_type(dict(Denomination="elément d'impression (matrice)",Domaine='estampe',Materiaux_techniques='bois'))[0])
 def test_book_and_album_not_counted_as_loose_sheets(self):
  for form in ['album','illustration de livre','périodique']:self.assertIsNone(n.physical_type(dict(Denomination=form,Domaine='arts graphiques',Materiaux_techniques='papier'))[0])
 def test_bound_support_held(self):self.assertIsNone(n.physical_type(dict(Denomination='dessin',Domaine='arts graphiques',Materiaux_techniques='Encre;papier',Mesures='21x30',Description="collé sur une page d'un livre"))[0])
 def test_logical_series_not_physical_album(self):
  d=dict(Denomination='dessin',Domaine='dessin;arts graphiques',Materiaux_techniques='Aquarelle;Papier',Mesures='21x30',Titre='Modèle; Ensemble de modèles',Historique='Série de dessins');self.assertEqual(n.physical_type(d)[0][0],'drawing')
 def test_sculpture_domain_suffix_supported(self):
  d=dict(Denomination='ronde-bosse',Domaine='sculpture (domaine)',Materiaux_techniques='Bronze',Mesures='H. 40');self.assertEqual(n.physical_type(d)[0][0],'sculpture')
 def test_source_mold_held(self):self.assertIsNone(n.physical_type(dict(Denomination='buste',Domaine='sculpture (domaine)',Materiaux_techniques='Plâtre',Mesures='H. 40',Description="moule d'atelier"))[0])
 def test_drawing_requires_physical_technique(self):self.assertIsNone(n.physical_type(dict(Denomination='dessin',Domaine='arts graphiques',Materiaux_techniques='',Mesures='21x30'))[0])
 def test_positive_record_preserves_source(self):
  d=copy.deepcopy(self.samples['M1108']);d.update(Denomination='dessin',Domaine='dessin;arts graphiques',Materiaux_techniques='Encre;Papier',Mesures='21x30',Millesime_de_creation='1850',Periode_de_creation='19e siècle',Auteur='anonyme (-)',Statut_juridique='');old=copy.deepcopy(d);result,reason=n.screen(d);self.assertIsNone(reason);self.assertEqual(d,old);self.assertEqual(result['facts']['creator_label'],'anonyme (-)')
if __name__=='__main__':unittest.main()
