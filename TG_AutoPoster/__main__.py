import argparse
import datetime
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger

from . import AutoPoster, __version__

if os.name != "nt":
    TEMP_DIR = TemporaryDirectory(prefix="TG_AutoPoster")
    CACHE_DIR = Path(TEMP_DIR.name)
else:
    CACHE_DIR = Path.cwd() / ".cache"
CONFIG_PATH = Path.cwd() / "config.yaml"


def create_parser():
    parser = argparse.ArgumentParser(
        prog="TG_AutoPoster",
        description="Telegram Bot for AutoPosting from VK",
        epilog="(C) 2018-2022 Adrian Polyakov\nReleased under the MIT License.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"TG_AutoPoster {__version__}",
    )
    parser.add_argument(
        "-6",
        "--ipv6",
        action="store_true",
        help="Использовать IPv6 при подключении к Telegram (IPv4 по умолчанию)",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=int,
        const=3600,
        default=3600,
        nargs="?",
        help="Проверять новые посты каждые N (по умолчанию 3600) секунд",
        metavar="N",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Абсолютный путь к конфиг файлу бота (по умолчанию {})".format(
            CONFIG_PATH
        ),
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=CACHE_DIR,
        help="Абсолютный путь к папке с кэшем бота (по умолчанию используется временная папка; .cache в Windows)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Режим отладки",
    )
    return parser


if __name__ == "__main__":
    args = create_parser().parse_args()

    logs_dir = args.config.parent.absolute() / "logs"

    if args.debug:
        logger.add(
            logs_dir / "bot_log_{time}_DEBUG.log",
            level="DEBUG",
            backtrace=True,
            diagnose=True,
            rotation="daily",
            retention=2,
        )
    else:
        logger.remove()
        logger.add(
            logs_dir / "bot_log_{time}.log",
            level="INFO",
            rotation="daily",
            retention="3 days",
            compression="zip",
        )

    logger.info("TG AutoPoster запущен")
    logger.debug(
        "Python {}\nTG_AutoPoster {}\nOS: {}\nConfig path: {}\nCache dir: {}\nPassed args:{}",
        sys.version,
        __version__,
        sys.platform,
        args.config,
        args.cache_dir,
        sys.argv[1:],
    )

    client = AutoPoster(
        config_path=args.config,
        logs_dir=logs_dir,
        cache_dir=args.cache_dir,
        ipv6=args.ipv6,
    )

    sleep_env = os.environ.get("TG_SLEEP")
    if sleep_env:
        if sleep_env.isnumeric():
            sleep_env = int(sleep_env)
        else:
            sleep_env = 3600

    scheduler = BackgroundScheduler()
    for domain in client.config.get("domains", {}).keys():
        if client.config["domains"][domain].get("use_long_poll"):
            scheduler.add_job(
                func=client.listen,
                args=(domain,),
            )
    scheduler.add_job(
        func=client.get_new_posts,
        trigger="interval",
        seconds=args.sleep or sleep_env,
        max_instances=1,
        next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=5),
    )
    scheduler.start()
    client.run()
