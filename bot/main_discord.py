"""
API realisation in DISCORD BOT
"""
if __name__ == '__main__':
    import json
    import aiohttp
    import logging

    from discord.ext import commands
    from typing import Optional

    from data import db_session

    from bot.discord_db_models import *

    # CONSTANTS
    with open('CONFIG.json') as f:
        CONFIG = json.load(f)

    HOST, API_VER, BOT_TOKEN = CONFIG['server'], CONFIG['api_ver'], CONFIG['bot_token']
    client = commands.Bot(command_prefix='?')
    logging.basicConfig(filename='bot.log')
    db_session.global_init(f'users.sqlite3')


    @client.event
    async def on_ready():
        logging.debug(f'BOT log on on {client.user.name}')
        print('im ready')


    @client.command()
    async def help(ctx):
        # TODO HELP
        await ctx.channel.send('#TODO HELP')


    @client.command()
    async def set_up_api_key(ctx, api_key):
        session = db_session.create_session()
        # Check if current user already in database
        user: Optional[DiscordUser] = session.query(DiscordUser).filter(DiscordUser.discord_id == ctx.author.id).first()
        if user is None:
            # User not in the base -> create user
            logging.info(f'User with {ctx.author.id} doesnt exist, creating new record')
            user = DiscordUser(discord_id=ctx.author.id, site_api_key=api_key)
            session.merge(user)
            session.commit()
            logging.info(f'Created new instance because user with id didnt exist')
            await ctx.channel.send(f'Your api key been successfully updated')
            await ctx.message.delete()
        else:
            logging.info(f'User already in base, updating existing information')
            user.site_api_key = api_key


    @client.command()
    async def my_api_key(ctx):
        session = db_session.create_session()
        logging.info(f'GET API key from {ctx.author}')
        user: Optional[DiscordUser] = session.query(DiscordUser).filter(DiscordUser.discord_id == ctx.author.id).first()

        if user is None:
            logging.info('user not in database')
            await ctx.author.send('You are not in database')
        else:
            logging.info(f'User in database, sending API key: {user.site_api_key}')
            await ctx.author.send(f'Your API key is {user.site_api_key}')


    @client.command()
    async def project_profile(ctx):
        pass


    @client.command()
    async def get_all_projects(ctx):
        # GET API key of user who requested
        session = db_session.create_session()
        api_key = session.query(DiscordUser.site_api_key).filter(DiscordUser.discord_id == ctx.author.id).first()[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{HOST}/api/v{API_VER}/projects?API_KEY={api_key}') as r:
                if r.status != 200:
                    await ctx.channel.send(f'Got code {r.status}')
                    response = await r.json()
                    await ctx.chanel.send(f'Response message ``{response["message"]}``')
                    logging.info(f'API key = {api_key}, status {r.status}, message {response["message"]}')
                else:
                    await ctx.channel.send(f'```{await r.json()}```')
                    logging.info(f'get_all_projects - OK')


    @client.command()
    async def get_all_users(ctx):
        # GET API key of user who requested
        session = db_session.create_session()
        api_key = session.query(DiscordUser.site_api_key).filter(DiscordUser.discord_id == ctx.author.id).first()[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://{HOST}/api/v{API_VER}/users?API_KEY={api_key}') as r:
                if r.status != 200:
                    await ctx.channel.send(f'Got code {r.status}')
                    response = await r.json()
                    await ctx.chanel.send(f'Response message{response["message"]}')
                    logging.info(f'API key = {api_key}, status {r.status}, message {response["message"]}')
                else:
                    await ctx.channel.send(f'```{await r.json()}```')
                    logging.info(f'get_all_users - OK')


    @client.command()
    async def get_user(ctx, user_id):
        # GET API key of user who requested
        session = db_session.create_session()
        api_key = session.query(DiscordUser.site_api_key).filter(DiscordUser.discord_id == ctx.author.id).first()[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(F'http://{HOST}/api/v{API_VER}/user/?API_KEY={api_key}&user_id={user_id}') as r:
                if r.status != 200:
                    await ctx.channel.send(f'Got code {r.status}')
                    response = await r.json()
                    await ctx.channel.send(f'Response message  ``{response["message"]}``')
                    logging.info(f'API key = {api_key}, status {r.status}, message {response["message"]}')
                else:
                    await ctx.channel.send(f'```{await r.json()}```')
                    logging.info(f'get_user - OK')


    @client.command()
    async def get_project(ctx, project_id):
        # GET API key of user who requested
        session = db_session.create_session()
        api_key = session.query(DiscordUser.site_api_key).filter(DiscordUser.discord_id == ctx.author.id).first()[0]

        async with aiohttp.ClientSession() as session:
            async with session.get(F'http://{HOST}/api/v{API_VER}/project/{project_id}') as r:
                if r.status != 200:
                    await ctx.channel.send(f'Got code {r.status}')
                    response = await r.json()
                    await ctx.chanel.send(f'Response message  ``{response["message"]}``')
                    logging.info(f'API key = {api_key}, status {r.status}, message {response["message"]}')
                else:
                    await ctx.channel.send(f'```{await r.json()}```')
                    logging.info(f'get_user - OK')


    client.run(BOT_TOKEN)
