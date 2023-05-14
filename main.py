import asyncio

import discord
from discord import HTTPException, Interaction
from python_aternos import AternosServer, Status, ServerStartError

from aternos_bot import AternosBot
from save_data import *


def nice_list(lines, prefix="") -> str:
    num_width = len(str(len(lines)))
    ls = [f"{prefix}{i + 1: >{num_width}}. {line}" for i, line in enumerate(lines)]
    return '\n'.join(ls)


def default_embed(**kwargs):
    return discord.Embed(colour=discord.Colour.green(), **kwargs)


def main():
    at_bot: AternosBot = AternosBot()

    def selected_server(saved: GuildSaves) -> AternosServer:
        return at_bot.aternos.list_servers()[saved.selected_server]

    def safe_fetch(server: AternosServer, ctx: ApplicationContext) -> AternosServer:
        try:
            server.fetch()
            return server
        except HTTPException as e:
            if e.status == 418:
                # We need to delete the session file and authenticate again
                at_bot.invalidate_session()
                print("Session invalidated, retrying...")
                return selected_server(GuildSaves(ctx))
            else:
                print(f"HTTPException: {e.status=}, {e.code=}, {e.text=}, {e.response=}")
                raise e

    @at_bot.at_command("servers", description="List all servers")
    async def handle_servers(_: discord.ApplicationContext):
        servers = at_bot.aternos.list_servers(cache=False)
        server_list = nice_list([server.address for server in servers])
        server_list = f"```{server_list}```"
        return default_embed(title="Servers", description=server_list)

    @at_bot.at_command("info", description="Prints info about the selected server")
    async def handle_info(ctx: discord.ApplicationContext):
        server = selected_server(GuildSaves(ctx))
        server_address = server.address
        server = safe_fetch(server, ctx)
        try:
            # Colors: 1 = red, 2 = green, 3 = yellow, 4 = blue
            c = {"offline": 1,
                 "error": 1,
                 "online": 2,
                 "starting": 3,
                 "loading": 3,
                 "preparing": 3,
                 "stopping": 4,
                 "saving": 4,
                 "confirm": 1
                 }[server.status]
        except KeyError:
            print(f"Server status code not found for {server.status}")
            c = 0
        server_status = f"\u001b[0;3{c}m{server.status}\u001b[0m"
        server_version = server.software + " " + server.version
        server_info = f"Address: {server_address}\n" \
                      f"Status: {server_status}\n" \
                      f"Version: {server_version}"
        server_info = f"```ansi\n{server_info}```"
        return default_embed(title="Server Info", description=server_info)

    @at_bot.at_command("start", description="Starts the selected server")
    async def handle_start(ctx: discord.ApplicationContext):
        server = selected_server(GuildSaves(ctx))
        server = safe_fetch(server, ctx)
        if server.status_num == Status.on:
            return f"Server is already online at `{server.address}`"
        try:
            server.start()
        except ServerStartError as _e:
            return f"Server failed to start: {_e}"
        r_interaction: Interaction = await ctx.respond("Starting server...")
        while (server.status_num != Status.loading and
               server.status_num != Status.starting and
               server.status_num != Status.on):
            server = safe_fetch(server, ctx)
            await asyncio.sleep(0.5)
        print(f"Server status: {server.status}, {server.status_num}")
        await r_interaction.edit_original_response(content=f"Server (`{server.address}`) is loading...")
        while (server.status_num != Status.starting and
               server.status_num != Status.on):
            server = safe_fetch(server, ctx)
            await asyncio.sleep(0.5)
        print(f"Server status: {server.status}, {server.status_num}")
        await r_interaction.edit_original_response(content=f"Server (`{server.address}`) is starting...")
        while server.status_num != Status.on:
            server = safe_fetch(server, ctx)
            await asyncio.sleep(0.5)
        print(f"Server status: {server.status}, {server.status_num}")
        await r_interaction.followup.send(
            content=f"<@{ctx.author.id}> Server is now online!\n"
                    f"Join now at `{server.address}`")
        pass

    @at_bot.at_command("select", description="Selects a server")
    async def handle_select(ctx: discord.ApplicationContext,
                            server_id: discord.Option(int, description="Server index")):
        server_id = server_id - 1
        if server_id < 0 or server_id >= len(at_bot.aternos.list_servers()):
            await ctx.respond("Invalid server index.\n"
                              "Use `/servers` to list all servers.")
            return
        saves = GuildSaves(ctx)
        saves.selected_server = server_id
        server = selected_server(saves)
        return default_embed(title="Server Selected",
                             description=f"Server {server_id + 1} "
                                         f"(`{server.address}`) selected.")

    @at_bot.event
    async def on_ready():
        print(f"{at_bot.user} has connected to Discord!")
        guilds = nice_list([guild.name for guild in at_bot.guilds], prefix="\t")
        print(f"Guilds: \n{guilds}")

    at_bot.at_run()


if __name__ == '__main__':
    main()
