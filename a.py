import discord
import os

TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Bot is ready.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!daily'):
        
        embed = create_embed('titre', 'desc', discord.Color.red(), 'author_name', 'https://www.manga-city.fr/wp-content/uploads/2022/02/Natsu-Fairy-Tail.jpg', 'https://www.manga-city.fr/wp-content/uploads/2022/02/Natsu-Fairy-Tail.jpg', 'footer', {'1': '2', '3': '4', '5': '6'})
        await message.channel.send(embed=embed)

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
    
    if author_name is not None and author_icon is not None:
        embed.set_author(name = author_name, icon_url = author_icon)  

    if footer is not None:
        embed.set_footer(text = footer)

    return embed

client.run(TOKEN)
