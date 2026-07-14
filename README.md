# Labo

Un espace d’expérimentation partagé entre Flo et Nox : idées, prototypes et petits outils testables, documentés et réversibles.

## Principes

- Une expérimentation = un dossier distinct dans [`experiments/`](experiments/).
- Les données d’exemple sont synthétiques ou publiques : aucun secret, identifiant domestique, média privé ou adresse locale.
- On commence petit : hypothèse, test minimal, résultat observé, prochaine décision.
- `main` reste stable. Nox peut y fusionner un travail lorsqu’il est relu, testé et jugé satisfaisant.
- Un prototype peut échouer ; il doit expliquer ce qui a été appris.

## Carte du dépôt

| Chemin | Rôle |
|---|---|
| `experiments/` | Prototypes isolés et exécutables |
| `ideas/` | Pistes à explorer avant de coder |
| `templates/experiment/` | Squelette d’une nouvelle expérience |
| `tools/` | Outils locaux pour entretenir le labo |
| `tests/` | Tests des outils transversaux |
| `docs/` | Méthode, sécurité et conventions |

## Démarrage rapide

```bash
python3 tools/new_experiment.py mon-idee --title "Mon idée"
python3 -m unittest discover -s tests -v
```

Le script crée un dossier `experiments/NNN-mon-idee/` à partir du modèle, sans dépendance externe.

## État actuel

- [`000-hello-lab`](experiments/000-hello-lab/) : expérience minimale servant de contrôle de fonctionnement.
- [`001-light-protocol-compiler`](experiments/001-light-protocol-compiler/) : compilateur local de scènes pour lumières synthétiques.
- [`ideas/README.md`](ideas/README.md) : jardin des pistes restant à explorer.

Voir [`docs/WORKFLOW.md`](docs/WORKFLOW.md) pour le cycle de travail complet.
