---
name: commit
description: Commiter et pusher les changements vers GitHub
allowed-tools: Bash
---

# Skill Commit

Ce skill permet de commiter les changements et les pusher vers le repository GitHub.

## Instructions

1. Vérifier le statut git actuel
2. Ajouter tous les fichiers modifiés
3. Créer un commit avec un message descriptif
4. Pusher vers origin main

## Commandes à exécuter

```bash
# Vérifier le statut
git status

# Ajouter tous les changements
git add .

# Demander à l'utilisateur un message de commit ou en générer un basé sur les changements
# Puis commiter
git commit -m "Message de commit"

# Pusher vers origin main
git push -u origin main
```

## Notes

- Toujours vérifier le statut avant de commiter
- Générer un message de commit descriptif basé sur les changements
- Le remote est configuré sur : https://github.com/NPC-lab-python/llm_labo.git
