# Sécurité et confidentialité

Ce dépôt est public. Les règles suivantes sont non négociables.

## Ne jamais publier

- mots de passe, tokens, clés privées ou fichiers `.env` ;
- adresses IP ou URL internes ;
- identifiants réels d’une maison connectée ;
- images de caméras, voix, historiques de présence ou données personnelles ;
- sauvegardes ou extraits de registres de services.

## Données autorisées

- données synthétiques clairement identifiées ;
- jeux de données publics avec leur licence et leur source ;
- configurations génériques utilisant des noms fictifs ;
- captures expurgées ne permettant pas d’identifier une personne ou un domicile.

## Avant chaque commit

```bash
git diff --cached
```

Vérifier explicitement l’absence de secrets et de données domestiques. En cas de doute, ne pas publier.
