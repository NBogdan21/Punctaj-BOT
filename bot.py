import discord
from discord import app_commands
from discord.ext import commands, tasks
import json, os
from datetime import datetime, UTC
import pytz, logging

# ── CONFIG ────────────────────────────────────────────────────

CONFIG_FILE = "config.json"
DB_FILE = "/data/date.json"  # 🔥 IMPORTANT PENTRU RAILWAY
ROL_ADMIN = "Los de la Sagrada"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ── DATE ──────────────────────────────────────────────────────

PRAGURI_AVANSARE = {"A1": 20, "A2": 25, "A3": 35, "A4": 40}
GRADE = ["A1", "A2", "A3", "A4", "A5"]
MINIM_SAPTAMANAL = 20
MINIM_RAIDURI_CAYO = 3

ACTIVITATI = {
    "raid_cayo": {"nume": "Raid Cayo", "puncte": 2},
    "actiune_oras": {"nume": "Actiune Oras", "puncte": 3},
}

# ── DATABASE ─────────────────────────────────────────────────

def incarca_date():
    if not os.path.exists(DB_FILE):
        d = {"membri": {}}
        salveaza_date(d)
        return d
    with open(DB_FILE, "r") as f:
        return json.load(f)

def salveaza_date(d):
    os.makedirs("/data", exist_ok=True)
    with open(DB_FILE, "w") as f:
        json.dump(d, f, indent=2)

# ── CONFIG ───────────────────────────────────────────────────

def incarca_config():
    if not os.path.exists(CONFIG_FILE):
        cfg = {"id_loguri": None}
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
        return cfg
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

config = incarca_config()
LOG_CHANNEL_ID = config.get("id_loguri")

# ── BOT ──────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ── READY ────────────────────────────────────────────────────

@bot.event
async def on_ready():
    log.info(f"✅ Bot online: {bot.user}")

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game("Sagrada")
    )

    try:
        await bot.tree.sync()
    except Exception as e:
        log.error(e)

# ── FUNCTIE LOGURI ───────────────────────────────────────────

async def trimite_log(interaction, mesaj):
    if not LOG_CHANNEL_ID:
        return

    canal = interaction.guild.get_channel(int(LOG_CHANNEL_ID))

    if not canal:
        try:
            canal = await interaction.guild.fetch_channel(int(LOG_CHANNEL_ID))
        except:
            log.error(f"❌ Nu gasesc canalul {LOG_CHANNEL_ID}")
            return

    await canal.send(mesaj)

# ── COMANDA TEST ─────────────────────────────────────────────

@bot.tree.command(name="test")
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Bot functioneaza!")

# ── ADAUGA PUNCTE ────────────────────────────────────────────

@bot.tree.command(name="adauga")
@app_commands.describe(user="User", puncte="Puncte")
async def adauga(interaction: discord.Interaction, user: discord.Member, puncte: int):

    date = incarca_date()
    uid = str(user.id)

    if uid not in date["membri"]:
        date["membri"][uid] = {
            "username": user.name,
            "puncte": 0
        }

    date["membri"][uid]["puncte"] += puncte
    salveaza_date(date)

    await interaction.response.send_message(f"✅ Ai adaugat {puncte} puncte lui {user.mention}")

    # 🔥 LOG
    await trimite_log(
        interaction,
        f"📊 {interaction.user.mention} a adaugat **{puncte}** puncte lui **{user.name}**"
    )

# ── PORNIRE ─────────────────────────────────────────────────

if __name__ == "__main__":
    token = os.getenv("TOKEN")

    if not token:
        log.error("❌ TOKEN lipsa!")
        exit()

    bot.run(token)
