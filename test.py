from pickle import FALSE
import discord
import json
from datetime import datetime, timedelta
import asyncio
import os
import random

TOKEN_2 = os.getenv('TOKEN_2')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

try:
    with open("log.json", "r") as file:
        log_data = json.load(file)
except FileNotFoundError:
    log_data = {}
    
try:
    with open("items.json", "r") as file:
        items = json.load(file)
except FileNotFoundError:
    items = {}

try:
    with open("mobs.json", "r") as file:
        mobs = json.load(file)
except FileNotFoundError:
    mobs = {}

try:
    with open("title.json", "r") as file:
        player_title = json.load(file)
except FileNotFoundError:
    player_title = {}

try:
    with open("battle.json", "r") as file:
        battle = json.load(file)
except FileNotFoundError:
    battle = {}

@client.event
async def on_ready():
    print("Bot is ready.")
    client.loop.create_task(hourly_mob())

class BattleView(discord.ui.View):
    def __init__(self, timeout=300):
        super().__init__(timeout=timeout)
        self.responded = False
        self.message = None


    @discord.ui.button(label="Combattre", style=discord.ButtonStyle.green, custom_id="button_fight")
    async def fight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.message is None:
            self.message = interaction.message
        
        try:
            with open("battle.json", "r") as file:
                battle = json.load(file)
        except FileNotFoundError:
            battle = {}

        if interaction.user.name not in log_data:
            log_data[interaction.user.name] = {"id": interaction.user.id, "avenger": False, "rank": 0, "gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}

        #if log_data[interaction.user.name]["penality"] > 0:
            # await interaction.response.send_message("Vous avez échoué lors de votre dernier combat, vous devez donc vous reposez encore", ephemeral=True)
            # battle["players"][interaction.user.name] = interaction.user.name        
        #else:
        await interaction.response.send_message("Vous partez affronter le monstre", ephemeral=True)
        battle["players"][interaction.user.name] = interaction.user.name

        attaquant = ""
        total_pv = 0
        total_for = 0
        total_def = 0
        for player in battle["players"]:
            attaquant += "<@" + str(log_data[player]['id']) + "> "
            total_pv += log_data[player]['stats']['pv']
            total_for += log_data[player]['stats']['for']
            total_def += log_data[player]['stats']['def']
        attaquant += '\n**PV : ' + str(total_pv) + ' :hearts:   For : ' + str(total_for) + ' :crossed_swords:   Def : ' + str(total_def) + ' :shield:**'
        
        embed = interaction.message.embeds[0]
        new_fields = []
        for field in embed.fields:
            if field.name == "Combattez ce monstre !" or field.name == "Combat initié par":
                new_fields.append({"name":"Combat initié par", "value":attaquant, "inline":False})
            else:
                new_fields.append({"name": field.name, "value": field.value, "inline": field.inline})
        embed.clear_fields()
        for field in new_fields:
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed)

        with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)
        with open("battle.json", "w") as file:
            json.dump(battle, file, indent=4)

    @discord.ui.button(label="Demander de l'aide", style=discord.ButtonStyle.red, custom_id="button_help")
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.message is None:
            self.message = interaction.message

        channel = client.get_channel(CHANNEL_ID)

        if channel is None:
            return

        try:
            with open("battle.json", "r") as file:
                battle = json.load(file)
        except FileNotFoundError:
            battle = {}

        avenger = []
        for author in log_data:
            if(author != interaction.user.name and author not in battle["players"] and log_data[author]["avenger"]):
                avenger.append(log_data[author]["id"])

        mentions = " ".join([f"<@{user_id}>" for user_id in avenger])
        if len(mentions) > 0:
            await channel.send(f'Aventuriers : {mentions} rassemblement !')
            await interaction.response.send_message("Le message d'aide a été envoyé !", ephemeral=True)
        else:
            await interaction.response.send_message("Il n'y a personne à appeler !", ephemeral=True)

        for child in self.children:
            if child.label == "Demander de l'aide":
                child.disabled = True
                await interaction.message.edit(view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

        try:
            with open("battle.json", "r") as file:
                battle = json.load(file)
        except FileNotFoundError:
            battle = {}

        channel = client.get_channel(CHANNEL_ID)

        players = []
        total_pv = 0
        total_for = 0
        total_def = 0

        for player in battle["players"]:
            players.append(log_data[player]['id'])
            total_pv += log_data[player]['stats']['pv']
            total_for += log_data[player]['stats']['for']
            total_def += log_data[player]['stats']['def']
        
        color = discord.Color.red()

        if len(players) == 0:
            title = "Personne n'a eu le courage d'affronter ce monstre"
            embed = create_embed(title=title, color=color)
        else:
            if combat(battle['mob']['name'], battle['mob']['lvl'], total_pv, total_for, total_def):
                res = ''
                gold = 0
                xp = 0
                level_xp = [500, 600, 720, 864, 1036, 1243, 1492, 1791, 2149, 2578, 3093, 3711, 4453, 5343, 6411, 7693, 9231, 11077, 13293, 15951, 19141, 22969, 27563, 33075, 39690, 47628, 57153, 68584, 82300, 98760, 118512, 142214, 170657, 204788, 245746, 294895, 353873, 424647, 509576, 611491, 733790, 880548, 1056657, 1267989, 1521587, 1825904, 2191085, 2629302, 3155163, 3786195, 4543434, 5452120, 6542544, 7851052, 9421262, 11305514, 13566617, 16279940, 19535928, 23443113, 28131736, 33758083, 40509700, 48611640, 58333968, 70000762, 84000914, 100801096, 120961315, 145153578, 174184293, 209021151, 250825381, 301090457, 361308548, 433570258, 520284309, 624341171, 749209405, 899051286, 1078861543, 1294633852, 1553560622, 1864272746, 2237127295, 2684552754, 3221463305, 3865755966, 4638907159, 5566688591, 6680026309, 8016031570, 9619237884, 11543158461, 13851790153, 16622148183, 19946577820, 23935893384, 28723072061, 34467686474, 41361223769, 49633468522, 59560162226, 71472194671, 85766633605, 102919960326, 123503952391, 148204742869, 177845691442, 213414829731]
                mob = battle['mob']['name']
                if(mobs[mob]['loot']["gold"] > 0):
                    res = 'Gold • ' + str(battle['mob']['lvl'] * mobs[mob]['loot']['gold']) + ' :coin:\n'
                    gold = battle['mob']['lvl'] * mobs[mob]['loot']['gold'] // len(players)
                if(mobs[mob]['loot']["xp"] > 0):
                    res += 'XP • ' + str(battle['mob']['lvl'] * mobs[mob]['loot']['xp']) + ' :diamond_shape_with_a_dot_inside:'
                    xp = battle['mob']['lvl'] * mobs[mob]['loot']['xp'] // len(players)
                for player in battle["players"]:
                    log_data[player]['gold'] += gold
                    log_data[player]['level']['xp'] += xp
                    for lvl_xp in level_xp[log_data[player]['level']['lvl']:]:
                        if log_data[player]['level']['xp'] > lvl_xp:
                            log_data[player]['level']['xp'] -= lvl_xp
                            log_data[player]['level']['lvl'] += 1
                            log_data[player]['stats']['pv'] = int(log_data[player]['stats']['pv'] * 1.001) + 1
                            log_data[player]['stats']['for'] = int(log_data[player]['stats']['for'] * 1.001) + 1
                            log_data[player]['stats']['def'] = int(log_data[player]['stats']['def'] * 1.001) + 1
                        else:
                            break
                title = "Victoire !"
                color = discord.Color.green()
                tabFields = {"Récompenses à se partager :" : res}
            else:
                title = "Défaite !"
                tabFields = {} #Penality

            mentions = " ".join([f"<@{user_id}>" for user_id in players])
            description = mentions
            embed = create_embed(title=title, description=description, color=color, tabFields=tabFields)
        
        await channel.send(embed=embed)

        with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)

async def hourly_mob():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        return

    while not client.is_closed():
        now = datetime.now()
        next_hour = (now + timedelta(seconds=10)).replace(microsecond=0) #a1b2
        wait_time = (next_hour - now).total_seconds()

        await asyncio.sleep(wait_time)

        
    # Récompenses Loot Partage récompenses compteur de kill = titre = stats bonus / retire des pv et en cas de defaite repos 3h pv 0 to 100% / regen pv stat regen / 10min max pv max / stats de degat crit chance crit precision esquive degat brut saignement
        random_number = random.randint(1, 100)
        for mob in mobs:
            spawn_rate = round(random.random(), 4)
            if(spawn_rate <= mobs[mob]['spawn_rate']):
                lvl = random.randint(mobs[mob]['min_level'], mobs[mob]['max_level'])
                title = mobs[mob]['name'] + ' LVL ' + str(lvl)
                tabFields = {'PV : ' + str(lvl * mobs[mob]['stats']['pv']) + ' :hearts:   For : ' + str(lvl * mobs[mob]['stats']['for']) + ' :crossed_swords:   Def : ' + str(lvl * mobs[mob]['stats']['def']) + ' :shield:' : '', 'Combattez ce monstre !' : ''}
                image = mobs[mob]['image']
                mob_name = mob

                if(lvl <= 0):
                    color = discord.Color.blue()
                else:
                    if(lvl <= 20):
                        color = discord.Color.green()
                    else:
                        if(lvl <= 50):
                            color = discord.Color.green()
                        else:
                            if(lvl <= 200):
                                color = discord.Color.yellow()
                            else:
                                if(lvl <= 300):
                                    color = discord.Color.orange()
                                else:
                                    if(lvl <= 500):
                                        color = discord.Color.red()
                                    else:
                                        if(lvl <= 1000):
                                            color = discord.Color.white()
                
                embed = create_embed(title=title, color=color, image=image, tabFields=tabFields)
                break;

        view = BattleView(timeout=5) #a1b2
        view.message = await channel.send(embed=embed, view=view)

        battle = {"mob": {"name": mob_name, "lvl": lvl}, "players": {}}

        with open("battle.json", "w") as file:
            json.dump(battle, file, indent=4)

@client.event
async def on_message(message):
    updated = False
    if message.author == client.user:
        return

    if message.content.startswith("!"):
        if message.author.name not in log_data:
            log_data[message.author.name] = {"id": message.author.id, "avenger": False, "rank": 0, "gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
            updated = True

    if message.content.startswith("!info"):
        embed = info_action()
        await message.channel.send(embed=embed)

    if message.content.startswith("!gold"):
        embed = me_action(message.author.name, message.author.avatar, message.author.global_name, 'gold')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!daily"):
        if await time_command(message, "!daily", 24):
            embed = daily_action(message.author.name, message.author.avatar, message.author.global_name)
            await message.channel.send(embed=embed)
        updated = True
    
    if message.content.startswith("!explore"):
        if await time_command(message, "!explore", 1):
            embed = explore_action(message.author.name, message.author.avatar, message.author.global_name)
            await message.channel.send(embed=embed)
        updated = True
        
    if message.content.startswith("!rank"):
        embed = me_action(message.author.name, message.author.avatar, message.author.global_name, 'rank')
        await message.channel.send(embed=embed)
        updated = True
    
    if message.content.startswith("!top-rank"):
        embed = top_action(message.author.name, 'rank')
        await message.channel.send(embed=embed)
        updated = True
    
    if message.content.startswith("!top-gold"):
        embed = top_action(message.author.name, 'gold')
        await message.channel.send(embed=embed)
        updated = True
    
    if message.content.startswith("!bag"):
        embed = me_action(message.author.name, message.author.avatar, message.author.global_name, 'bag')
        await message.channel.send(embed=embed)
        updated = True
    
    if message.content.startswith("!purchase"):
        command_and_argument = message.content.split(maxsplit=1)
        
        if len(command_and_argument) == 2:
            command, item = command_and_argument
            item = item.title()
            embed = purchase_action(message.author.name, message.author.avatar, message.author.global_name, item)
            updated = True
        else:
            title = 'Achat'
            tabFields = {'Faites !purchase nom_item' : ''}
            color = discord.Color.red()
            embed = create_embed(title=title, color=color, author_name=message.author.global_name, author_icon=message.author.avatar, tabFields=tabFields)
        
        await message.channel.send(embed=embed)
    
    if message.content.startswith("!market"):
        embed = market_action()
        await message.channel.send(embed=embed)

    if message.content.startswith("!notif"):
        embed = notif_action(message.author.name)
        await message.channel.send(embed=embed)
        updated = True
           
    if message.content.startswith("!dungeon"):
        pass #dungeon_action

    if updated:
        with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)

def info_action():
    tabFields = {
        '!gold :' : 'Pour voir combien de gold vous avez.',
        '!rank :' : 'Pour voir vos stats.',
        '!daily :' : 'Pour récupérer des golds toutes les 24h.',
        '!explore :' : 'Pour récupérer 100 golds toutes les heures.',
        '!market :' : 'Pour acheter de quoi devenir plus fort.',
        '!top-gold :' : 'Pour voir le classement en Gold.',
        '!top-rank :' : 'Pour voir le classement en Rank.',
        '!bag :' : 'Pour voir ce que vous avez dans votre sac.',
        '!purchase :' : 'Pour acheter un item au market.',
        '!notif :' : "Pour rejoindre la liste des chads notifiés lors d'une demande d'aide",
        '!awaken :' : '[En travaux]',
        '!dungeon :' : '[En travaux]',
    }
    color = discord.Color.blue()
    title = 'Informations'
    return create_embed(title=title, color=color, tabFields=tabFields)

def market_action():
    base_items = ':billed_cap: Casquette • Def+1 • 500 :coin:\n:shirt: Tshirt • Def+2 • 1000 :coin:\n:jeans: Jean • Def+2 • 1000 :coin:\n:athletic_shoe: Baskets • Def+1 • 500 :coin:\n:dagger: Dague • For+3 • 1500 :coin:'
    material_items = ':regional_indicator_s: Étherium • 360000 :coin:\n:regional_indicator_a: Adamantium • 120000 :coin:\n:regional_indicator_b: Orichalque • 40000 :coin:\n:regional_indicator_c: Mithril • 13000 :coin:\n:regional_indicator_d: Argent • 4500 :coin:\n:regional_indicator_e: Fer • 1500 :coin:\n:regional_indicator_f: Cuir • 500 :coin:'
    rune_items = ':fire: Feu • For+1 • 5000 :coin:\n:seedling: Terre • Def+1 • 5000 :coin:\n:droplet: Eau • PV+100 • 5000 :coin:'
    rank_items = '<:Legendaire:1222193258403336222> Légendaire • 500000 :coin:\n<:Epique:1222193241022136491> Épique • 50000 :coin:\n<:Rare:1222193217957662760> Rare • 5000 :coin:'
    
    tabFields = {
        'Équipements de base : ' : base_items,
        'Matériaux : ' : material_items,
        'Runes : ' : rune_items,
        'Gemmes d\'éveil : ' : rank_items,
    }
    color = discord.Color.lighter_grey()
    title = 'Boutique'
    return create_embed(title=title, color=color, tabFields=tabFields)

def get_time(author_name, command):
    time = None
    
    if author_name in log_data and command in log_data[author_name]:
        time = log_data[author_name][command]

    return time
        
def check_time(author_name, command, cooldown: int):
    now = datetime.now()
    time = get_time(author_name, command)
    
    if time is None:
        time = str(now)
        
        if author_name in log_data:
            log_data[author_name][command] = time
        else:
            log_data[author_name] = {command: time}
        
        return True, None

    time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f")

    cooldown = timedelta(hours=cooldown)
    
    cooldown_time = time + cooldown
    check = cooldown_time < now
    waiting_time = None
    
    if not check:
        difference = cooldown_time - now
        waiting_time = string_time(difference)

    return check, waiting_time

def string_time(difference):
    waiting_time = None
    
    minutes, seconds = divmod(difference.total_seconds(), 60)
    hours, minutes = divmod(minutes, 60)
    
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    
    if hours > 1:
        waiting_time = f"{hours} heures"
    else:
        if hours == 1:
            waiting_time = "1 heure"
            
    if minutes > 1:
        if waiting_time is None:
            waiting_time = f"{minutes} minutes"
        else:
            waiting_time = waiting_time + f" et {minutes} minutes"
    else:
        if minutes == 1:
            if waiting_time is None:
                waiting_time = "1 minute"
            else:
                waiting_time = waiting_time + " et 1 minute"

    if seconds > 1:
        if waiting_time is None:
            waiting_time = f"{seconds} secondes"
        else:
            waiting_time = waiting_time + f" et {seconds} secondes"
    else:
        if seconds == 1:
            if waiting_time is None:
                waiting_time = "1 seconde"
            else:
                waiting_time = waiting_time + " et 1 seconde"
    
    if waiting_time is None:
        waiting_time = "0 seconde."
    else:
        waiting_time = waiting_time + "."
        
    return waiting_time

async def time_command(message, command, cooldown):
    author_name = message.author.name
    check, waiting_time = check_time(author_name, command, cooldown)
    
    if check:
        log_data[author_name][command] = str(datetime.now())
        return True
    else:
        await message.channel.send("Vous devez attendre encore " + waiting_time)
        return False

def me_action(author_name, author_icon, global_name, type):
    
    if author_name in log_data:
        if type not in log_data[author_name]:
            if type == 'bag':
                log_data[author_name][type] = {}
            else:
                log_data[author_name][type] = 0
    else:
        if type == 'bag':
            log_data[author_name] = {type: {}}
        else:
            log_data[author_name] = {type: 0}
    
    res = log_data[author_name][type]
    
    if type == 'gold':
        tabFields = {'Gold :' : str(res) + ' :coin:'}
        color = discord.Color.gold()
    else:
        rank = ['Pas d\'éveil', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s: :regional_indicator_s:']
        if type == 'rank':
            tabFields = {'Level :' : str(log_data[author_name]['level']['lvl']), 'Rank :' : rank[res], 'Stats :' : '', 'PV : ' + str(log_data[author_name]['stats']['pv']) + ' :hearts:': '', 'For : ' + str(log_data[author_name]['stats']['for']) + ' :crossed_swords:' : '', 'Def : ' + str(log_data[author_name]['stats']['def']) + ' :shield:': ''}
            color = discord.Color.dark_purple()
        else:
            bag = ''
            casquette = ''
            tshirt = ''
            jean = ''
            baskets = ''
            if type == 'bag':
                if res != {}:
                    for item in res:
                        if 'rank' in log_data[author_name][type][item] and log_data[author_name][type][item]['rank'] > 0:
                            if item == 'Casquette':
                                casquette = log_data[author_name][type][item]['icon'] + rank[log_data[author_name][type][item]['rank']] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n';
                            else:
                                if item == 'Tshirt':
                                    tshirt = log_data[author_name][type][item]['icon'] + rank[log_data[author_name][type][item]['rank']] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n';
                                else:
                                    if item == 'Jean':
                                        jean = log_data[author_name][type][item]['icon'] + rank[log_data[author_name][type][item]['rank']] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n';
                                    else:
                                        if item == 'Baskets':
                                            baskets = log_data[author_name][type][item]['icon'] + rank[log_data[author_name][type][item]['rank']] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n';
                                        else:  
                                            bag += log_data[author_name][type][item]['icon'] + rank[log_data[author_name][type][item]['rank']] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n'
                        else:
                            bag += log_data[author_name][type][item]['icon'] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n'
                    bag = casquette + tshirt + jean + baskets + bag
                else:
                    bag = 'Rien'
                tabFields = {'Vous avez :' : bag}
                color = discord.Color.dark_teal()
    
    footer = None
    if type != 'bag':     
        footer = 'Classement ' + type + ' : ' + ranking(type, author_name)
    return create_embed(color=color, author_name=global_name, author_icon=author_icon, footer=footer, tabFields=tabFields)

def top_action(author_name, type):
    if author_name in log_data:
        if type not in log_data[author_name]:
            log_data[author_name][type] = 0
    else:
        log_data[author_name] = {type: 0}

    filtered_authors = [author for author in log_data.keys() if type in log_data[author]]
    sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x][type], reverse=True)

    if(type == 'rank'):
        rank = ['Pas d\'éveil', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s: :regional_indicator_s:']

    tabFields = {}
    for i in range(len(sorted_authors)):
        if i > 8:
            break
        if(type == 'gold'):
            if i == 0:
                tabFields[''] = '**' + str(i+1) + '. ' + sorted_authors[i] + '  •  ' + str(log_data[sorted_authors[i]][type]) + ' :coin:\n'
            else:
                tabFields[''] += str(i+1) + '. ' + sorted_authors[i] + '  •  ' + str(log_data[sorted_authors[i]][type]) + ' :coin:\n'
        else:
            if(type == 'rank'):
                if i == 0:
                    tabFields[''] = '**' + str(i+1) + '. ' + sorted_authors[i] + '  •  ' + rank[log_data[sorted_authors[i]][type]] + '\n'
                else:
                    tabFields[''] += str(i+1) + '. ' + sorted_authors[i] + '  •  ' + rank[log_data[sorted_authors[i]][type]] + '\n'
    
    target_index = sorted_authors.index(author_name)
    ranking_position = target_index + 1
    
    tabFields[''] += '**'
    title = 'Classement ' + type
    color = discord.Color.blue()
    footer = 'Votre classement : ' + str(ranking_position) + '/' + str(len(sorted_authors))
    return create_embed(title=title, color=color, footer=footer, tabFields=tabFields)

def daily_action(author_name, author_icon, global_name):
    if author_name in log_data:
        if 'gold' in log_data[author_name]:
            log_data[author_name]['gold'] += 500
        else:
            log_data[author_name]['gold'] = 500
    else:
        log_data[author_name] = {'gold': 500}

    title = 'Daily bonus !'
    tabFields = {'Vous récupérez : ' : '500 :coin:'}
    color = discord.Color.green()
    footer = 'Revenez également demain !'
    return create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, footer=footer, tabFields=tabFields)

def explore_action(author_name, author_icon, global_name):
    if author_name in log_data:
        if 'gold' in log_data[author_name]:
            log_data[author_name]['gold'] += 100
        else:
            log_data[author_name]['gold'] = 100
    else:
        log_data[author_name] = {'gold': 100}

    title = 'Exploration bonus !'
    tabFields = {'Vous récupérez : ' : '100 :coin:'}
    color = discord.Color.green()
    footer = 'Revenez dans 1 heure !'
    return create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, footer=footer, tabFields=tabFields)


def create_embed(title = None, description = None, color = None, author_name = None, author_icon = None, image = None, footer = None, tabFields = None):
    embed = discord.Embed(
        title = title,
        description = description,
        color = color
    )
    
    if tabFields is not None:
        for name, value in tabFields.items():
            embed.add_field(name = name, value = value, inline = False)
            
    if image is not None:
        embed.set_image(url = image)
    
    if author_name is not None and author_icon is not None :
        embed.set_author(name = author_name, icon_url = author_icon)  

    if footer is not None:
        embed.set_footer(text = footer)

    return embed

def ranking(type, author_name):
    filtered_authors = [author for author in log_data.keys() if type in log_data[author]]
    sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x][type], reverse=True)
    target_index = sorted_authors.index(author_name)
    ranking_position = target_index + 1
    return str(ranking_position) + '/' + str(len(sorted_authors))

def purchase_action(author_name, author_icon, global_name, item):
    title = 'Achat'
    if item in items:
        if author_name in log_data:
            if 'gold' not in log_data[author_name]:
                log_data[author_name]['gold'] = 0
        else:
            log_data[author_name] = {'gold': 0}
        
        gold = log_data[author_name]['gold']
        
        if gold < items[item]['price']:
            manque = items[item]['price'] - gold
            tabFields = {'Vous n\'avez pas assez de gold, il vous manque : ' : str(manque) + ' :coin:'}
            color = discord.Color.red()
        else:
            upgrade = True
            if 'requirements' in items[item]:
                if 'Casquette' in log_data[author_name]['bag'] and log_data[author_name]['bag']['Casquette']['rank'] == items[item]['requirements']:
                    log_data[author_name]['bag']['Casquette']['rank'] += 1
                    upgrade = True
                else:
                    if 'Tshirt' in log_data[author_name]['bag'] and log_data[author_name]['bag']['Tshirt']['rank']  == items[item]['requirements']:
                        log_data[author_name]['bag']['Tshirt']['rank'] += 1
                        upgrade = True
                    else:
                        if 'Jean' in log_data[author_name]['bag'] and log_data[author_name]['bag']['Jean']['rank']  == items[item]['requirements']:
                            log_data[author_name]['bag']['Jean']['rank'] += 1
                            upgrade = True
                        else:
                            if 'Baskets' in log_data[author_name]['bag'] and log_data[author_name]['bag']['Baskets']['rank']  == items[item]['requirements']:
                                log_data[author_name]['bag']['Baskets']['rank'] += 1
                                upgrade = True
                            else:
                                if 'Dague' in log_data[author_name]['bag'] and log_data[author_name]['bag']['Dague']['rank']  == items[item]['requirements']:
                                    log_data[author_name]['bag']['Dague']['rank'] += 1
                                    upgrade = True
                                else:
                                    upgrade = False
            
            if 'unique' in items[item] and item in log_data[author_name]['bag']:
                tabFields = {'Ceci est un item unique, vous le possédez déjà.' : ''}
                color = discord.Color.red()
            else:
                if upgrade:
                    log_data[author_name]['gold'] = log_data[author_name]['gold'] - items[item]['price']
                    if 'stats' in items[item]:
                        if 'pv' in items[item]['stats']:
                            log_data[author_name]['stats']['pv'] += items[item]['stats']['pv']
                        if 'for' in items[item]['stats']:
                            log_data[author_name]['stats']['for'] += items[item]['stats']['for']
                        if 'def' in items[item]['stats']:
                            log_data[author_name]['stats']['def'] += items[item]['stats']['def']
                    tabFields = {'Vous venez d\'acheter : ' : items[item]['icon'] + ' ' + item}
                    color = discord.Color.green()
                    
                    materiaux = ['Cuir', 'Fer', 'Argent', 'Mithril', 'Orichalque', 'Adamantium', 'Étherium']
                    if item not in materiaux:
                        if item in log_data[author_name]['bag']:
                            log_data[author_name]['bag'][item]['quantity'] += 1
                        else:
                            if 'rank' in items[item]:
                                log_data[author_name]['bag'][item] = {'quantity': 1, 'icon': items[item]['icon'], 'rank': items[item]['rank']}
                            else:
                                log_data[author_name]['bag'][item] = {'quantity': 1, 'icon': items[item]['icon']}
                else:
                    rank = ['Basique', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:']
                    tabFields = {'L\'achat est impossible vérifie si vous avez au moins 1 équipement de rang ' + rank[items[item]['requirements']] : ''}
                    color = discord.Color.red()
    else:
        tabFields = {'Vérifiez l\'appélation de ce que vous voulez acheter.' : ''}
        color = discord.Color.red()
    
    return create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, tabFields=tabFields)

def combat(mob_name, mob_lvl, total_pv, total_for, total_def):
    mob_pv = mob_lvl * mobs[mob_name]['stats']['pv']
    mob_for = mob_lvl * mobs[mob_name]['stats']['for']
    mob_def = mob_lvl * mobs[mob_name]['stats']['def']

    # while mob_pv > 0 and total_pv > 0:
    #     mob_pv = mob_pv - max((total_for-mob_def), 10)
    #     if(mob_pv <= 0):
    #         return True
    #     total_pv = total_pv - max((mob_for-total_def), 10)
    #     if(total_pv <= 0):
    #         return False
    if (mob_pv // (total_for * (1 - (mob_def / (100 + mob_def))))) > (total_pv / (mob_for * (1 - (total_def / (100 + total_def))))):
        return False
    return True

def notif_action(author_name):
    chad = ""
    if log_data[author_name]['avenger']:
        log_data[author_name]['avenger'] = False
        title = "Vous ne serez plus notifié lorsqu'une personne demande de l'aide"
    else:
        log_data[author_name]['avenger'] = True
        title = "Desormais vous serez notifié lorsqu'une personne demande de l'aide"
    
    for player in log_data:
        if(log_data[player]['avenger']):
            chad += "<@" + str(log_data[player]['id']) + ">" + " "
    description = "Liste des chads actuelle : " + chad
    color = discord.Color.green()
    return create_embed(title=title, color=color, description=description)

client.run(TOKEN_2)
