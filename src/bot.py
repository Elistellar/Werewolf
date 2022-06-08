import logging as log

from discord import Embed
from discord import Game as GameActivity
from discord import Intents, Interaction, PermissionOverwrite
from discord.ext.commands import Bot
from discord import app_commands

from .database import Database
from .lang import Lang
from .settings import Settings

Settings.load()

intents = Intents.default()
intents.message_content = True

bot = Bot(command_prefix='/', intents=intents, owner_id=Settings['owner_id'])

# events
@bot.event
async def on_ready():
    Lang.load(bot)
    Database.load()
    
    await bot.tree.sync()
    
    log.info('Bot ready !')
    
    await bot.change_presence(activity=GameActivity(Settings['activity']))
    
    
# commands
async def update_settings_panel(interaction: Interaction):
    
    game_data = Database.select('games', ['settings_channel_id', 'settings_panel_id', 'werewolves_number', 'villagers_number', 'cupid', 'little_girl', 'hunter', 'thief'], f"owner_id='{interaction.user.id}'")[0]
    
    print(game_data)
    
    settings_channel = interaction.guild.get_channel(game_data['settings_channel_id'])
    settings_panel = settings_channel.get_partial_message(game_data['settings_panel_id'])
    
    players = Database.select('players', ['user_id'], f"game_id='{game_data['id']}'")
    
    await settings_panel.edit(embed=Embed(
        title='Paramètres de la Partie',
        description=Lang.get('settings_description', {
            'werewolves_nb': game_data['werewolves_number'],
            'villagers_nb': game_data['villagers_number'],
            'cupid': game_data['cupid'],
            'little_girl': game_data['little_girl'],
            'hunter': game_data['hunter'],
            'thief': game_data['thief'],
            'players': [player['user_id'] for player in players]
        }),
        color=eval('0x' + Settings['embed_color'][1:])
    ))
    

@bot.tree.command(name='new_game', description='Create a new game.')
async def new_game(interaction: Interaction):
    
    
    # ensure player not already in a game
    player_data = Database.select('players', ['game_id'], f"user_id = '{interaction.user.id}'")
    if len(player_data) > 0:
        game_data = Database.select('games', ['voice_channel_id'], f"id = '{player_data[0]['game_id']}'")[0]
        
        await interaction.response.send_message(Lang['new_already_in_game'].format(game_data['voice_channel_id']), ephemeral=True)
        return
    
    # create a new game
    await interaction.response.send_message(Lang['creating_new_game'], ephemeral=True)
    
    category = await interaction.guild.create_category(
        Lang['category_name'].format(interaction.user.name),
        overwrites= {
            interaction.guild.default_role: PermissionOverwrite(read_messages=False),
            interaction.guild.me: PermissionOverwrite(read_messages=True),
            interaction.user: PermissionOverwrite(read_messages=True),
        }
    )
    settings_channel = await category.create_text_channel(
        Lang['settings_channel_name'],
        overwrites= {
            interaction.guild.default_role: PermissionOverwrite(read_messages=False),
            interaction.guild.me: PermissionOverwrite(read_messages=True),
            interaction.user: PermissionOverwrite(read_messages=True),
        }
    )
    voice_channel      = await category.create_voice_channel(Lang['voice_channel_name'])
    werewolves_channel = await category.create_text_channel(
        Lang['werewolves_channel_name'],
        overwrites= {
            interaction.guild.default_role: PermissionOverwrite(read_messages=False),
            interaction.guild.me: PermissionOverwrite(read_messages=True),
        }
    )
    
    Database.insert('games', {
        'owner_id': interaction.user.id,
        'guild_id': interaction.guild_id,
        'category_id': category.id,
        'settings_channel_id': settings_channel.id,
        'werewolves_channel_id': werewolves_channel.id,
        'voice_channel_id': voice_channel.id,
        'settings_panel_id': None,
        
        'werewolves_number': Settings['default_werewolves_number'],
        'villagers_number': Settings['default_villagers_number'],
        'little_girl': Settings['default_little_girl_presence'],
        'hunter': Settings['default_hunter_presence'],
        'cupid': Settings['default_cupid_presence'],
        'thief': Settings['default_thief_presence'],
        
        'sheriff_user_id': None,
        'night_number': 0,
        'night_state': 0,
        'heal_potion': True,
        'death_potion': True,
    })
    
    game_data = Database.select('games', ['id', 'werewolves_number', 'villagers_number', 'cupid', 'little_girl', 'hunter', 'thief'], f"owner_id = '{interaction.user.id}'")[0]
    
    Database.insert('players', {
        'user_id': interaction.user.id,
        'game_id': game_data['id'],
        'role_id': None,
        'is_alive': True,
        'is_ready': False,
    })  
        
    settings_panel = await settings_channel.send(embed=Embed(
        title=Lang['settings_title'],
        description=Lang.get('settings_description', {
            'werewolves_nb': game_data['werewolves_number'],
            'villagers_nb': game_data['villagers_number'],
            'cupid': game_data['cupid'],
            'little_girl': game_data['little_girl'],
            'hunter': game_data['hunter'],
            'thief': game_data['thief'],
            'players': [interaction.user.id]
        }),
        color=eval('0x' + Settings['embed_color'][1:])
    ))
    
    Database.update('games', {'settings_panel_id': settings_panel.id}, f"id='{game_data['id']}'")
    
    await interaction.followup.edit_message((await interaction.original_message()).id, content=Lang['new_game_created'])

@bot.tree.command(name='stop', description='End the current game')
async def stop(interaction: Interaction):
    game_data = Database.select('games', ['id', 'category_id'], f"owner_id = '{interaction.user.id}'")
    
    if not game_data:
        await interaction.response.send_message(Lang['unexisting_game'], ephemeral=True)
        return

    game_data = game_data[0]

    category = interaction.guild.get_channel(game_data['category_id'])
    for channel in category.channels:
        await channel.delete()
    await category.delete()
    
    Database.delete('games', f"owner_id = '{interaction.user.id}'")
    Database.delete('players', f"game_id = '{game_data['id']}'")
    
    await interaction.response.send_message('Partie stoppée !', ephemeral=True)

@bot.tree.command(name='cupidon', description='Change la présence de Cupidon dans la partie')
@app_commands.rename(presence='présence')
async def cupid(interaction: Interaction, presence: bool):
    
    Database.update('games', {'cupid': presence}, f"owner_id = '{interaction.user.id}'")
    
    await update_settings_panel(interaction)    
    await interaction.response.send_message(Lang['success'], ephemeral=True)
    
@bot.tree.command(name='petite_fille', description='Change la présence de la Petite Fille dans la partie')
@app_commands.rename(presence='présence')
async def little_girl(interaction: Interaction, presence: bool):
    
    Database.update('games', {'little_girl': presence}, f"owner_id = '{interaction.user.id}'")
    
    await update_settings_panel(interaction)    
    await interaction.response.send_message(Lang['success'], ephemeral=True)
    
@bot.tree.command(name='chasseur', description='Change la présence du Chasseur dans la partie')
@app_commands.rename(presence='présence')
async def hunter(interaction: Interaction, presence: bool):
    
    Database.update('games', {'hunter': presence}, f"owner_id = '{interaction.user.id}'")
    
    await update_settings_panel(interaction)    
    await interaction.response.send_message(Lang['success'], ephemeral=True)
    
@bot.tree.command(name='voleur', description='Change la présence du Voleur dans la partie')
@app_commands.rename(presence='présence')
async def thief(interaction: Interaction, presence: bool):
    
    Database.update('games', {'thief': presence}, f"owner_id = '{interaction.user.id}'")
    
    await update_settings_panel(interaction)    
    await interaction.response.send_message(Lang['success'], ephemeral=True)

@bot.tree.command(name='villageois', description='Change le nombre de Villageois dans la partie')
@app_commands.rename(nb='nombre')
async def villagers(interaction: Interaction, nb: int):
    
    if nb < 0:
        await interaction.response.send_message(Lang['negative_number'], ephemeral=True)
        return
    
    Database.update('games', {'villagers_number': nb}, f"owner_id = '{interaction.user.id}'")
    
    await update_settings_panel(interaction)    
    await interaction.response.send_message(Lang['success'], ephemeral=True)
    
@bot.tree.command(name='loups-garous', description='Change le nombre de Loups Garous dans la partie')
@app_commands.rename(nb='nombre')
async def werewolves(interaction: Interaction, nb: int):
    
    if nb < 0:
        await interaction.response.send_message(Lang['negative_number'], ephemeral=True)
        return
    if nb == 0:
        await interaction.response.send_message(Lang['at_least_one_werewolf'], ephemeral=True)
        return
    
    Database.update('games', {'werewolves_number': nb}, f"owner_id = '{interaction.user.id}'")
    
    await update_settings_panel(interaction)    
    await interaction.response.send_message(Lang['success'], ephemeral=True)
