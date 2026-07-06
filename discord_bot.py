import discord
from discord import app_commands
import math
from dotenv import load_dotenv
import os
import json
import random
from discord.ext import commands

# -------------------------------------------------
# Discord Bot Auftrag für Videospielhilfen
# -------------------------------------------------

load_dotenv()


TOKEN = "NeedsToReset"

GUILD_ID = discord.Object(id=HereIsID)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


DATA_FILE = "event_data.json"

AURA_TYPES = ["Sword", "Helmet", "Wax Seal", "Crown", "Book", "Shield"]

# lädt die gespeicherten Eventdaten aus der File

def load_event_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# wie werden Eventdaten gespeichert

def save_event_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def default_user_data(username):
    return {
        "name": username,
        "edicts": 0,
        "armor": 0,
        "aura": 0,
        "aura_types": {
            "Sword": 0,
            "Helmet": 0,
            "Wax Seal": 0,
            "Crown": 0,
            "Book": 0,
            "Shield": 0
        },
        "history": []
    }


event_group = app_commands.Group(
    name="event",
    description="Event Fortschritt speichern"
)

# Discord-Kommando, mit dem Spieler ihre Eventergebenisse speichern können und später aufrufen

@event_group.command(name="add", description="Speichert dein Event-Ergebnis")
@app_commands.describe(
    event="king, duke, earl, alliance duke, alliance earl, ressource, mini game single, mini game total",
    platzierung="Deine Platzierung",
    auratyp="Aura-Typ auswählen"
)
@app_commands.choices(auratyp=[
    app_commands.Choice(name="None", value="None"),
    app_commands.Choice(name="Sword", value="Sword"),
    app_commands.Choice(name="Helmet", value="Helmet"),
    app_commands.Choice(name="Wax Seal", value="Wax Seal"),
    app_commands.Choice(name="Crown", value="Crown"),
    app_commands.Choice(name="Book", value="Book"),
    app_commands.Choice(name="Shield", value="Shield"),
])
async def event_add(
    interaction: discord.Interaction,
    event: str,
    platzierung: int,
    auratyp: app_commands.Choice[str]
):
    event = event.lower()
    rewards = get_rewards(event, platzierung)

    if rewards is None:
        await interaction.response.send_message(
            "❌ Ungültiges Event oder Platzierung nicht im Reward-Bereich.",
            ephemeral=True
        )
        return

    aura_amount = rewards["aura"]
    aura_type = auratyp.value

    if aura_amount > 0 and aura_type == "None":
        await interaction.response.send_message(
            "❌ Dieses Event gibt Aura. Bitte wähle einen Aura-Typ aus.",
            ephemeral=True
        )
        return

    if aura_amount == 0:
        aura_type = "None"

    user_id = str(interaction.user.id)
    username = interaction.user.display_name
    data = load_event_data()

    if user_id not in data:
        data[user_id] = default_user_data(username)

    if "aura_types" not in data[user_id]:
        data[user_id]["aura_types"] = default_user_data(username)["aura_types"]

    data[user_id]["name"] = username
    data[user_id]["edicts"] += rewards["edicts"]
    data[user_id]["armor"] += rewards["armor"]
    data[user_id]["aura"] += aura_amount

    if aura_amount > 0:
        data[user_id]["aura_types"][aura_type] += aura_amount

    data[user_id]["history"].append({
        "event": event,
        "placement": platzierung,
        "edicts": rewards["edicts"],
        "armor": rewards["armor"],
        "aura": aura_amount,
        "aura_type": aura_type
    })

    save_event_data(data)

    await interaction.response.send_message(
        f"✅ **Event gespeichert für {username}**\n"
        f"Event: **{event}**\n"
        f"Platzierung: **{platzierung}**\n\n"
        f"📜 Edikte: **+{rewards['edicts']}**\n"
        f"🛡️ Rüstung: **+{rewards['armor']}**\n"
        f"✨ Aura: **+{aura_amount} {aura_type}**"
    )


@event_group.command(name="stats", description="Zeigt deinen gespeicherten Fortschritt")
async def event_stats(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    data = load_event_data()

    if user_id not in data:
        await interaction.response.send_message(
            "❌ Du hast noch keine Events gespeichert.",
            ephemeral=True
        )
        return

    user = data[user_id]
    aura_types = user.get("aura_types", {})

    aura_text = "\n".join(
        f"{aura_name}: **{aura_types.get(aura_name, 0)}**"
        for aura_name in AURA_TYPES
    )

    await interaction.response.send_message(
        f"📊 **Event Fortschritt von {interaction.user.display_name}**\n\n"
        f"📜 Edikte: **{user['edicts']}**\n"
        f"🛡️ Rüstung: **{user['armor']}**\n"
        f"✨ Aura gesamt: **{user['aura']}**\n\n"
        f"**Aura Typen:**\n{aura_text}"
    )


@event_group.command(name="history", description="Zeigt deine letzten gespeicherten Events")
async def event_history(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    data = load_event_data()

    if user_id not in data or len(data[user_id]["history"]) == 0:
        await interaction.response.send_message("❌ Keine History gefunden.", ephemeral=True)
        return

    history = data[user_id]["history"][-10:]

    text = ""
    for entry in history:
        text += (
            f"**{entry['event']}** Platz {entry['placement']} → "
            f"📜 {entry['edicts']} | 🛡️ {entry['armor']} | "
            f"✨ {entry['aura']} {entry.get('aura_type', 'None')}\n"
        )

    await interaction.response.send_message(
        f"📜 **Letzte Events von {interaction.user.display_name}**\n\n{text}"
    )


@event_group.command(name="reset", description="Setzt deinen eigenen Event-Fortschritt zurück")
async def event_reset(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    data = load_event_data()

    if user_id not in data:
        await interaction.response.send_message("❌ Du hast keine Daten zum Löschen.", ephemeral=True)
        return

    del data[user_id]
    save_event_data(data)

    await interaction.response.send_message("✅ Dein Event-Fortschritt wurde zurückgesetzt.", ephemeral=True)


try:
    bot.tree.add_command(event_group, guild=GUILD_ID)
except app_commands.CommandAlreadyRegistered:
    pass


# infos welche events welche belohnungen geben für berechnung
EVENT_REWARDS = {
    "king": {
        (1, 1): {"edicts": 175, "armor": 348, "aura": 20},
        (2, 2): {"edicts": 150, "armor": 300, "aura": 18},
        (3, 3): {"edicts": 125, "armor": 252, "aura": 16},
        (4, 5): {"edicts": 100, "armor": 210, "aura": 14},
        (6, 10): {"edicts": 75, "armor": 174, "aura": 12},
        (11, 20): {"edicts": 60, "armor": 138, "aura": 10},
        (21, 50): {"edicts": 45, "armor": 108, "aura": 8},
        (51, 100): {"edicts": 35, "armor": 81, "aura": 6},
    },
    "duke": {
        (1, 1): {"edicts": 100, "armor": 210, "aura": 12},
        (2, 2): {"edicts": 80, "armor": 174, "aura": 10},
        (3, 3): {"edicts": 60, "armor": 138, "aura": 8},
        (4, 5): {"edicts": 45, "armor": 108, "aura": 6},
        (6, 10): {"edicts": 30, "armor": 81, "aura": 4},
        (11, 20): {"edicts": 20, "armor": 54, "aura": 3},
        (21, 50): {"edicts": 15, "armor": 36, "aura": 2},
        (51, 100): {"edicts": 10, "armor": 27, "aura": 1},
    },
    "earl": {
        (1, 1): {"edicts": 30, "armor": 108, "aura": 10},
        (2, 2): {"edicts": 20, "armor": 81, "aura": 7},
        (3, 3): {"edicts": 15, "armor": 63, "aura": 5},
        (4, 5): {"edicts": 10, "armor": 51, "aura": 4},
        (6, 10): {"edicts": 7, "armor": 39, "aura": 3},
        (11, 20): {"edicts": 5, "armor": 27, "aura": 2},
        (21, 50): {"edicts": 3, "armor": 18, "aura": 1},
        (51, 150): {"edicts": 1, "armor": 9, "aura": 1},
    },
    "alliance duke": {
        (1, 1): {"edicts": 30, "armor": 75, "aura": 4},
        (2, 2): {"edicts": 20, "armor": 54, "aura": 3},
        (3, 3): {"edicts": 15, "armor": 36, "aura": 2},
        (4, 5): {"edicts": 10, "armor": 18, "aura": 1},
        (6, 10): {"edicts": 5, "armor": 9, "aura": 1},
        (11, 25): {"edicts": 1, "armor": 0, "aura": 0},
    },
    "alliance earl": {
        (1, 1): {"edicts": 15, "armor": 42, "aura": 4},
        (2, 2): {"edicts": 12, "armor": 30, "aura": 3},
        (3, 3): {"edicts": 9, "armor": 21, "aura": 2},
    },
    "ressource": {
        (1, 1): {"edicts": 10, "armor": 42, "aura": 0},
        (2, 2): {"edicts": 7, "armor": 30, "aura": 0},
        (3, 3): {"edicts": 5, "armor": 21, "aura": 0},
        (4, 5): {"edicts": 3, "armor": 15, "aura": 0},
        (6, 10): {"edicts": 2, "armor": 9, "aura": 0},
    },
    "mini game single": {
        (1, 1): {"edicts": 6, "armor": 18, "aura": 0},
        (2, 2): {"edicts": 5, "armor": 15, "aura": 0},
        (3, 3): {"edicts": 4, "armor": 12, "aura": 0},
        (4, 5): {"edicts": 3, "armor": 9, "aura": 0},
        (6, 10): {"edicts": 2, "armor": 6, "aura": 0},
        (11, 20): {"edicts": 1, "armor": 3, "aura": 0},
    },
    "mini game total": {
        (1, 1): {"edicts": 15, "armor": 54, "aura": 0},
        (2, 2): {"edicts": 12, "armor": 42, "aura": 0},
        (3, 3): {"edicts": 9, "armor": 33, "aura": 0},
        (4, 5): {"edicts": 7, "armor": 24, "aura": 0},
        (6, 10): {"edicts": 5, "armor": 18, "aura": 0},
        (11, 20): {"edicts": 3, "armor": 12, "aura": 0},
        (21, 50): {"edicts": 2, "armor": 6, "aura": 0},
    },
}


def get_rewards(event_name, placement):
    event_name = event_name.lower()

    if event_name not in EVENT_REWARDS:
        return None

    for (start, end), rewards in EVENT_REWARDS[event_name].items():
        if start <= placement <= end:
            return rewards

    return None

# cmd
@bot.event
async def on_ready():

    print(f"{bot.user} ist online!")

    try:
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"{len(synced)} Slash Commands synchronisiert")
    except Exception as e:
        print(e)


@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")





# berechnet die Buffs die eine Spielsektion namens "Vittori" je nach Level gibt. 

@bot.tree.command(name="vittori", description="Berechnet Vittori Buffs (Level 1-50)", guild=GUILD_ID)
async def vittori(interaction: discord.Interaction, level: int):
    if level < 1 or level > 50:
        await interaction.response.send_message(
            "❌ This is no number between 1-50",
            ephemeral=True
        )
        return

    point_cost = {
        13: 7000,
        14: 8000,
        15: 9000,
        16: 10000,
        17: 12000,
        18: 14000,
        19: 16000,
        20: 18000,
        21: 20000,
        22: 22000,
        23: 24000,
        24: 26000,
        25: 28000,
        26: 30000,
        27: 32000,
        28: 34000,
        29: 36000,
        30: 38000,
        31: 40000,
        32: 42000,
        33: 44000,
        34: 46000,
        35: 48000,
        36: 50000,
        37: 52000,
        38: 55000,
        39: 58000,
        40: 61000,
        41: 64000,
        42: 67000,
        43: 70000,
        44: 73000,
        45: 76000,
        46: 79000,
        47: 82000,
        48: 85000,
        49: 88000,
        50: 91000
    }

    cost = point_cost.get(level)

    if cost is None:
        cost_text = "Unknown"
        attribute_bonus = "Unknown"
    else:
        cost_text = f"{cost:,}"
        attribute_bonus = f"{cost * 4:,}"

    decor_multiplier = (level - 1) // 3 + 1

    strength = 0
    intellect = 0
    leadership = 0
    charisma = 0

    if level >= 5:
        strength = 1
    if level >= 8:
        intellect = 1
    if level >= 11:
        leadership = 1
    if level >= 14:
        charisma = 1

    if level >= 17:
        strength = 2
    if level >= 20:
        intellect = 2
    if level >= 23:
        leadership = 2
    if level >= 26:
        charisma = 2

    if level >= 29:
        strength = 3
    if level >= 32:
        intellect = 3
    if level >= 35:
        leadership = 3
    if level >= 38:
        charisma = 3

    if level >= 41:
        strength = 4
    if level >= 44:
        intellect = 4
    if level >= 47:
        leadership = 4
    if level >= 50:
        charisma = 4

    if level <= 2:
        heir = 2
    elif level <= 5:
        heir = 6
    elif level <= 8:
        heir = 12
    elif level <= 11:
        heir = 18
    elif level <= 14:
        heir = 24
    elif level <= 17:
        heir = 30
    elif level <= 20:
        heir = 36
    elif level <= 23:
        heir = 42
    elif level <= 26:
        heir = 48
    elif level <= 29:
        heir = 54
    elif level <= 32:
        heir = 60
    elif level <= 35:
        heir = 66
    elif level <= 38:
        heir = 72
    elif level <= 41:
        heir = 78
    elif level <= 44:
        heir = 84
    elif level <= 47:
        heir = 90
    else:
        heir = 96

    embed = discord.Embed(
        title=f"⚔️ Vittori Level {level} ({cost_text} points)",
        description="Vittori Buff Calculator",
        color=0x9b59b6
    )

    embed.add_field(
        name="🔷 Decor Multiplier",
        value=f"×{decor_multiplier}",
        inline=False
    )

    embed.add_field(
        name="📈 Attribute Bonus",
        value=f"+{attribute_bonus}",
        inline=False
    )

    embed.add_field(
        name="🧬 Talent Bonuses",
        value=(
            f"Strength +{strength} 💪\n"
            f"Intellect +{intellect} 🧠\n"
            f"Leadership +{leadership} ⚔️\n"
            f"Charisma +{charisma} 💬"
        ),
        inline=False
    )

    embed.add_field(
        name="🌱 Heir Growth",
        value=f"+{heir}%",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# Babypower Berechnung Bot

@bot.tree.command(name="babypower", description="Berechnet Baby Power Range", guild=GUILD_ID)
@app_commands.describe(
    intimacy="Deine Intimität",
    vittori_percentage="Vittori Prozentwert"
)
async def babypower(interaction: discord.Interaction, intimacy: float, vittori_percentage: float):
    x = intimacy * 10 * (1 + vittori_percentage / 100)
    y = intimacy * 21.7 * (1 + vittori_percentage / 100)

    await interaction.response.send_message(
        f"👶 **Baby Power Calculator**\n"
        f"Your babies will have a power of **{x:,.2f} - {y:,.2f} million**"
    )

# Royal Racing Event Infotext
@bot.tree.command(name="mounts", description="Zeigt Royal Racing Mounts", guild=GUILD_ID)
async def mounts(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐎 Royal Racing",
        description="Dates of Royal Racing Mounts",
        color=0x8e44ad
    )

    embed.add_field(
        name="🔄 Royal Racing Order",
        value="Horse, Boar → Bison, Goat x2\n→ White Rhino → Deer → Elephant x5\n→ War Bear → Lion → Warg → Tiger",
        inline=False
    )

    embed.add_field(
        name="📅 Royal Racing Dates",
        value=(
            "July 🐺\n"
            "August 🐯\n"
            "September 🐻\n"
            "October 🦁\n"
            "November 🐺\n"
            "December 🐯\n"
            "January 🐻\n"
            "February 🦁\n"
            "March 🐺\n"
            "April 🐯"
        ),
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# Knightencounter Infotext
@bot.tree.command(name="knightencounter", description="Shows Knight Encounter Timeline", guild=GUILD_ID)
async def knightencounter(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ Knight Encounter",
        description="Timeline of Knight Encounter Knights",
        color=0x3498db
    )

    embed.add_field(
        name="📅 Encounter Timeline",
        value=(
            "January    🔴 Anthony\n"
            "February   🩷 Brad\n"
            "March      🩷 Rose\n"
            "April      🔵 Plato\n"
            "May        🔴 Leonidas\n"
            "June       🔵 Archimedis\n"
            "July       🔴 Hannibal\n"
            "August     🩵 Aspasia\n"
            "September  🧡 Mulan\n"
            "October    🔵 Thales\n"
            "November   🔴 Biggus Dickus\n"
            "December   🔵 Sokrates"
        ),
        inline=False
    )

    await interaction.response.send_message(embed=embed)


    await interaction.response.send_message(embed=embed)

# Bot der Ritter ärgert
@bot.tree.command(name="drake", description="Deal with Francis Drake", guild=GUILD_ID)
async def drake(interaction: discord.Interaction):

    methods = [
        "🐟 Francis Drake was slapped by a giant tuna.",
        "🏴‍☠️ Francis Drake walked the plank voluntarily after seeing the odds.",
        "🍊 Francis Drake was defeated by an angry orange.",
        "🐉 Francis Drake was launched into the horizon by a dragon.",
        "🪑 Francis Drake was hit with a flying chair.",
        "🍌 Francis Drake slipped on a banana peel and vanished dramatically.",
        "🚀 Francis Drake was sent into orbit by a cannon.",
        "🤜🥝💥 Kiwi smashed"
    ]

    await interaction.response.send_message(random.choice(methods))
    
# Würfel
@bot.tree.command(name="dice", description="Würfelt eine Zahl von 1 bis 6", guild=GUILD_ID)
async def dice(interaction: discord.Interaction):
    zahl = random.randint(1, 6)
    await interaction.response.send_message(f"🎲 Du hast eine {zahl} gewürfelt!")

# Rechner für Rittermacht
@bot.tree.command(name="knightpower", description="Berechnet Knight Power", guild=GUILD_ID)
@app_commands.describe(
    stars="Anzahl Talent Sterne",
    level="Knight Level",
    book_bonus="Book Bonus Wert"
)
async def knightpower(interaction: discord.Interaction, stars: int, level: int, book_bonus: float):
    result = (stars * level * 20) + (100 * math.sqrt(book_bonus))
    await interaction.response.send_message(f"⚔️ Knight Power: {result:,.2f}")

# Rechner für Rittertalente
@bot.tree.command(name="talentbonus", description="Berechnet Talent Bonus", guild=GUILD_ID)
@app_commands.describe(
    stars="Talent Sterne",
    level="Level"
)
async def talentbonus(interaction: discord.Interaction, stars: float, level: int):
    lvl = level - 1
    result = (stars / 10) * (100 + 3 * lvl + (lvl ** 2))
    await interaction.response.send_message(f"🧠 Talent Bonus: {result:,.2f}")

# Ballroom-Rechner
@bot.tree.command(name="ballroom", description="Lover Power Ballroom Tanz", guild=GUILD_ID)
async def ballroom(interaction: discord.Interaction, charm: float):
    result = 67 * charm * (charm + 100) / 1000
    await interaction.response.send_message(f"💃 Ballroom Power: {result:,.2f}")

# Liebhaberrechner
@bot.tree.command(name="greetpower", description="Lover Power Greetings", guild=GUILD_ID)
async def greetpower(interaction: discord.Interaction, charm: float):
    result = 3 * charm * (charm + 100) / 1000
    await interaction.response.send_message(f"🤝 Greeting Power: {result:,.2f}")

bot.run(TOKEN)