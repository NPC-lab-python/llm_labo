---
paths:
  - "**/*.py"
---

# Règles Python

## Style de Code
- Utiliser des f-strings pour le formatage de chaînes
- Préférer les list comprehensions aux boucles simples
- Utiliser des type hints pour les paramètres et retours de fonctions
- Docstrings obligatoires pour les fonctions publiques (format Google)

## Imports
- Ordre : stdlib, packages tiers, imports locaux
- Un import par ligne
- Pas d'imports wildcard (`from x import *`)

## Nommage
- Variables et fonctions : `snake_case`
- Classes : `PascalCase`
- Constantes : `UPPER_SNAKE_CASE`
- Variables privées : préfixe `_`

## Gestion des Erreurs
- Attraper des exceptions spécifiques, pas `Exception` générique
- Logger les erreurs avec contexte
- Utiliser des messages d'erreur explicites
