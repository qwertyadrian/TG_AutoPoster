from loguru import logger as log
from .TG_AutoPoster import AutoPoster, create_parser


if __name__ == "__main__":
    args = create_parser().parse_args()
    if args.debug:
        log.add("./logs/bot_log_DEBUG.log", level="DEBUG", rotation="5 MB")
    else:
        log.remove()
        log.add("./logs/bot_log_{time}.log")
    log.info("Начало работы.")
    autoposter = AutoPoster(config_path=args.config, cache_dir=args.cache_dir, ipv6=args.ipv6)
    autoposter.IGNORE_ERRORS = args.ignore_errors
    if args.loop or args.sleep:
        sleep_time = args.sleep if args.sleep else 3600
        log.info("Программе был передан аргумент --loop (-l). Запуск бота в бесконечном цикле.")
        autoposter.infinity_run(interval=sleep_time)
    else:
        autoposter.run()
    log.info("Работа завершена. Выход.")
