# Pistes à explorer

Ce document est un jardin d’idées, pas une feuille de route. Une idée n’entre dans `experiments/` qu’après avoir reçu une hypothèse testable et un périmètre minimal.

## 1. Light Protocol Compiler

**État :** premier incrément validé dans [`experiments/001-light-protocol-compiler`](../experiments/001-light-protocol-compiler/). Prochaine piste : diagnostics de compilation et validation complète des plages.

Décrire des ambiances lumineuses dans un format générique, puis produire des actions compatibles avec les capacités déclarées de lumières **fictives** : couleur HS, température de blanc, luminosité et indisponibilité.

**Premier test :** vérifier qu’aucune commande de couleur n’est envoyée à une lumière limitée au blanc réglable.

## 2. Cue Observatory

Transformer une liste synthétique de cues, temps et marqueurs en une chronologie lisible : densité des appels, transitions simultanées et points de vigilance pour une régie lumière.

**Premier test :** générer un rapport Markdown à partir d’un petit fichier CSV fictif.

## 3. Home Twin

Créer un simulateur local minimal de maison connectée avec des entités synthétiques. Il permettrait de tester des automatisations sans toucher à une installation réelle.

**Premier test :** simuler présence, luminosité et disponibilité, puis rejouer un scénario déterministe.

## 4. Obsidian Project Radar

Analyser un coffre de démonstration pour repérer les projets dormants, prochaines actions absentes et liens orphelins, sans envoyer les notes vers un service externe.

**Premier test :** produire un tableau de bord à partir de dix notes Markdown synthétiques.

## 5. Cat Signal Lab

Explorer localement la distinction entre mouvements anodins et événements utiles dans des séquences publiques ou synthétiques, avec une attention particulière aux faux positifs et à la confidentialité.

**Premier test :** définir le protocole d’évaluation avant tout modèle.

## Critères de sélection

La prochaine idée choisie devrait être :

1. utile à Flo ou à l’apprentissage de Nox ;
2. testable en moins d’une session ;
3. locale ou gratuite pour le premier prototype ;
4. sans donnée privée ;
5. capable de produire une preuve observable.
