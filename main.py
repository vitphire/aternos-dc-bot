import asyncio

import discord
from discord import Bot
from dotenv import load_dotenv
from python_aternos import Client, AternosServer, Status

from save_data import *


def get_env(key):
    return os.getenv(key) or os.environ.get(key)


def nice_list(lines, prefix="") -> str:
    num_width = len(str(len(lines)))
    ls = [f"{prefix}{i + 1: >{num_width}}. {line}" for i, line in enumerate(lines)]
    return '\n'.join(ls)


def default_embed(**kwargs):
    return discord.Embed(colour=discord.Colour.green(), **kwargs)


def main():
    load_dotenv()

    token = get_env('DISCORD_TOKEN')
    if token is None:
        raise Exception('DISCORD_TOKEN is not set')

    aternos_username = get_env('ATERNOS_USERNAME')
    aternos_password = get_env('ATERNOS_PASSWORD')
    if aternos_username is None or aternos_password is None:
        raise Exception('ATERNOS_USERNAME or ATERNOS_PASSWORD is not set')

    bot: Bot = discord.Bot()
    aternos: Client = Client.from_credentials(aternos_username,
                                              aternos_password,
                                              sessions_dir=os.getcwd())

    def current_server(saved: GuildSaves) -> AternosServer:
        return aternos.list_servers(cache=False)[saved.selected_server]

    @bot.command(name="servers", description="List all servers")
    async def handle_servers(ctx: discord.Message):
        servers = aternos.list_servers(cache=False)
        server_list = nice_list([server.address for server in servers])
        server_list = f"```{server_list}```"
        await ctx.respond(embed=default_embed(title="Servers", description=server_list))

    @bot.command(name="info", description="Prints info about the selected server")
    async def handle_info(ctx: discord.ApplicationContext):
        server = current_server(GuildSaves(ctx))
        server.fetch()
        server_address = server.address
        try:
            # Colors: 1 = red, 2 = green, 3 = yellow, 4 = blue
            c = {Status.off: 1,
                 Status.on: 2,
                 Status.starting: 3,
                 Status.shutdown: 4,
                 Status.loading: 3,
                 Status.error: 1,
                 Status.preparing: 3,
                 Status.confirm: 1
                 }[server.status_num]
        except ValueError:
            print(f"Server status code not found for {server.status}")
            c = 0
        server_status = f"\u001b[0;3{c}m{server.status}\u001b[0m"
        server_version = server.software + " " + server.version
        server_info = f"Address: {server_address}\n" \
                      f"Status: {server_status}\n" \
                      f"Version: {server_version}"
        server_info = f"```ansi\n{server_info}```"
        await ctx.respond(embed=default_embed(title="Server Info", description=server_info))
        pass

    @bot.command(name="start", description="Starts the selected server")
    async def handle_start(ctx: discord.ApplicationContext):
        server = current_server(GuildSaves(ctx))
        server.start()
        await ctx.respond("Starting server...")
        while server.status_num != Status.starting:
            server.fetch()
            await asyncio.sleep(0.5)
        await ctx.respond(f"Server (`{server.address}`) is starting...")
        while server.status_num != Status.on:
            server.fetch()
            await asyncio.sleep(0.5)
        await ctx.respond(f"<@{ctx.author.id}> Server started!\n"
                          f"Join now at `{server.address}`")
        pass

    @bot.command(name="select", description="Selects a server")
    async def handle_select(ctx: discord.ApplicationContext,
                            server_id: discord.Option(int, description="Server index")):
        server_id = server_id - 1
        if server_id < 0 or server_id >= len(aternos.list_servers(cache=False)):
            await ctx.respond("Invalid server index.\n"
                              "Use `/servers` to list all servers.")
            return
        saves = GuildSaves(ctx)
        saves.selected_server = server_id
        server = current_server(saves)
        await ctx.respond(embed=default_embed(title="Server Selected",
                                              description=f"Server {server_id + 1} "
                                                          f"(`{server.address}`) selected."))

    @bot.event
    async def on_ready():
        print(f"{bot.user} has connected to Discord!")
        guilds = nice_list([guild.name for guild in bot.guilds], prefix="\t")
        print(f"Guilds: \n{guilds}")

    bot.run(token)


if __name__ == '__main__':
    main()
