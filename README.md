# 🚔 Bot Poliție — Sistem Puncte & Grad
### Discord Bot pentru Comunitate Roleplay Poliție

---

## 📋 Cuprins
1. [Cerințe de Sistem](#cerințe)
2. [Instalare](#instalare)
3. [Configurare](#configurare)
4. [Crearea Botului Discord](#creare-bot)
5. [Pornire Bot](#pornire)
6. [Comenzi Disponibile](#comenzi)
7. [Sistemul de Puncte](#sistemul-de-puncte)
8. [Resetare Automată](#resetare-automată)
9. [Fișiere Generate](#fișiere)
10. [Depanare Probleme](#depanare)

---

## ✅ Cerințe

- **Python 3.10+** (recomandat 3.11 sau 3.12)
- **Conexiune internet** stabilă
- Un cont **Discord Developer** (gratuit)

---

## 🚀 Instalare

### Pasul 1 — Clonează / Descarcă fișierele
Pune toate fișierele (`bot.py`, `requirements.txt`, `config.json`) într-un folder.

### Pasul 2 — Instalează dependențele

```bash
# Instalează Python dacă nu ai deja
# https://www.python.org/downloads/

# Instalează pachetele necesare
pip install -r requirements.txt
```

---

## ⚙️ Configurare

Deschide fișierul `config.json` și completează câmpurile:

```json
{
  "token": "TOKEN_BOT_AICI",          ← Token-ul botului tău (obligatoriu!)
  "prefix": "!",                       ← Prefixul pentru comenzi clasice
  "canal_rapoarte": "123456789",       ← ID-ul canalului unde merg rapoartele săptămânale
  "rol_admin": "987654321",            ← ID-ul rolului de admin (opțional)
  "zi_resetare": "luni",              ← Ziua resetării săptămânale
  "ora_resetare": "00:00",            ← Ora resetării (format 24h)
  "timezone": "Europe/Bucharest"      ← Fusul orar
}
```

### Cum găsești ID-ul unui canal/rol:
1. Activează **Modul Dezvoltator** în Discord:
   `Setări Utilizator → Avansat → Modul Dezvoltator`
2. Click dreapta pe canal/rol → **Copiază ID**

---

## 🤖 Crearea Botului Discord

1. Mergi la [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** → dă-i un nume (ex: `Bot Poliție`)
3. Mergi la secțiunea **"Bot"** → Click **"Add Bot"**
4. La **TOKEN** → Click **"Reset Token"** → Copiază token-ul
   > ⚠️ **ATENȚIE:** Nu împărtăși token-ul cu nimeni!
5. Activează aceste **Privileged Gateway Intents**:
   - ✅ `PRESENCE INTENT`
   - ✅ `SERVER MEMBERS INTENT`
   - ✅ `MESSAGE CONTENT INTENT`

### Invitarea Botului pe Server:
1. Mergi la **OAuth2 → URL Generator**
2. Selectează scope: `bot` + `applications.commands`
3. Selectează permisiuni:
   - `Read Messages/View Channels`
   - `Send Messages`
   - `Embed Links`
   - `Use Slash Commands`
   - `Manage Roles` *(opțional, pentru auto-rol)*
4. Copiază URL-ul generat și deschide-l în browser
5. Selectează serverul tău și confirmă

---

## ▶️ Pornire Bot

```bash
python bot.py
```

La prima pornire, vei vedea în consolă:
```
✅ Bot conectat ca BotPoliție#1234 (ID: ...)
✅ Sincronizate 9 comenzi slash
✅ Task-uri periodice pornite
```

> 💡 **Sfat:** Folosește [PM2](https://pm2.keymetrics.io/) sau un VPS pentru a ține botul pornit permanent.

---

## 📜 Comenzi Disponibile

### 👤 Comenzi pentru Toți Membrii

| Comandă | Descriere |
|---------|-----------|
| `/profil` | Afișează propriul profil |
| `/profil @user` | Afișează profilul altui membru |
| `/clasament` | Clasamentul săptămânal complet |
| `/ajutor` | Ghid complet al comenzilor |

### 🛡️ Comenzi Admin (necesită `Manage Roles`)

| Comandă | Descriere |
|---------|-----------|
| `/adauga_puncte` | Adaugă puncte cu dropdown de selecție |
| `/sterge_puncte` | Șterge puncte cu dropdown de selecție |
| `/resetare_puncte @user` | Resetează complet punctele unui membru |
| `/adauga_membru @user` | Înregistrează un nou membru |
| `/verificare_saptamana` | Raport membri sub pragul minim |

### ⚙️ Comenzi Administrator (necesită `Administrator`)

| Comandă | Descriere |
|---------|-----------|
| `/sterge_membru @user` | Șterge definitiv un membru din baza de date |
| `/resetare_saptamanala` | Execută manual resetarea săptămânală |

---

## 🎯 Sistemul de Puncte

### Activități și Recompense

| Activitate | Puncte |
|-----------|--------|
| 🏝️ Raid Cayo | +2 |
| 🏙️ Prezență Acțiune Oraș | +3 |
| ⚓ Prezență Acțiune Cayo | +3 |
| 🚔 Capturat Hot (cu bodycam) | +1 |
| 📦 Livrat 200 Coca | +2 |
| 📦 Livrat 400 Crack | +3 |
| ⚗️ Procesat 200 Coca | +2 |
| ⚗️ Procesat 400 Crack | +3 |
| 🌿 Recoltat 1000 Frunze de Coca | +2 |

### Praguri de Avansare

| De la | La | Puncte Necesare |
|-------|-----|-----------------|
| A1 | A2 | 20 puncte |
| A2 | A3 | 25 puncte |
| A3 | A4 | 35 puncte |
| A4 | A5 | 40 puncte |

### ⚠️ Reguli Săptămânale

- **Minim 20 puncte** pe săptămână (altfel retrogradare automată)
- **Minim 3 raiduri Cayo** pe săptămână
- Avansarea la grad superior este **automată** la atingerea pragului

---

## 🔄 Resetare Automată

Botul execută automat la **Luni 00:00 (ora București)**:

1. ✅ Verifică toți membrii
2. ⬇️ Retrogradează membrii sub **20 puncte**
3. 📋 Salvează istoricul în `date.json`
4. 🔄 Resetează punctele și raidurile la 0
5. 📢 Trimite raportul în canalul configurat

**Alertă automată Duminică 18:00** — notifică membrii în risc de retrogradare.

---

## 📁 Fișiere Generate

```
discord-bot/
├── bot.py          ← Codul principal al botului
├── config.json     ← Configurare (TOKEN, canale, etc.)
├── date.json       ← Baza de date (generată automat)
├── bot.log         ← Log-uri (generat automat)
└── requirements.txt
```

### Structura date.json:
```json
{
  "membri": {
    "123456789": {
      "username": "Nume#1234",
      "grad": "A2",
      "puncte_saptamanale": 15,
      "puncte_totale": 150,
      "raiduri_cayo": 2,
      "activitati": { "raid_cayo": 2, "actiune_oras": 3 },
      "avertismente": 0,
      "inregistrat_la": "2024-01-01T00:00:00",
      "ultima_activitate": "2024-01-07T15:30:00",
      "istoric_resetari": []
    }
  },
  "ultima_resetare": "2024-01-08T00:00:00",
  "saptamana_curenta": "2024-W02"
}
```

---

## 🔧 Depanare Probleme

### "Comenzile slash nu apar"
→ Așteaptă 1-5 minute după pornire. Dacă persistă, verifică permisiunile botului pe server.

### "Missing Permissions" la comenzi
→ Asigură-te că rolul tău Discord are permisiunea `Manage Roles` sau `Administrator`.

### Botul se oprește singur
→ Verifică `bot.log` pentru erori. Asigură-te că token-ul este valid și că intents sunt activate.

### Resetarea nu se face automat
→ Verifică că fusul orar din `config.json` este corect (`Europe/Bucharest`).
→ Botul trebuie să fie **pornit** în momentul resetării.

---

## 📞 Support

Dacă întâmpini probleme, verifică:
1. `bot.log` — conține toate erorile
2. Că token-ul din `config.json` este valid
3. Că Python 3.10+ este instalat: `python --version`
4. Că pachetele sunt instalate: `pip install -r requirements.txt`

---

*Bot creat cu discord.py 2.3 | Sistem Puncte Poliție Roleplay*
