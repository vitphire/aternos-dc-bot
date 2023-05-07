from functools import wraps

import discord

from save_data import GuildSaves


class AternosBot(discord.Bot):
    """
    This is a wrapper class for discord.py's Bot class.
    It adds some extra functionality that is specific to the Aternos bot.
    """

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
