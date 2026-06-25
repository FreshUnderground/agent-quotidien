# Agent quotidien — 100 % hébergé en ligne

Agent automatique pour **Dieu-Merci Kamina** — chaque matin à **6h Kinshasa**, sans PC allumé.

## Ce qu'il fait

**1 email** + **1 WhatsApp** regroupant :

| Section | Contenu |
|---------|---------|
| ☕ Kawa Kanzururu | Posts réseaux + conseils images |
| 📱 UZAAPP | Produits web + conception visuelle |
| 💻 INVESTEE-GROUP | Posts B2B + conseils visuels |
| 📋 Appels d'offres | AO IT/fournitures RDC |

**Destinataire :** dieumercikamina@gmail.com | +243 975 955 375

---

## Hébergement cloud

```
GitHub Actions (gratuit)  →  Cursor Cloud Agent  →  Gmail + WhatsApp
        ↑                           ↑
   planifie 6h/jour          cherche données web
```

👉 **Guide complet : [HEBERGEMENT-EN-LIGNE.md](HEBERGEMENT-EN-LIGNE.md)**

### Démarrage rapide (5 étapes)

1. Créer un dépôt GitHub **privé**
2. Pousser ce dossier (`git push`)
3. Ajouter 3 secrets : `CURSOR_API_KEY`, `SMTP_PASSWORD`, `CALLMEBOT_APIKEY`
4. **Actions** → **Run workflow** (test)
5. C'est tout — automatique chaque matin

---

## Secrets à configurer sur GitHub

| Secret | Source |
|--------|--------|
| `CURSOR_API_KEY` | cursor.com/dashboard |
| `SMTP_PASSWORD` | Gmail mot de passe application |
| `CALLMEBOT_APIKEY` | WhatsApp CallMeBot |

---

## Fichiers importants

| Fichier | Rôle |
|---------|------|
| `.github/workflows/briefing-quotidien.yml` | Planificateur cloud |
| `prompts/briefing-quotidien.md` | Instructions agent |
| `src/run_daily.py` | Lancement + notifications |
| `output/` | Archives des briefings |

---

## Dans Cursor (manuel)

Demandez ici à tout moment : *« Quoi faire aujourd'hui ? »*, *« Briefing UZAAPP »*, ou envoyez une image.

Skills : `C:\Users\DIEU-MERCI\.cursor\skills\`

---

## Coût

| Service | Prix |
|---------|------|
| GitHub Actions | Gratuit |
| CallMeBot WhatsApp | Gratuit |
| Gmail | Gratuit |
| Cursor Cloud Agent | Usage tokens (comme l'IDE) |

---

Dieu-Merci Kamina — Kawa Kanzururu & INVESTEE-GROUP, Butembo, RDC.
