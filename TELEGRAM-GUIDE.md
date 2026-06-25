# Telegram — CallMeBot (gratuit)

Recevez le briefing aussi sur **Telegram**, en plus de l'email et WhatsApp.

Telegram permet des messages **plus longs** que WhatsApp (meilleur résumé).

---

## Option A — Message privé (recommandé, plus simple)

**Pas besoin de clé API** — seulement votre pseudo Telegram.

### Étapes (2 minutes)

1. Installez **Telegram** sur votre téléphone
2. Cherchez **@CallMeBot_txtbot**
3. Appuyez **Démarrer** ou envoyez :
   ```
   /start
   ```
4. Notez votre **pseudo Telegram** (Paramètres → Nom d'utilisateur)
   - Exemple : `@dieumercikamina`

### Configuration

Dans `.env` et secrets GitHub :

```
SEND_TELEGRAM=true
TELEGRAM_MODE=user
TELEGRAM_USER=@votre_pseudo_telegram
```

Secret GitHub : `TELEGRAM_USER` (ex: `@dieumercikamina`)

### Test dans le navigateur

Remplacez `@votre_pseudo` :

```
https://api.callmebot.com/text.php?user=@votre_pseudo&text=Test+briefing+Kawa+Kanzururu
```

---

## Option B — Groupe Telegram

Utile si plusieurs personnes de l'équipe doivent recevoir le briefing.

### Étapes

1. `/start` sur **@CallMeBot_txtbot**
2. Créez un groupe Telegram (ex: « Briefing Kawa Investee »)
3. Ajoutez **@API_CallMeBot** au groupe
4. Allez sur [callmebot.com — Telegram Group](https://www.callmebot.com/blog/telegram-group-messages-api-easy/)
5. Entrez votre pseudo → **Get ApiKey**

### Configuration

```
SEND_TELEGRAM=true
TELEGRAM_MODE=group
TELEGRAM_GROUP_APIKEY=votre_cle_groupe
```

Secret GitHub : `TELEGRAM_GROUP_APIKEY`

---

## Récapitulatif des 3 canaux

| Canal | Contenu | Config |
|-------|---------|--------|
| ✉️ **Email** | Complet (HTML) | `SMTP_PASSWORD` |
| 📱 **WhatsApp** | Résumé court | `CALLMEBOT_APIKEY` |
| ✈️ **Telegram** | Résumé détaillé | `TELEGRAM_USER` ou `TELEGRAM_GROUP_APIKEY` |

---

## Dépannage Telegram

| Problème | Solution |
|----------|----------|
| NOT AUTHORIZED | Renvoyez `/start` à @CallMeBot_txtbot |
| Pas de message | Vérifiez le pseudo avec @ (ex: `@dieumerci`) |
| Groupe ne reçoit pas | @API_CallMeBot est bien dans le groupe ? |

---

Dieu-Merci Kamina — dieumercikamina@gmail.com
