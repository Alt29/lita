from pickle import FALSE
import discord
import json
from datetime import datetime, timedelta
import os

TOKEN = os.getenv('TOKEN')

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


@client.event
async def on_ready():
    print("Bot is ready.")


@client.event
async def on_message(message):
    updated = False
    if message.author == client.user:
        return

    if message.content.startswith("!"):
        if message.author.name not in log_data:
            log_data[message.author.name] = {"rank": 0, "gold": 0, "!daily": "2024-01-01 11:11:11.111111", "bag": {}, "stats": {"pv": 1000, "for": 10, "def": 10}}
            updated = True

    if message.content.startswith("!info"):
        embed = info_action()
        await message.channel.send(embed=embed)

    if message.content.startswith("!gold"):
        embed = me_action(message.author.name, message.author.avatar, message.author.global_name, 'gold')
        await message.channel.send(embed=embed)
        updated = True

    if message.content.startswith("!daily"):
        if await time_command(message, "!daily", 1):
            embed = daily_action(message.author.name, message.author.avatar, message.author.global_name)
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
        '!market :' : 'Pour acheter de quoi devenir plus fort.',
        '!top-gold :' : 'Pour voir le classement en Gold.',
        '!top-rank :' : 'Pour voir le classement en Rank.',
        '!bag :' : 'Pour voir ce que vous avez dans votre sac.',
        '!purchase :' : 'Pour acheter un item au market.',
        '!awaken :' : '[En travaux]',
        '!dungeon :' : '[En travaux]',
    }
    color = discord.Color.blue()
    title = 'Informations'
    return create_embed(title=title, color=color, tabFields=tabFields)

def market_action():
    base_items = ':billed_cap: Casquette • Def+1 • 500 :coin:\n:shirt: T-shirt • Def+2 • 1000 :coin:\n:jeans: Jean • Def+2 • 1000 :coin:\n:athletic_shoe: Baskets • Def+1 • 500 :coin:\n:dagger: Dague • For+3 • 1500 :coin:'
    material_items = ':regional_indicator_s: Étherium • 360000 :coin:\n:regional_indicator_a: Adamantium • 120000 :coin:\n:regional_indicator_b: Orichalque • 40000 :coin:\n:regional_indicator_c: Mithril • 13000 :coin:\n:regional_indicator_d: Argent • 4500 :coin:\n:regional_indicator_e: Fer • 1500 :coin:\n:regional_indicator_f: Cuir • 500 :coin:'
    rune_items = ':fire: Feu • For+1 • 5000 :coin:\n:seedling: Terre • Def+1 • 5000 :coin:\n:droplet: Eau • PV+100 • 5000 :coin:'
    rank_items = ':Legendaire: Légendaire • 500000 :coin:\n:Epique: Épique • 50000 :coin:\n:Rare: Rare • 5000 :coin:'
    
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

    cooldown = timedelta(seconds=cooldown)
    
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
            tabFields = {'Rank :' : rank[res], 'Stats :' : '', 'PV : ' + str(log_data[author_name]['stats']['pv']) + ' :hearts:': '', 'For : ' + str(log_data[author_name]['stats']['for']) + ' :crossed_swords:' : '', 'Def : ' + str(log_data[author_name]['stats']['def']) + ' :shield:': ''}
            color = discord.Color.dark_purple()
        else:
            bag = ''
            if type == 'bag':
                if res != {}:
                    for item in res:
                        if 'rank' in log_data[author_name][type][item] and log_data[author_name][type][item]['rank'] > 0:
                            bag += log_data[author_name][type][item]['icon'] + rank[log_data[author_name][type][item]['rank']] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n'
                        else:
                            bag += log_data[author_name][type][item]['icon'] + ' ' + item + ' • ' + str(log_data[author_name][type][item]['quantity']) + '\n'
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
                    if 'T-shirt' in log_data[author_name]['bag'] and log_data[author_name]['bag']['T-shirt']['rank']  == items[item]['requirements']:
                        log_data[author_name]['bag']['T-shirt']['rank'] += 1
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

client.run(TOKEN)
