import os
from functools import wraps

import discord
from discord import HTTPException
from dotenv import load_dotenv
from python_aternos import Client


class AternosBot(discord.Bot):
    """
    This is a wrapper class for discord.py's Bot class.
    It adds some extra functionality that is specific to the Aternos bot.
    """

    @staticmethod
    def get_env(key):
        return os.getenv(key) or os.environ.get(key)

    def __init__(self, sessions_dir=os.getcwd(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        load_dotenv()

        self._dc_token = self.get_env('DISCORD_TOKEN')
        if self._dc_token is None:
            raise Exception('DISCORD_TOKEN is not set')

        self.aternos_username = self.get_env('ATERNOS_USERNAME')
        self.aternos_password = self.get_env('ATERNOS_PASSWORD')
        self.sessions_dir = sessions_dir
        if self.aternos_username is None or self.aternos_password is None:
            raise Exception('ATERNOS_USERNAME or ATERNOS_PASSWORD is not set')

        self.aternos = self.authenticate()

    def at_command(self, name, **kwargs):
        """
        This is a decorator that adds a command to the bot.
        It is a wrapper around the `Bot.command` decorator.
        """

        def decorator(func):
            @wraps(func)
            async def logged_func(ctx, *args, **kwargs_):
                print(f"{func.__name__} was called with args: {args=}, {kwargs_=}")
                try:
                    result = await func(ctx, *args, **kwargs_)
                except Exception as e:
                    await ctx.respond("Handling this command raised an error.\n"
                                      "Contact vitphire#1440 for help.")
                    raise e
                if isinstance(result, discord.Embed):
                    print("Responding with embed:")
                    print(f"\t{result.title=}")
                    print(f"\t{result.description=}")
                    await ctx.respond(embed=result)
                elif isinstance(result, str):
                    print(f"Responding with string: {result=}")
                    await ctx.respond(result)
                else:
                    return result

            return self.command(name=name, **kwargs)(logged_func)

        return decorator

    def at_run(self):
        try:
            self.run(self._dc_token)
        except HTTPException as e:
            print("Discord HTTPException:\n"
                  f"{e.status=}\n"
                  f"{e.code=}\n"
                  f"{e.text=}\n"
                  f"{e.response=}")
            seconds_to_wait = int(e.response.headers["Retry-After"])
            print(f"Wait {seconds_to_wait // 60} minutes and {seconds_to_wait % 60} seconds and try again.")

    def invalidate_session(self):
        os.remove(self.aternos.session_file(self.aternos_username, self.sessions_dir))
        self.aternos = self.authenticate()

    def authenticate(self):
        return Client.from_credentials(self.aternos_username,
                                       self.aternos_password,
                                       sessions_dir=self.sessions_dir)
