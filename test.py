from pickle import FALSE
import discord
from discord import app_commands
import json
from datetime import datetime, timedelta
import asyncio
import os
import random
import unicodedata

TOKEN = os.getenv('TOKEN')
SAKURA_CHANNEL_ID = int(os.getenv('SAKURA_CHANNEL_ID'))
ENCHERE_SAKURA_CHANNEL_ID = int(os.getenv('ENCHERE_SAKURA_CHANNEL_ID'))

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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

try:
    with open("wheel.json", "r") as file:
        wheel = json.load(file)
except FileNotFoundError:
    wheel = {}

try:
    with open("craft.json", "r") as file:
        craft = json.load(file)
except FileNotFoundError:
    craft = {}
    
try:
    with open("classes.json", "r") as file:
        classes = json.load(file)
except FileNotFoundError:
    classes = {}

try:
    with open("brocante.json", "r") as file:
        brocante = json.load(file)
except FileNotFoundError:
    brocante = {}

@client.event
async def on_ready():
    print("Bot is ready.")
    await tree.sync()
    print("Commandes synchronisées avec succès.")
    client.loop.create_task(hourly_mob())

class BattleView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.message = None


    @discord.ui.button(label="Combattre", style=discord.ButtonStyle.green, custom_id="button_fight")
    async def fight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.timeout = 0
        if self.message is None:
            self.message = interaction.message

        try:
            with open("battle.json", "r") as file:
                battle = json.load(file)
        except FileNotFoundError:
            battle = {}

        if interaction.user.name not in log_data:
            max_place = max((player["place"] for player in log_data.values()), default=0)
            place = max_place + 1
            log_data[interaction.user.name] = {"id": interaction.user.id, "global_name": interaction.user.global_name, "avatar": str(interaction.user.avatar), "avenger": False, "rank": 0, "place": place,"gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
        else:
            if 'global_name' not in log_data[interaction.user.name] or 'avatar' not in log_data[interaction.user.name]:
                log_data[interaction.user.name]['global_name'] = interaction.user.global_name
                log_data[interaction.user.name]['avatar'] = str(interaction.user.avatar)

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

        channel = client.get_channel(SAKURA_CHANNEL_ID)

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

        channel = client.get_channel(SAKURA_CHANNEL_ID)

        players = []
        total_pv = 0
        total_for = 0
        total_def = 0

        for player in battle["players"]:
            players.append(log_data[player]['id'])
            if "classe" in log_data[player] and "name" in log_data[player]["classe"] and log_data[player]["classe"]["name"] == "Assassin":
                total_pv += log_data[player]['stats']['pv'] * 2
                total_for += log_data[player]['stats']['for'] * 2
                total_def += log_data[player]['stats']['def'] * 2
            else:
                total_pv += log_data[player]['stats']['pv']
                total_for += log_data[player]['stats']['for']
                total_def += log_data[player]['stats']['def']

        color = discord.Color.red()

        if len(players) == 0:
            title = "Personne n'a eu le courage d'affronter ce monstre"
            embed = create_embed(title=title, color=color)
        else:
            nbr_debuffer = 0
            
            for player in battle["players"]:
                if "classe" in log_data[player] and "name" in log_data[player]["classe"] and log_data[player]["classe"]["name"] == "Débuffer":
                    nbr_debuffer += 1
                    log_data[player]["classe"]["progression 1"] += 1
                    
            res_combat = combat(battle['mob']['name'], battle['mob']['lvl'], total_pv, total_for, total_def, nbr_debuffer)
            
            if res_combat:
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
                    
                player_levelup = ""
                bonus_xp = ""
                
                for player in battle["players"]:
                    level_up = 0
                    log_data[player]['gold'] += gold
                    
                    if "classe" in log_data[player] and "name" in log_data[player]["classe"] and log_data[player]["classe"]["name"] == "Assassin":
                        log_data[player]["classe"]["progression 1"] += 1
                    
                    now = datetime.now()
                    boosted_time = datetime.strptime(log_data[player]["xp_boosted"], "%Y-%m-%d %H:%M:%S.%f")
                    
                    if boosted_time > now:
                        xp_win = xp*2
                        bonus_xp = bonus_xp + "<@" + str(log_data[player]['id']) + "> + " + str(xp) + " :diamond_shape_with_a_dot_inside:\n"
                    else:
                        xp_win = xp
                        
                    log_data[player]['level']['xp'] += xp_win
                    
                    for lvl_xp in level_xp[log_data[player]['level']['lvl']:]:
                        if log_data[player]['level']['xp'] > lvl_xp:
                            log_data[player]['level']['xp'] -= lvl_xp
                            log_data[player]['level']['lvl'] += 1
                            
                            if "PointXP" in log_data[player]['bag']:
                                log_data[player]['bag']['PointXP']["quantity"] += 1
                            else:
                                log_data[player]['bag']['PointXP'] = {"quantity": 1, "icon": ":white_flower:"}
                                
                            level_up += 1
                        else:
                            break
                    
                    if level_up > 0:
                        player_levelup = player_levelup + "<@" + str(log_data[player]['id']) + "> + " + str(level_up) + " level\n"
                        
                if player_levelup == "":
                    if bonus_xp == "":
                        tabFields = {"Récompenses à se partager :" : res}
                    else:
                        tabFields = {"Récompenses à se partager :" : res, "Bonus boost XP :" : bonus_xp}
                else:
                    if bonus_xp == "":
                        tabFields = {"Récompenses à se partager :" : res, "Level UP :" : player_levelup}
                    else:
                        tabFields = {"Récompenses à se partager :" : res, "Bonus boost XP :" : bonus_xp, "Level UP :" : player_levelup}

                title = "Victoire !"
                color = discord.Color.green()
                battle['status'] = 'victoire'
            else:
                title = "Défaite !"
                tabFields = {} #Penality
                battle['status'] = 'defaite'

            mentions = " ".join([f"<@{user_id}>" for user_id in players])
            description = mentions
            embed = create_embed(title=title, description=description, color=color, tabFields=tabFields)

        await channel.send(embed=embed)

        with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)

        with open("battle.json", "w") as file:
            json.dump(battle, file, indent=4)

class EnchereView(discord.ui.View):
    def __init__(self, timeout, lot):
        super().__init__(timeout=timeout)
        self.message = None
        self.lot = lot

    @discord.ui.button(label="+ 500", style=discord.ButtonStyle.green, custom_id="btn_500")
    async def btn_500(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.timeout = 0
        if self.message is None:
            self.message = interaction.message

        try:
            with open("enchere.json", "r") as file:
                enchere = json.load(file)
        except FileNotFoundError:
            enchere = {}

        if interaction.user.name not in log_data:
            max_place = max((player["place"] for player in log_data.values()), default=0)
            place = max_place + 1
            log_data[interaction.user.name] = {"id": interaction.user.id, "global_name": interaction.user.global_name, "avatar": str(interaction.user.avatar), "avenger": False, "rank": 0, "place": place,"gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
        else:
            if 'global_name' not in log_data[interaction.user.name] or 'avatar' not in log_data[interaction.user.name]:
                log_data[interaction.user.name]['global_name'] = interaction.user.global_name
                log_data[interaction.user.name]['avatar'] = str(interaction.user.avatar)

        await interaction.response.send_message("Votre mise a été prise en compte", ephemeral=True)

        lot = self.lot
        enchere[lot]['last_price'] += 500
        enchere[lot]['last_player'] = interaction.user.name
        enchere[lot]['join_player'][interaction.user.name] = enchere[lot]['last_price']

        embed = interaction.message.embeds[0]
        id = str(log_data[interaction.user.name]['id'])
        embed.clear_fields()
        embed.add_field(name="Plus grosse mise : ", value= str(enchere[lot]['last_price']) + ' <:sakura_coin:1217220808083247154> <@' + id + '>', inline=True)
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed)

        with open("enchere.json", "w") as file:
            json.dump(enchere, file, indent=4)

    @discord.ui.button(label="+ 1 000", style=discord.ButtonStyle.green, custom_id="btn_1000")
    async def btn_1000(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.timeout = 0
        if self.message is None:
            self.message = interaction.message

        try:
            with open("enchere.json", "r") as file:
                enchere = json.load(file)
        except FileNotFoundError:
            enchere = {}

        if interaction.user.name not in log_data:
            max_place = max((player["place"] for player in log_data.values()), default=0)
            place = max_place + 1
            log_data[interaction.user.name] = {"id": interaction.user.id, "global_name": interaction.user.global_name, "avatar": str(interaction.user.avatar), "avenger": False, "rank": 0, "place": place,"gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
        else:
            if 'global_name' not in log_data[interaction.user.name] or 'avatar' not in log_data[interaction.user.name]:
                log_data[interaction.user.name]['global_name'] = interaction.user.global_name
                log_data[interaction.user.name]['avatar'] = str(interaction.user.avatar)

        await interaction.response.send_message("Votre mise a été prise en compte", ephemeral=True)

        lot = self.lot
        enchere[lot]['last_price'] += 1000
        enchere[lot]['last_player'] = interaction.user.name
        enchere[lot]['join_player'][interaction.user.name] = enchere[lot]['last_price']

        embed = interaction.message.embeds[0]
        id = str(log_data[interaction.user.name]['id'])
        embed.clear_fields()
        embed.add_field(name="Plus grosse mise : ", value= str(enchere[lot]['last_price']) + ' <:sakura_coin:1217220808083247154> <@' + id + '>', inline=True)
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed)

        with open("enchere.json", "w") as file:
            json.dump(enchere, file, indent=4)


    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

        try:
            with open("enchere.json", "r") as file:
                enchere = json.load(file)
        except FileNotFoundError:
            enchere = {}

        channel = client.get_channel(ENCHERE_SAKURA_CHANNEL_ID)
        lot = self.lot

        title = "Fin de l'enchère !"
        color = discord.Color.green()
        if enchere[lot]['last_player'] == "":
            title = "Aucun participant"
            color = discord.Color.red()
            embed = create_embed(title=title, color=color)
        else:
            winner = '<@' + str(log_data[enchere[lot]['last_player']]['id']) + '>'
            gain = str(enchere[lot]['quantity']) + ' :coin:'
            mise = str(enchere[lot]['last_price']) + ' <:sakura_coin:1217220808083247154>'
            participants = ""
            for player in enchere[lot]['join_player']:
                participants += '<@' + str(log_data[player]['id']) + '> ' + str(enchere[lot]['join_player'][player]) + ' <:sakura_coin:1217220808083247154>\n'
            tabFields = {"Vainqueur des enchères :" : winner, "Gains :" : gain, "Mise :" : mise, "Participants :" : participants}
            embed = create_embed(title=title, color=color, tabFields=tabFields)

            log_data[enchere[lot]['last_player']]['gold'] += enchere[lot]['quantity']

        await channel.send(embed=embed)

        with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)

class EveilView(discord.ui.View):
    def __init__(self, timeout, nbr_gem, gem_type, author_name):
        super().__init__(timeout=timeout)
        self.nbr_gem = nbr_gem
        self.gem_type = gem_type
        self.message = None
        self.author_name = author_name

    @discord.ui.button(label="M'éveiller", style=discord.ButtonStyle.green, custom_id="btn_eveil")
    async def btn_eveil(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.name == self.author_name:
            rank = ['Pas d\'éveil', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s: :regional_indicator_s:', '???']
            self.timeout = 0
            if self.message is None:
                self.message = interaction.message

            if interaction.user.name not in log_data:
                max_place = max((player["place"] for player in log_data.values()), default=0)
                place = max_place + 1
                log_data[interaction.user.name] = {"id": interaction.user.id, "global_name": interaction.user.global_name, "avatar": str(interaction.user.avatar), "avenger": False, "rank": 0, "place": place,"gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
            else:
                if 'global_name' not in log_data[interaction.user.name] or 'avatar' not in log_data[interaction.user.name]:
                    log_data[interaction.user.name]['global_name'] = interaction.user.global_name
                    log_data[interaction.user.name]['avatar'] = str(interaction.user.avatar)

            log_data[interaction.user.name]['rank'] += 1
            log_data[interaction.user.name]['bag'][self.gem_type]['quantity'] -= self.nbr_gem
            if log_data[interaction.user.name]['bag'][self.gem_type]['quantity'] == 0:
                del log_data[interaction.user.name]['bag'][self.gem_type]

            await interaction.response.send_message("Vous vous êtes éveillé au rang : " + rank[log_data[interaction.user.name]['rank']] + ', félicitations !')

            for child in self.children:
                child.disabled = True
                await interaction.message.edit(view=self)

            with open("log.json", "w") as file:
                json.dump(log_data, file, indent=4)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)    
class BoostXPView(discord.ui.View):
    def __init__(self, timeout, author_name):
        super().__init__(timeout=timeout)
        self.message = None
        self.author_name = author_name

    @discord.ui.button(label="Utiliser", style=discord.ButtonStyle.green, custom_id="btn_boostxp")
    async def btn_boostxp(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.name == self.author_name:
            self.timeout = 0
            if self.message is None:
                self.message = interaction.message

            if interaction.user.name not in log_data:
                max_place = max((player["place"] for player in log_data.values()), default=0)
                place = max_place + 1
                log_data[interaction.user.name] = {"id": interaction.user.id, "global_name": interaction.user.global_name, "avatar": str(interaction.user.avatar), "avenger": False, "rank": 0, "place": place,"gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
            else:
                if 'global_name' not in log_data[interaction.user.name] or 'avatar' not in log_data[interaction.user.name]:
                    log_data[interaction.user.name]['global_name'] = interaction.user.global_name
                    log_data[interaction.user.name]['avatar'] = str(interaction.user.avatar)

            now = datetime.now()
            last_boosted_time = datetime.strptime(log_data[interaction.user.name]['xp_boosted'], "%Y-%m-%d %H:%M:%S.%f")
            
            if last_boosted_time > now:
                choice_date = last_boosted_time
            else:
                choice_date = now
            
            boost_duration = choice_date + timedelta(days=1)
            log_data[interaction.user.name]['xp_boosted'] = str(boost_duration)
            log_data[interaction.user.name]['bag']["BoostXP"]['quantity'] -= 1
            
            if log_data[interaction.user.name]['bag']["BoostXP"]['quantity'] == 0:
                del log_data[interaction.user.name]['bag']["BoostXP"]

            formatted_boost_duration = boost_duration.strftime("%d/%m/%Y à %Hh%M")  # Reformater

            await interaction.response.send_message("Votre gain d'XP est multiplié par 2, fin de l'effet le " + formatted_boost_duration)

            for child in self.children:
                child.disabled = True
                await interaction.message.edit(view=self)

            with open("log.json", "w") as file:
                json.dump(log_data, file, indent=4)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

class WheelView(discord.ui.View):
    def __init__(self, timeout, author_name):
        super().__init__(timeout=timeout)
        self.message = None
        self.author_name = author_name

    @discord.ui.button(label="Tenter ma chance", style=discord.ButtonStyle.green, custom_id="btn_wheel")
    async def btn_wheel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.name == self.author_name:
            self.timeout = 0
            if self.message is None:
                self.message = interaction.message

            if interaction.user.name not in log_data:
                max_place = max((player["place"] for player in log_data.values()), default=0)
                place = max_place + 1
                log_data[interaction.user.name] = {"id": interaction.user.id, "global_name": interaction.user.global_name, "avatar": str(interaction.user.avatar), "avenger": False, "rank": 0, "place": place,"gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
            else:
                if 'global_name' not in log_data[interaction.user.name] or 'avatar' not in log_data[interaction.user.name]:
                    log_data[interaction.user.name]['global_name'] = interaction.user.global_name
                    log_data[interaction.user.name]['avatar'] = str(interaction.user.avatar)

            id = str(log_data[interaction.user.name]['id'])

            if 'Ticket' in log_data[interaction.user.name]['bag']:
                log_data[interaction.user.name]['bag']['Ticket']['quantity'] -= 1
                if log_data[interaction.user.name]['bag']['Ticket']['quantity'] == 0:
                    del log_data[interaction.user.name]['bag']['Ticket']

                alea = random.randint(1, 100)
                if alea <= 1:
                    lot = 1
                else:
                    if alea <= 7:
                        lot = 2
                    else:
                        if alea <= 16:
                            lot = 3
                        else:
                            if alea <= 25:
                                lot = 4
                            else:
                                if alea <= 34:
                                    lot = 5
                                else:
                                    if alea <= 47:
                                        lot = 6
                                    else:
                                        if alea <= 52:
                                            lot = 7
                                        else:
                                            if alea <= 65:
                                                lot = 8
                                            else:
                                                if alea <= 81:
                                                    lot = 9
                                                else:
                                                    if alea <= 90:
                                                        lot = 10
                                                    else:
                                                        if alea <= 93:
                                                            lot = 11
                                                        else:
                                                            lot = 12

                await interaction.response.send_message(wheel['gain_' + str(lot)]['url'])

                price = wheel['gain_' + str(lot)]['price']['title']

                item = wheel['gain_' + str(lot)]['price']['item']

                if item in items:
                    price += ' ' + items[item]['icon']

                    if item in log_data[interaction.user.name]['bag']:
                        log_data[interaction.user.name]['bag'][item]['quantity'] += wheel['gain_' + str(lot)]['price']['quantity']
                    else:
                        log_data[interaction.user.name]['bag'][item] = {'quantity': wheel['gain_' + str(lot)]['price']['quantity'], 'icon': items[item]['icon']}

                    if 'stats' in items[item]:
                        if 'pv' in items[item]['stats']:
                            log_data[interaction.user.name]['stats']['pv'] += items[item]['stats']['pv'] * wheel['gain_' + str(lot)]['price']['quantity']
                        if 'for' in items[item]['stats']:
                            log_data[interaction.user.name]['stats']['for'] += items[item]['stats']['for'] * wheel['gain_' + str(lot)]['price']['quantity']
                        if 'def' in items[item]['stats']:
                            log_data[interaction.user.name]['stats']['def'] += items[item]['stats']['def'] * wheel['gain_' + str(lot)]['price']['quantity']

                else:
                    if item == 'Gold':
                        log_data[interaction.user.name]['gold'] += 50000
                    else:
                        if item == 'Rien':
                            price = 'absolument rien'
                        else:
                            if item == 'Classe':
                                price = 'le déblocage de sa classe ! !'
                                if 'classe' in log_data[interaction.user.name]:
                                    log_data[interaction.user.name]['classe']['quantity'] += 1
                                else:
                                    log_data[interaction.user.name]['classe'] = {'unlock': True, 'quantity': 1}

                await interaction.followup.send("|| " + "<@" + id + ">" + " remporte " + price + " ! ||")
            else:
                await interaction.response.send_message("<@" + id + ">" + ", reviens lorsque tu auras des tickets.")

            for child in self.children:
                child.disabled = True
                await interaction.message.edit(view=self)

            with open("log.json", "w") as file:
                json.dump(log_data, file, indent=4)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

class CraftView(discord.ui.View):
    def __init__(self, timeout, item, quantity, author_name):
        super().__init__(timeout=timeout)
        self.message = None
        self.item = item
        self.quantity = quantity
        self.author_name = author_name

    @discord.ui.button(label="Crafter", style=discord.ButtonStyle.green, custom_id="btn_craft")
    async def btn_craft(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.name == self.author_name:
            self.timeout = 0
            if self.message is None:
                self.message = interaction.message

            if interaction.user.name not in log_data:
                max_place = max((player["place"] for player in log_data.values()), default=0)
                place = max_place + 1
                log_data[interaction.user.name] = {"id": interaction.user.id, "global_name": interaction.user.global_name, "avatar": str(interaction.user.avatar), "avenger": False, "rank": 0, "place": place,"gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
            else:
                if 'global_name' not in log_data[interaction.user.name] or 'avatar' not in log_data[interaction.user.name]:
                    log_data[interaction.user.name]['global_name'] = interaction.user.global_name
                    log_data[interaction.user.name]['avatar'] = str(interaction.user.avatar)

            id = str(log_data[interaction.user.name]['id'])

            for item in craft[self.item]['craft']['item']:
                log_data[interaction.user.name]['bag'][item]['quantity'] -= craft[self.item]['craft']['item'][item] * self.quantity
                if log_data[interaction.user.name]['bag'][item]['quantity'] == 0:
                    del log_data[interaction.user.name]['bag'][item]

                if 'stats' in items[item]:
                    if 'pv' in items[item]['stats']:
                        log_data[interaction.user.name]['stats']['pv'] -= items[item]['stats']['pv'] * craft[self.item]['craft']['item'][item] * self.quantity
                    if 'for' in items[item]['stats']:
                        log_data[interaction.user.name]['stats']['for'] -= items[item]['stats']['for'] * craft[self.item]['craft']['item'][item] * self.quantity
                    if 'def' in items[item]['stats']:
                        log_data[interaction.user.name]['stats']['def'] -= items[item]['stats']['def'] * craft[self.item]['craft']['item'][item] * self.quantity

            if self.item in log_data[interaction.user.name]['bag']:
                log_data[interaction.user.name]['bag'][self.item]['quantity'] += craft[self.item]['quantity'] * self.quantity
            else:
                log_data[interaction.user.name]['bag'][self.item] = {"quantity": craft[self.item]['quantity'] * self.quantity, "icon": craft[self.item]['icon']}

            if 'stats' in craft[self.item]:
                if 'pv' in craft[self.item]['stats']:
                    log_data[interaction.user.name]['stats']['pv'] += craft[self.item]['stats']['pv'] * craft[self.item]['quantity'] * self.quantity
                if 'for' in craft[self.item]['stats']:
                    log_data[interaction.user.name]['stats']['for'] += craft[self.item]['stats']['for'] * craft[self.item]['quantity'] * self.quantity
                if 'def' in craft[self.item]['stats']:
                    log_data[interaction.user.name]['stats']['def'] += craft[self.item]['stats']['def'] * craft[self.item]['quantity'] * self.quantity

            await interaction.response.send_message("<@" + id + ">" + " vient de crafter " + str(craft[self.item]['quantity'] * self.quantity) + ' ' + self.item + ' ' + craft[self.item]['icon'])

            for child in self.children:
                child.disabled = True
                await interaction.message.edit(view=self)

            with open("log.json", "w") as file:
                json.dump(log_data, file, indent=4)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

async def hourly_mob():
    await client.wait_until_ready()
    channel = client.get_channel(SAKURA_CHANNEL_ID)
    if channel is None:
        return

    while not client.is_closed():
        now = datetime.now()
        next_hour = (now + timedelta(minutes=15)).replace(second=0, microsecond=0) #a1b2
        wait_time = (next_hour - now).total_seconds()

        await asyncio.sleep(wait_time)

        try:
            with open("battle.json", "r") as file:
                battle = json.load(file)
        except FileNotFoundError:
            battle = {}
        
        if 'status' in battle:
            status = battle['status']
        else:
            status = 'defaite'
        
        old_lvl = battle['mob']['lvl']
        
        if status == 'victoire':
            mob_lvl = random.randint(old_lvl+1, old_lvl+old_lvl//2+1)
        else:
            mob_lvl = random.randint(old_lvl//2, old_lvl+1)

        if mob_lvl < 1:
            mob_lvl = 1
            
        if mob_lvl >= 749 and mob_lvl < 1124:
            mob_lvl = 749
            
        if mob_lvl >= 1124:
            mob_lvl = 1000
        
        spawn_rate = round(random.random(), 4)

        for mob in mobs:
            if mobs[mob]['min_level'] <= mob_lvl and mobs[mob]['max_level'] > mob_lvl:
                if(spawn_rate <= mobs[mob]['spawn_rate']):
                    lvl = mob_lvl
                    title = mobs[mob]['name'] + ' LVL ' + str(lvl)
                    tabFields = {'PV : ' + str(lvl * mobs[mob]['stats']['pv']) + ' :hearts:   For : ' + str(lvl * mobs[mob]['stats']['for']) + ' :crossed_swords:   Def : ' + str(lvl * mobs[mob]['stats']['def']) + ' :shield:' : '', 'Combattez ce monstre !' : ''}
                    image = mobs[mob]['image']
                    mob_name = mob

                    if(lvl <= 50):
                        color = discord.Color.green()
                    else:
                        if(lvl <= 100):
                            color = discord.Color.yellow()
                        else:
                            if(lvl <= 250):
                                color = discord.Color.orange()
                            else:
                                if(lvl <= 500):
                                    color = discord.Color.red()
                                else:
                                    if(lvl <= 750):
                                        color = discord.Color.purple()
                                    else:
                                        if(lvl <= 1000):
                                            color = discord.Color.white()

                    embed = create_embed(title=title, color=color, image=image, tabFields=tabFields)
                    break;

        view = BattleView(timeout=600) #a1b2
        view.message = await channel.send(embed=embed, view=view)

        battles = {"mob": {"name": mob_name, "lvl": lvl}, "players": {}}

        with open("battle.json", "w") as file:
            json.dump(battles, file, indent=4)

@client.event
async def on_message(message):
    updated = False
    if message.author == client.user:
        return

    if message.content.startswith("!"):
        if message.author.name not in log_data:
            max_place = max((player["place"] for player in log_data.values()), default=0)
            place = max_place + 1
            log_data[message.author.name] = {"id": message.author.id, "global_name": message.author.global_name, "avatar": str(message.author.avatar), "avenger": False, "rank": 0, "place": place, "gold": 0, "!daily": "2024-01-01 11:11:11.111111", "!explore": "2024-01-01 11:11:11.111111", "!train": "2024-01-01 11:11:11.111111", "xp_boosted": "2024-01-01 11:11:11.111111", "bag": {}, "level": {"lvl": 0, "xp": 0}, "stats": {"pv": 1000, "for": 10, "def": 10}, "deaths": 0, "penality": 0, "mobs_kill": {"Slime": 0, "Squelette": 0, "Loup": 0, "Gobelin": 0, "Troll": 0, "Serpent":0, "Dragon": 0, "Demon": 0, "Devoreur": 0}, "title": {}}
            updated = True
        else:
            if 'global_name' not in log_data[message.author.name] or 'avatar' not in log_data[message.author.name]:
                log_data[message.author.name]['global_name'] = message.author.global_name
                log_data[message.author.name]['avatar'] = str(message.author.avatar)
                updated = True

    if message.content.startswith("!info"):
        embed = info_action()
        await message.channel.send(embed=embed)

    if message.content.startswith("!cd"):
        name = message.author.name
        avatar = message.author.avatar
        global_name = message.author.global_name
        command_and_argument = message.content.split(maxsplit=1)
        if len(command_and_argument) == 2:
            command, cible = command_and_argument
            for player in log_data:
                if cible == '<@' + str(log_data[player]['id']) + '>':
                    name = player
                    if 'avatar' in log_data[player]:
                        avatar = log_data[player]['avatar']
                    else:
                        avatar = None

                    if 'global_name' in log_data[player]:
                        global_name = log_data[player]['global_name']
                    else:
                        global_name = None

        embed = cd_action(name, avatar, global_name)
        await message.channel.send(embed=embed)

    if message.content.startswith("!eveil"):
        if await time_command(message, "!eveil", 0.0025):
            embed, view = eveil_action(message.author.name, message.author.avatar, message.author.global_name)
            if view is not None:
                view.message = await message.channel.send(embed=embed, view=view)
            else:
                await message.channel.send(embed=embed)
            updated = True
    
    if message.content.startswith("!boostxp"):
        if await time_command(message, "!boostxp", 0.0025):
            embed, view = boostxp_action(message.author.name, message.author.avatar, message.author.global_name)
            if view is not None:
                view.message = await message.channel.send(embed=embed, view=view)
            else:
                await message.channel.send(embed=embed)
            updated = True

    if message.content.startswith("!sw"):
        if await time_command(message, "!sw", 0.0025):
            embed, view = wheel_action(message.author.name, message.author.avatar, message.author.global_name)
            view.message = await message.channel.send(embed=embed, view=view)
            updated = True

    if message.content.startswith("!craft"):
        if await time_command(message, "!craft", 0.0025):
            command_and_argument = message.content.split(maxsplit=2)

            if len(command_and_argument) == 2 or len(command_and_argument) == 3 :
                if len(command_and_argument) == 2:
                    command, item = command_and_argument
                    quantity = 1
                else:
                    command, item, quantity = command_and_argument
                    if is_integer(quantity) and int(quantity) > 0:
                        quantity = int(quantity)
                    else:
                        quantity = 1
                item = item.title()

                if item not in craft:
                    title = 'Vérifiez l\'appélation de ce que vous voulez crafter.'
                    tabFields = {'Faites !craft pour voir la liste des crafts disponibles.' : ''}
                    color = discord.Color.red()
                    embed = create_embed(title=title, color=color, tabFields=tabFields)
                    await message.channel.send(embed=embed)
                else:
                    embed, view = craft_action(message.author.name, message.author.avatar, message.author.global_name, item, quantity)

                    if view is not None:
                        view.message = await message.channel.send(embed=embed, view=view)
                    else:
                        await message.channel.send(embed=embed)

                    updated = True
            else:
                title = 'Craft'
                tabFields = {'Faites !craft nom_item optionnel_quantité' : '', 'Liste des crafts disponibles : ' : '', 'Gemmes d\'éveil :' : '<:Epique:1222193241022136491> Epique\n<:Legendaire:1222193258403336222> Legendaire\n', 'Runes améliorées :' : ':boom: Brasier • For+40\n:volcano: Volcan • For+600\n:herb: Branche • Def+80\n:deciduous_tree: Arbre • Def+1200\n:sweat_drops: Mer • PV+5000\n:ocean: Ocean • PV+75000'}
                color = discord.Color.lighter_grey()
                embed = create_embed(title=title, color=color, tabFields=tabFields)
                await message.channel.send(embed=embed)

    if message.content.startswith("!materiaux") or message.content.startswith("!matériaux"):
        embed = materiaux_action()
        await message.channel.send(embed=embed)

    if message.content.startswith("!donates"):
        if message.author.id == 701782195844546662:
            command_and_argument = message.content.split(maxsplit=2)
            title = "Commande erronée"
            description = "Voici un exemple : !donates @user 123"
            color = discord.Color.orange()

            if len(command_and_argument) == 3:
                command, cible, montant = command_and_argument
                for player in log_data:
                    if cible == '<@' + str(log_data[player]['id']) + '>' and is_integer(montant) and int(montant) > 0:
                        log_data[player]['gold'] += int(montant)
                        title = "Gold donnés"
                        description = "Vous donnez " + montant + " :coin: à " + cible
                        color = discord.Color.green()
                        updated = True
        else:
            title = "Commande non autorisée"
            description = "Vous n'avait pas les droits requis pour cette commande"
            color = discord.Color.orange()

        embed = create_embed(title=title, description=description, color=color)
        await message.channel.send(embed=embed)

    if message.content.startswith("!removes"):
        if message.author.id == 701782195844546662:
            command_and_argument = message.content.split(maxsplit=2)
            title = "Commande erronée"
            description = "Voici un exemple : !removes @user 123"
            color = discord.Color.orange()

            if len(command_and_argument) == 3:
                command, cible, montant = command_and_argument
                for player in log_data:
                    if cible == '<@' + str(log_data[player]['id']) + '>' and is_integer(montant) and int(montant) > 0:
                        log_data[player]['gold'] -= int(montant)
                        title = "Gold retirés"
                        description = "Vous retirez " + montant + " :coin: à " + cible
                        color = discord.Color.green()
                        updated = True
        else:
            title = "Commande non autorisée"
            description = "Vous n'avait pas les droits requis pour cette commande"
            color = discord.Color.orange()

        embed = create_embed(title=title, description=description, color=color)
        await message.channel.send(embed=embed)

    if message.content.startswith("!send"):
        command_and_argument = message.content.split(maxsplit=2)
        title = "Commande erronée"
        description = "Voici un exemple : !send @user 123"
        color = discord.Color.orange()

        if len(command_and_argument) == 3:
            command, cible, montant = command_and_argument
            for player in log_data:
                if player != message.author.name:
                    if cible == '<@' + str(log_data[player]['id']) + '>' and is_integer(montant) and int(montant) > 0:
                        if log_data[message.author.name]['gold'] >= int(montant):
                            log_data[message.author.name]['gold'] -= int(montant)
                            log_data[player]['gold'] += int(montant)
                            title = "Gold envoyés"
                            description = "Vous envoyez " + montant + " :coin: à " + cible + "\nVotre nouveau solde : " + str(log_data[message.author.name]['gold']) + " :coin:"
                            color = discord.Color.green()
                            updated = True
                        else:
                            title = "Vous n'avez pas assez de :coin:"
                            description = "Votre solde : " + str(log_data[message.author.name]['gold']) + " :coin:"

        embed = create_embed(title=title, description=description, color=color)
        await message.channel.send(embed=embed)

    if message.content.startswith("!fight"):
        command_and_argument = message.content.split(maxsplit=1)
        title = "Commande erronée"
        description = "Voici un exemple : !fight @user"
        color = discord.Color.orange()

        if len(command_and_argument) == 2:
            command, cible = command_and_argument
            for player in log_data:
                if player != message.author.name:
                    if cible == '<@' + str(log_data[player]['id']) + '>':
                        if log_data[player]['place'] < log_data[message.author.name]['place']:
                            sum_author_stats = int(log_data[message.author.name]['stats']['pv']/250 + log_data[message.author.name]['stats']['for']/2 + log_data[message.author.name]['stats']['def']/4)
                            sum_cible_stats = int(log_data[player]['stats']['pv']/250 + log_data[player]['stats']['for']/2 + log_data[player]['stats']['def']/4)
                            if sum_author_stats > sum_cible_stats:
                                place_win = log_data[player]['place']
                                log_data[player]['place'] = log_data[message.author.name]['place']
                                log_data[message.author.name]['place'] = place_win
                                title = "Combat remporté"
                                description = "**" + "\n<@" + str(log_data[message.author.name]['id']) + ">\n" + 'PV : ' + str(log_data[message.author.name]['stats']['pv']) + ' :hearts:   For : ' + str(log_data[message.author.name]['stats']['for']) + ' :crossed_swords:   Def : ' + str(log_data[message.author.name]['stats']['def']) + ' :shield:' + "\nvs\n" + "<@" + str(log_data[player]['id']) + ">\n" + 'PV : ' + str(log_data[player]['stats']['pv']) + ' :hearts:   For : ' + str(log_data[player]['stats']['for']) + ' :crossed_swords:   Def : ' + str(log_data[player]['stats']['def']) + ' :shield:'  + "\n\nVous remportez votre combat contre <@" + str(log_data[player]['id']) + "> et vous récupérez sa place au !top-rank" + "**"
                                color = discord.Color.green()
                                updated = True
                            else:
                                title = "Combat perdu"
                                description = "**" + "\n<@" + str(log_data[message.author.name]['id']) + ">\n" + 'PV : ' + str(log_data[message.author.name]['stats']['pv']) + ' :hearts:   For : ' + str(log_data[message.author.name]['stats']['for']) + ' :crossed_swords:   Def : ' + str(log_data[message.author.name]['stats']['def']) + ' :shield:' + "\nvs\n" + "<@" + str(log_data[player]['id']) + ">\n" + 'PV : ' + str(log_data[player]['stats']['pv']) + ' :hearts:   For : ' + str(log_data[player]['stats']['for']) + ' :crossed_swords:   Def : ' + str(log_data[player]['stats']['def']) + ' :shield:'  + "\n\nVous perdez votre combat contre <@" + str(log_data[player]['id']) + ">\nVotre place au !top-rank est inchangée" + "**"
                                color = discord.Color.red()
                        else:
                            title = "Vous ne pouvez pas défier quelqu'un qui est plus bas au classement !top-rank que vous"
                            description = "Visez plus haut"

        footer = "Classement rank : " + str(log_data[message.author.name]['place']) + '/' + str(len(log_data))
        embed = create_embed(title=title, description=description, color=color, footer=footer)
        await message.channel.send(embed=embed)

    if message.content.startswith("!enchere"):
        image = None
        footer = None
        if message.author.id == 701782195844546662:
            command_and_argument = message.content.split(maxsplit=3)
            title = "Commande erronée"
            description = "Voici un exemple : !enchere numéro-lot quantité mise-à-prix"
            color = discord.Color.orange()

            if len(command_and_argument) == 4:
                try:
                    with open("enchere.json", "r") as file:
                        enchere = json.load(file)
                except FileNotFoundError:
                    enchere = {}

                command, lot, quantity, start_price = command_and_argument
                if lot in enchere:
                    channel = client.get_channel(ENCHERE_SAKURA_CHANNEL_ID)
                    if channel is None:
                        return
                    title = "Lot n°" + str(lot) + ' : ' + str(enchere[lot]['name']) + ' ' + str(quantity) + ' :coin:'
                    description = "Mise à prix : " + str(start_price) + " <:sakura_coin:1217220808083247154>"
                    color = discord.Color.dark_teal()
                    image = enchere[lot]['image']
                    enchere[lot]['is_played'] = True
                    enchere[lot]['quantity'] = int(quantity)
                    enchere[lot]['start_price'] = int(start_price)
                    enchere[lot]['last_price'] = int(start_price)
                    enchere[lot]['last_player'] = ""
                    enchere[lot]['join_player'] = {}

                    embed = create_embed(title=title, description=description, color=color, image=image)
                    view = EnchereView(timeout=3600, lot=lot)
                    view.message = await channel.send(embed=embed, view=view)

                    with open("enchere.json", "w") as file:
                        json.dump(enchere, file, indent=4)
                else:
                    embed = create_embed(title=title, description=description, color=color, image=image)
                    await message.channel.send(embed=embed)
            else:
                embed = create_embed(title=title, description=description, color=color, image=image)
                await message.channel.send(embed=embed)
        else:
            title = "Commande non autorisée"
            description = "Vous n'avait pas les droits requis pour cette commande"
            color = discord.Color.orange()
            embed = create_embed(title=title, description=description, color=color, image=image)
            await message.channel.send(embed=embed)

    if message.content.startswith("!gold"):
        name = message.author.name
        avatar = message.author.avatar
        global_name = message.author.global_name
        command_and_argument = message.content.split(maxsplit=1)
        if len(command_and_argument) == 2:
            command, cible = command_and_argument
            for player in log_data:
                if cible == '<@' + str(log_data[player]['id']) + '>':
                    name = player
                    if 'avatar' in log_data[player]:
                        avatar = log_data[player]['avatar']
                    else:
                        avatar = None

                    if 'global_name' in log_data[player]:
                        global_name = log_data[player]['global_name']
                    else:
                        global_name = None

        embed = me_action(name, avatar, global_name, 'gold')
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

    if message.content.startswith("!compter"):
        if message.author.id == 518397017072992257 or message.author.id == 802116818134892545:
            if await time_command(message, "!compter", 24):
                gain = 1072 * max(log_data[message.author.name]['rank'] * 4, 1)
                gain = gain * 2
                embed = compter_action(message.author.name, message.author.avatar, message.author.global_name, gain)
                await message.channel.send(embed=embed)
            updated = True
        else:
            title = "Commande non autorisée"
            description = "Vous n'avait pas les droits requis pour cette commande"
            color = discord.Color.orange()
            embed = create_embed(title=title, description=description, color=color)
            await message.channel.send(embed=embed)

    if message.content.startswith("!train"):
        if await time_command(message, "!train", 3):
            embed = train_action(message.author.name, message.author.avatar, message.author.global_name)
            await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!profil"):
        name = message.author.name
        avatar = message.author.avatar
        global_name = message.author.global_name
        command_and_argument = message.content.split(maxsplit=1)
        if len(command_and_argument) == 2:
            command, cible = command_and_argument
            for player in log_data:
                if cible == '<@' + str(log_data[player]['id']) + '>':
                    name = player
                    if 'avatar' in log_data[player]:
                        avatar = log_data[player]['avatar']
                    else:
                        avatar = None

                    if 'global_name' in log_data[player]:
                        global_name = log_data[player]['global_name']
                    else:
                        global_name = None

        embed = me_action(name, avatar, global_name, 'profil')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!top-rank"):
        embed = top_action(message.author.name, 'place')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!top-eveil"):
        embed = top_action(message.author.name, 'rank')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!top-gold"):
        embed = top_action(message.author.name, 'gold')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!top-level"):
        embed = top_action(message.author.name, 'level')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!top-pv"):
        embed = top_action(message.author.name, 'pv')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!top-for"):
        embed = top_action(message.author.name, 'for')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!top-def"):
        embed = top_action(message.author.name, 'def')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!bag"):
        name = message.author.name
        avatar = message.author.avatar
        global_name = message.author.global_name
        command_and_argument = message.content.split(maxsplit=1)
        if len(command_and_argument) == 2:
            command, cible = command_and_argument
            for player in log_data:
                if cible == '<@' + str(log_data[player]['id']) + '>':
                    name = player
                    if 'avatar' in log_data[player]:
                        avatar = log_data[player]['avatar']
                    else:
                        avatar = None

                    if 'global_name' in log_data[player]:
                        global_name = log_data[player]['global_name']
                    else:
                        global_name = None

        embed = me_action(name, avatar, global_name, 'bag')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!purchase"):
        command_and_argument = message.content.split(maxsplit=2)

        if len(command_and_argument) == 2 or len(command_and_argument) == 3 :
            if len(command_and_argument) == 2:
                command, item = command_and_argument
                quantity = 1
            else:
                command, item, quantity = command_and_argument
                if is_integer(quantity) and int(quantity) > 0:
                    quantity = int(quantity)
                else:
                    quantity = 1
            item = item.title()
            embed = purchase_action(message.author.name, message.author.avatar, message.author.global_name, item, quantity)
            updated = True
        else:
            title = 'Achat'
            tabFields = {'Faites !purchase nom_item optionnel_quantité' : ''}
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

    if message.content.startswith("!classe"):
        command_and_argument = message.content.split()
        
        if len(command_and_argument) == 1:
            embed = classe_action("simple")
        else:
            classe = " ".join(command_and_argument[1:])
            classe = normalize_text(classe)
            embed = classe_info_action(classe) 

        await message.channel.send(embed=embed)

    if message.content.startswith("!select"):
        if "classe" in log_data[message.author.name] and "name" not in log_data[message.author.name]["classe"]:
            command_and_argument = message.content.split()
            
            if len(command_and_argument) == 1:
                embed = create_embed(title="Choix de classe", color=discord.Color.red(), description="Pour choisir votre classe faites **!select nom de la classe**", footer="Pour voir les classes disponibles faites !classe")
            else:
                classe = " ".join(command_and_argument[1:])
                classe = normalize_text(classe)

                if classe in classes:
                    log_data[message.author.name]["classe"]["name"] = classes[classe]["name"]
                    log_data[message.author.name]["classe"]["icon"] = classes[classe]["icon"]
                    
                    if classe == "assassin":
                        log_data[message.author.name]["classe"]["progression 1"] = 0
                        log_data[message.author.name]["classe"]["progression 2"] = "Pas encore crafter" #a1b2 à faire
                    
                    if classe == "debuffer":
                        log_data[message.author.name]["classe"]["progression 1"] = 0
                        log_data[message.author.name]["classe"]["progression 2"] = "Pas encore crafter" #a1b2 à faire
                    
                    updated = True
                    
                    title = "Félicitation !"
                    description = f"<@{message.author.id}> vous êtes désormais un {classes[classe]["icon"]} {classes[classe]["name"]} !\n Vous pouvez désormais faire **/{classe}** pour obtenir des informations cachées sur votre classe !"
                    color = discord.Color.green()
                    embed = create_embed(title=title, description=description, color=color)
                else:
                    title = 'Erreur dans la commande'
                    description = "Vérifiez l'orthographe de la classe (pas de classe exaltée ici), majuscule ou accent par exemple"
                    color = discord.Color.red()
                    embed = create_embed(title=title, color=color, description=description)
        else:
            title = "Commande non autorisée"
            description = "Vous n'avait pas les droits requis pour cette commande"
            color = discord.Color.orange()
            footer = "Débloquez cette commande avec la Sakura Wheel (natsu)"
            embed = create_embed(title=title, description=description, color=color, footer=footer)

        
        await message.channel.send(embed=embed)

    if updated:
        with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)

@tree.command(name="cd", description="Voir les cooldown.")
async def cd_command(interaction: discord.Interaction, cible: str = None):
    name = interaction.user.name
    avatar = interaction.user.avatar
    global_name = interaction.user.global_name

    if cible:
        for player in log_data:
            if cible == f'<@{log_data[player]["id"]}>':
                name = player
                avatar = log_data[player].get("avatar", None)
                global_name = log_data[player].get("global_name", None)
                break
        else:
            await interaction.response.send_message("Cible non-trouvé !", ephemeral=True)
            return

    embed = cd_action(name, avatar, global_name)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="market", description="Voir le marché.")
async def market_command(interaction: discord.Interaction):
    embed = market_action()
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="assassin", description="Affiche des informations cachées sur la classe Assassin.")
async def assassin_command(interaction: discord.Interaction):
    if "classe" in log_data[interaction.user.name] and "name" in log_data[interaction.user.name]["classe"] and log_data[interaction.user.name]["classe"]["name"] == "Assassin":
        title = "Informations cachées sur la classe :dagger: Assassin"
        description = "**Pour exalter votre classe :dagger: Assassin en la classe :cyclone: Faucheur d'âmes, réussissez ces quêtes :**\n\n**Quête 1 • **" + classes["assassin"]["details"]["Quete 1"]["quete"] + "\n**Récompense • **" + classes["assassin"]["details"]["Quete 1"]["recompense"] + "\n**Progression • **" + "[" + str(log_data[interaction.user.name]["classe"]["progression 1"]) + "/100]" + "\n\n**Quête 2 • **" + classes["assassin"]["details"]["Quete 2"]["quete"] + "\n **Récompense • **" + classes["assassin"]["details"]["Quete 2"]["recompense"] + "\n**Progression • **" + log_data[interaction.user.name]["classe"]["progression 2"]
        embed = create_embed(title=title, description=description, color=discord.Color.blue())
    else:
        title = "Commande non autorisée"
        description = "Vous n'avait pas les droits requis pour cette commande"
        color = discord.Color.orange()

        embed = create_embed(title=title, description=description, color=color)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
@tree.command(name="debuffer", description="Affiche des informations cachées sur la classe Débuffer.")
async def debuffer_command(interaction: discord.Interaction):
    if "classe" in log_data[interaction.user.name] and "name" in log_data[interaction.user.name]["classe"] and log_data[interaction.user.name]["classe"]["name"] == "Débuffer":
        title = "Informations cachées sur la classe :chains: Débuffer"
        description = "**Pour exalter votre classe :chains: Débuffer en la classe :japanese_ogre: Démon maudit, réussissez ces quêtes :**\n\n**Quête 1 • **" + classes["debuffer"]["details"]["Quete 1"]["quete"] + "\n**Récompense • **" + classes["debuffer"]["details"]["Quete 1"]["recompense"] + "\n**Progression • **" + "[" + str(log_data[interaction.user.name]["classe"]["progression 1"]) + "/200]" + "\n\n**Quête 2 • **" + classes["debuffer"]["details"]["Quete 2"]["quete"] + "\n **Récompense • **" + classes["debuffer"]["details"]["Quete 2"]["recompense"] + "\n**Progression • **" + log_data[interaction.user.name]["classe"]["progression 2"]
        embed = create_embed(title=title, description=description, color=discord.Color.blue())
    else:
        title = "Commande non autorisée"
        description = "Vous n'avait pas les droits requis pour cette commande"
        color = discord.Color.orange()

        embed = create_embed(title=title, description=description, color=color)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
@tree.command(name="info", description="Information sur les commandes.")
async def info_command(interaction: discord.Interaction):
    embed = info_action()
    await interaction.response.send_message(embed=embed, ephemeral=True)
    
@tree.command(name="brocante", description="Voir la brocante.")
async def brocante_command(interaction: discord.Interaction):
    title = "Brocante"
    description = "**Vente • Vendeur • Quantité • Item • Prix unitaire\n**"
    for sale in brocante:
        description += f" **{sale}** • <@{brocante[sale]["seller_id"]}> • {brocante[sale]["quantity"]} • {items[brocante[sale]["item"]]["icon"]} {brocante[sale]["item"]} • {brocante[sale]["price"]} :coin:\n"
    
    if description == "**Vente • Vendeur • Quantité • Item • Prix unitaire\n**":
        description = "**Il n'y a pas d'item en vente.**"
    
    footer = "Faites /buy vente quantité, pour acheter des items de la brocante."
    
    embed = create_embed(title=title, color=discord.Color.blue(), description=description, footer=footer)

    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="sell", description="Vente d'items entre joueurs.")
@app_commands.describe(item="Choisissez un item à mettre en vente", prix="Fixez un prix unitaire", quantité="Choisissez une quantité à mettre en vente")
async def sell_command(interaction: discord.Interaction, item: str, prix: int, quantité: int = 1):
    
    if item == None:
        await interaction.response.send_message("Vous n'avez pas d'items vendables.", ephemeral=True)
        return
    
    my_items = []

    for bag_item in log_data[interaction.user.name]["bag"]:
        if bag_item != "Casquette" and bag_item != "Tshirt" and bag_item != "Jean" and bag_item != "Baskets" and bag_item != "Dague" and bag_item != "PointXP" :
            my_items.append(bag_item)
    
    if item not in my_items:
        await interaction.response.send_message("Vous ne pouvez pas vendre cet item.", ephemeral=True)
        return
    
    if prix < 0 :
        await interaction.response.send_message("Le prix ne peut être négatif.", ephemeral=True)
        return
    
    if quantité <= 0 :
        await interaction.response.send_message("La quantité doit être d'au moins 1.", ephemeral=True)
        return
    
    if quantité > log_data[interaction.user.name]["bag"][item]["quantity"]:
        await interaction.response.send_message("Vous n'avez pas autant d'exemplaires.", ephemeral=True)
        return
    else:
        log_data[interaction.user.name]["bag"][item]["quantity"] -= quantité
        
        if log_data[interaction.user.name]["bag"][item]["quantity"] == 0:
            del log_data[interaction.user.name]['bag'][item]
        
        if "stats" in items[item]:
            if "pv" in items[item]["stats"]:
                log_data[interaction.user.name]["stats"]["pv"] -= items[item]["stats"]["pv"] * quantité
                
            if "for" in items[item]["stats"]:
                log_data[interaction.user.name]["stats"]["for"] -= items[item]["stats"]["for"] * quantité
                
            if "def" in items[item]["stats"]:
                log_data[interaction.user.name]["stats"]["def"] -= items[item]["stats"]["def"] * quantité
        
        existing = None
        
        for sale in brocante:
            if brocante[sale]["seller_id"] == interaction.user.id and brocante[sale]["item"] == item and brocante[sale]["price"] == prix:
                existing = sale 
        
        if existing:
            brocante[existing]["quantity"] += quantité
        else:
            brocante["Vente " + str(len(brocante) + 1)] = {"seller_id": interaction.user.id, "seller_name": interaction.user.name, "item": item, "price": prix, "quantity": quantité}
    
    with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)
            
    with open("brocante.json", "w") as file:
            json.dump(brocante, file, indent=4)

    title = "Mise en vente"
    description = f"**Item • **{items[item]["icon"]} {item}\n **Quantité • **{quantité}\n **Prix unitaire • **{prix} :coin:"
    footer = "Faites /brocante pour voir les items en vente."
    
    embed = create_embed(title=title, color=discord.Color.blue(), author_name=interaction.user.global_name, author_icon=interaction.user.avatar, description=description, footer=footer)

    await interaction.response.send_message(embed=embed)

@sell_command.autocomplete("item")
async def item_autocomplete(interaction: discord.Interaction, current: str):
    my_items = []

    for item in log_data[interaction.user.name]["bag"]:
        if item != "Casquette" and item != "Tshirt" and item != "Jean" and item != "Baskets" and item != "Dague" and item != "PointXP" :
            my_items.append(item)
    
    suggestions = [
        app_commands.Choice(name=item, value=item) 
        for item in my_items if current.lower() in item.lower()
    ][:25]
    
    return suggestions

@tree.command(name="buy", description="Achat d'items entre joueurs.")
@app_commands.describe(vente="Choisissez une vente", quantité="Choisissez une quantité d'items à acheter")
async def buy_command(interaction: discord.Interaction, vente: str, quantité: int = 1):
    
    if vente == None:
        await interaction.response.send_message("Il n'y a pas d'item en vente.", ephemeral=True)
        return
    
    if vente not in brocante:
        await interaction.response.send_message("Cette vente n'est pas dans la brocante.", ephemeral=True)
        return
    
    if quantité <= 0 :
        await interaction.response.send_message("La quantité doit être d'au moins 1.", ephemeral=True)
        return
    
    if quantité > brocante[vente]["quantity"]:
        await interaction.response.send_message("Il n'a pas autant d'exemplaires en vente.", ephemeral=True)
        return
    else:
        item = brocante[vente]["item"]
        price = brocante[vente]["price"] * quantité
        seller_name = brocante[vente]["seller_name"]
        seller_id = brocante[vente]["seller_id"]
        
        if log_data[interaction.user.name]["gold"] >= price:
            log_data[interaction.user.name]["gold"] -= price
            log_data[seller_name]["gold"] += price
            brocante[vente]["quantity"] -= quantité
            
            if brocante[vente]["quantity"] == 0:
                keys_list = list(brocante.keys())
                index_vente = keys_list.index(vente)
                
                for i in range(index_vente, len(keys_list) - 1):
                    brocante[keys_list[i]] = brocante[keys_list[i + 1]]

                del brocante[keys_list[-1]] 
            
            if item in log_data[interaction.user.name]["bag"]:
                log_data[interaction.user.name]["bag"][item]["quantity"] += quantité
            else:
                log_data[interaction.user.name]["bag"][item] = {'quantity': quantité, 'icon': items[item]['icon']}
        
        
            if "stats" in items[item]:
                if "pv" in items[item]["stats"]:
                    log_data[interaction.user.name]["stats"]["pv"] += items[item]["stats"]["pv"] * quantité
                    
                if "for" in items[item]["stats"]:
                    log_data[interaction.user.name]["stats"]["for"] += items[item]["stats"]["for"] * quantité
                    
                if "def" in items[item]["stats"]:
                    log_data[interaction.user.name]["stats"]["def"] += items[item]["stats"]["def"] * quantité
        
        else:
            await interaction.response.send_message("Vous n'avez pas assez de gold.", ephemeral=True)
            return

    with open("log.json", "w") as file:
            json.dump(log_data, file, indent=4)
            
    with open("brocante.json", "w") as file:
            json.dump(brocante, file, indent=4)

    title = "Achat"
    description = f"<@{log_data[interaction.user.name]["id"]}> vient d'acheter {quantité} {items[item]['icon']} {item} à <@{seller_id}> pour {price} :coin:"
    footer = "Faites /brocante pour voir les items en vente."
    
    embed = create_embed(title=title, color=discord.Color.green(), author_name=interaction.user.global_name, author_icon=interaction.user.avatar, description=description, footer=footer)

    await interaction.response.send_message(embed=embed)

@buy_command.autocomplete("vente")
async def vente_autocomplete(interaction: discord.Interaction, current: str):
    ventes = []
    
    for sale in brocante:
        ventes.append(sale)
    
    suggestions = [
        app_commands.Choice(name=vente, value=vente) 
        for vente in ventes if current.lower() in vente.lower()
    ][:25]
    
    return suggestions

async def time_command(message, command, cooldown):
    author_name = message.author.name
    check, waiting_time = check_time(author_name, command, cooldown)

    if check:
        if command == '!daily':
            log_data[author_name]['last_daily'] = log_data[author_name][command]

        log_data[author_name][command] = str(datetime.now())

        return True
    else:
        await message.channel.send("Vous devez attendre encore " + waiting_time)
        return False

def info_action():
    tabFields = {
        '!gold :' : 'Pour voir combien de gold vous avez.',
        '!profil :' : 'Pour voir vos stats.',
        '!daily :' : 'Pour récupérer des golds toutes les 24h, ne perdez pas votre série.',
        '!compter :' : 'Pour les tenants du record dans #compter.',
        '!explore :' : 'Explorez les profondeurs pour des golds toutes les heures.',
        '!train :' : 'Pour un entraînement digne des plus grand, gagnez de l\'xp toutes les 3h.',
        '!cd ou /cd :' : 'Pour voir vos cooldown.',
        '!market ou /market :' : 'Pour acheter de quoi devenir plus fort.',
        '!craft :' : 'Pour crafter des items.',
        '!materiaux :' : 'Pour voir les stats des matériaux.',
        '!top-[rank/gold/eveil/level/pv/for/def] :' : 'Pour voir un classement en particulier.',
        '!fight :' : 'Pour se disputer le haut du classement !top-rank.',
        '!bag :' : 'Pour voir ce que vous avez dans votre sac.',
        '!purchase :' : 'Pour acheter un item au market.',
        '!notif :' : "Pour rejoindre la liste des chads notifiés lors d'une demande d'aide",
        '!send :' : "Pour envoyer de l'argent",
        '!eveil :' : 'Brisez vos limites !',
        '!sw :' : 'Tenter votre chance à la Sakura Wheel !',
        '!classe :' : '[En travaux] :construction:',
        '!boostxp :' : 'Utilisez vos Boost XP !',
        '/sell item prix quantité :' : 'Mettre en vente vos items à la brocante. :new:',
        '/buy vente quantité :' : 'Achetez des items à la brocante. :new:',
        '/brocante :' : 'Pour voir la brocante. :new:',
        '!select nom de la classe :' : 'Pour choisir votre classe. :new:'
    }
    color = discord.Color.blue()
    title = 'Informations'
    return create_embed(title=title, color=color, tabFields=tabFields)

def cd_action(author_name, author_icon, global_name):
    daily_check, daily_waiting_time = check_time(author_name, '!daily', 24)
    train_check, train_waiting_time = check_time(author_name, '!train', 3)
    explore_check, explore_waiting_time = check_time(author_name, '!explore', 1)

    if daily_check:
        daily_waiting_time = ":white_check_mark: Vous pouvez faire la commande dès à présent !"
    else:
        daily_waiting_time = ":x: " + daily_waiting_time

    if explore_check:
        explore_waiting_time = ":white_check_mark: Vous pouvez faire la commande dès à présent !"
    else:
        explore_waiting_time = ":x: " + explore_waiting_time

    if train_check:
        train_waiting_time = ":white_check_mark: Vous pouvez faire la commande dès à présent !"
    else:
        train_waiting_time = ":x: " + train_waiting_time

    if '!compter' in log_data[author_name]:
        compter_check,compter_waiting_time = check_time(author_name, '!compter', 24)

        if compter_check:
            compter_waiting_time = ":white_check_mark: Vous pouvez faire la commande dès à présent !"
        else:
            compter_waiting_time = ":x: " + compter_waiting_time

        tabFields = {
            '!daily :' : daily_waiting_time,
            '!compter :' : compter_waiting_time,
            '!train :' : train_waiting_time,
            '!explore :' : explore_waiting_time
        }
    else:
        tabFields = {
            '!daily :' : daily_waiting_time,
            '!train :' : train_waiting_time,
            '!explore :' : explore_waiting_time
        }

    color = discord.Color.blue()
    title = 'Cooldown'
    embed = create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, tabFields=tabFields)
    return embed

def eveil_action(author_name, author_icon, global_name):
    view = None
    player_rank = log_data[author_name]['rank']
    rank = ['Pas d\'éveil', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s: :regional_indicator_s:', ':regional_indicator_z:', ':regional_indicator_z: :regional_indicator_z:', ':regional_indicator_z: :regional_indicator_z: :regional_indicator_z:']
    current_rank = rank[player_rank]
    next_rank = rank[player_rank + 1]

    res, owned, nbr_gem, gem_type = gems_required(author_name, player_rank + 1)

    tabFields = {
        'Rang d\'éveil' : current_rank + ' :arrow_right: ' + next_rank,
        'Gemmes d\'éveil : ' : res,
    }

    if owned:
        title = 'Éveil'
        color = discord.Color.blue()
        view = EveilView(timeout=6, nbr_gem=nbr_gem, gem_type=gem_type, author_name=author_name)
    else:
        title = 'Gemmes d\'éveil manquantes'
        color = discord.Color.red()

    embed = create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, tabFields=tabFields)

    return embed, view

def boostxp_action(author_name, author_icon, global_name):
    view = None

    if "BoostXP" in log_data[author_name]["bag"] and log_data[author_name]["bag"]["BoostXP"]["quantity"] > 0:
        title = "Vous avez " + str(log_data[author_name]["bag"]["BoostXP"]["quantity"]) + " BoostXP :diamond_shape_with_a_dot_inside:"
        description = "Voulez-vous en utiliser 1 ? Ceci vous confèrera un bonus d'xp de +100% pendant 24h."
        color = discord.Color.blue()
        view = BoostXPView(timeout=6, author_name=author_name)
    else:
        title = "Vous n'avez pas de BoostXP"
        description = "Vous pouvez en acheter dans le !market ou bien en gagner avec la Sakura Wheel !sw"
        color = discord.Color.red()

    embed = create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, description=description)

    return embed, view

def wheel_action(author_name, author_icon, global_name):
    title = 'Sakura Wheel'
    description = 'Faites tourner la roue contre un ticket :tickets: !'
    color = discord.Color.blue()
    view = WheelView(timeout=6, author_name=author_name)

    embed = create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, description=description)

    return embed, view

def craft_action(author_name, author_icon, global_name, item, quantity):
    view = None
    description = 'Modèle du craft unitaire :'
    image = craft[item]['craft']['image']

    owned = item_required(author_name, item, quantity)

    if owned:
        title = 'Craft de ' + str(quantity) + ' ' + item + ' ' + craft[item]['icon']
        color = discord.Color.blue()
        view = CraftView(timeout=6, item=item, quantity=quantity, author_name=author_name)
    else:
        title = 'Vous n\'avez pas de quoi crafter ' + str(quantity) + ' ' + item + ' ' + craft[item]['icon']
        color = discord.Color.red()

    embed = create_embed(title=title, color=color, image=image, author_name=global_name, author_icon=author_icon, description=description)

    return embed, view

def item_required(author_name, item, quantity):
    for item_required in craft[item]['craft']['item']:
        if item_required not in log_data[author_name]['bag'] or craft[item]['craft']['item'][item_required] * quantity > log_data[author_name]['bag'][item_required]['quantity']:
            return False

    return True

def gems_required(author_name, rank):
    gem_rank = (rank-1) // 3
    nbr_gem = rank % 3

    if nbr_gem == 0:
        nbr_gem = 3

    if gem_rank == 0:
        gem = '<:Rare:1222193217957662760> Rare'
        gem_type = 'Rare'
    else:
        if gem_rank == 1:
            gem = '<:Epique:1222193241022136491> Epique'
            gem_type = 'Epique'
        else:
            if gem_rank == 2:
                gem = '<:Legendaire:1222193258403336222> Legendaire'
                gem_type = 'Legendaire'
            else:
                if gem_rank == 3:
                    gem = ':octagonal_sign: Ultime'
                    gem_type = 'Ultime'
                 

    if gem_type in log_data[author_name]['bag']:
        quantity = log_data[author_name]['bag'][gem_type]['quantity']
    else:
        quantity = 0

    nbr_gem = nbr_gem * nbr_gem
    res = str(quantity) + '/' + str(nbr_gem) + ' • ' + gem
    if quantity >= nbr_gem:
        owned = True
    else:
        owned = False

    return res, owned, nbr_gem, gem_type

def materiaux_action():
    tabFields = {
        ':regional_indicator_s: Étherium :' : 'PV : 35 000 :hearts:\nFor : 50 :crossed_swords:\nDef : 350 :shield:\nPrix : 360 000 :coin:',
        ':regional_indicator_a: Adamantium :' : 'PV : 12 000 :hearts:\nFor : 30 :crossed_swords:\nDef : 120 :shield:\nPrix : 120 000 :coin:',
        ':regional_indicator_b: Orichalque :' : 'PV : 3 500 :hearts:\nFor : 20 :crossed_swords:\nDef : 35 :shield:\nPrix : 40 000 :coin:',
        ':regional_indicator_c: Mithril :' : 'PV : 1 000 :hearts:\nFor : 4 :crossed_swords:\nDef : 16 :shield:\nPrix : 13 000 :coin:',
        ':regional_indicator_d: Argent :' : 'PV : 300 :hearts:\nFor : 2 :crossed_swords:\nDef : 4 :shield:\nPrix : 4 500 :coin:',
        ':regional_indicator_e: Fer :' : 'PV : 200 :hearts:\nFor : 1 :crossed_swords:\nDef : 3 :shield:\nPrix : 1 500 :coin:',
        ':regional_indicator_f: Cuir :' : 'PV : 100 :hearts:\nDef : 2 :shield:\nPrix : 500 :coin:',
    }
    color = discord.Color.blue()
    title = 'Matériaux'
    return create_embed(title=title, color=color, tabFields=tabFields)

def market_action():
    base_items = ':billed_cap: Casquette • Def+1 • 500 :coin:\n:shirt: Tshirt • Def+2 • 1000 :coin:\n:jeans: Jean • Def+2 • 1000 :coin:\n:athletic_shoe: Baskets • Def+1 • 500 :coin:\n:dagger: Dague • For+3 • 1500 :coin:'
    material_items = ':regional_indicator_s: Étherium • 360000 :coin:\n:regional_indicator_a: Adamantium • 120000 :coin:\n:regional_indicator_b: Orichalque • 40000 :coin:\n:regional_indicator_c: Mithril • 13000 :coin:\n:regional_indicator_d: Argent • 4500 :coin:\n:regional_indicator_e: Fer • 1500 :coin:\n:regional_indicator_f: Cuir • 500 :coin:'
    rune_items = ':fire: Feu • For+2 • 2000 :coin:\n:seedling: Plante • Def+4 • 2000 :coin:\n:droplet: Eau • PV+250 • 2000 :coin:'
    rank_items = '<:Legendaire:1222193258403336222> Legendaire • 500000 :coin:\n<:Epique:1222193241022136491> Epique • 50000 :coin:\n<:Rare:1222193217957662760> Rare • 5000 :coin:'
    other_items = ':tickets: Ticket • 60000 :coin:\n:diamond_shape_with_a_dot_inside: BoostXP • 50000 :coin:'

    tabFields = {
        'Pour acheter : ' : '!purchase nom_item',
        'Équipements de base : ' : base_items,
        'Matériaux : ' : material_items,
        'Runes : ' : rune_items,
        'Gemmes d\'éveil :' : rank_items,
        'Autres :' : other_items
    }
    color = discord.Color.lighter_grey()
    title = 'Boutique'
    return create_embed(title=title, color=color, tabFields=tabFields)

def classe_action(type):
    
    listes_classes = ""
    
    for classe in classes:
        if type == "simple":
            listes_classes = listes_classes + classes[classe]["icon"] + " " + classes[classe]["name"] + "\n"
        else:
            listes_classes = listes_classes + classes[classe]["evolve"]["icon"] + " " + classes[classe]["evolve"]["name"] + "\n"
            
    if type == "simple":
        title = "Découvrez quelle classe vous convient le mieux !"
        tabFields = {'Classes :' : "**" + listes_classes + "**"}
        footer = "Plus d'info : !classe nom_classe ou !classe exaltee"
    else:
        title = "Découvrez quelle classe exaltee vous convient le mieux !"
        tabFields = {'Classes exaltées :' : "**" + listes_classes + "**"}
        footer = "Plus d'info : !classe nom_classe ou !classe"
    
    color = discord.Color.lighter_grey()
    
    return create_embed(title=title, color=color, tabFields=tabFields, footer=footer)

def classe_info_action(info_classe):
    if info_classe == "exaltee":
        return classe_action("exaltee")
    
    for classe in classes:
        color = discord.Color.lighter_grey()
        if normalize_text(classes[classe]["name"]) == info_classe:
            description = classes[classe]["description"]
            title = classes[classe]["icon"] + " " + classes[classe]["name"]
            return create_embed(title=title, color=color, description=description)
        else:
            if normalize_text(classes[classe]["evolve"]["name"]) == info_classe:
                description = classes[classe]["evolve"]["description"]
                title = classes[classe]["evolve"]["icon"] + " " + classes[classe]["evolve"]["name"]
                return create_embed(title=title, color=color, description=description)
      
    description = "Vérifiez l'orthographe de la classe, majuscule ou accent par exemple"
    color = discord.Color.red()
    title = 'Erreur dans la commande'
               
    return create_embed(title=title, color=color, description=description)
    
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

    if type == 'profil':
        res = log_data[author_name]['rank']
    else:
        res = log_data[author_name][type]

    if type == 'gold':
        tabFields = {'Gold :' : str(res) + ' :coin:'}
        color = discord.Color.gold()
    else:
        rank = ['Pas d\'éveil', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s: :regional_indicator_s:']
        if type == 'profil':
            level_xp = [500, 600, 720, 864, 1036, 1243, 1492, 1791, 2149, 2578, 3093, 3711, 4453, 5343, 6411, 7693, 9231, 11077, 13293, 15951, 19141, 22969, 27563, 33075, 39690, 47628, 57153, 68584, 82300, 98760, 118512, 142214, 170657, 204788, 245746, 294895, 353873, 424647, 509576, 611491, 733790, 880548, 1056657, 1267989, 1521587, 1825904, 2191085, 2629302, 3155163, 3786195, 4543434, 5452120, 6542544, 7851052, 9421262, 11305514, 13566617, 16279940, 19535928, 23443113, 28131736, 33758083, 40509700, 48611640, 58333968, 70000762, 84000914, 100801096, 120961315, 145153578, 174184293, 209021151, 250825381, 301090457, 361308548, 433570258, 520284309, 624341171, 749209405, 899051286, 1078861543, 1294633852, 1553560622, 1864272746, 2237127295, 2684552754, 3221463305, 3865755966, 4638907159, 5566688591, 6680026309, 8016031570, 9619237884, 11543158461, 13851790153, 16622148183, 19946577820, 23935893384, 28723072061, 34467686474, 41361223769, 49633468522, 59560162226, 71472194671, 85766633605, 102919960326, 123503952391, 148204742869, 177845691442, 213414829731]
            
            classe_name = "Aucune"
            
            if "classe" in log_data[author_name] and "name" in log_data[author_name]['classe'] and "icon" in log_data[author_name]['classe']:
                classe_name = log_data[author_name]['classe']["icon"] + " " + log_data[author_name]['classe']["name"]

            tabFields = {"Classe": classe_name, "Level :" : str(log_data[author_name]['level']['lvl']) + " [" + str(log_data[author_name]['level']['xp']) + "/" + str(level_xp[log_data[author_name]['level']['lvl']]) + "] (" + str(f"{log_data[author_name]['level']['xp'] * 100 / level_xp[log_data[author_name]['level']['lvl']]:.2f}") + " %)", 'Rang :' : rank[res], 'Stats :' : '', 'PV : ' + str(log_data[author_name]['stats']['pv']) + ' :hearts:': '', 'For : ' + str(log_data[author_name]['stats']['for']) + ' :crossed_swords:' : '', 'Def : ' + str(log_data[author_name]['stats']['def']) + ' :shield:': ''}
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
        if type == 'profil':
            footer = 'Classement level : ' + ranking('level', author_name)
        else:
            footer = 'Classement ' + type + ' : ' + ranking(type, author_name)
    return create_embed(color=color, author_name=global_name, author_icon=author_icon, footer=footer, tabFields=tabFields)

def top_action(author_name, type):
    if type == 'pv' or type == 'for' or type == 'def' or type == 'place':
        filtered_authors = [author for author in log_data.keys() if 'stats' in log_data[author]]
    else :
        filtered_authors = [author for author in log_data.keys() if type in log_data[author]]
    filtered_authors_id = []
    for author in filtered_authors:
        filtered_authors_id.append("<@" + str(log_data[author]['id']) + ">")

    if type == 'level':
        sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x][type]['lvl'], reverse=True)
    else:
        if type == 'pv' or type == 'for' or type == 'def':
           sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x]['stats'][type], reverse=True)
        else:
            if type == 'place':
                sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x][type], reverse=False)
            else:
                sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x][type], reverse=True)

    if(type == 'rank'):
        rank = ['Pas d\'éveil', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s: :regional_indicator_s:']

    tabFields = {}
    for i in range(len(sorted_authors)):
        if i > 8:
            break
        if(type == 'gold'):
            if i == 0:
                tabFields[''] = '**' + str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  ' + str(log_data[sorted_authors[i]][type]) + ' :coin:\n'
            else:
                tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  ' + str(log_data[sorted_authors[i]][type]) + ' :coin:\n'
        else:
            if(type == 'rank'):
                if i == 0:
                    tabFields[''] = '**' + str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  ' + rank[log_data[sorted_authors[i]][type]] + '\n'
                else:
                    tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  ' + rank[log_data[sorted_authors[i]][type]] + '\n'
            else:
                if(type == 'level'):
                    if i == 0:
                        tabFields[''] = '**' + str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  Level ' + str(log_data[sorted_authors[i]][type]['lvl']) + '\n'
                    else:
                        tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  Level ' + str(log_data[sorted_authors[i]][type]['lvl']) + '\n'
                else:
                    if(type == 'pv'):
                        if i == 0:
                            tabFields[''] = '**' + str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  PV : ' + str(log_data[sorted_authors[i]]['stats'][type]) + ' :hearts:\n'
                        else:
                            tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  PV : ' + str(log_data[sorted_authors[i]]['stats'][type]) + ' :hearts:\n'
                    else:
                        if(type == 'for'):
                            if i == 0:
                                tabFields[''] = '**' + str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  For : ' + str(log_data[sorted_authors[i]]['stats'][type]) + ' :crossed_swords:\n'
                            else:
                                tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  For : ' + str(log_data[sorted_authors[i]]['stats'][type]) + ' :crossed_swords:\n'
                        else:
                            if(type == 'def'):
                                if i == 0:
                                    tabFields[''] = '**' + str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  Def : ' + str(log_data[sorted_authors[i]]['stats'][type]) + ' :shield:\n'
                                else:
                                    tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  Def : ' + str(log_data[sorted_authors[i]]['stats'][type]) + ' :shield:\n'
                            else:
                                if(type == 'place'):
                                    if i == 0:
                                        tabFields[''] = '**' + str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  :crown:\n'
                                    else:
                                        if i == 1:
                                            tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  :second_place:\n'
                                        else:
                                            if i == 2:
                                                tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>  •  :third_place:\n'
                                            else:
                                                tabFields[''] += str(i+1) + '. <@' + str(log_data[sorted_authors[i]]['id']) + '>\n'

    target_index = sorted_authors.index(author_name)
    ranking_position = target_index + 1

    tabFields[''] += '**'
    if type == 'rank' :
        title = 'Classement éveil'
    else:
        title = 'Classement ' + type
    color = discord.Color.blue()
    footer = 'Votre classement : ' + str(ranking_position) + '/' + str(len(sorted_authors))
    return create_embed(title=title, color=color, footer=footer, tabFields=tabFields)

def daily_action(author_name, author_icon, global_name):
    if author_name in log_data:
        if 'max_daily' in log_data[author_name]:
            now = datetime.now()
            daily_date_str = log_data[author_name]['last_daily']
            daily_date = datetime.fromisoformat(daily_date_str)
            time_difference = now - daily_date
            if time_difference < timedelta(hours=48):
                log_data[author_name]['max_daily'] += 500
            else:
                log_data[author_name]['max_daily'] = 500
        else:
            log_data[author_name]['max_daily'] = 500

        if 'gold' in log_data[author_name]:
            log_data[author_name]['gold'] += log_data[author_name]['max_daily']
        else:
            log_data[author_name]['gold'] = log_data[author_name]['max_daily']
    else:
        log_data[author_name] = {'max_daily': 500}
        log_data[author_name] = {'gold': log_data[author_name]['max_daily']}

    title = 'Daily Streak ' + str(log_data[author_name]['max_daily']//500) +  ' :fire: !'
    tabFields = {'Vous récupérez : ' : str(log_data[author_name]['max_daily']) + ' :coin:'}
    color = discord.Color.green()
    footer = 'Revenez également demain !'
    return create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, footer=footer, tabFields=tabFields)

def explore_action(author_name, author_icon, global_name):
    rank = log_data[author_name]['rank']
    num = (rank + 1) * 100
    num_90 = (num * 90) // 100
    num_110 = (num * 110) // 100
    alea = random.randint(num_90, num_110)
    
    random_number = random.randint(1, 1000)
    if random_number <= 210:
        title = 'I • L\'Antre de l\'Ours'
        alea = alea + 25 + rank * 40
    else:
        if random_number <= 410:
            title = 'II • La Forêt des Tentations'
            alea = alea + 50 + rank * 90
        else:
            if random_number <= 590:
                title = 'III • Les Grandes Falaises'
                alea = alea + 100 + rank * 140 
            else:
                if random_number <= 750:
                    title = 'IV • Les Profondeurs de la Coupe'
                    alea = alea + 200 + rank * 190
                else:
                    if random_number <= 890:
                        title = 'V • La Mer des Cadavres'
                        alea = alea + 400 + rank * 240
                    else:
                        if random_number <= 970:
                            title = 'VI • La Capitale des Non-Retournés'
                            alea = alea + 800 + rank * 300
                        else:
                            title = 'VII • La Dernière Épreuve'
                            alea = alea + 1600 + rank * 500

    alea = alea * (rank + 1)

    if author_name in log_data:
        if 'gold' in log_data[author_name]:
            log_data[author_name]['gold'] += alea
        else:
            log_data[author_name]['gold'] = alea
    else:
        log_data[author_name] = {'gold': alea}


    tabFields = {'Vous récupérez : ' : str(alea) + ' :coin:'}
    color = discord.Color.green()
    footer = 'Revenez dans 1 heure !'
    return create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, footer=footer, tabFields=tabFields)

def compter_action(author_name, author_icon, global_name, record):
    log_data[author_name]['gold'] += record

    title = 'Pour vos exploits dans #compter !'
    tabFields = {'Vous récupérez : ' : str(record) + ' :coin:'}
    color = discord.Color.green()
    footer = 'Revenez demain !'
    return create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, footer=footer, tabFields=tabFields)

def train_action(author_name, author_icon, global_name):
    level_xp = [500, 600, 720, 864, 1036, 1243, 1492, 1791, 2149, 2578, 3093, 3711, 4453, 5343, 6411, 7693, 9231, 11077, 13293, 15951, 19141, 22969, 27563, 33075, 39690, 47628, 57153, 68584, 82300, 98760, 118512, 142214, 170657, 204788, 245746, 294895, 353873, 424647, 509576, 611491, 733790, 880548, 1056657, 1267989, 1521587, 1825904, 2191085, 2629302, 3155163, 3786195, 4543434, 5452120, 6542544, 7851052, 9421262, 11305514, 13566617, 16279940, 19535928, 23443113, 28131736, 33758083, 40509700, 48611640, 58333968, 70000762, 84000914, 100801096, 120961315, 145153578, 174184293, 209021151, 250825381, 301090457, 361308548, 433570258, 520284309, 624341171, 749209405, 899051286, 1078861543, 1294633852, 1553560622, 1864272746, 2237127295, 2684552754, 3221463305, 3865755966, 4638907159, 5566688591, 6680026309, 8016031570, 9619237884, 11543158461, 13851790153, 16622148183, 19946577820, 23935893384, 28723072061, 34467686474, 41361223769, 49633468522, 59560162226, 71472194671, 85766633605, 102919960326, 123503952391, 148204742869, 177845691442, 213414829731]

    rank = log_data[author_name]['rank']
    num = (rank + 1) * 100
    num_90 = (num * 90) // 100
    num_110 = (num * 110) // 100
    alea = random.randint(num_90, num_110)

    random_number = random.randint(1, 1000)
    if random_number <= 220:
        title = 'I • La Porte de l\'Ouverture'
        alea = alea + 25 + rank * 40
    else:
        if random_number <= 400:
            title = 'II • La Porte de l\'Énergie'
            alea = alea + 50 + rank * 90
        else:
            if random_number <= 560:
                title = 'III • La Porte de la Vie'
                alea = alea + 100 + rank * 140 
            else:
                if random_number <= 700:
                    title = 'IV • La Porte de la Douleur'
                    alea = alea + 200 + rank * 190
                else:
                    if random_number <= 820:
                        title = 'V • La Porte de la Forêt'
                        alea = alea + 400 + rank * 240
                    else:
                        if random_number <= 910:
                            title = 'VI • La Porte de la Vision'
                            alea = alea + 800 + rank * 290
                        else:
                            if random_number <= 970:
                                title = 'VII • La Porte de l\'Insanité'
                                alea = alea + 1600 + rank * 350
                            else:
                                title = 'VIII • La Porte de la Mort'
                                alea = alea + 3200 + rank * 500

    alea = alea * (rank + 1) * 5
    
    now = datetime.now()
    boosted_time = datetime.strptime(log_data[author_name]["xp_boosted"], "%Y-%m-%d %H:%M:%S.%f")
    if boosted_time > now:
        xp_win = alea*2
    else:
        xp_win = alea
    
    log_data[author_name]['level']['xp'] += xp_win
    
    level_up = 0

    for lvl_xp in level_xp[log_data[author_name]['level']['lvl']:]:
        if log_data[author_name]['level']['xp'] > lvl_xp:
            log_data[author_name]['level']['xp'] -= lvl_xp
            log_data[author_name]['level']['lvl'] += 1
            
            if "PointXP" in log_data[author_name]['bag']:
                log_data[author_name]['bag']['PointXP']["quantity"] += 1
            else:
                log_data[author_name]['bag']['PointXP'] = {"quantity": 1, "icon": ":white_flower:"}

            level_up += 1
        else:
            break
        
    gain_xp = f"{alea} :diamond_shape_with_a_dot_inside:"
    player_levelup = f"<@{log_data[author_name]['id']}> + {level_up} level ({log_data[author_name]["level"]["lvl"]})" if level_up > 0 else None

    tabFields = {"Vous gagnez :" : gain_xp}

    if xp_win == alea * 2:
        tabFields["Bonus boost XP :"] = gain_xp
    if player_levelup:
        tabFields["Level UP :"] = player_levelup
    
    color = discord.Color.green()
    footer = 'Revenez dans 3 heures !'
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
    if type == 'level':
        sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x][type]['lvl'], reverse=True)
    else:
        sorted_authors = sorted(filtered_authors, key=lambda x: log_data[x][type], reverse=True)
    target_index = sorted_authors.index(author_name)
    ranking_position = target_index + 1
    return str(ranking_position) + '/' + str(len(sorted_authors))

def purchase_action(author_name, author_icon, global_name, item, quantity):
    title = 'Achat'
    if item in items and 'price' in items[item]:
        if author_name in log_data:
            if 'gold' not in log_data[author_name]:
                log_data[author_name]['gold'] = 0
        else:
            log_data[author_name] = {'gold': 0}

        gold = log_data[author_name]['gold']

        if 'unique' in items[item] or 'requirements' in items[item]:
            quantity = 1

        if gold < items[item]['price'] * quantity:
            manque = items[item]['price'] * quantity - gold
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
                    log_data[author_name]['gold'] = log_data[author_name]['gold'] - items[item]['price'] * quantity
                    if 'stats' in items[item]:
                        if 'pv' in items[item]['stats']:
                            log_data[author_name]['stats']['pv'] += items[item]['stats']['pv'] * quantity
                        if 'for' in items[item]['stats']:
                            log_data[author_name]['stats']['for'] += items[item]['stats']['for'] * quantity
                        if 'def' in items[item]['stats']:
                            log_data[author_name]['stats']['def'] += items[item]['stats']['def'] * quantity
                    tabFields = {'Vous venez d\'acheter : ' : items[item]['icon'] + ' ' + item + " x" + str(quantity)}
                    color = discord.Color.green()

                    materiaux = ['Cuir', 'Fer', 'Argent', 'Mithril', 'Orichalque', 'Adamantium', 'Étherium']
                    if item not in materiaux:
                        if item in log_data[author_name]['bag']:
                            log_data[author_name]['bag'][item]['quantity'] += quantity
                        else:
                            if 'rank' in items[item]:
                                log_data[author_name]['bag'][item] = {'quantity': quantity, 'icon': items[item]['icon'], 'rank': items[item]['rank']}
                            else:
                                log_data[author_name]['bag'][item] = {'quantity': quantity, 'icon': items[item]['icon']}
                else:
                    rank = ['Basique', ':regional_indicator_f:', ':regional_indicator_e:', ':regional_indicator_d:', ':regional_indicator_c:', ':regional_indicator_b:', ':regional_indicator_a:', ':regional_indicator_s:', ':regional_indicator_s: :regional_indicator_s:']
                    tabFields = {'L\'achat est impossible vérifie si vous avez au moins 1 équipement de rang ' + rank[items[item]['requirements']] : ''}
                    color = discord.Color.red()
    else:
        tabFields = {'Vérifiez l\'appélation de ce que vous voulez acheter.' : ''}
        color = discord.Color.red()

    return create_embed(title=title, color=color, author_name=global_name, author_icon=author_icon, tabFields=tabFields)

def combat(mob_name, mob_lvl, total_pv, total_for, total_def, nbr_debuffer):
    if nbr_debuffer > 0:
        debuff = 0.9 ** nbr_debuffer
    else:
        debuff = 1
        
    mob_pv = (mob_lvl * mobs[mob_name]['stats']['pv']) * debuff
    mob_for = (mob_lvl * mobs[mob_name]['stats']['for']) * debuff
    mob_def = (mob_lvl * mobs[mob_name]['stats']['def']) * debuff

    sum_mob_stats = int(mob_pv/250 + mob_for/2 + mob_def/4)
    sum_plaayers_stats = int(total_pv/250 + total_for/2 + total_def/4)
    if sum_mob_stats > sum_plaayers_stats:
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

def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def normalize_text(text):
    text = text.lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

client.run(TOKEN)
