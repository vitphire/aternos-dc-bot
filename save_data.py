import json
import os

from discord import ApplicationContext


def save_data(guild_id: int, key: str, value: str) -> None:
    filename = os.path.join('saved', f'{guild_id}.json')
    if not os.path.exists('saved'):
        os.mkdir('saved')
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump({}, f)
    with open(filename, 'r') as f:
        saved = json.load(f)
        saved[key] = value
    with open(filename, 'w') as f:
        json.dump(saved, f)


def get_data(guild_id: int, key: str) -> str | None:
    filename = os.path.join('saved', f'{guild_id}.json')
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as f:
        saved = json.load(f)
        return saved.get(key)


class GuildSaves:
    """
    This class is used to save data for a specific guild.
    """

    def __init__(self, ctx: ApplicationContext):
        guild_id = ctx.guild_id
        self.guild_id = guild_id

    @property
    def selected_server(self) -> int:
        return int(get_data(self.guild_id, 'selected_server') or 0)

    @selected_server.setter
    def selected_server(self, value: int) -> None:
        save_data(self.guild_id, 'selected_server', str(value))
