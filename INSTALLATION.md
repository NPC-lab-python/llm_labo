# Guide d'Installation - RAG System

Ce guide détaille l'installation complète du système RAG sur Windows.

---

## Table des matières

1. [Prérequis](#1-prérequis)
2. [Installation de Miniconda](#2-installation-de-miniconda)
3. [Création de l'environnement](#3-création-de-lenvironnement)
4. [Configuration des clés API](#4-configuration-des-clés-api)
5. [Lancement de l'API](#5-lancement-de-lapi)
6. [Exposer l'API sur Internet](#6-exposer-lapi-sur-internet)
7. [Dépannage](#7-dépannage)

---

## 1. Prérequis

### Logiciels requis
- **Windows 10/11** (64-bit)
- **Git** : https://git-scm.com/download/win

### Clés API à obtenir
| Service | URL | Utilisation |
|---------|-----|-------------|
| Anthropic | https://console.anthropic.com/ | LLM Claude |
| Voyage AI | https://dash.voyageai.com/ | Embeddings |

---

## 2. Installation de Miniconda

### Étape 2.1 : Télécharger Miniconda

Télécharger l'installateur Windows :
https://docs.conda.io/en/latest/miniconda.html

Ou directement :
https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe

### Étape 2.2 : Installer Miniconda

1. Exécuter l'installateur `Miniconda3-latest-Windows-x86_64.exe`
2. Accepter la licence
3. Choisir "Just Me" (recommandé)
4. Garder le chemin par défaut : `C:\Users\<VotreNom>\miniconda3`
5. **IMPORTANT** : Cocher les deux options :
   - [x] Add Miniconda3 to my PATH environment variable
   - [x] Register Miniconda3 as my default Python
6. Cliquer sur "Install"

### Étape 2.3 : Vérifier l'installation

Ouvrir un **nouveau** terminal PowerShell :

```powershell
conda --version
```

Résultat attendu : `conda 24.x.x` (ou supérieur)

---

## 3. Création de l'environnement

### Étape 3.1 : Cloner le projet

```powershell
cd C:\Users\<VotreNom>\Documents
git clone https://github.com/NPC-lab-python/llm_labo.git
cd llm_labo
```

### Étape 3.2 : Créer l'environnement Conda

```powershell
conda env create -f environment.yml
```

Cette commande :
- Crée un environnement nommé `rag_env`
- Installe Python 3.11
- Installe toutes les dépendances (FastAPI, ChromaDB, Anthropic, etc.)

**Durée** : 5-10 minutes selon la connexion

### Étape 3.3 : Activer l'environnement

```powershell
conda activate rag_env
```

Le prompt devient : `(rag_env) PS C:\...>`

### Étape 3.4 : Vérifier l'installation

```powershell
python --version
# Résultat attendu : Python 3.11.x

pip list | findstr anthropic
# Résultat attendu : anthropic 0.x.x
```

---

## 4. Configuration des clés API

### Étape 4.1 : Créer le fichier .env

```powershell
copy .env.example .env
```

### Étape 4.2 : Éditer le fichier .env

Ouvrir `.env` avec un éditeur (Notepad, VS Code, etc.) :

```powershell
notepad .env
```

### Étape 4.3 : Remplir les clés API

```env
# === Anthropic API (Claude) ===
ANTHROPIC_API_KEY=sk-ant-api03-VOTRE_CLE_ICI
CLAUDE_MODEL=claude-sonnet-4-20250514

# === Voyage AI API (Embeddings) ===
VOYAGE_API_KEY=pa-VOTRE_CLE_ICI
VOYAGE_EMBED_MODEL=voyage-3
```

### Où trouver les clés ?

**Clé Anthropic :**
1. Aller sur https://console.anthropic.com/
2. Se connecter / Créer un compte
3. Menu "API Keys" → "Create Key"
4. Copier la clé `sk-ant-api03-...`

**Clé Voyage AI :**
1. Aller sur https://dash.voyageai.com/
2. Se connecter / Créer un compte
3. Menu "API Keys" → "Create new API key"
4. Copier la clé `pa-...`

---

## 5. Lancement de l'API

### Étape 5.1 : Activer l'environnement (si pas déjà fait)

```powershell
conda activate rag_env
```

### Étape 5.2 : Lancer l'API

```powershell
cd C:\Users\<VotreNom>\Documents\llm_labo
python main.py
```

### Étape 5.3 : Vérifier le fonctionnement

Résultat attendu dans le terminal :
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Étape 5.4 : Tester l'API

Ouvrir un navigateur :
- **Documentation Swagger** : http://localhost:8000/docs
- **Health Check** : http://localhost:8000/api/v1/health

Résultat attendu du health check :
```json
{
  "status": "ok",
  "chroma_status": "ok",
  "claude_status": "configured",
  "voyage_status": "configured",
  "document_count": 0
}
```

---

## 6. Exposer l'API sur Internet

Pour permettre à des collègues d'accéder à l'API depuis l'extérieur.

### Option A : Cloudflare Tunnel (recommandé)

**Avantages** : Gratuit, stable, pas de limite de débit

#### Installation

```powershell
winget install cloudflare.cloudflared
```

Ou télécharger : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

#### Utilisation

Dans un **nouveau terminal** (garder l'API qui tourne dans l'autre) :

```powershell
cloudflared tunnel --url http://localhost:8000
```

Résultat :
```
Your quick tunnel has been created!
https://random-words-abc.trycloudflare.com
```

Partager cette URL à vos collègues. La documentation sera accessible sur :
`https://random-words-abc.trycloudflare.com/docs`

### Option B : Ngrok

#### Installation

1. Créer un compte : https://ngrok.com/signup
2. Télécharger : https://ngrok.com/download
3. Extraire `ngrok.exe` dans un dossier (ex: `C:\Tools\`)
4. Configurer le token :

```powershell
ngrok config add-authtoken VOTRE_TOKEN
```

#### Utilisation

```powershell
ngrok http 8000
```

---

## 7. Dépannage

### Problème : `conda` n'est pas reconnu

**Solution** : Fermer et rouvrir le terminal, ou ajouter Conda au PATH :
```powershell
$env:Path += ";C:\Users\<VotreNom>\miniconda3\condabin"
```

### Problème : `ModuleNotFoundError: No module named 'xxx'`

**Solution** : Réinstaller les dépendances :
```powershell
conda activate rag_env
pip install anthropic voyageai
```

### Problème : L'environnement `rag_env` existe déjà

**Solution** : Le supprimer et recréer :
```powershell
conda deactivate
conda env remove -n rag_env
conda env create -f environment.yml
```

### Problème : Port 8000 déjà utilisé

**Solution** : Changer le port dans `.env` :
```env
API_PORT=8001
```

### Problème : `claude_status: not_configured`

**Solution** : Vérifier que la clé API dans `.env` est correcte et ne contient pas d'espaces.

### Problème : Erreur SSL avec Cloudflare

**Solution** : Utiliser HTTP en local :
```powershell
cloudflared tunnel --url http://localhost:8000
```
(et non `https://`)

---

## Commandes utiles

```powershell
# Activer l'environnement
conda activate rag_env

# Désactiver l'environnement
conda deactivate

# Voir les environnements installés
conda env list

# Mettre à jour les dépendances
pip install --upgrade anthropic voyageai

# Arrêter l'API
Ctrl + C

# Voir les logs de l'API
# (Les logs s'affichent directement dans le terminal)
```

---

## Architecture réseau

```
┌─────────────────────────────────────────────────────────────┐
│                        VOTRE PC                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Conda     │    │    API      │    │  ChromaDB   │     │
│  │  rag_env    │───►│  FastAPI    │───►│  (local)    │     │
│  │  Python 3.11│    │  :8000      │    │             │     │
│  └─────────────┘    └──────┬──────┘    └─────────────┘     │
│                            │                                 │
└────────────────────────────┼─────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Cloudflare    │
                    │     Tunnel      │
                    └────────┬────────┘
                             │
              https://xxx.trycloudflare.com
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    ┌─────────┐        ┌─────────┐        ┌─────────┐
    │Collègue1│        │Collègue2│        │Collègue3│
    └─────────┘        └─────────┘        └─────────┘
```

---

## Support

- Documentation API : http://localhost:8000/docs
- Repository : https://github.com/NPC-lab-python/llm_labo
