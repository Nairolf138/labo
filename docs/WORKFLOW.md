# Workflow du labo

## 1. Formuler

Chaque expérience commence par une phrase falsifiable : « Si nous faisons X, nous devrions observer Y. »

## 2. Isoler

Créer un dossier dédié :

```bash
python3 tools/new_experiment.py nom-court --title "Titre lisible"
```

Le numéro est attribué automatiquement. Ne jamais réutiliser le dossier d’une autre expérience pour aller plus vite.

## 3. Construire petit

Le premier incrément doit pouvoir être exécuté ou vérifié en quelques minutes. Préférer la bibliothèque standard, le local et l’open source. Documenter toute dépendance ajoutée.

## 4. Vérifier

Une expérience prête à être partagée contient au minimum :

- son objectif et son hypothèse ;
- une commande reproductible ;
- un résultat réel, y compris si le résultat est négatif ;
- les risques, limites et données utilisées ;
- une prochaine décision : continuer, pivoter, archiver.

## 5. Partager sans imposer

- branche `nox/...` ;
- commits conventionnels et ciblés ;
- jamais de push direct sur `main` ;
- jamais de fusion sans validation explicite de Flo.

## Statuts suggérés

- `seed` : idée formalisée ;
- `active` : prototype en cours ;
- `validated` : hypothèse confirmée avec preuve ;
- `paused` : en attente d’une ressource ou décision ;
- `archived` : apprentissage conservé, travail arrêté.
