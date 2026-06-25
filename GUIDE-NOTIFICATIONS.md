# Guide — Email & WhatsApp quotidiens

Vous recevrez **1 email** et **1 message WhatsApp** chaque matin, tout regroupé :

| Dans le même message | Contenu |
|---------------------|---------|
| ☕ Kawa Kanzururu | Posts + conseils images |
| 📱 UZAAPP | Produits web + conception visuelle |
| 💻 INVESTEE-GROUP | Posts B2B + conseils visuels |
| 📋 Appels d'offres | AO IT/fournitures RDC |

- **Email** = version complète
- **WhatsApp** = résumé (détail dans l'email)

---

## Configuration email (Gmail)

1. Compte Google → [Mots de passe d'application](https://myaccount.google.com/apppasswords)
2. Créez un mot de passe pour « Courrier »
3. Dans `.env` :

```
NOTIFY_EMAIL=votre@gmail.com
SMTP_USER=votre@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

Vous recevrez **4 emails** chaque matin (un par marque).

---

## Configuration WhatsApp (CallMeBot — gratuit)

Idéal pour recevoir un **résumé** sur WhatsApp ; le détail complet reste dans l'email.

1. Enregistrez **+34 644 71 83 72** dans vos contacts (nom : CallMeBot)
2. Sur WhatsApp, envoyez à ce contact :
   ```
   I allow callmebot to send me messages
   ```
3. Vous recevez une **API key**
4. Dans `.env` :

```
WHATSAPP_PHONE=+243XXXXXXXXX
CALLMEBOT_APIKEY=votre_cle
WHATSAPP_PROVIDER=callmebot
```

Vous recevrez **4 messages WhatsApp** (résumé de chaque section).

**Alternative pro :** Twilio WhatsApp (payant) — voir `.env.example`.

---

## Test sans agent Cursor (notifications seules)

Si vous avez déjà un fichier `output/briefing-AAAA-MM-JJ.md` :

```powershell
cd C:\Users\DIEU-MERCI\agent-quotidien
python src\run_daily.py --notify-only
```

---

## Ce que contient chaque briefing

### Kawa Kanzururu
- Posts Facebook, LinkedIn, TikTok, X
- **Conception image** : sujet, cadrage, couleurs, texte sur visuel, brief créatif

### UZAAPP
- **Veille produits** : 1–2 produits repérés sur sites e-commerce
- **Fiche créative** : bannière, story, mockup app, CTA
- Posts pour promouvoir le produit via UZAAPP

### INVESTEE-GROUP
- Posts LinkedIn/Facebook B2B
- **Visuels à créer** : services IT, formations, IM-SYSTEM
- Idée carrousel 3 slides

### Appels d'offres
- Tableau AO du jour (réf, objet, date limite, lien)
- Éligibilité INVESTEE-GROUP
- Actions immédiates

---

## Dans Cursor (manuel, à tout moment)

Sans attendre le matin, demandez ici :

```
Briefing UZAAPP : cherche un produit tendance et fais-moi une conception visuelle
```

```
Conseils images Kawa Kanzururu pour cette semaine
```

```
Quels appels d'offres IT aujourd'hui en RDC ?
```

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Email non reçu | Vérifier mot de passe application Gmail (pas le mot de passe normal) |
| WhatsApp CallMeBot | Renvoyer « I allow callmebot… » ; vérifier numéro avec indicatif +243 |
| 1 seul message au lieu de 4 | Vérifier que l'agent utilise les marqueurs `=== KAWA_KANZURURU ===` etc. |
| Message WhatsApp tronqué | Normal (limite) — ouvrir l'email pour le détail |
