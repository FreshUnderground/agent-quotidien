# Hébergement 100 % en ligne

Votre agent tourne **24h/24 dans le cloud** — votre PC peut rester éteint.

```
┌─────────────────────────────────────────────────────────────┐
│                    INTERNET (cloud)                          │
├─────────────────────────────────────────────────────────────┤
│  GitHub Actions          Cursor Cloud         CallMeBot      │
│  (planificateur)    →    (IA + recherche)  →  Gmail          │
│  tous les jours 6h       web, AO, posts        WhatsApp      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              dieumercikamina@gmail.com
              +243 975 955 375 (WhatsApp)
```

**Coût :** GitHub Actions = gratuit | Cursor Cloud = usage tokens | CallMeBot = gratuit

---

## Étape 1 — Compte GitHub (gratuit)

1. Créez un compte sur [github.com](https://github.com) si besoin
2. Créez un dépôt **privé** (recommandé) : `agent-quotidien-dieumerci`

---

## Étape 2 — Envoyer le projet sur GitHub

Sur votre PC, dans PowerShell :

```powershell
cd C:\Users\DIEU-MERCI\agent-quotidien
git init
git add .
git commit -m "Agent quotidien Kawa UZAAPP Investee"
git branch -M main
git remote add origin https://github.com/VOTRE_COMPTE/agent-quotidien-dieumerci.git
git push -u origin main
```

Remplacez `VOTRE_COMPTE` par votre nom d'utilisateur GitHub.

> Si `git` n'est pas installé : [git-scm.com/download/win](https://git-scm.com/download/win)

---

## Étape 3 — Secrets GitHub (clés sécurisées)

Dans votre dépôt GitHub :

**Settings → Secrets and variables → Actions → New repository secret**

Ajoutez **exactement ces 3 secrets** :

| Nom du secret | Où l'obtenir |
|---------------|--------------|
| `CURSOR_API_KEY` | [cursor.com/dashboard](https://cursor.com/dashboard) → API Keys |
| `SMTP_PASSWORD` | [Mot de passe application Gmail](https://myaccount.google.com/apppasswords) |
| `CALLMEBOT_APIKEY` | WhatsApp → contact CallMeBot (+34 644 71 83 72) → message `I allow callmebot to send me messages` |

Votre email et téléphone sont déjà dans le workflow (pas besoin de secret).

---

## Étape 4 — Activer GitHub Actions

1. Onglet **Actions** du dépôt
2. Si demandé : **I allow all actions**
3. Cliquez **Briefing quotidien** → **Run workflow** → **Run workflow**

⏱ Attendez 5–15 minutes (l'agent Cursor travaille dans le cloud).

Vous recevrez :
- ✉️ **1 email** sur dieumercikamina@gmail.com
- 📱 **1 WhatsApp** sur +243 975 955 375
- 📁 Copie archivée dans `output/` sur GitHub

---

## Étape 5 — Automatique chaque matin

Rien à faire. Le workflow tourne **tous les jours à 6h00** (heure de Kinshasa).

Cron configuré : `0 5 * * *` (UTC).

---

## Lancer manuellement (à tout moment)

GitHub → **Actions** → **Briefing quotidien** → **Run workflow**

Utile pour tester sans attendre le matin.

---

## Voir les briefings passés

1. GitHub → votre dépôt → dossier `output/`
2. Fichiers : `briefing-2026-06-25.md`, etc.

Accessible depuis le téléphone via l'app GitHub.

---

## Connexion avec Cursor (ici)

Les runs cloud apparaissent aussi sur [cursor.com/agents](https://cursor.com/agents).

Vous pouvez continuer la conversation dans Cursor après le briefing automatique.

---

## Checklist finale

- [ ] Dépôt GitHub créé (privé)
- [ ] Code poussé (`git push`)
- [ ] Secret `CURSOR_API_KEY` ajouté
- [ ] Secret `SMTP_PASSWORD` ajouté (Gmail)
- [ ] Secret `CALLMEBOT_APIKEY` ajouté (WhatsApp)
- [ ] Premier **Run workflow** réussi
- [ ] Email + WhatsApp reçus

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Workflow ne démarre pas | Actions activées ? Dépôt public ou plan GitHub OK |
| Email non reçu | Vérifier `SMTP_PASSWORD` = mot de passe **application** Gmail |
| WhatsApp non reçu | Renvoyer message à CallMeBot ; vérifier `CALLMEBOT_APIKEY` |
| Agent Cursor échoue | Vérifier `CURSOR_API_KEY` et crédit Cursor |
| Timeout 45 min | Relancer manuellement ; vérifier status sur cursor.com/agents |

---

## Contact configuré

- Email : dieumercikamina@gmail.com
- WhatsApp : +243 975 955 375
- Format : **1 message regroupé** (Kawa + UZAAPP + Investee + AO)

Dieu-Merci Kamina — Butembo, RDC
