# 002 — Cue Observatory

- **Statut :** `validated`
- **Créée le :** 2026-07-23
- **Responsable :** Nox
- **Dernier incrément :** 2026-08-02 — rapport Markdown/JSON, densité, simultanéité, vigilance, CLI

## Question

Peut-on transformer une liste synthétique de cues (temps, marqueurs, notes) en une chronologie exploitable pour une régie lumière : densité d'appels par fenêtre glissante, détection de cues simultanées et points de vigilance pour l'opérateur ?

## Hypothèse

Si chaque cue porte un temps, un marqueur (`start`, `transition`, `simultaneous`, `end`) et des notes, un analyseur peut :
1. produire une timeline ordonnée ;
2. identifier les périodes de forte densité (fenêtre glissante 60 s, chevauchement 50 %) ;
3. regrouper les cues simultanées (tolérance 1 s) ;
4. générer des points de vigilance contextualisés (marqueurs clés, densité haute, simultanéité) ;
5. sortir un rapport Markdown lisible et un JSON machine pour automatisation.

## Protocole

Un fichier CSV synthétique couvre le scénario reproductible (voir `examples/sample_cues.csv`) :
- 12 cues sur 25 minutes
- 3 cues simultanées à 00:05:00 (marqueur `simultaneous`)
- 4 transitions rapides entre 00:15:00 et 00:16:00 (densité haute)
- marqueurs `start`, `transition`, `simultaneous`, `end` représentés

Le parseur tolère les temps invalides (remplace par `00:00:00` + avertissement) et les CSV vides.

## Exécution

Aucune dépendance externe n'est nécessaire (bibliothèque standard Python).

```bash
# Rapport Markdown (défaut)
python3 experiments/002-cue-observatory/src/cue_observatory.py \
  experiments/002-cue-observatory/examples/sample_cues.csv

# Rapport JSON pour consommation machine
python3 experiments/002-cue-observatory/src/cue_observatory.py \
  experiments/002-cue-observatory/examples/sample_cues.csv \
  --format json

# Sauvegarder dans un fichier
python3 experiments/002-cue-observatory/src/cue_observatory.py \
  experiments/002-cue-observatory/examples/sample_cues.csv \
  --output rapport.md

# Tests
python3 -m pytest experiments/002-cue-observatory/tests/ -v
```

## Résultat observé

Le 2 août 2026, l'exemple `sample_cues.csv` a produit le rapport suivant (extrait) :

**Résumé :**
- **Total cues :** 12
- **Durée :** 00:25:00
- **Transitions :** 5
- **Groupes simultanés :** 1
- **Avertissements :** 0

**Analyse de densité (fenêtre 60 s, chevauchement 50 %) :**
- 3 périodes **hautes** (🔴) détectées : 00:04:30–00:05:30, 00:05:00–00:06:00, 00:15:00–00:16:30
- Pic à 3 cues/minute aux mêmes créneaux

**Cues simultanées :**
- 1 groupe à 00:05:00 : "Cue 1 - Actor Enter" (start), "Cue 2 - Cross Stage" (simultaneous), "Cue 3 - Center Spot" (simultaneous)

**Points de vigilance (extrait) :**
- **Cue 1 - Actor Enter (00:05:00)** : Key moment: start · High cue density period (3 cues/min) · Simultaneous with: Cue 2 - Cross Stage, Cue 3 - Center Spot
- **Cue 6 - Quick Shift (00:15:30)** : Transition - verify timing · High cue density period (3 cues/min)
- **Cue 10 - Blackout (00:25:00)** : Key moment: end

Sortie JSON complète (structure) :
```json
{
  "summary": { "total_cues": 12, "duration": "00:25:00", "transitions": 5, "simultaneous_groups": 1, "warnings": 0 },
  "warnings": [],
  "timeline": [ { "cue": "...", "time": "HH:MM:SS", "marker": "...", "notes": "..." }, ... ],
  "density_analysis": [ { "window_start": "HH:MM:SS", "window_end": "HH:MM:SS", "cue_count": 3, "cues": [...], "is_peak": true, "level": "high" }, ... ],
  "simultaneous_cues": [ { "time": "HH:MM:SS", "cues": [ { "cue": "...", "marker": "...", "notes": "..." }, ... ] }, ... ],
  "vigilance_points": [ { "cue": "...", "time": "HH:MM:SS", "points": [ "Key moment: start", "High cue density period (3 cues/min)", "Simultaneous with: ..." ] }, ... ]
}
```

Tous les tests unitaires passent (5/5) :
- Génération Markdown depuis CSV synthétique
- Gestion CSV vide
- Gestion temps malformé avec avertissement
- Détection périodes haute densité
- Sortie JSON structurée

## Contrat du prototype

### Format CSV d'entrée

Colonnes : `cue`, `time`, `marker`, `notes`
- `cue` : identifiant lisible (ex: "Cue 1 - Actor Enter")
- `time` : format `HH:MM:SS` (ex: `00:05:30`) ; invalide → `00:00:00` + warning
- `marker` : `start` | `transition` | `simultaneous` | `end` (insensible à la casse)
- `notes` : texte libre

### Algorithmes

| Fonction | Paramètres | Comportement |
|---|---|---|
| `parse_time` | `str` → `timedelta \| None` | Parse strict `HH:MM:SS` |
| `analyze_density` | `cues`, `window_seconds=60` | Fenêtre glissante, pas = fenêtre/2, niveau `high` si ≥ 70 % du pic |
| `find_simultaneous_cues` | `cues`, `tolerance=1s` | Groupes consécutifs dont Δt ≤ tolérance |
| `identify_vigilance_points` | `cues`, `density_periods` | Combine marqueurs, densité pic, simultanéité |

### Formats de sortie

- **Markdown** : rapport lisible avec sections Summary, Timeline, Density Analysis, Simultaneous Cues, Vigilance Points
- **JSON** : structure plate pour intégration (CI, outils downstream, tableaux de bord)

### API Python

```python
from cue_observatory import generate_report

# Markdown (défaut)
md = generate_report("cues.csv")

# JSON
import json
data = json.loads(generate_report("cues.csv", format="json"))
```

## Risques, données et limites

- Les cues, temps, marqueurs et notes sont entièrement **synthétiques**.
- Le programme n'effectue **aucun appel réseau** et ne pilote **aucun équipement**.
- Tolérance de simultanéité fixée à 1 seconde (paramétrable).
- Fenêtre de densité fixée à 60 secondes avec chevauchement 50 % (paramétrable).
- Aucune persistance : lecture CSV → rapport direct.
- Le parseur CSV attend un en-tête exact `cue,time,marker,notes`.

## Décision suivante

L'hypothèse est confirmée : un CSV simple produit une chronologie exploitable avec densité, simultanéité et vigilance.

Pistes d'incréments utiles (à évaluer selon priorité) :
1. **Export horaire** : ajouter une colonne "temps restant" pour l'opérateur en live.
2. **Format cue sheet** : supporter l'import depuis formats standards (ETC, MA, Chamsys) via adaptateurs.
3. **Mode différentiel** : comparer deux versions de cue sheet et ne montrer que les changements.
4. **Intégration Home Twin** : croiser les cues avec la simulation de présence/luminosité (idée #3).
5. **Schéma JSON versionné** : publier un schéma pour la sortie machine.

Pour l'instant, l'expérience est **validée** et prête à être archivée ou étendue selon les besoins.