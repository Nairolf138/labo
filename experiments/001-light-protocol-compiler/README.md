# 001 — Light Protocol Compiler

- **Statut :** `validated`
- **Créée le :** 2026-07-14
- **Responsable :** Nox

## Question

Peut-on compiler une ambiance lumineuse générique sans transmettre à une lumière une propriété qu’elle ne déclare pas prendre en charge ?

## Hypothèse

Si chaque lumière synthétique publie ses capacités, le compilateur peut filtrer une scène générique et ne produire que des commandes compatibles, tout en écartant les lumières indisponibles.

## Test minimal

Trois lumières fictives couvrent le premier périmètre :

- une lampe blanc réglable (`brightness`, `color_temperature`) ;
- une lumière couleur (`brightness`, `hs_color`) ;
- une lumière couleur indisponible.

La scène demande volontairement des propriétés incompatibles. Le résultat ne doit contenir ni couleur HS pour la première, ni température de couleur pour la deuxième, ni commande pour la troisième.

## Exécution

Aucune dépendance externe n’est nécessaire.

```bash
python3 experiments/001-light-protocol-compiler/src/main.py \
  --devices experiments/001-light-protocol-compiler/examples/devices.json \
  --scene experiments/001-light-protocol-compiler/examples/scene.json

python3 -m unittest discover \
  -s experiments/001-light-protocol-compiler/tests -v
```

## Résultat observé

Le 14 juillet 2026, l’exemple a produit deux commandes :

```json
[
  {
    "target": "reading_lamp",
    "brightness": 72,
    "color_temperature": 3100
  },
  {
    "target": "stage_wash",
    "brightness": 40,
    "hue": 215,
    "saturation": 60
  }
]
```

La couleur demandée à `reading_lamp` et la température demandée à `stage_wash` sont absentes. `offline_lamp` n’apparaît pas. Les six tests de comportement et de ligne de commande passent.

**Conclusion :** l’hypothèse est confirmée pour ce protocole minimal.

## Contrat du prototype

- `brightness` est un pourcentage compris entre 0 et 100 ; une valeur hors plage est refusée.
- `color_temperature` est exprimée en kelvins.
- `hue` est exprimée en degrés et `saturation` en pourcentage.
- Une capacité absente entraîne le filtrage silencieux de la propriété correspondante.
- `available: false` entraîne le filtrage de la cible entière.

## Risques, données et limites

- Les noms, capacités et scènes fournis sont entièrement synthétiques.
- Le programme n’effectue aucun appel réseau et ne pilote aucun appareil.
- Il ne valide pas encore tout le schéma JSON, les plages HS et de température, ni les cibles inconnues.
- Le filtrage silencieux est pratique pour ce test, mais une intégration réelle devrait aussi produire des diagnostics explicites.

## Décision suivante

Continuer avec un rapport de compilation structuré (`commands`, `warnings`, `errors`) et une validation complète des plages, toujours sur données fictives et sans adaptateur domotique réel.
