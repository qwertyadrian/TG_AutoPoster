from pathlib import Path
from typing import Union

import yaml
from pyrogram import Client


class AutoPoster(Client):
    def __init__(
        self, config_path: Union[str, Path] = Path("config.yaml"), ipv6: bool = False
    ):
        name = self.__class__.__name__.lower()

        self.config_path = Path(config_path).absolute()

        with self.config_path.open() as stream:
            self.config: dict = yaml.safe_load(stream)

        self.admin_id = self.config.get("settings", {}).get("admins_id", [])

        if self.config.get("proxy"):
            proxy = self.config["proxy"]
            proxy["scheme"] = "socks5"
        else:
            proxy = None

        super().__init__(
            name,
            api_id=self.config["telegram"]["api_id"],
            api_hash=self.config["telegram"]["api_hash"],
            bot_token=self.config["telegram"]["bot_token"],
            proxy=proxy,
            ipv6=ipv6,
            plugins=dict(
                root=f"TG_AutoPoster_v3.plugins",
            ),
        )
