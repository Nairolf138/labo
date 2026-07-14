# 000 — Hello Lab

- **Statut :** `validated`
- **Question :** le dépôt peut-il héberger une expérience Python minimale, exécutable et testée sans dépendance ?
- **Hypothèse :** une fonction pure et un test `unittest` suffisent comme contrôle initial.

## Exécuter

Depuis ce dossier :

```bash
python3 src/index.py
python3 -m unittest discover -s tests -v
```

## Résultat attendu

Le programme affiche `Nox Lab opérationnel.` et le test passe.

## Apprentissage

Le squelette minimal fonctionne avec la bibliothèque standard. Cette expérience sert uniquement de référence structurelle.
