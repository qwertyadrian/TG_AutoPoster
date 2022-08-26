from configparser import ConfigParser
from pathlib import Path


def ini_to_dict(config_path: Path) -> dict:
    config = ConfigParser()
    config.read(config_path)

    result = {
        "vk": {},
        "telegram": {},
        "settings": {},
        "domains": {},
    }

    for option in config.options("global"):
        if option == "login":
            result["vk"][option] = config.get("global", option)
        elif option == "pass":
            result["vk"]["password"] = config.get("global", option)
        elif option == "token":
            result["vk"][option] = config.get("global", option)
        else:
            result["settings"][option] = determine_type(
                config, "global", option
            )

    for option in config.options("pyrogram"):
        result["telegram"][option] = determine_type(config, "pyrogram", option)

    if config.has_section("proxy"):
        for option in config.options("proxy"):
            result["proxy"][option] = determine_type(config, "proxy", option)

    for section in (
        config.sections()[3:]
        if config.has_section("proxy")
        else config.sections()[2:]
    ):
        result["domains"][section] = {}
        for option in config.options(section):
            result["domains"][section][option] = determine_type(
                config, section, option
            )

    return result


def determine_type(config: ConfigParser, section: str, option: str):
    value = config.get(section, option)
    if option == "send_reposts":
        if value in ("yes", "True", "all", "2"):
            value = True
        elif value in ("no", "False", "0"):
            value = False
        else:
            value = "post_only"
    elif option == "what_to_send":
        value = value.split(",")
    elif value.isdigit() or value[1:].isdigit():
        value = int(value)
    elif value in ("yes", "True"):
        value = True
    elif value in ("no", "False"):
        value = False
    return value
