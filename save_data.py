import json
import os


def save_data(guild_id: int, key: str, value: str) -> None:
    if not os.path.exists('saved.json'):
        with open('saved.json', 'w') as f:
            json.dump({}, f)
    with open('saved.json', 'rw') as f:
        saved = json.load(f)
        if str(guild_id) not in saved:
            saved[str(guild_id)] = {}
        saved[str(guild_id)][key] = value
        json.dump(saved, f)


def get_data(guild_id: int, key: str) -> str | None:
    if not os.path.exists('saved.json'):
        with open('saved.json', 'w') as f:
            json.dump({}, f)
    with open('saved.json', 'r') as f:
        saved = json.load(f)
        if str(guild_id) not in saved:
            return None
        return saved[str(guild_id)][key]


class GuildSaves:
    def __init__(self, guild_id):
        self.guild_id = guild_id

    @property
    def selected_server(self) -> int:
        return int(get_data(self.guild_id, 'selected_server') or 0)

    @selected_server.setter
    def selected_server(self, value: int) -> None:
        save_data(self.guild_id, 'selected_server', str(value))

    @property
    def selected_channel_id(self) -> int:
        return int(get_data(self.guild_id, 'selected_channel')) or 0

    @selected_channel_id.setter
    def selected_channel_id(self, value: int) -> None:
        save_data(self.guild_id, 'selected_channel', str(value))
