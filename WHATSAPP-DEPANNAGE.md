# WhatsApp CallMeBot — dépannage

CallMeBot est **gratuit mais instable**. Le bot se remplit souvent (« Bot is full ») et le numéro change.

---

## Procédure à suivre (essayez chaque numéro)

### Numéro 1 (officiel actuel)
1. Ajoutez **+34 694 23 41 84** dans vos contacts (nom : CallMeBot)
2. Sur WhatsApp, envoyez **exactement** :
   ```
   I allow callmebot to send me messages
   ```
3. Attendez 2 minutes — vous devez recevoir :
   ```
   API Activated for your phone number. Your APIKEY is XXXXXX
   ```

### Si pas de réponse — Numéro 2 (bot de remplacement)
1. Ajoutez **+34 621 08 34 84**
2. Même message : `I allow callmebot to send me messages`

### Si vous aviez déjà une clé — Récupération
Envoyez à l'un des numéros ci-dessus :
```
Recover APIKey
```

### Si le bot répond « Bot is full »
Le message indique un **nouveau numéro** — utilisez celui-là.

### Si toujours rien après 2 minutes
- Attendez **24 heures** et réessayez
- Vérifiez que WhatsApp fonctionne (internet, numéro +243 actif)
- Essayez en **4G** plutôt qu'en WiFi

---

## Activer WhatsApp dans l'agent

Quand vous avez la clé, dans `.env` et sur GitHub Secrets :

```
SEND_WHATSAPP=true
CALLMEBOT_APIKEY=votre_cle_ici
```

Secret GitHub : `CALLMEBOT_APIKEY`

---

## En attendant : email seul (déjà actif)

L'agent envoie **déjà votre briefing par email** chaque jour sur :

**dieumercikamina@gmail.com**

WhatsApp est optionnel — vous ne bloquez pas le déploiement.

Dans GitHub workflow, mettez temporairement :
```yaml
SEND_WHATSAPP: "false"
```

---

## Alternatives WhatsApp (si CallMeBot ne marche jamais)

| Option | Prix | Difficulté |
|--------|------|------------|
| **Email seul** | Gratuit | ✅ Déjà configuré |
| **Telegram CallMeBot** | Gratuit | Facile — bot Telegram souvent plus stable |
| **TextMeBot** | Payant faible | callmebot.com recommande |
| **Twilio WhatsApp** | Payant | Pro, fiable |

### Option Telegram (gratuit, recommandé en secours)

1. Installez Telegram
2. Cherchez **@CallMeBot** ou suivez [callmebot.com](https://www.callmebot.com)
3. `/start` puis activation API Telegram
4. On peut ajouter Telegram à l'agent si vous voulez

---

## Test manuel dans le navigateur

Remplacez phone, text et apikey :

```
https://api.callmebot.com/whatsapp.php?phone=243975955375&text=Test&apikey=VOTRE_CLE
```

Si ça marche dans le navigateur, ça marchera dans l'agent.

---

Dieu-Merci — +243 975 955 375
