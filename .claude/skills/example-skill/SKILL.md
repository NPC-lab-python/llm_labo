---
name: example-skill
description: Exemple de skill - à personnaliser. Utiliser pour voir comment créer un skill.
allowed-tools: Read, Grep, Glob
---

# Skill d'Exemple

Ce fichier montre la structure d'un skill Claude Code.

## Comment Créer un Skill

1. Créer un dossier dans `.claude/skills/` avec le nom du skill
2. Créer un fichier `SKILL.md` dans ce dossier
3. Ajouter le frontmatter YAML avec `name`, `description`, et `allowed-tools`
4. Écrire les instructions que Claude doit suivre

## Structure du Frontmatter

```yaml
---
name: mon-skill           # Nom unique du skill
description: Description  # Quand utiliser ce skill
allowed-tools: Read, Bash # Outils autorisés
---
```

## Bonnes Pratiques

- Description claire avec des mots-clés que l'utilisateur dirait
- Instructions précises et actionables
- Exemples concrets quand possible
