# Activer GitHub Actions — étape par étape

Si vous voyez **「There are no workflow runs yet」**, suivez ces étapes **dans l'ordre**.

---

## Étape 1 — Activer Actions (obligatoire la 1ère fois)

1. Allez sur : https://github.com/FreshUnderground/agent-quotidien
2. Cliquez l'onglet **「Actions」** (en haut)
3. Si vous voyez un écran vert « Get started with GitHub Actions » :
   - Cliquez **「I understand my workflows, go ahead and enable them」**
   - Ou **「Autoriser les workflows」** en français

Sans cette étape, **aucun workflow ne démarre**, même après un push.

---

## Étape 2 — Ajouter les secrets

https://github.com/FreshUnderground/agent-quotidien/settings/secrets/actions

Cliquez **「New repository secret」** pour chaque :

| Name | Secret |
|------|--------|
| `CURSOR_API_KEY` | Votre clé `crsr_...` (cursor.com/dashboard) |
| `SMTP_PASSWORD` | Mot de passe application Gmail |
| `CALLMEBOT_APIKEY` | `6382163` |

---

## Étape 3 — Lancer manuellement

1. **Actions** → menu gauche **「Briefing quotidien」**
2. Bouton **「Run workflow」** (à droite, au-dessus de la liste)
3. Branche **main** → **「Run workflow」**

⏱ Attendez 5–20 minutes.

---

## Étape 4 — Vérifier le résultat

| Couleur | Signification |
|---------|---------------|
| 🟡 Jaune | En cours — patientez |
| 🟢 Vert | Réussi — vérifiez email/WhatsApp |
| 🔴 Rouge | Erreur — cliquez dessus, lisez le message |

---

## Test rapide (workflow simple)

Si « Briefing quotidien » n'apparaît pas, lancez d'abord **「Test connexion」** dans Actions.

---

## Lien direct Actions

https://github.com/FreshUnderground/agent-quotidien/actions
