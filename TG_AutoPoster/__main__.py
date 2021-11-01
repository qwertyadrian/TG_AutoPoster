from loguru import logger as log
from .TG_AutoPoster import AutoPoster, create_parser
import os


if __name__ == "__main__":
    args = create_parser().parse_args()
    if args.debug:
        log.add("./logs/bot_log_DEBUG.log", level="DEBUG", rotation="5 MB")
    else:
        log.remove()
        log.add("./logs/bot_log_{time}.log")
    log.info("Начало работы.")
    autoposter = AutoPoster(
        config_path=args.config, cache_dir=args.cache_dir, ipv6=args.ipv6
    )
    if args.loop or args.sleep:
        sleep_time = args.sleep if args.sleep else 3600
        log.info(
            "Программе был передан аргумент --loop (-l). "
            "Запуск бота в бесконечном цикле."
        )
        autoposter.infinity_run(interval=sleep_time)
    elif os.getenv("TG_SLEEP") or os.getenv("TG_LOOP"):
        try:
            sleep_time = int(os.getenv("TG_SLEEP"))
        except ValueError:
            log.warning(
                "Переменная окружения TG_SLEEP задана неверно, "
                "используется значение 3600"
            )
            sleep_time = 3600
        log.info(
            "При запуске программы была найдена переменная окружения TG_LOOP. "
            "Запуск бота в бесконечном цикле."
        )
        autoposter.infinity_run(interval=sleep_time)
    else:
        autoposter.run()
    log.info("Работа завершена. Выход.")
