"""
╔══════════════════════════════════════════════════════════════╗
║         BOT POLITIE - SISTEM PUNCTE SI GRAD                  ║
╚══════════════════════════════════════════════════════════════╝
Comenzi: /panou  /profil  /clasament  /ajutor
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import json, os
from datetime import datetime
import pytz, logging

CONFIG_FILE = "config.json"
DB_FILE = "date.json"
ROL_ADMIN = "Los de la Sagrada"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()])
log = logging.getLogger(__name__)

PRAGURI_AVANSARE = {"A1": 20, "A2": 25, "A3": 35, "A4": 40}
GRADE = ["A1", "A2", "A3", "A4", "A5"]
MINIM_SAPTAMANAL = 20
MINIM_RAIDURI_CAYO = 3

ACTIVITATI = {
    "raid_cayo":            {"nume": "Raid Cayo",                    "puncte": 2, "emoji": "🏝️"},
    "actiune_oras":         {"nume": "Prezenta Actiune Oras",        "puncte": 3, "emoji": "🏙️"},
    "actiune_cayo":         {"nume": "Prezenta Actiune Cayo",        "puncte": 3, "emoji": "⚓"},
    "capturat_hot":         {"nume": "Capturat Hot (bodycam)",       "puncte": 1, "emoji": "🚔"},
    "livrat_200_coca":      {"nume": "Livrat 200 Coca",              "puncte": 2, "emoji": "📦"},
    "livrat_400_crack":     {"nume": "Livrat 400 Crack",             "puncte": 3, "emoji": "📦"},
    "procesat_200_coca":    {"nume": "Procesat 200 Coca",            "puncte": 2, "emoji": "⚗️"},
    "procesat_400_crack":   {"nume": "Procesat 400 Crack",          "puncte": 3, "emoji": "⚗️"},
    "recoltat_1000_frunze": {"nume": "Recoltat 1000 Frunze Coca",   "puncte": 2, "emoji": "🌿"},
}

# ── BAZA DE DATE ──────────────────────────────────────────────

def incarca_date():
    if not os.path.exists(DB_FILE):
        d = {"membri": {}, "ultima_resetare": datetime.utcnow().isoformat(), "saptamana_curenta": _get_sapt()}
        salveaza_date(d); return d
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salveaza_date(d):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def _get_sapt():
    now = datetime.utcnow()
    return f"{now.year}-W{now.isocalendar()[1]:02d}"

# ── CONFIG ────────────────────────────────────────────────────

def incarca_config():
    if not os.path.exists(CONFIG_FILE):
        cfg = {"token": "TOKEN_BOT_AICI", "prefix": "!", "canal_rapoarte": None, "timezone": "Europe/Bucharest"}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return cfg
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

config = incarca_config()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=config.get("prefix", "!"), intents=intents)

# ── HELPERS ───────────────────────────────────────────────────

def are_rol_admin(member):
    if member.guild_permissions.administrator:
        return True
    return any(r.name == ROL_ADMIN for r in member.roles)

def verifica_avansare(date, uid):
    if uid not in date["membri"]: return None
    m = date["membri"][uid]
    g = m["grad"]
    if g in PRAGURI_AVANSARE and m["puncte_saptamanale"] >= PRAGURI_AVANSARE[g]:
        idx = GRADE.index(g)
        if idx < len(GRADE) - 1:
            ng = GRADE[idx + 1]; m["grad"] = ng
            return f"🎉 **AVANSAT!** {g} → **{ng}**"
    return None

def bara(p, mx, l=10):
    if mx == 0: return "█" * l
    u = min(int(p / mx * l), l)
    return "█" * u + "░" * (l - u)

def make_embed_profil(uid, m):
    g = m["grad"]; p = m["puncte_saptamanale"]; r = m.get("raiduri_cayo", 0)
    if g in PRAGURI_AVANSARE:
        pr = PRAGURI_AVANSARE[g]; ng = GRADE[GRADE.index(g) + 1]
        prog = f"`{bara(p, pr)}` {p}/{pr} → **{ng}**"
    else:
        prog = "✅ Grad maxim!"
    emb = discord.Embed(title=f"👮 Profil — {m['username']}",
        color=discord.Color.green() if p >= MINIM_SAPTAMANAL else discord.Color.orange(),
        timestamp=datetime.utcnow())
    emb.add_field(name="🏅 Grad", value=f"**{g}**", inline=True)
    emb.add_field(name="⭐ Puncte Sapt.", value=f"**{p}**", inline=True)
    emb.add_field(name="📈 Total", value=f"**{m.get('puncte_totale',0)}**", inline=True)
    emb.add_field(name="🏝️ Raiduri Cayo", value=f"{'✅' if r>=MINIM_RAIDURI_CAYO else '❌'} {r}/{MINIM_RAIDURI_CAYO}", inline=True)
    emb.add_field(name="📊 Status", value="✅ In regula" if p >= MINIM_SAPTAMANAL else f"⚠️ Lipsesc {MINIM_SAPTAMANAL-p} pct", inline=True)
    emb.add_field(name="⚠️ Avertismente", value=str(m.get("avertismente", 0)), inline=True)
    emb.add_field(name="📉 Progres", value=prog, inline=False)
    actv = m.get("activitati", {})
    if actv:
        lst = "\n".join(f"{ACTIVITATI[k]['emoji']} {ACTIVITATI[k]['nume']}: **{v}x**" for k, v in actv.items() if k in ACTIVITATI)
        if lst: emb.add_field(name="📋 Activitati", value=lst[:1024], inline=False)
    emb.set_footer(text=f"Inregistrat la {m.get('inregistrat_la','')[:10]}")
    return emb

# ── RESETARE LOGICA ───────────────────────────────────────────

async def executa_resetare():
    date = incarca_date()
    ts = datetime.utcnow().isoformat()
    retro, av_pct, av_raid = [], [], []
    for uid, m in date["membri"].items():
        p = m["puncte_saptamanale"]; r = m.get("raiduri_cayo", 0); g = m["grad"]
        if p < MINIM_SAPTAMANAL:
            av_pct.append(m["username"]); m["avertismente"] = m.get("avertismente", 0) + 1
            idx = GRADE.index(g)
            if idx > 0:
                ng = GRADE[idx - 1]; m["grad"] = ng
                retro.append(f"{m['username']} ({g} → {ng})")
        if r < MINIM_RAIDURI_CAYO: av_raid.append(m["username"])
        m.setdefault("istoric_resetari", []).append({"data": ts, "puncte": p, "raiduri": r, "grad": g})
        m["puncte_saptamanale"] = 0; m["raiduri_cayo"] = 0; m["activitati"] = {}
    date["ultima_resetare"] = ts; date["saptamana_curenta"] = _get_sapt()
    salveaza_date(date)
    emb = discord.Embed(title="🔄 Resetare Saptamanala Completa",
        description=f"Saptamana **{_get_sapt()}** procesata.", color=discord.Color.blue(), timestamp=datetime.utcnow())
    emb.add_field(name="👥 Total", value=str(len(date["membri"])), inline=True)
    emb.add_field(name="⬇️ Retrogradati", value=str(len(retro)), inline=True)
    emb.add_field(name="⚠️ Avertizati", value=str(len(av_pct)), inline=True)
    if retro: emb.add_field(name="⬇️ Retrogradati", value="\n".join(f"• {r}" for r in retro)[:1024], inline=False)
    if av_pct: emb.add_field(name="⚠️ Sub Minim Puncte", value=", ".join(av_pct[:20]), inline=False)
    if av_raid: emb.add_field(name="🏝️ Sub Minim Raiduri", value=", ".join(av_raid[:20]), inline=False)
    return emb

# ── VIEWS ─────────────────────────────────────────────────────

class PanouPrincipal(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def check_admin(self, interaction):
        return True


    @discord.ui.button(label="➕ Adauga Puncte", style=discord.ButtonStyle.green, custom_id="p_adauga", row=0)
    async def btn_adauga(self, interaction, button):
        if not await self.check_admin(interaction): return
        date = incarca_date()
        if not date["membri"]:
            await interaction.response.send_message("❌ Nu exista membri!", ephemeral=True); return
        membri = [(uid, m["username"]) for uid, m in date["membri"].items()]
        emb = discord.Embed(title="➕ Adauga Puncte", description="Selecteaza membrul si activitatea, apoi apasa **Confirma**.", color=discord.Color.green())
        await interaction.response.send_message(embed=emb, view=ViewSelectPuncte(membri, "adauga", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="➖ Sterge Puncte", style=discord.ButtonStyle.red, custom_id="p_sterge", row=0)
    async def btn_sterge(self, interaction, button):
        if not await self.check_admin(interaction): return
        date = incarca_date()
        if not date["membri"]:
            await interaction.response.send_message("❌ Nu exista membri!", ephemeral=True); return
        membri = [(uid, m["username"]) for uid, m in date["membri"].items()]
        emb = discord.Embed(title="➖ Sterge Puncte", description="Selecteaza membrul si activitatea, apoi apasa **Confirma**.", color=discord.Color.red())
        await interaction.response.send_message(embed=emb, view=ViewSelectPuncte(membri, "sterge", interaction.user.id), ephemeral=True)

    @discord.ui.button(label="🔄 Resetare Puncte", style=discord.ButtonStyle.grey, custom_id="p_reset_m", row=0)
    async def btn_reset_pct(self, interaction, button):
        if not await self.check_admin(interaction): return
        date = incarca_date()
        if not date["membri"]:
            await interaction.response.send_message("❌ Nu exista membri!", ephemeral=True); return
        membri = [(uid, m["username"]) for uid, m in date["membri"].items()]
        emb = discord.Embed(title="🔄 Resetare Puncte Membru", description="Selecteaza membrul.", color=discord.Color.orange())
        await interaction.response.send_message(embed=emb, view=ViewSelectResetare(membri, interaction.user.id), ephemeral=True)

    @discord.ui.button(label="👤 Profil Membru", style=discord.ButtonStyle.blurple, custom_id="p_profil", row=1)
    async def btn_profil(self, interaction, button):
        date = incarca_date()
        if not date["membri"]:
            await interaction.response.send_message("❌ Nu exista membri!", ephemeral=True); return
        membri = [(uid, m["username"]) for uid, m in date["membri"].items()]
        emb = discord.Embed(title="👤 Profil Membru", description="Selecteaza membrul.", color=discord.Color.blurple())
        await interaction.response.send_message(embed=emb, view=ViewSelectProfil(membri, interaction.user.id), ephemeral=True)

    @discord.ui.button(label="➕ Adauga Membru", style=discord.ButtonStyle.green, custom_id="p_add_m", row=1)
    async def btn_add_m(self, interaction, button):
        if not await self.check_admin(interaction): return
        await interaction.response.send_modal(ModalAdaugaMembru())

    @discord.ui.button(label="🗑️ Sterge Membru", style=discord.ButtonStyle.red, custom_id="p_del_m", row=1)
    async def btn_del_m(self, interaction, button):
        if not await self.check_admin(interaction): return
        date = incarca_date()
        if not date["membri"]:
            await interaction.response.send_message("❌ Nu exista membri!", ephemeral=True); return
        membri = [(uid, m["username"]) for uid, m in date["membri"].items()]
        emb = discord.Embed(title="🗑️ Sterge Membru", description="Selecteaza membrul.", color=discord.Color.red())
        await interaction.response.send_message(embed=emb, view=ViewSelectSterge(membri, interaction.user.id), ephemeral=True)

    @discord.ui.button(label="🏆 Clasament", style=discord.ButtonStyle.blurple, custom_id="p_cls", row=2)
    async def btn_cls(self, interaction, button):
        date = incarca_date()
        if not date["membri"]:
            await interaction.response.send_message("❌ Nu exista membri!", ephemeral=True); return
        sortati = sorted(date["membri"].items(), key=lambda x: x[1]["puncte_saptamanale"], reverse=True)
        medalii = ["🥇", "🥈", "🥉"]
        linii = []
        for i, (uid, m) in enumerate(sortati[:20]):
            e = medalii[i] if i < 3 else f"`{i+1:2d}.`"
            s = "✅" if m["puncte_saptamanale"] >= MINIM_SAPTAMANAL else "⚠️"
            rd = "✅" if m.get("raiduri_cayo", 0) >= MINIM_RAIDURI_CAYO else f"🏝️{m.get('raiduri_cayo',0)}"
            linii.append(f"{e} **{m['username']}** — `{m['grad']}` | **{m['puncte_saptamanale']}** pct {s} {rd}")
        total = len(date["membri"]); sub = sum(1 for m in date["membri"].values() if m["puncte_saptamanale"] < MINIM_SAPTAMANAL)
        emb = discord.Embed(title="🏆 Clasament Saptamanal", description=f"Saptamana **{_get_sapt()}**", color=discord.Color.gold(), timestamp=datetime.utcnow())
        emb.add_field(name=f"Top {min(len(sortati),20)}", value="\n".join(linii) or "—", inline=False)
        emb.add_field(name="👥 Total", value=str(total), inline=True)
        emb.add_field(name="✅ La Punct", value=str(total-sub), inline=True)
        emb.add_field(name="⚠️ Sub Minim", value=str(sub), inline=True)
        await interaction.response.send_message(embed=emb)

    @discord.ui.button(label="📋 Verificare Saptamana", style=discord.ButtonStyle.grey, custom_id="p_verif", row=2)
    async def btn_verif(self, interaction, button):
        if not await self.check_admin(interaction): return
        date = incarca_date()
        sub_p = [m for m in date["membri"].values() if m["puncte_saptamanale"] < MINIM_SAPTAMANAL]
        sub_r = [m for m in date["membri"].values() if m.get("raiduri_cayo", 0) < MINIM_RAIDURI_CAYO]
        emb = discord.Embed(title="📋 Raport Verificare", color=discord.Color.orange(), timestamp=datetime.utcnow())
        emb.add_field(name=f"⚠️ Sub Minim Puncte ({len(sub_p)})",
            value="\n".join(f"• **{m['username']}** ({m['grad']}) — {m['puncte_saptamanale']}/{MINIM_SAPTAMANAL}" for m in sub_p)[:1024] or "✅ Toti sunt ok!",
            inline=False)
        emb.add_field(name=f"🏝️ Sub Minim Raiduri ({len(sub_r)})",
            value="\n".join(f"• **{m['username']}** — {m.get('raiduri_cayo',0)}/{MINIM_RAIDURI_CAYO}" for m in sub_r)[:1024] or "✅ Toti sunt ok!",
            inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @discord.ui.button(label="🔁 Resetare Saptamanala", style=discord.ButtonStyle.danger, custom_id="p_reset_s", row=2)
    async def btn_reset_s(self, interaction, button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Doar **Administratorii** pot face resetarea manuala!", ephemeral=True); return
        emb = discord.Embed(title="⚠️ Confirmare Resetare Saptamanala",
            description="Aceasta actiune reseteaza **toate** punctele si retrogradaza membrii sub minim.\n**Nu poate fi anulata!**",
            color=discord.Color.red())
        await interaction.response.send_message(embed=emb, view=ViewConfirmResetSapt(interaction.user.id), ephemeral=True)


class ViewSelectPuncte(discord.ui.View):
    def __init__(self, membri, actiune, autor_id):
        super().__init__(timeout=120)
        self.actiune = actiune; self.autor_id = autor_id
        self.sel_uid = None; self.sel_actv = None
        date = incarca_date()
        opts = []
        for uid, uname in membri[:25]:
            m = date["membri"].get(uid, {})
            opts.append(discord.SelectOption(label=uname[:100], value=uid,
                description=f"Grad: {m.get('grad','A1')} | Pct: {m.get('puncte_saptamanale',0)}", emoji="👮"))
        if opts:
            s = discord.ui.Select(placeholder="🔍 Selecteaza membrul...", options=opts, custom_id="sm")
            s.callback = self.on_m; self.add_item(s)
        semn = "+" if actiune == "adauga" else "-"
        oa = [discord.SelectOption(label=a["nume"][:100], value=k,
            description=f"{semn}{a['puncte']} puncte", emoji=a["emoji"]) for k, a in ACTIVITATI.items()]
        sa = discord.ui.Select(placeholder="🎯 Selecteaza activitatea...", options=oa, custom_id="sa")
        sa.callback = self.on_a; self.add_item(sa)
        bc = discord.ui.Button(label="✅ Confirma", style=discord.ButtonStyle.green, custom_id="bc")
        bc.callback = self.on_c; self.add_item(bc)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌ Doar initiatorul poate folosi acest meniu!", ephemeral=True); return False
        return True

    async def on_m(self, interaction):
        self.sel_uid = interaction.data["values"][0]; await interaction.response.defer()

    async def on_a(self, interaction):
        self.sel_actv = interaction.data["values"][0]; await interaction.response.defer()

    async def on_c(self, interaction):
        if not self.sel_uid or not self.sel_actv:
            await interaction.response.send_message("⚠️ Selecteaza si membrul si activitatea!", ephemeral=True); return
        date = incarca_date()
        if self.sel_uid not in date["membri"]:
            await interaction.response.send_message("❌ Membrul nu exista!", ephemeral=True); return
        m = date["membri"][self.sel_uid]; actv = ACTIVITATI[self.sel_actv]; pct = actv["puncte"]
        if self.actiune == "adauga":
            m["puncte_saptamanale"] += pct; m["puncte_totale"] = m.get("puncte_totale", 0) + pct
            if self.sel_actv == "raid_cayo": m["raiduri_cayo"] = m.get("raiduri_cayo", 0) + 1
            m.setdefault("activitati", {})[self.sel_actv] = m["activitati"].get(self.sel_actv, 0) + 1
            txt = f"+{pct}"; culoare = discord.Color.green()
        else:
            sc = min(pct, m["puncte_saptamanale"]); m["puncte_saptamanale"] = max(0, m["puncte_saptamanale"] - pct)
            txt = f"-{sc}"; culoare = discord.Color.red()
        mg = verifica_avansare(date, self.sel_uid)
        m["ultima_activitate"] = datetime.utcnow().isoformat(); salveaza_date(date)
        emb = discord.Embed(title=f"{actv['emoji']} Puncte {'Adaugate' if self.actiune=='adauga' else 'Sterse'}", color=culoare, timestamp=datetime.utcnow())
        emb.add_field(name="👮 Membru", value=f"**{m['username']}**", inline=True)
        emb.add_field(name="🎯 Activitate", value=actv["nume"], inline=True)
        emb.add_field(name="📊 Modificare", value=f"`{txt}`", inline=True)
        emb.add_field(name="⭐ Total Sapt.", value=f"**{m['puncte_saptamanale']}** pct", inline=True)
        emb.add_field(name="🏅 Grad", value=f"**{m['grad']}**", inline=True)
        emb.add_field(name="🏝️ Raiduri Cayo", value=f"{m.get('raiduri_cayo',0)}/{MINIM_RAIDURI_CAYO}", inline=True)
        if mg: emb.add_field(name="🎖️ Schimbare Grad", value=mg, inline=False)
        emb.set_footer(text=f"Actiune de {interaction.user.display_name}")
        await interaction.response.edit_message(embed=emb, view=None); self.stop()


class ViewSelectProfil(discord.ui.View):
    def __init__(self, membri, autor_id):
        super().__init__(timeout=60); self.autor_id = autor_id
        date = incarca_date()
        opts = [discord.SelectOption(label=un[:100], value=uid,
            description=f"Grad: {date['membri'].get(uid,{}).get('grad','A1')} | Pct: {date['membri'].get(uid,{}).get('puncte_saptamanale',0)}", emoji="👮")
            for uid, un in membri[:25]]
        if opts:
            s = discord.ui.Select(placeholder="🔍 Selecteaza membrul...", options=opts)
            s.callback = self.on_sel; self.add_item(s)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌", ephemeral=True); return False
        return True

    async def on_sel(self, interaction):
        uid = interaction.data["values"][0]; date = incarca_date()
        if uid not in date["membri"]:
            await interaction.response.send_message("❌ Membrul nu exista!", ephemeral=True); return
        await interaction.response.edit_message(embed=make_embed_profil(uid, date["membri"][uid]), view=None); self.stop()


class ViewSelectResetare(discord.ui.View):
    def __init__(self, membri, autor_id):
        super().__init__(timeout=60); self.autor_id = autor_id
        date = incarca_date()
        opts = [discord.SelectOption(label=un[:100], value=uid,
            description=f"Grad: {date['membri'].get(uid,{}).get('grad','A1')} | Pct: {date['membri'].get(uid,{}).get('puncte_saptamanale',0)}", emoji="👮")
            for uid, un in membri[:25]]
        if opts:
            s = discord.ui.Select(placeholder="🔍 Selecteaza membrul...", options=opts)
            s.callback = self.on_sel; self.add_item(s)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌", ephemeral=True); return False
        return True

    async def on_sel(self, interaction):
        uid = interaction.data["values"][0]; date = incarca_date()
        if uid not in date["membri"]: await interaction.response.send_message("❌", ephemeral=True); return
        m = date["membri"][uid]
        emb = discord.Embed(title="⚠️ Confirmare Resetare",
            description=f"Resetezi punctele lui **{m['username']}**?\nAre **{m['puncte_saptamanale']}** puncte acum.", color=discord.Color.orange())
        await interaction.response.edit_message(embed=emb, view=ViewConfirmResetMembru(uid, m["username"], self.autor_id)); self.stop()


class ViewConfirmResetMembru(discord.ui.View):
    def __init__(self, uid, username, autor_id):
        super().__init__(timeout=30); self.uid = uid; self.username = username; self.autor_id = autor_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌", ephemeral=True); return False
        return True

    @discord.ui.button(label="✅ Da, Reseteaza", style=discord.ButtonStyle.danger)
    async def da(self, interaction, button):
        date = incarca_date()
        if self.uid in date["membri"]:
            m = date["membri"][self.uid]; v = m["puncte_saptamanale"]
            m["puncte_saptamanale"] = 0; m["raiduri_cayo"] = 0; m["activitati"] = {}
            salveaza_date(date)
            emb = discord.Embed(title="🔄 Puncte Resetate", color=discord.Color.orange())
            emb.add_field(name="Puncte Sterse", value=str(v), inline=True)
            emb.add_field(name="Puncte Acum", value="0", inline=True)
            await interaction.response.edit_message(embed=emb, view=None)
        self.stop()

    @discord.ui.button(label="❌ Anuleaza", style=discord.ButtonStyle.secondary)
    async def nu(self, interaction, button):
        await interaction.response.edit_message(content="❌ Anulat.", embed=None, view=None); self.stop()


class ViewSelectSterge(discord.ui.View):
    def __init__(self, membri, autor_id):
        super().__init__(timeout=60); self.autor_id = autor_id
        date = incarca_date()
        opts = [discord.SelectOption(label=un[:100], value=uid,
            description=f"Grad: {date['membri'].get(uid,{}).get('grad','A1')}", emoji="👮")
            for uid, un in membri[:25]]
        if opts:
            s = discord.ui.Select(placeholder="🔍 Selecteaza membrul...", options=opts)
            s.callback = self.on_sel; self.add_item(s)

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌", ephemeral=True); return False
        return True

    async def on_sel(self, interaction):
        uid = interaction.data["values"][0]; date = incarca_date()
        if uid not in date["membri"]: await interaction.response.send_message("❌", ephemeral=True); return
        username = date["membri"][uid]["username"]
        emb = discord.Embed(title="⚠️ Confirmare Stergere",
            description=f"Elimini definitiv pe **{username}** din baza de date?", color=discord.Color.red())
        await interaction.response.edit_message(embed=emb, view=ViewConfirmSterge(uid, username, self.autor_id)); self.stop()


class ViewConfirmSterge(discord.ui.View):
    def __init__(self, uid, username, autor_id):
        super().__init__(timeout=30); self.uid = uid; self.username = username; self.autor_id = autor_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌", ephemeral=True); return False
        return True

    @discord.ui.button(label="✅ Da, Sterge", style=discord.ButtonStyle.danger)
    async def da(self, interaction, button):
        date = incarca_date()
        if self.uid in date["membri"]: del date["membri"][self.uid]; salveaza_date(date)
        emb = discord.Embed(title="🗑️ Membru Sters", description=f"**{self.username}** eliminat.", color=discord.Color.red())
        await interaction.response.edit_message(embed=emb, view=None); self.stop()

    @discord.ui.button(label="❌ Anuleaza", style=discord.ButtonStyle.secondary)
    async def nu(self, interaction, button):
        await interaction.response.edit_message(content="❌ Anulat.", embed=None, view=None); self.stop()


class ViewConfirmResetSapt(discord.ui.View):
    def __init__(self, autor_id):
        super().__init__(timeout=30); self.autor_id = autor_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌", ephemeral=True); return False
        return True

    @discord.ui.button(label="✅ Da, Reseteaza Tot", style=discord.ButtonStyle.danger)
    async def da(self, interaction, button):
        await interaction.response.defer(ephemeral=True)
        emb = await executa_resetare()
        await interaction.followup.send(embed=emb, ephemeral=True); self.stop()

    @discord.ui.button(label="❌ Anuleaza", style=discord.ButtonStyle.secondary)
    async def nu(self, interaction, button):
        await interaction.response.edit_message(content="❌ Anulat.", embed=None, view=None); self.stop()


class ModalAdaugaMembru(discord.ui.Modal, title="Adauga Membru Nou"):
    username = discord.ui.TextInput(label="Nume Discord", placeholder="ex: IonPopescu", max_length=100)
    user_id = discord.ui.TextInput(label="ID Discord (click dreapta -> Copiaza ID)", placeholder="ex: 123456789012345678", max_length=20)
    grad = discord.ui.TextInput(label="Grad initial (A1/A2/A3/A4/A5)", default="A1", max_length=2)

    async def on_submit(self, interaction):
        uid = self.user_id.value.strip(); uname = self.username.value.strip()
        gv = self.grad.value.strip().upper()
        if gv not in GRADE:
            await interaction.response.send_message(f"❌ Grad invalid! Alege: {', '.join(GRADE)}", ephemeral=True); return
        if not uid.isdigit():
            await interaction.response.send_message("❌ ID-ul trebuie sa fie doar cifre!", ephemeral=True); return
        date = incarca_date()
        if uid in date["membri"]:
            await interaction.response.send_message(f"⚠️ Membrul cu ID `{uid}` exista deja!", ephemeral=True); return
        date["membri"][uid] = {
            "username": uname, "grad": gv, "puncte_saptamanale": 0, "puncte_totale": 0,
            "raiduri_cayo": 0, "activitati": {}, "avertismente": 0,
            "inregistrat_la": datetime.utcnow().isoformat(), "ultima_activitate": None, "istoric_resetari": []
        }
        salveaza_date(date)
        emb = discord.Embed(title="✅ Membru Inregistrat", color=discord.Color.green(), timestamp=datetime.utcnow())
        emb.add_field(name="👮 Nume", value=uname, inline=True)
        emb.add_field(name="🆔 ID", value=uid, inline=True)
        emb.add_field(name="🏅 Grad", value=gv, inline=True)
        emb.set_footer(text=f"Adaugat de {interaction.user.display_name}")
        await interaction.response.send_message(embed=emb, ephemeral=True)

# ── TASK-URI PERIODICE ────────────────────────────────────────

@tasks.loop(hours=1)
async def task_reset_sapt():
    tz = pytz.timezone(config.get("timezone", "Europe/Bucharest"))
    acum = datetime.now(tz)
    if acum.weekday() == 0 and acum.hour == 0:
        date = incarca_date()
        if date.get("saptamana_curenta") == _get_sapt(): return
        log.info("⏰ Resetare automata saptamanala...")
        emb = await executa_resetare()
        cid = config.get("canal_rapoarte")
        if cid:
            c = bot.get_channel(int(cid))
            if c: await c.send(embed=emb)

@tasks.loop(hours=24)
async def task_alerta():
    tz = pytz.timezone(config.get("timezone", "Europe/Bucharest"))
    acum = datetime.now(tz)
    if acum.weekday() == 6 and acum.hour == 18:
        date = incarca_date()
        sub = [m for m in date["membri"].values() if m["puncte_saptamanale"] < MINIM_SAPTAMANAL]
        cid = config.get("canal_rapoarte")
        if cid and sub:
            c = bot.get_channel(int(cid))
            if c:
                emb = discord.Embed(title="⚠️ ALERTA — Membri Sub Minim",
                    description=f"Resetarea are loc in **~6 ore**! {len(sub)} membri sunt in risc:", color=discord.Color.red(), timestamp=datetime.utcnow())
                emb.add_field(name="Membri in Risc",
                    value="\n".join(f"• **{m['username']}** ({m['grad']}) — {m['puncte_saptamanale']}/{MINIM_SAPTAMANAL} pct" for m in sub[:20])[:1024], inline=False)
                await c.send(embed=emb)

# ── COMENZI SLASH ─────────────────────────────────────────────

@bot.event
async def on_ready():
    log.info(f"✅ Bot conectat ca {bot.user} (ID: {bot.user.id})")
    bot.add_view(PanouPrincipal())
    try:
        synced = await bot.tree.sync()
        log.info(f"✅ Sincronizate {len(synced)} comenzi slash")
    except Exception as e:
        log.error(f"❌ Eroare sincronizare: {e}")
    task_reset_sapt.start()
    task_alerta.start()
    log.info("✅ Bot gata!")

@bot.tree.command(name="panou", description="Afiseaza panoul principal cu butoane de administrare")
async def panou(interaction: discord.Interaction):
    date = incarca_date()
    emb = discord.Embed(
        title="🚔 Panou Administrare — Sistem Puncte Politie",
        description=(
            f"**Saptamana:** {_get_sapt()}  |  **Membri:** {len(date['membri'])}\n\n"
            f"Foloseste butoanele pentru a gestiona membrii si punctele.\n"
            f"🔒 Actiunile administrative necesita rolul **{ROL_ADMIN}**."
        ),
        color=discord.Color.blue(), timestamp=datetime.utcnow()
    )
    emb.add_field(name="📊 Reguli Saptamanale", value=f"• Minim **{MINIM_SAPTAMANAL}** puncte\n• Minim **{MINIM_RAIDURI_CAYO}** raiduri Cayo\n• Sub minim → Retrogradare Luni", inline=True)
    emb.add_field(name="🏅 Praguri Avansare", value="\n".join(f"**{g}** → **{GRADE[GRADE.index(g)+1]}** = {p} pct" for g, p in PRAGURI_AVANSARE.items()), inline=True)
    emb.set_footer(text="Panoul ramane activ permanent")
    await interaction.response.send_message(embed=emb, view=PanouPrincipal())

@bot.tree.command(name="profil", description="Afiseaza profilul tau sau al altui membru")
@app_commands.describe(utilizator="Mentioneaza utilizatorul (optional)")
async def profil(interaction: discord.Interaction, utilizator: discord.Member = None):
    if utilizator is None: utilizator = interaction.user
    date = incarca_date(); uid = str(utilizator.id)
    if uid not in date["membri"]:
        await interaction.response.send_message(f"❌ **{utilizator.display_name}** nu este inregistrat! Un admin trebuie sa il adauge din panou.", ephemeral=True); return
    await interaction.response.send_message(embed=make_embed_profil(uid, date["membri"][uid]))

@bot.tree.command(name="clasament", description="Afiseaza clasamentul saptamanal")
async def clasament(interaction: discord.Interaction):
    date = incarca_date()
    if not date["membri"]:
        await interaction.response.send_message("❌ Nu exista membri!", ephemeral=True); return
    sortati = sorted(date["membri"].items(), key=lambda x: x[1]["puncte_saptamanale"], reverse=True)
    medalii = ["🥇", "🥈", "🥉"]
    linii = []
    for i, (uid, m) in enumerate(sortati[:20]):
        e = medalii[i] if i < 3 else f"`{i+1:2d}.`"
        s = "✅" if m["puncte_saptamanale"] >= MINIM_SAPTAMANAL else "⚠️"
        rd = "✅" if m.get("raiduri_cayo",0) >= MINIM_RAIDURI_CAYO else f"🏝️{m.get('raiduri_cayo',0)}"
        linii.append(f"{e} **{m['username']}** — `{m['grad']}` | **{m['puncte_saptamanale']}** pct {s} {rd}")
    total = len(date["membri"]); sub = sum(1 for m in date["membri"].values() if m["puncte_saptamanale"] < MINIM_SAPTAMANAL)
    emb = discord.Embed(title="🏆 Clasament Saptamanal", description=f"Saptamana **{_get_sapt()}**", color=discord.Color.gold(), timestamp=datetime.utcnow())
    emb.add_field(name=f"Top {min(len(sortati),20)}", value="\n".join(linii) or "—", inline=False)
    emb.add_field(name="👥 Total", value=str(total), inline=True)
    emb.add_field(name="✅ La Punct", value=str(total-sub), inline=True)
    emb.add_field(name="⚠️ Sub Minim", value=str(sub), inline=True)
    await interaction.response.send_message(embed=emb)

@bot.tree.command(name="ajutor", description="Afiseaza ghidul comenzilor")
async def ajutor(interaction: discord.Interaction):
    emb = discord.Embed(title="🚔 Ghid Bot Politie", color=discord.Color.blue())
    emb.add_field(name="📌 Comenzi", value="`/panou` — Panoul cu butoane\n`/profil [@user]` — Profil si puncte\n`/clasament` — Top membri\n`/ajutor` — Acest meniu", inline=False)
    emb.add_field(name="🔒 Din Panou", value=f"➕ Adauga/➖ Sterge/🔄 Reseteaza Puncte\n👤 Profil | ➕ Adauga | 🗑️ Sterge Membru\n🏆 Clasament | 📋 Verificare | 🔁 Resetare Sapt.\n\n*Necesita rol: **{ROL_ADMIN}***", inline=False)
    actv = "\n".join(f"{a['emoji']} {a['nume']}: **+{a['puncte']}** pct" for a in ACTIVITATI.values())
    emb.add_field(name="🎯 Activitati & Puncte", value=actv, inline=False)
    await interaction.response.send_message(embed=emb)

@bot.tree.error
async def on_err(interaction: discord.Interaction, error):
    log.error(f"Eroare: {error}")
    if not interaction.response.is_done():
        await interaction.response.send_message(f"❌ Eroare: `{error}`", ephemeral=True)

import os

if __name__ == "__main__":
    token = os.getenv("TOKEN")

    if not token:
        log.error("❌ TOKEN lipsa din Railway Variables!")
        exit(1)

    log.info("🚔 Pornire Bot Sagrada...")
    bot.run(token, log_handler=None)
