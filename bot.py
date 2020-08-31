import discord
from discord.ext import commands
from disputils import BotEmbedPaginator
import json

import processing
from scraping import HandSpeak, LifePrint
import settings
from connections import query_database
    
def get_prefix(bot, message):
    default_prefix = settings.command_prefix
    if not message.guild:
        return commands.when_mentioned_or(default_prefix)(bot, message)

    guild_id = str(message.guild.id)
    
    query = f'''
    SELECT prefix FROM prefixes
    WHERE guild = '{guild_id}'
    '''
    rows = query_database(query)
    if not rows:
        return commands.when_mentioned_or(default_prefix)(bot, message)
    
    prefix = rows[0][0]
    return commands.when_mentioned_or(prefix)(bot, message)

client = commands.Bot(command_prefix=get_prefix)
client.remove_command('help')

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    prefix = settings.command_prefix
    await client.change_presence(activity=discord.Game(f"{prefix}help"))

@client.event
async def on_guild_remove(guild):
    query = f'''
    DELETE FROM prefixes WHERE guild = '{str(guild.id)}'
    '''
    query_database(query)

@commands.has_permissions(administrator=True)
@client.command()
async def setprefix(ctx, prefix):
    query = '''
    INSERT INTO prefixes(guild, prefix) 
    VALUES(%s, %s)
    ON CONFLICT(guild)
    DO UPDATE SET prefix = EXCLUDED.prefix;
    '''
    query_database(query, (str(ctx.guild.id), prefix))
    await ctx.send(f'Prefix changed to: {prefix}')

@setprefix.error
async def setprefix_error(error, ctx):
    if isinstance(error, commands.MissingPermissions):
        text = "Sorry {}, you do not have permissions to do that!".format(ctx.message.author)
        await ctx.send(text)

@client.command()
async def help(ctx):
    command_prefix = ctx.prefix
    commands = {
        "setprefix": f"Usage: `{command_prefix}setprefix ?` | Sets the prefix for bot commands.",
        "sign":f"Usage: `{command_prefix}sign dog` or `{command_prefix}sign lp dog` | Searches handspeak.com, lifeprint.com and google for the ASL sign. Can search handspeak or lifeprint specifically as well.",
        "random":f"Usage: `{command_prefix}random` or `{command_prefix}rv` | Gets a random video from lifeprint.com.",
        "wotd": f"Usage: `{command_prefix}wotd` | Gets the Word of the Day from handspeak.com.",
        "fingers":f"Usage: `{command_prefix}fingers` or `{command_prefix}fs` | Shows the ASL alphabet and resources for fingerspelling.",
        "handshapes":f"Usage: `{command_prefix}handshapes B`, `{command_prefix}handshapes`, `{command_prefix}hs`| Shows handshapes guide from Lifeprint.com"
    }
    
    embed = discord.Embed(
        title = "Commands",
        colour=discord.Colour.orange()
    )
    for command in commands:
        embed.add_field(name=command_prefix+command,value = commands[command], inline=False)
    embed.add_field(name="Support Server", value = "https://discord.gg/8tHa6cb")
    embed.add_field(name = "Invite me to your server", value = "[Use this invite link](https://discord.com/oauth2/authorize?client_id=676113360642899988&scope=bot&permissions=93248)")
    await ctx.send(embed = embed)

@client.command(aliases=['rv'])
async def random(ctx):
    lp = LifePrint()
    await ctx.send(lp.randomVid())

@client.command()
async def sign(ctx, *args):
    valid_lp_args = ['lp','lifeprint']
    valid_hs_args = ['hs','handspeak']
    site = ''

    if args == ():
        raise commands.UserInputError

    if args[0] in valid_lp_args or args[0] in valid_hs_args:
        site = args[0]
        search_input = ' '.join(args[1:])
    else:
        search_input = ' '.join(args[:])
    
    if site in valid_lp_args:
        lp = LifePrint()

        results = lp.search(search_input)
        embeds = processing.embeds_generator(results, search_input)

        if len(embeds) == 1:
            await ctx.send(embed=embeds[0])
        else:
            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
    elif site in valid_hs_args:
        hs = HandSpeak()
        search_results = hs.search(search_input)
        num_pages = search_results['numPages']

        if num_pages > 1:
            embeds = []
            current_page = 1
            for i in range(num_pages):#pylint: disable=unused-variable
                embeds.append(hs.makeSearchEmbed(search_results['queryResults'], search_input))
                current_page+=1
                search_results = hs.search(search_input, current_page=current_page)

            paginator = BotEmbedPaginator(ctx, embeds)
            await paginator.run()
            
        else:
            embed = hs.makeSearchEmbed(search_results['queryResults'], search_input)
            await ctx.send(embed=embed)
    else:
        lp = LifePrint()
        hs = HandSpeak()

        results_lp = lp.search(search_input)
        results_hs = hs.search(search_input)

        #if len(results_lp) > 10 or results_hs['numPages'] > 1:
        #    embeds = []
            # pagination

        list_string_lp = processing.search_result_list(results_lp)
        list_string_hs = results_hs['queryResults']

        query_formatted = '+'.join(search_input.split())

        embed = discord.Embed(
            title=f"Search results: {search_input}",
            colour=discord.Colour.red()
        )

        embed.add_field(name='Lifeprint.com',value=list_string_lp, inline=True)
        embed.add_field(name='Handspeak.com',value=list_string_hs, inline=True)
        embed.add_field(name='Google', value=f'[See Google search results >>](https://www.google.com/search?hl=en&q=ASL+sign+for+{query_formatted})', inline=False)

        await ctx.send(embed=embed)

@sign.error
async def sign_error(ctx, error):
    prefix = ctx.prefix
    if isinstance(error, commands.UserInputError):
        await ctx.send(f"Please specify words to search. Eg. `{prefix}sign dog`")

@client.command()
async def wotd(ctx):
    hs = HandSpeak()
    wotd_video = hs.wordOfTheDay()
    await ctx.send(wotd_video)

@client.command(aliases=['fingerspelling','fs','alphabet'])
async def fingers(ctx):
    embed = discord.Embed(
        title="ASL Fingerspelling",
        description="[Fingerspelling practice and more ►](https://www.lifeprint.com/asl101/fingerspelling/index.htm)",
        colour = discord.Colour.red()
    )
    embed.set_footer(text="Lifeprint.com")
    embed.set_image(url="https://www.lifeprint.com/asl101/fingerspelling/images/abc1280x960.png")
    await ctx.send(embed=embed)

@client.command(aliases=['handshape','hs'])
async def handshapes(ctx, *args):
    input = ' '.join(args[:])
    command_prefix = ctx.prefix
    if not args:
        embed = discord.Embed(
            title="All Handshapes",
            description="A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z, BENT V, BENT HAND, CLAW HAND, CLOSED HAND, CURVED HAND, HORNS, INDEX, OPEN HAND",
            url = "https://www.lifeprint.com/asl101/pages-layout/handshapes.htm",
            colour=discord.Colour.red()
        )
        embed.set_footer(text=f"Tip: You can also show a specific handshape Eg. {command_prefix}handshape horns")
        await ctx.send(embed=embed)
        return

    with open("handshapes.json","r") as f:
        h = json.loads(f.read())
    
    shape = input.upper()
    handshapes = h[0]

    if shape not in handshapes.keys():
        raise commands.BadArgument
    
    embeds = []
    for s in handshapes[shape]:
        version = s['version']
        description = s['description']
        embed = discord.Embed(
            title = f"{shape} - {version}",
            description = description,
            url = "https://www.lifeprint.com/asl101/pages-layout/handshapes.htm",
            colour = discord.Colour.red()
        )
        embed.set_image(url=s['img_url'])
        embeds.append(embed)
    paginator = BotEmbedPaginator(ctx, embeds)
    await paginator.run()

@handshapes.error
async def handshapes_error(ctx, error):
    prefix = ctx.prefix
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"Please enter a valid handshape. Enter {prefix}handshapes to see all shapes.")


client.run(settings.token)