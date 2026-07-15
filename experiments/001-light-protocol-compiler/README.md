# 001 — Light Protocol Compiler

- **Statut :** `validated`
- **Créée le :** 2026-07-14
- **Responsable :** Nox
- **Dernier incrément :** 2026-07-15 — diagnostics structurés et validation des plages

## Question

Peut-on compiler une ambiance lumineuse générique sans transmettre à une lumière une propriété qu’elle ne déclare pas prendre en charge, tout en expliquant chaque omission et chaque entrée invalide ?

## Hypothèse

Si chaque lumière synthétique publie ses capacités, le compilateur peut produire les commandes valides, isoler les cibles fautives et rendre ses décisions auditables dans un rapport `commands` / `warnings` / `errors`.

## Protocole

Trois lumières fictives couvrent le scénario reproductible :

- une lampe blanc réglable (`brightness`, `color_temperature`) ;
- une lumière couleur (`brightness`, `hs_color`) ;
- une lumière couleur indisponible.

La scène demande volontairement des propriétés incompatibles. Le résultat ne doit contenir ni couleur HS pour la première, ni température de couleur pour la deuxième, ni commande pour la troisième. Chaque omission doit désormais avoir un diagnostic.

## Exécution

Aucune dépendance externe n’est nécessaire.

```bash
python3 experiments/001-light-protocol-compiler/src/main.py \
  --devices experiments/001-light-protocol-compiler/examples/devices.json \
  --scene experiments/001-light-protocol-compiler/examples/scene.json

python3 -m unittest discover \
  -s experiments/001-light-protocol-compiler/tests -v
```

`--strict` conserve le rapport JSON sur la sortie standard, mais renvoie le code `2` si `errors` n’est pas vide. Ce mode permet d’utiliser le compilateur dans une CI sans perdre les diagnostics.

## Résultat observé

Le 15 juillet 2026, l’exemple a produit deux commandes, quatre avertissements et aucune erreur :

```json
{
  "commands": [
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
  ],
  "warnings": [
    {
      "code": "unsupported_property",
      "target": "reading_lamp",
      "property": "hue",
      "message": "'reading_lamp' does not support 'hue'; property omitted"
    },
    {
      "code": "unsupported_property",
      "target": "reading_lamp",
      "property": "saturation",
      "message": "'reading_lamp' does not support 'saturation'; property omitted"
    },
    {
      "code": "unsupported_property",
      "target": "stage_wash",
      "property": "color_temperature",
      "message": "'stage_wash' does not support 'color_temperature'; property omitted"
    },
    {
      "code": "target_unavailable",
      "target": "offline_lamp",
      "message": "target 'offline_lamp' is unavailable; command omitted"
    }
  ],
  "errors": []
}
```

Les propriétés incompatibles sont absentes des commandes mais visibles dans `warnings`. Une cible inconnue, une structure invalide ou une valeur hors plage apparaît dans `errors` sans empêcher la compilation des autres cibles valides. Une cible qui possède au moins une erreur de valeur ne reçoit aucune commande : la compilation est atomique par cible.

**Conclusion :** l’hypothèse est confirmée pour un protocole local à quatre propriétés. Le rapport rend maintenant le filtrage observable et exploitable par une machine.

## Contrat du prototype

### Valeurs

- `brightness` : nombre, booléens exclus, entre 0 et 100 inclus ;
- `hue` : nombre, entre 0 inclus et 360 exclu ;
- `saturation` : nombre, entre 0 et 100 inclus ;
- `color_temperature` : nombre compris dans `color_temperature_range` du périphérique ; la plage par défaut est `[1000, 10000]` kelvins ;
- une plage de température déclarée doit être une liste croissante de deux nombres.

### Diagnostics

| Niveau | Code | Signification |
|---|---|---|
| warning | `unsupported_property` | propriété omise car la capacité correspondante est absente |
| warning | `target_unavailable` | commande omise car la cible déclare `available: false` |
| error | `unknown_target` | cible de scène absente du document des périphériques |
| error | `value_out_of_range` | valeur prise en charge mais invalide |
| error | `invalid_scene` | document de scène ou propriétés d’une cible mal formés |
| error | `invalid_devices` | racine du document des périphériques mal formée |
| error | `invalid_device` | capacités ou plage d’un périphérique mal formées |

L’ordre des commandes et diagnostics suit l’ordre des cibles et propriétés JSON, ce qui rend les résultats déterministes.

### API Python

- `compile_report(scene, devices)` est l’API recommandée : elle agrège les diagnostics et poursuit sur les cibles indépendantes ;
- `compile_scene(scene, devices)` reste disponible pour compatibilité : elle renvoie seulement les commandes et lève `ValueError` à la première valeur prise en charge invalide.

## Risques, données et limites

- Les noms, capacités et scènes fournis sont entièrement synthétiques.
- Le programme n’effectue aucun appel réseau et ne pilote aucun appareil.
- Le prototype ne connaît que quatre propriétés et ne garantit pas la conformité à un protocole domotique réel.
- Les diagnostics sont des dictionnaires Python/JSON, sans schéma JSON versionné.
- Le mode strict échoue sur les erreurs, pas sur les avertissements.
- `compile_scene` est une API historique moins robuste que `compile_report` face aux documents structurellement invalides.

## Décision suivante

Le prochain incrément utile est de définir un schéma de protocole versionné et des tests de compatibilité, ou de passer à l’idée **Cue Observatory** afin d’éviter de transformer ce prototype local en intégration domotique réelle.
